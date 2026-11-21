#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/dump-runtime.lua (needs lua5.1; skipped with a reason if missing)."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "dump-runtime.lua"
LUA = shutil.which("lua5.1")

CORE = 'local ADDON, WPS = ...\nWPS.L = { quest = {}, npc = {}, ui = {} }\n'
TOC = "## Interface: 16001\n\nCore.lua\nData\\A.lua\nData\\B.lua\nQuest.lua\n"


@unittest.skipUnless(LUA, "lua5.1 is not installed; dump-runtime.lua cannot be tested")
class DumpRuntimeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addon = Path(self.tmp.name)
        (self.addon / "Data").mkdir()
        self.write("Core.lua", CORE)
        self.write("wow_pa_svenska.toc", TOC)

    def write(self, rel, text):
        (self.addon / rel).write_bytes(text.encode("utf-8"))

    def dump(self, check=True):
        return subprocess.run([LUA, str(SCRIPT), str(self.addon)], capture_output=True, check=check)

    def lines(self):
        return self.dump().stdout.decode("utf-8").splitlines()

    def test_numeric_and_string_keys_are_distinct(self):
        self.write("Data/A.lua", 'local _, WPS = ...\nWPS.L.npc = { [123]="a", ["123"]="b" }\n')
        self.write("Data/B.lua", "local _, WPS = ...\n")
        self.assertEqual(self.lines(), ["npc\tn\t123\t=\ts\ta", "npc\ts\t123\t=\ts\tb"])

    def test_numbers_sort_numerically_before_strings(self):
        self.write("Data/A.lua", 'local _, WPS = ...\nWPS.L.npc = { [10]="x", [9]="y", ["a"]="z" }\n')
        self.write("Data/B.lua", "local _, WPS = ...\n")
        self.assertEqual([l.split("\t")[1:3] for l in self.lines()], [["n", "9"], ["n", "10"], ["s", "a"]])

    def test_real_and_escaped_line_breaks_differ(self):
        # Lua "\n" is a real line break; Lua "\\n" is backslash + n.
        self.write("Data/A.lua", 'local _, WPS = ...\nWPS.L.ui = { ["real"]="a\\r\\nb\\tc", ["lit"]="a\\\\r\\\\nb" }\n')
        self.write("Data/B.lua", "local _, WPS = ...\n")
        got = {l.split("\t")[2]: l.split("\t")[5] for l in self.lines()}
        self.assertEqual(got["real"], "a\\r\\nb\\tc")
        self.assertEqual(got["lit"], "a\\\\r\\\\nb")
        self.assertNotEqual(got["real"], got["lit"])

    def test_control_characters_and_utf8(self):
        self.write("Data/A.lua", 'local _, WPS = ...\nWPS.L.ui = { x="\\1åäö\\127" }\n')
        self.write("Data/B.lua", "local _, WPS = ...\n")
        self.assertEqual(self.lines(), ["ui\ts\tx\t=\ts\t\\x01åäö\\x7F"])

    def test_structured_entries_and_nested_arrays(self):
        self.write("Data/A.lua", 'local _, WPS = ...\nWPS.L.quest = { [5]={t="T", o="O", l={"one","two"}} }\n')
        self.write("Data/B.lua", "local _, WPS = ...\n")
        self.assertEqual(self.lines(), [
            "quest\tn\t5\tl[1]\ts\tone",
            "quest\tn\t5\tl[2]\ts\ttwo",
            "quest\tn\t5\to\ts\tO",
            "quest\tn\t5\tt\ts\tT",
        ])

    def test_files_load_in_toc_order_and_later_files_see_earlier_ones(self):
        self.write("Data/A.lua", 'local _, WPS = ...\nWPS.L.npc[1] = "first"\n')
        self.write("Data/B.lua", 'local _, WPS = ...\nWPS.L.npc[1] = WPS.L.npc[1] .. "+second"\n')
        self.assertEqual(self.lines(), ["npc\tn\t1\t=\ts\tfirst+second"])

    def test_only_data_files_from_toc_are_loaded(self):
        self.write("Data/A.lua", "local _, WPS = ...\n")
        self.write("Data/B.lua", "local _, WPS = ...\n")
        self.write("Data/Unlisted.lua", 'local _, WPS = ...\nWPS.L.npc[1] = "x"\n')
        self.write("Quest.lua", "this is not valid lua (it needs the game)\n")
        self.assertEqual(self.lines(), [])

    def test_output_is_deterministic(self):
        entries = ",".join(f'["k{i}"]="v{i}"' for i in range(300))
        self.write("Data/A.lua", f"local _, WPS = ...\nWPS.L.ui = {{ {entries} }}\n")
        self.write("Data/B.lua", "local _, WPS = ...\n")
        self.assertEqual(self.dump().stdout, self.dump().stdout)

    def test_unexpected_input_fails_instead_of_dumping_partial_data(self):
        self.write("Data/B.lua", "local _, WPS = ...\n")
        for name, body in {
            "syntax error": "WPS.L.npc = {",
            "runtime error": "error('boom')",
            "extra WPS key": "local _, WPS = ...\nWPS.other = {}",
            "nested too deep": "local _, WPS = ...\nWPS.L.npc[1] = { a = { b = { c = 1 } } }",
            "function value": "local _, WPS = ...\nWPS.L.npc[1] = function() end",
        }.items():
            with self.subTest(name):
                self.write("Data/A.lua", body)
                result = self.dump(check=False)
                self.assertEqual(result.returncode, 1)
                self.assertIn(b"dump-runtime:", result.stderr)

    def test_missing_core_init_fails(self):
        self.write("Core.lua", "-- no initialiser here\n")
        self.write("Data/A.lua", "local _, WPS = ...\n")
        self.write("Data/B.lua", "local _, WPS = ...\n")
        self.assertEqual(self.dump(check=False).returncode, 1)

    def test_real_repository_dump_is_stable_and_complete(self):
        first = subprocess.run([LUA, str(SCRIPT), str(ROOT)], capture_output=True, check=True).stdout
        second = subprocess.run([LUA, str(SCRIPT), str(ROOT)], capture_output=True, check=True).stdout
        self.assertEqual(first, second)
        tables = {line.split(b"\t", 1)[0] for line in first.splitlines()}
        for name in (b"quest", b"npc", b"item", b"spell", b"gossip", b"zone", b"ui", b"qtext"):
            self.assertIn(name, tables)
        self.assertTrue(all(len(l.split(b"\t")) == 6 for l in first.splitlines()))


if __name__ == "__main__":
    unittest.main()
