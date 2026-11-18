#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/combine-wdb.py (stdlib unittest)."""
import importlib.util
import os
import struct
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "combine-wdb.py"


def load_module():
    spec = importlib.util.spec_from_file_location("combine_wdb", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cw = load_module()


def quest_wdb(path, records):
    """Write a minimal WQST file: records is a list of (id, text)."""
    header = b"TSQW" + struct.pack("<I", 70938) + b"enUS" + struct.pack("<II", 0, 0) + b"\0" * 4
    body = b""
    for rid, text in records:
        blob = struct.pack("<I", 0) + text.encode("utf-8") + b"\0"
        body += struct.pack("<II", rid, len(blob)) + blob
    with open(path, "wb") as fh:
        fh.write(header + body + b"\0" * 8)


LONG_A = "A long quest text about wolves that is definitely over fifty characters."
LONG_B = "A different long quest text about bears that is also over fifty characters."


class CombineLinesTest(unittest.TestCase):
    def test_id_dedupe_keeps_first(self):
        a = "id\ttext\n1\tfirst\n2\tsecond\n"
        b = "id\ttext\n2\tother\n3\tthird\n"
        header, rows, removed = cw.combine_lines("id\ttext", [a, b], "id")
        self.assertEqual(header, "id\ttext")
        self.assertEqual(rows, ["1\tfirst", "2\tsecond", "3\tthird"])
        self.assertEqual(removed, 1)

    def test_line_dedupe_keeps_same_id_with_other_name(self):
        # Game object entry ids repeat, so only identical rows are removed.
        a = "id\tname\textra\n5\tPoster A\t\n"
        b = "id\tname\textra\n5\tPoster B\t\n5\tPoster A\t\n"
        _, rows, removed = cw.combine_lines("id\tname\textra", [a, b], "line")
        self.assertEqual(rows, ["5\tPoster A\t", "5\tPoster B\t"])
        self.assertEqual(removed, 1)

    def test_header_only_block_gives_no_rows(self):
        _, rows, removed = cw.combine_lines("id\ttext", ["id\ttext\n"], "id")
        self.assertEqual((rows, removed), ([], 0))


class EndToEndTest(unittest.TestCase):
    def test_two_folders_are_combined(self):
        with tempfile.TemporaryDirectory() as tmp:
            one = os.path.join(tmp, "one")
            two = os.path.join(tmp, "two")
            out = os.path.join(tmp, "out")
            os.makedirs(one)
            os.makedirs(two)
            quest_wdb(os.path.join(one, "a.wdb"), [(1, LONG_A), (2, LONG_A)])
            quest_wdb(os.path.join(two, "b.wdb"), [(2, LONG_B), (3, LONG_B)])

            cw.main([one, two, "--out-dir", out])

            with open(os.path.join(out, "questcache-en.tsv"), encoding="utf-8") as fh:
                lines = fh.read().split("\n")
            self.assertEqual(lines[0], "id\ttext")
            ids = [line.split("\t")[0] for line in lines[1:] if line]
            self.assertEqual(ids, ["1", "2", "3"])
            self.assertIn(LONG_A, lines[2])  # id 2 keeps the first folder's text

    def test_recursive_reads_subfolders(self):
        with tempfile.TemporaryDirectory() as tmp:
            sub = os.path.join(tmp, "1")
            out = os.path.join(tmp, "out")
            os.makedirs(sub)
            quest_wdb(os.path.join(sub, "questcache.wdb"), [(7, LONG_A)])

            with self.assertRaises(SystemExit):
                cw.main([tmp, "--out-dir", out])  # not found without -r

            cw.main([tmp, "-r", "--out-dir", out])
            with open(os.path.join(out, "questcache-en.tsv"), encoding="utf-8") as fh:
                self.assertIn("7\t" + LONG_A, fh.read())


if __name__ == "__main__":
    unittest.main()
