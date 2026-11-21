#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/datalua.py: reading and editing the real Data/*.lua formats."""
import importlib.util
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LUA = shutil.which("lua5.1")


def load_module():
    spec = importlib.util.spec_from_file_location("datalua", ROOT / "tools" / "datalua.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dl = load_module()

HEAD = "-- header comment åäö\nlocal _, WPS = ...\n"

QUEST = (HEAD + "WPS.L.quest = {\n"
         '[2]={t="Sharptalons klo",d="Rad ett.\\n\\nRad två med \\"citat\\" och \\\\ snedstreck.",l={"Ta klon."}},\n'
         '[5]={t="Kort",c="Belöning",l={"a","b","c"}},\n'
         '[99]={t="Spaced", o="Mål", d="Text"}, -- merged style\n'
         "\n"
         "-- section comment\n"
         '[100]={o="Bara mål"},\n'
         "}\n")
ITEM = (HEAD + "WPS.L.item = {\n"
        '[25]={n="Slitet kortsvärd"},\n'
        '[287505]={h=3305331836,n="Mört löparkött",d="Kyle skulle njuta."},\n'
        "}\n")
NPC = HEAD + 'WPS.L.npc = {\n[3]="Köttätare",\n[30]="Skogsspindel",\n}\n'
GOSSIP = HEAD + 'WPS.L.gossip = {\n["100_094194f4"]="Var försiktig.",\n["12_2c8ce38d"]="Stridsmästare",\n}\n'
UI = (HEAD + "WPS.L.ui = {\n"
      '["Zebra"]="Sebra",\n'
      '["Apple"]="Äpple",\n'
      "\n"
      "---------------------------------------------------------------------------\n"
      "-- A section\n"
      '["Maximum"]="Maximalt", -- alternativ: "Högsta antal"\n'
      "}\n")
ASSIGN = (HEAD + "local ui = WPS.L.ui\n\n-- Tabs\n"
          'ui["Character"] = "Rollfigur"\n'
          'ui["Reputation"] = "Anseende"\n')
TWO_TABLES = (HEAD + 'WPS.L.names_a = {\n["A"]="a",\n}\nWPS.L.names_b = {\n["B"]="b",\n}\n')


def parse(text):
    return dl.DataFile.parse(text)


class ReadTest(unittest.TestCase):
    def test_quest_values_fields_and_lists(self):
        q = parse(QUEST).table("quest")
        self.assertEqual(q.get(2), {"t": "Sharptalons klo",
                                    "d": 'Rad ett.\n\nRad två med "citat" och \\ snedstreck.',
                                    "l": ["Ta klon."]})
        self.assertEqual(list(q.get(2)), ["t", "d", "l"])           # field order kept
        self.assertEqual(q.get(5)["l"], ["a", "b", "c"])
        self.assertEqual(q.get(99), {"t": "Spaced", "o": "Mål", "d": "Text"})  # ", " spacing
        self.assertEqual(q.get(100), {"o": "Bara mål"})
        self.assertEqual(q.keys(), [2, 5, 99, 100])

    def test_item_numeric_hash_field(self):
        i = parse(ITEM).table("item")
        self.assertEqual(i.get(287505), {"h": 3305331836, "n": "Mört löparkött", "d": "Kyle skulle njuta."})
        self.assertIsInstance(i.get(287505)["h"], int)

    def test_scalar_values_and_string_keys(self):
        self.assertEqual(parse(NPC).table("npc").get(3), "Köttätare")
        g = parse(GOSSIP).table("gossip")
        self.assertEqual(g.get("12_2c8ce38d"), "Stridsmästare")
        self.assertEqual(g.keys(), ["100_094194f4", "12_2c8ce38d"])

    def test_numeric_and_string_keys_are_different(self):
        t = parse(HEAD + 'WPS.L.x = {\n[123]="num",\n["123"]="str",\n}\n').table("x")
        self.assertEqual(t.get(123), "num")
        self.assertEqual(t.get("123"), "str")
        self.assertEqual(len(t), 2)
        self.assertEqual(t.duplicates, [])

    def test_trailing_comment_is_kept_apart_from_the_value(self):
        n = parse(UI).table("ui").index["Maximum"]
        self.assertEqual(n.entry.value, "Maximalt")
        self.assertEqual(n.entry.comment, 'alternativ: "Högsta antal"')

    def test_several_tables_in_one_file(self):
        df = parse(TWO_TABLES)
        self.assertEqual(list(df.tables), ["names_a", "names_b"])
        self.assertEqual(df.table("names_b").get("B"), "b")

    def test_assignment_style_ui_extra(self):
        t = parse(ASSIGN).table("ui")
        self.assertEqual(t.style, "assign")
        self.assertEqual(t.items(), [("Character", "Rollfigur"), ("Reputation", "Anseende")])

    def test_duplicate_keys_are_reported_and_last_wins_as_in_lua(self):
        t = parse(HEAD + 'WPS.L.npc = {\n[3]="first",\n[4]="x",\n[3]="second",\n}\n').table("npc")
        self.assertEqual(t.get(3), "second")
        self.assertEqual(t.duplicates, [(3, [4, 6])])

    def test_decimal_and_other_simple_escapes(self):
        t = parse(HEAD + 'WPS.L.x = {\n[1]="a\\001b\\9c\\"d\\\'e\\tf",\n}\n').table("x")
        self.assertEqual(t.get(1), "a\x01b\tc\"d'e\tf")


class RoundTripTest(unittest.TestCase):
    def test_every_format_round_trips_byte_for_byte(self):
        for name, text in (("quest", QUEST), ("item", ITEM), ("npc", NPC), ("gossip", GOSSIP),
                           ("ui", UI), ("assign", ASSIGN), ("two", TWO_TABLES)):
            with self.subTest(name):
                self.assertEqual(parse(text).text(), text)

    def test_missing_final_newline_and_odd_spacing_are_preserved(self):
        text = HEAD + 'WPS.L.npc = {\n  [3] = "a" ,   \n[4]="b",\n}'
        self.assertEqual(parse(text).text(), text)

    def test_value_and_key_formatting_matches_the_real_style(self):
        e = dl.Entry(2, {"t": "T", "d": 'a\n"b"\\', "l": ["x", "y"]})
        self.assertEqual(e.format(), '[2]={t="T",d="a\\n\\"b\\"\\\\",l={"x","y"}},')
        self.assertEqual(dl.Entry("k\"q", "v").format(), '["k\\"q"]="v",')
        self.assertEqual(dl.Entry(5, {"h": 3305331836, "n": "N"}).format(), '[5]={h=3305331836,n="N"},')
        self.assertEqual(dl.Entry("a", "b", "note", "assign", "ui").format(), 'ui["a"] = "b" -- note')

    def test_writer_output_parses_back_to_the_same_value(self):
        values = ["plain", 'q"uote', "back\\slash", "line\nbreak", "tab\there", "ctrl\x01\x7f", "åäö $B $N %s |cffff0000x|r"]
        text = HEAD + "WPS.L.x = {\n}\n"
        df = parse(text)
        df.insert("x", [(i, v) for i, v in enumerate(values)])
        again = parse(df.text()).table("x")
        self.assertEqual([again.get(i) for i in range(len(values))], values)

    def test_real_data_files_round_trip_and_parse(self):
        for path in sorted((ROOT / "Data").glob("*.lua")):
            with self.subTest(path.name):
                df = dl.DataFile.read(path)
                self.assertEqual(df.text().encode("utf-8"), path.read_bytes())
                self.assertTrue(df.tables)
                for t in df.tables.values():
                    self.assertEqual(t.duplicates, [], f"{path.name} {t.name}")

    @unittest.skipUnless(LUA, "lua5.1 is not installed; cannot compare against the Lua runtime")
    def test_parsed_values_match_what_lua_loads(self):
        """Parse every Data file in Python and compare with tools/dump-runtime.lua byte for byte."""
        def esc(s):
            return re.sub(r"[\x00-\x1f\x7f\\]", lambda m: {"\\": "\\\\", "\t": "\\t", "\n": "\\n", "\r": "\\r"}.get(
                m.group()) or "\\x%02X" % ord(m.group()), s)

        def val(x):
            return ("n", str(x)) if isinstance(x, int) else ("s", esc(x))

        rows = []
        for path in (ROOT / "Data").glob("*.lua"):
            for name, t in dl.DataFile.read(path).tables.items():
                for key, v in t.items():
                    kt, ks = ("n", str(key)) if isinstance(key, int) else ("s", esc(key))
                    if isinstance(v, dict):
                        for f, fv in v.items():
                            if isinstance(fv, list):
                                for i, x in enumerate(fv, 1):
                                    rows.append((name, kt, ks, f"{f}[{i}]", "s", esc(x)))
                            else:
                                rows.append((name, kt, ks, f) + val(fv))
                    else:
                        rows.append((name, kt, ks, "=") + val(v))
        rows.sort(key=lambda r: (r[0].encode(), r[1] != "n", int(r[2]) if r[1] == "n" else r[2].encode(), r[3].encode()))
        mine = "".join("\t".join(r) + "\n" for r in rows).encode()
        lua = subprocess.run([LUA, str(ROOT / "tools" / "dump-runtime.lua"), str(ROOT)],
                             capture_output=True, check=True).stdout
        self.assertEqual(mine, lua)


class UnknownSyntaxTest(unittest.TestCase):
    def assertRejected(self, text, fragment, line=None):
        with self.assertRaises(dl.DataError) as cm:
            parse(text)
        self.assertIn(fragment, str(cm.exception))
        if line is not None:
            self.assertEqual(cm.exception.line, line)

    def test_unknown_constructs_fail_with_the_line_number(self):
        body = HEAD + "WPS.L.x = {\n%s\n}\n"
        cases = {
            "multi-line string": ('[1]="abc', "unterminated"),
            "single quotes": ("[1]='abc',", "expected"),
            "float": ('[1]={h=1.5,n="x"},', "number"),
            "negative number": ('[1]={h=-1,n="x"},', "integer"),
            "hex escape": ('[1]="a\\x41",', "escape"),
            "high decimal escape": ('[1]="a\\200",', "ASCII"),
            "line continuation": ('[1]="a\\', "continuation"),
            "two entries on one line": ('[1]="a",[2]="b",', "unexpected text"),
            "missing comma": ('[1]="a"', "','"),
            "nested table": ('[1]={a={b={"x"}}},', "string"),
            "boolean value": ("[1]=true,", "expected"),
            "call": ('[1]=f("a"),', "expected"),
            "bare key": ('abc="a",', "expected"),
            "negative key": ('[-1]="a",', "integer"),
            "long string": ("[1]=[[abc]],", "expected"),
            "block comment": ("--[[ hi ]]", "block comments"),
            "duplicate field": ('[1]={n="a",n="b"},', "duplicate field"),
            "trailing garbage": ('[1]="a", x', "unexpected text"),
        }
        for name, (line, fragment) in cases.items():
            with self.subTest(name):
                self.assertRejected(body % line, fragment, line=4)

    def test_top_level_and_structure_errors(self):
        self.assertRejected(HEAD + "print('x')\n", "unknown syntax", 3)
        self.assertRejected(HEAD + "WPS.L.x = {\n[1]=\"a\",\n", "not closed")
        self.assertRejected(HEAD + 'WPS.L.x = {\n}\nWPS.L.x = {\n}\n', "defined twice", 5)
        self.assertRejected(HEAD + 'local ui = WPS.L.ui\nother["a"] = "b"\n', "unknown syntax", 4)
        self.assertRejected(HEAD + 'WPS.L.x = {\n}\n[1]="a",\n', "unknown syntax", 5)

    def test_encoding_and_line_endings(self):
        self.assertRejected(HEAD.replace("\n", "\r\n"), "CR characters")
        self.assertRejected("﻿" + HEAD, "byte order mark")
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.lua"
            bad.write_bytes(b"-- caf\xe9\n")
            with self.assertRaises(dl.DataError) as cm:
                dl.DataFile.read(bad)
            self.assertIn("UTF-8", str(cm.exception))

    def test_failed_read_leaves_the_file_untouched_and_cli_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Data.lua"
            text = HEAD + 'WPS.L.x = {\n[1]="ok",\n[2]=weird,\n}\n'
            path.write_text(text, encoding="utf-8")
            result = subprocess.run(["python3", str(ROOT / "tools" / "datalua.py"), "--rewrite", str(path)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Data.lua:5:", result.stdout)
            self.assertEqual(path.read_text(encoding="utf-8"), text)
            self.assertEqual([p.name for p in Path(tmp).iterdir()], ["Data.lua"])


class InsertTest(unittest.TestCase):
    def test_sorted_table_gets_new_keys_in_place_and_nothing_else_moves(self):
        before = parse(QUEST)
        df = parse(QUEST)
        n = df.insert("quest", [(150, {"t": "Efter"}), (1, {"t": "Före"}), (3, {"t": "Mitt"}), (98, {"t": "Nära"})])
        self.assertEqual(n, 4)
        self.assertEqual(df.table("quest").keys(), [1, 2, 3, 5, 98, 99, 100, 150])
        old_lines = QUEST.split("\n")
        new_lines = df.text().split("\n")
        # every original line is still there, in the same order
        it = iter(new_lines)
        self.assertTrue(all(any(l == m for m in it) for l in old_lines))
        self.assertIn('[3]={t="Mitt"},', new_lines)
        self.assertEqual(new_lines.index('[1]={t="Före"},'), 3)       # first entry, after the "{" line
        self.assertEqual(new_lines[new_lines.index('[150]={t="Efter"},') + 1], "}")
        # the section comment and blank line before [100] were not displaced
        self.assertEqual(new_lines[new_lines.index('[100]={o="Bara mål"},') - 2:new_lines.index('[100]={o="Bara mål"},')],
                         ["", "-- section comment"])
        self.assertEqual(before.table("quest").keys(), [2, 5, 99, 100])

    def test_inserting_into_a_sorted_string_table(self):
        df = parse(GOSSIP)
        df.insert("gossip", [("13_1fb7c34c", "Stallmästare")])
        self.assertEqual(df.table("gossip").keys(), ["100_094194f4", "12_2c8ce38d", "13_1fb7c34c"])

    def test_unsorted_table_appends_after_the_last_entry_in_key_order(self):
        df = parse(UI)
        df.insert("ui", [("Mango", "Mango"), ("Banana", "Banan")])
        keys = df.table("ui").keys()
        self.assertEqual(keys, ["Zebra", "Apple", "Maximum", "Banana", "Mango"])
        lines = df.text().split("\n")
        self.assertEqual(lines[-4:], ['["Banana"]="Banan",', '["Mango"]="Mango",', "}", ""])

    def test_inserting_into_an_empty_table_and_a_table_with_two_blocks(self):
        df = parse(HEAD + "WPS.L.x = {\n}\n")
        df.insert("x", [(7, "a"), (3, "b")])
        self.assertEqual(df.text(), HEAD + 'WPS.L.x = {\n[3]="b",\n[7]="a",\n}\n')
        df = parse(TWO_TABLES)
        df.insert("names_b", [("A", "x")])
        self.assertEqual(df.table("names_a").keys(), ["A"])
        self.assertEqual(df.table("names_b").keys(), ["A", "B"])

    def test_assignment_style_table_appends_assignments(self):
        df = parse(ASSIGN)
        df.insert("ui", [("Title", "Titel")])
        self.assertEqual(df.text(), ASSIGN + 'ui["Title"] = "Titel"\n')

    def test_insert_refuses_existing_duplicate_and_mixed_keys(self):
        df = parse(QUEST)
        for items in ([(2, {"t": "x"})], [(7, "a"), (7, "b")], [("7", "a")], [(8, "a"), ("9", "b")]):
            with self.subTest(items=items):
                with self.assertRaises(dl.DataError):
                    df.insert("quest", items)
        self.assertEqual(df.text(), QUEST)           # nothing changed by the failed attempts

    def test_unsupported_values_are_rejected_before_anything_is_added(self):
        df = parse(NPC)
        for bad in (True, 1.5, -3, {"a": {"b": "c"}}, ["x", 1], None):
            with self.subTest(bad=bad):
                with self.assertRaises(dl.DataError):
                    df.insert("npc", [(99, bad)])
        self.assertEqual(df.text(), NPC)

    def test_comment_is_added_to_new_lines_only(self):
        df = parse(NPC)
        df.insert("npc", [(31, "Ny")], comment="batch 7")
        self.assertEqual(df.text().split("\n")[-3], '[31]="Ny", -- batch 7')

    def test_intentional_difference_marker_survives_reading_replacing_and_writing(self):
        text = (HEAD + "WPS.L.qtext = {\n"
                '["Carnage"]="Carnage", -- wps:skillnad varelsens namn, kvar på engelska\n'
                '["Other"]="Annat",\n}\n')
        marker = '["Carnage"]="Carnage", -- wps:skillnad varelsens namn, kvar på engelska'
        df = parse(text)
        self.assertEqual(df.text(), text)                              # a plain round trip
        self.assertEqual(df.table("qtext").index["Carnage"].entry.comment,
                         "wps:skillnad varelsens namn, kvar på engelska")
        df.insert("qtext", [("Zed", "Zed")])                           # inserting elsewhere
        self.assertIn(marker, df.text())
        df.replace("qtext", "Carnage", "Blodbad")                      # replacing the value
        self.assertIn('["Carnage"]="Blodbad", -- wps:skillnad varelsens namn, kvar på engelska', df.text())
        path = Path(tempfile.mkdtemp()) / "Glossary.lua"
        self.addCleanup(shutil.rmtree, path.parent)
        path.write_text(text, encoding="utf-8")
        df = dl.DataFile.read(str(path))
        df.write()                                                     # the atomic writer
        self.assertEqual(path.read_text(encoding="utf-8"), text)
        self.assertEqual(dl.main(["--rewrite", str(path)]), 0)         # and the --rewrite command
        self.assertEqual(path.read_text(encoding="utf-8"), text)

    def test_replace_rewrites_one_line_and_keeps_its_comment(self):
        df = parse(UI)
        df.replace("ui", "Maximum", "Högsta")
        self.assertIn('["Maximum"]="Högsta", -- alternativ: "Högsta antal"', df.text())
        self.assertEqual(df.text().count("\n"), UI.count("\n"))
        with self.assertRaises(dl.DataError):
            df.replace("ui", "Nope", "x")


class WriteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_write_replaces_the_target_atomically_and_leaves_no_temp_file(self):
        path = self.dir / "Npc.lua"
        path.write_text(NPC, encoding="utf-8")
        os.chmod(path, 0o640)
        df = dl.DataFile.read(path)
        df.insert("npc", [(31, "Ny")])
        df.write()
        self.assertEqual(path.read_text(encoding="utf-8"), NPC.replace("}\n", '[31]="Ny",\n}\n'))
        self.assertEqual(os.stat(path).st_mode & 0o777, 0o640)
        self.assertEqual([p.name for p in self.dir.iterdir()], ["Npc.lua"])

    def test_unchanged_file_is_rewritten_identically(self):
        path = self.dir / "Quest.lua"
        path.write_bytes(QUEST.encode("utf-8"))
        dl.DataFile.read(path).write()
        self.assertEqual(path.read_bytes(), QUEST.encode("utf-8"))

    def test_failing_check_keeps_the_original_and_removes_the_temp_file(self):
        path = self.dir / "Npc.lua"
        path.write_text(NPC, encoding="utf-8")
        df = dl.DataFile.read(path)
        df.insert("npc", [(31, "Ny")])

        def boom(tmp):
            self.assertTrue(os.path.exists(tmp))
            raise RuntimeError("check failed")

        with self.assertRaises(RuntimeError):
            df.write(check=boom)
        self.assertEqual(path.read_text(encoding="utf-8"), NPC)
        self.assertEqual([p.name for p in self.dir.iterdir()], ["Npc.lua"])

    def test_write_refuses_a_result_that_does_not_parse(self):
        path = self.dir / "Npc.lua"
        path.write_text(NPC, encoding="utf-8")
        df = dl.DataFile.read(path)
        df.nodes[-2].text = "[31]=broken,"          # simulate a bug in an editing step
        with self.assertRaises(dl.DataError):
            df.write()
        self.assertEqual(path.read_text(encoding="utf-8"), NPC)
        self.assertEqual([p.name for p in self.dir.iterdir()], ["Npc.lua"])

    def test_edited_file_is_valid_lua(self):
        luac = shutil.which("luac5.1")
        if not luac:
            self.skipTest("luac5.1 is not installed")
        path = self.dir / "Quest.lua"
        path.write_text(QUEST, encoding="utf-8")
        df = dl.DataFile.read(path)
        df.insert("quest", [(3, {"t": 'Citat "x" \\ \n', "l": ["a"]}), (200, {"t": "Slut"})])
        df.write()
        subprocess.run([luac, "-p", str(path)], check=True)


if __name__ == "__main__":
    unittest.main()
