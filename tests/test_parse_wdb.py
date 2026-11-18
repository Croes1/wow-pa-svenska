#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the WDB cache parser."""
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "parse-wdb.py"


def make_cache(magic, records=()):
    header = magic.encode("ascii")[::-1] + struct.pack("<I", 70938) + b"SUne" + b"\0" * 12
    body = b"".join(
        struct.pack("<II", record_id, len(blob)) + blob
        for record_id, blob in records
    )
    return header + body + b"\0" * 8


class ParseWdbTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def run_parser(self, magic, records=()):
        cache_path = self.root / "cache.wdb"
        output_path = self.root / "cache.tsv"
        cache_path.write_bytes(make_cache(magic, records))
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(cache_path), "tsv", str(output_path)],
            capture_output=True,
            text=True,
        )
        return result, output_path

    def test_page_text_records_export_page_id_and_text(self):
        blob = struct.pack("<III", 2013, 2014, 0) + b"A page of lore.\0"
        result, output_path = self.run_parser("WPTX", [(2013, blob)])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(output_path.read_text(encoding="utf-8"), "id\ttext\n2013\tA page of lore.\n")

    def test_gameobject_records_remain_supported(self):
        blob = struct.pack("<II", 0, 734) + b"Old Iron Gate\0"
        result, output_path = self.run_parser("WGOB", [(15, blob)])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(output_path.read_text(encoding="utf-8"), "id\tname\textra\n734\tOld Iron Gate\n")

    def test_empty_npc_and_petition_caches_export_headers(self):
        for magic in ("WNPC", "WPTN"):
            with self.subTest(magic=magic):
                result, output_path = self.run_parser(magic)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(output_path.read_text(encoding="utf-8"), "id\ttext\n")

    def test_nonempty_npc_and_petition_caches_fail_clearly(self):
        for magic in ("WNPC", "WPTN"):
            with self.subTest(magic=magic):
                result, _ = self.run_parser(magic, [(1, b"unknown payload")])
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("record format is not supported", result.stderr)

    def test_unknown_magic_is_rejected(self):
        result, _ = self.run_parser("WXYZ")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported cache magic: WXYZ", result.stderr)


if __name__ == "__main__":
    unittest.main()
