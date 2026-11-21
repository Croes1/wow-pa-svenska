#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/check-data.py: gossip key port, validation rules, search."""
import contextlib
import importlib.util
import io
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "check-data.py"
LUA = shutil.which("lua5.1")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cd = load("check_data", TOOL)
dl = load("datalua_for_check_tests", ROOT / "tools" / "datalua.py")

# English texts whose keys exist in the real Data/Gossip.lua (identified by length and hash).
REAL_GOSSIP = {
    "Battlemaster": "12_2c8ce38d", "Guild Master": "12_500dffe6", "Stable Master": "13_1fb7c34c",
    "Class Trainer": "13_61a63af0", "Auction House": "13_f610e09c", "Gryphon Master": "14_53a93198",
    "Weapons Trainer": "15_b33ac7d7", "Bank of Ironforge": "17_7f16ad01", "Profession Trainer": "18_e5e1f322",
    "Return me to life.": "18_06544588", "Mage": "4_7c88f2ff", "Rogue": "5_0e097d27", "Hunter": "6_b855f19b",
    "Priest": "6_cac5f13c", "Shaman": "6_d10c32bd", "Warlock": "7_175aafb8", "Warrior": "7_175de20b",
    "Paladin": "7_fc103d3e", "Mailbox": "7_14f13df1", "The Inn": "7_3faa8a4b",
}


class GossipKeyTest(unittest.TestCase):
    def test_port_reproduces_real_keys_from_data_gossip_lua(self):
        table = dl.DataFile.read(ROOT / "Data" / "Gossip.lua").table("gossip")
        for english, key in REAL_GOSSIP.items():
            with self.subTest(english):
                self.assertIn(key, table, "the fixture key must exist in Data/Gossip.lua")
                self.assertEqual(cd.gossip_key(english), key)

    def test_key_shape_and_utf8_byte_length(self):
        self.assertEqual(cd.gossip_key(""), "0_00001505")
        key = cd.gossip_key("Hälsningar, vän")
        self.assertTrue(key.startswith(f"{len('Hälsningar, vän'.encode('utf-8'))}_"))
        self.assertRegex(key, r"^[0-9]+_[0-9a-f]{8}$")

    def test_normalisation_rules(self):
        self.assertEqual(cd.gossip_key("a\r\nb"), cd.gossip_key("a\nb"))                 # \r\n -> \n
        self.assertNotEqual(cd.gossip_key("a\rb"), cd.gossip_key("a\nb"))                # a lone \r stays
        self.assertEqual(cd.gossip_key("Hi Thrall, bye Thrall.", "Thrall"), cd.gossip_key("Hi $N, bye $N."))
        self.assertEqual(cd.gossip_key("Hi Ana-Maria.", "Ana-Maria"), cd.gossip_key("Hi $N."))
        self.assertEqual(cd.gossip_key("Hi Thrall."), cd.gossip_key("Hi Thrall.", None))
        self.assertNotEqual(cd.gossip_key("Hi Thrall."), cd.gossip_key("Hi Thrall.", "Thrall"))

    def test_every_real_key_has_the_expected_shape(self):
        table = dl.DataFile.read(ROOT / "Data" / "Gossip.lua").table("gossip")
        for key in table.keys():
            self.assertRegex(key, r"^[0-9]+_[0-9a-f]{8}$")

    @unittest.skipUnless(LUA, "lua5.1 is not installed; cannot compare with the real Lua code")
    def test_port_equals_the_real_key_and_lookup_in_gossiptext_lua(self):
        """Run the real GossipText.lua (Key, Lookup, the QUEST_GREETING path) and compare."""
        cases = [
            ("Battlemaster", None), ("Class Trainer", "Thrall"), ("Hello, Thrall. Welcome back, Thrall!", "Thrall"),
            ("Line one\r\nLine two\r\n\r\nLine three, $N.", None), ("Mixed\nand\r\nbreaks with Ana-Maria", "Ana-Maria"),
            ("Hälsningar från Örnnästet, åäö ÅÄÖ", None), ("Lone\rcarriage return", None),
            ("Thralls and Thrall and thrall", "Thrall"), ("Name inside Maltheraa word", "Mal"),
            ("100% sure? (really) [yes] {no} ^$.*+-?", "x"), ("Ünïcödé ñame Zoë", "Zoë"), ("x", None),
            ("A" * 300, None), ("tab\there", None),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            harness = Path(tmp) / "harness.lua"
            harness.write_text(HARNESS, encoding="utf-8")
            lines = []
            for text, player in cases:
                lines.append("\t".join([text.encode().hex(), (player or "").encode().hex(),
                                        cd.gossip_key(text, player).encode().hex()]))
            result = subprocess.run([LUA, str(harness), str(ROOT / "GossipText.lua")], input="\n".join(lines) + "\n",
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.split(), ["MATCH"] * len(cases), result.stdout)
            # The test has teeth: a key computed without the normalisation must NOT be found.
            wrong = []
            for text, player in [("a\r\nb", None), ("Hi Thrall.", "Thrall")]:
                raw = cd.wps_hash(text)
                wrong.append("\t".join([text.encode().hex(), (player or "").encode().hex(),
                                        ("%d_%08x" % (len(text.encode()), raw)).encode().hex()]))
            result = subprocess.run([LUA, str(harness), str(ROOT / "GossipText.lua")], input="\n".join(wrong) + "\n",
                                    capture_output=True, text=True)
            self.assertEqual(result.stdout.split(), ["NOMATCH"] * 2, result.stdout)

    @unittest.skipUnless(LUA, "lua5.1 is not installed")
    def test_wps_hash_equals_core_lua(self):
        core = (ROOT / "Core.lua").read_text(encoding="utf-8")
        body = re.search(r"function WPS\.Hash\(s\)\n.*?\nend\n", core, re.S).group()
        texts = ["", "a", "Battlemaster", "åäö", "x" * 500, "Kyle would enjoy a bite of this juicy treat!"]
        script = "WPS={}\n" + body + 'for line in io.lines() do print(WPS.Hash((line:gsub("%x%x", function(h) return string.char(tonumber(h,16)) end)))) end\n'
        result = subprocess.run([LUA, "-e", script], input="\n".join(t.encode().hex() for t in texts) + "\n",
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([int(x) for x in result.stdout.split()], [cd.wps_hash(t) for t in texts])


HARNESS = r'''
-- Drives the real GossipText.lua: stdin lines "hexEnglish<TAB>hexPlayer<TAB>hexPythonKey";
-- prints MATCH if the entry stored under the Python key is shown for that English text.
local addonFile = arg[1]
local function unhex(h) return (h:gsub("%x%x", function(x) return string.char(tonumber(x, 16)) end)) end
local WPS = { L = { gossip = {} }, hooks = {} }
local player
function WPS.On() return true end
function WPS.Expand(s) return s end
function WPS.Remember() end
local inits = {}
function WPS.OnLogin(fn) inits[#inits + 1] = fn end
function UnitName(unit) if unit == "player" then return player end return "npc" end
local onEvent
function CreateFrame() local f = {} function f:RegisterEvent() end
	function f:SetScript(_, fn) onEvent = fn end return f end
C_Timer = { After = function(_, fn) fn() end }
local fs = {}
function fs:GetText() return self.text end
function fs:SetText(t) self.text = t end
GreetingText = fs
assert(loadfile(addonFile))("wow_pa_svenska", WPS)
for _, fn in ipairs(inits) do fn() end
for line in io.lines() do
	local en, pl, key = line:match("^(%x*)\t(%x*)\t(%x*)$")
	en, pl, key = unhex(en), unhex(pl), unhex(key)
	player = pl ~= "" and pl or nil
	WPS.L.gossip = { [key] = "SVENSKA" }
	fs.text = en
	onEvent(nil, "QUEST_GREETING")
	print(fs.text == "SVENSKA" and "MATCH" or "NOMATCH")
end
'''


# --------------------------------------------------------------------------
# Validation rules, on small fixture data directories
# --------------------------------------------------------------------------

HEAD = "local _, WPS = ...\n"


class CheckCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def data(self, **tables):
        """tables: file name -> (table name, body lines). Replaces whatever was there before."""
        for old in self.dir.glob("*.lua"):
            old.unlink()
        for name, (table, body) in tables.items():
            (self.dir / name).write_text(HEAD + f"WPS.L.{table} = {{\n" + "\n".join(body) + "\n}\n", encoding="utf-8")

    def check(self, **tables):
        self.data(**tables)
        findings, _counts = cd.run_checks(str(self.dir))
        return findings

    def codes(self, severity, **tables):
        return sorted({f.code for f in self.check(**tables) if f.severity == severity})

    def errors(self, **tables):
        return self.codes("ERROR", **tables)

    def warnings(self, **tables):
        return self.codes("WARN", **tables)

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cd.main(["--data-dir", str(self.dir), *args])
        return code, out.getvalue()


class ErrorRulesTest(CheckCase):
    def test_clean_data_has_no_findings(self):
        findings = self.check(**{
            "Quest.lua": ("quest", ['[1]={t="T",d="D",o="O",p="P",c="C",l={"a","b"}},', '[2]={t="Bara titel"},']),
            "Item.lua": ("item", ['[1]={n="Namn"},', '[2]={h=3305331836,n="Namn",d="Text"},']),
            "Spell.lua": ("spell", ['[1]={n="Namn"},', '[2]={e="Deal $s1 damage.",n="N",d="Gör $s1 skada."},',
                                    '[3]={ea="Absorbs $w1.",n="N",a="Absorberar $w1."},', '[4]={n="N",c="Form"},']),
            "Npc.lua": ("npc", ['[1]="Namn",']),
            "Gossip.lua": ("gossip", ['["7_175de20b"]="Krigare",']),
            "Ui.lua": ("ui", ['["Level %d"]="Nivå %d",', '["Accept"]="Acceptera",']),
        })
        self.assertEqual([f.text() for f in findings], [])

    def test_duplicate_keys(self):
        self.assertEqual(self.errors(**{"Npc.lua": ("npc", ['[1]="a",', '[2]="b",', '[1]="c",'])}), ["duplicate-key"])
        self.assertEqual(self.errors(**{"Ui.lua": ("ui", ['["A"]="a",', '["A"]="b",'])}), ["duplicate-key"])

    def test_numeric_and_string_keys_are_not_interchangeable(self):
        self.assertEqual(self.errors(**{"Npc.lua": ("npc", ['["123"]="a",'])}), ["bad-key"])
        self.assertEqual(self.errors(**{"Npc.lua": ("npc", ['[0]="a",'])}), ["bad-key"])
        self.assertEqual(self.errors(**{"Ui.lua": ("ui", ["[5]=\"a\","])}), ["bad-key"])
        self.assertEqual(self.errors(**{"Gossip.lua": ("gossip", ['["12_XYZ"]="a",'])}), ["bad-key"])
        self.assertEqual(self.errors(**{"Gossip.lua": ("gossip", ["[5]=\"a\","])}), ["bad-key"])

    def test_empty_and_wrong_typed_values(self):
        self.assertEqual(self.errors(**{"Npc.lua": ("npc", ['[1]="",', '[2]="  ",'])}), ["bad-value"])
        self.assertEqual(self.errors(**{"Quest.lua": ("quest", ['[1]={t=""},'])}), ["bad-value", "missing-field"])
        self.assertEqual(self.errors(**{"Quest.lua": ("quest", ['[1]={t="T",x="?"},'])}), ["bad-value"])
        self.assertEqual(self.errors(**{"Quest.lua": ("quest", ['[1]={t="T",l={}},'])}), ["bad-value"])
        self.assertEqual(self.errors(**{"Quest.lua": ("quest", ['[1]={t="T",l={""}},'])}), ["bad-value"])
        self.assertEqual(self.errors(**{"Quest.lua": ("quest", ['[1]={},'])}), ["bad-value"])
        self.assertEqual(self.errors(**{"Quest.lua": ("quest", ['[1]="a string",'])}), ["bad-value"])
        self.assertEqual(self.errors(**{"Npc.lua": ("npc", ['[1]={n="a"},'])}), ["bad-value"])
        self.assertEqual(self.errors(**{"Item.lua": ("item", ['[1]={h=4294967296,n="N",d="D"},'])}), ["bad-value"])
        self.assertEqual(self.errors(**{"Item.lua": ("item", ['[1]={h="12",n="N",d="D"},'])}), ["bad-value"])

    def test_required_fields(self):
        self.assertEqual(self.errors(**{"Quest.lua": ("quest", ['[1]={l={"a"}},'])}), ["missing-field"])
        self.assertEqual(self.errors(**{"Item.lua": ("item", ['[1]={d="Text"},'])}), ["missing-field"])
        self.assertEqual(self.errors(**{"Item.lua": ("item", ['[1]={n="N",d="Text"},'])}), ["missing-field"])
        self.assertEqual(self.errors(**{"Spell.lua": ("spell", ['[1]={n="N",a="Text"},'])}), ["missing-field"])
        self.assertEqual(self.errors(**{"Spell.lua": ("spell", ['[1]={e="Only english"},'])}), ["missing-field"])

    def test_double_escaped_line_breaks_and_control_characters(self):
        self.assertEqual(self.errors(**{"Quest.lua": ("quest", ['[1]={t="T",d="a\\\\r\\\\nb"},'])}), ["literal-escape"])
        self.assertEqual(self.errors(**{"Npc.lua": ("npc", ['[1]="a\\\\nb",'])}), ["literal-escape"])
        self.assertEqual(self.errors(**{"Quest.lua": ("quest", ['[1]={t="T",d="a\\nb\\n\\nc"},'])}), [])   # real breaks are fine
        self.assertEqual(self.errors(**{"Quest.lua": ("quest", ['[1]={t="T",d="a\\r\\nb"},'])}), ["control-char"])
        self.assertEqual(self.errors(**{"Quest.lua": ("quest", ['[1]={t="T",d="a\\001b"},'])}), ["control-char"])

    def test_lost_placeholders_are_errors(self):
        cases = {
            "ui %s": {"Ui.lua": ("ui", ['["Level %s"]="Nivå",'])},
            "ui colour end": {"Ui.lua": ("ui", ['["|cffff0000Red|r"]="|cffff0000Röd",'])},
            "ui colour start": {"Ui.lua": ("ui", ['["|cffff0000Red|r"]="Röd|r",'])},
            "zone $N": {"Zone.lua": ("zone", ['["Hello $N"]="Hej",'])},
            "names": {"Glossary.lua": ("names_general", ['["Press %s now"]="Tryck nu",'])},
            "spell e>d": {"Spell.lua": ("spell", ['[1]={e="Deal $s1 damage.",n="N",d="Skada."},'])},
            "spell ea>a": {"Spell.lua": ("spell", ['[1]={ea="Absorbs $w1.",n="N",a="Absorberar."},'])},
            "spell formula": {"Spell.lua": ("spell", ['[1]={e="Heal ${$m1*2}.",n="N",d="Läker."},'])},
            "spell condition": {"Spell.lua": ("spell", ['[1]={e="$?a123[A][B]",n="N",d="AB"},'])},
            "qtext $B": {"Glossary.lua": ("qtext", ['["One.$B$BTwo."]="Ett. Två.",'])},
            "doubled token": {"Ui.lua": ("ui", ['["%s of %s"]="%s av",'])},
        }
        for name, tables in cases.items():
            with self.subTest(name):
                self.assertEqual(self.errors(**tables), ["token-lost"])

    def test_text_inside_conditionals_and_plurals_is_free(self):
        ok = {
            "Spell.lua": ("spell", [
                '[1]={e="Deals $s1 $lpoint:points; of damage.",n="N",d="Orsakar $s1 $lpoäng:poäng; skada."},',
                '[2]={e="Conjures $s1 $lcinnamon roll:cinnamon rolls;, for $ghis:her; allies.",n="N",'
                'd="Frammanar $s1 $lkanelbulle:kanelbullar;, för $ghans:hennes; bundsförvanter."},',
                '[3]={e="$?a12792[20%][30%]",n="N",d="$?a12792[20 %][30 %]"},',
                '[4]={e="Takes $w1$B$Bmore.",n="N",d="Tar $w1$b$bmer."},',
            ])}
        self.assertEqual(self.codes("ERROR", **ok), [])
        self.assertEqual(self.codes("WARN", **ok), [])

    def test_parse_error_is_an_error_but_other_files_are_still_checked(self):
        self.data(**{"Npc.lua": ("npc", ['[1]=oops,']), "Ui.lua": ("ui", ['["A"]="",'])})
        findings, _ = cd.run_checks(str(self.dir))
        self.assertEqual(sorted((f.code, Path(f.file).name) for f in findings),
                         [("bad-value", "Ui.lua"), ("parse-error", "Npc.lua")])
        parse_error = next(f for f in findings if f.code == "parse-error")
        self.assertEqual(parse_error.line, 3)


class WarningRulesTest(CheckCase):
    def test_added_placeholders_and_changed_colours_are_warnings_only(self):
        self.assertEqual(self.warnings(**{"Ui.lua": ("ui", ['["Rank"]="Grad %s",'])}), ["token-added"])
        self.assertEqual(self.warnings(**{"Ui.lua": ("ui", ['["|cnHIGHLIGHT_FONT_COLOR:%s|r pts"]="|cffffd200%s|r poäng",'])}),
                         ["colour-changed"])
        self.assertEqual(self.errors(**{"Ui.lua": ("ui", ['["|cnHIGHLIGHT_FONT_COLOR:%s|r pts"]="|cffffd200%s|r poäng",'])}), [])
        self.assertEqual(self.warnings(**{"Ui.lua": ("ui", ['["|cFFFFFFFFHit|r"]="|cffffffffTräff|r",'])}), [])

    def test_unused_fields(self):
        self.assertEqual(self.warnings(**{"Item.lua": ("item", ['[1]={h=5,n="N"},'])}), ["unused-field"])
        self.assertEqual(self.warnings(**{"Spell.lua": ("spell", ['[1]={e="x",n="N"},'])}), ["unused-field"])
        self.assertEqual(self.warnings(**{"Spell.lua": ("spell", ['[1]={ea="x",n="N"},'])}), ["unused-field"])

    def test_entry_format_and_field_order(self):
        self.assertEqual(self.warnings(**{"Quest.lua": ("quest", ['[1]={t="T", o="O", d="D"},'])}), ["entry-format", "field-order"])
        self.assertEqual(self.warnings(**{"Npc.lua": ("npc", ['[1]="a", '])}), ["entry-format"])
        self.assertEqual(self.warnings(**{"Npc.lua": ("npc", ['[1] = "a",'])}), ["entry-format"])
        self.assertEqual(self.warnings(**{"Npc.lua": ("npc", ['[1]="a\\9b",'])}), ["entry-format"])
        self.assertEqual(self.warnings(**{"Ui.lua": ("ui", ['["A"]="a", -- a note'])}), [])        # comments are fine
        finding = next(f for f in self.check(**{"Npc.lua": ("npc", ['[1]="a", '])}) if f.code == "entry-format")
        self.assertIn("column 9", finding.message)

    def test_edge_whitespace_and_inconsistent_terms(self):
        self.assertEqual(self.warnings(**{"Ui.lua": ("ui", ['[" Season 1"]="Säsong 1",'])}), ["edge-whitespace"])
        self.assertEqual(self.warnings(**{"Ui.lua": ("ui", ['[" Season 1"]=" Säsong 1",'])}), [])
        findings = self.check(**{"Ui.lua": ("ui", ['["Ogre"]="Oger",', '["ogre"]="Oger",']),
                                 "Zone.lua": ("zone", ['["Ogre"]="Jätte",'])})
        self.assertEqual([f.code for f in findings], ["inconsistent"])
        self.assertIn("zone['Ogre'] -> 'Jätte'", findings[0].message)
        same = self.check(**{"Ui.lua": ("ui", ['["Ogre"]="Oger",', '["ogre"]="oger",']), "Zone.lua": ("zone", ['["Ogre"]="Oger",'])})
        self.assertEqual(same, [])                                                                    # same term, same Swedish

    def test_warnings_never_change_the_exit_status(self):
        self.data(**{"Quest.lua": ("quest", ['[1]={t="T", o="O", d="D"},'])})
        code, out = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("errors:   0", out)
        self.assertIn("warnings: 2", out)
        self.assertIn("RESULT: OK", out)

    def test_errors_set_exit_status_1_and_are_listed_in_full(self):
        self.data(**{"Npc.lua": ("npc", ['[1]="",', '[2]="",'])})
        code, out = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertEqual(out.count("ERROR [bad-value]"), 2)
        self.assertIn("ERRORS - do not merge", out)

    def test_warning_listing_is_limited_unless_asked_for(self):
        self.data(**{"Npc.lua": ("npc", [f'[{i}]="a", ' for i in range(1, 9)])})
        _, out = self.run_cli("check", "--examples", "2")
        self.assertIn("8 warning(s) [entry-format], first 2:", out)
        self.assertEqual(out.count("WARN  [entry-format]"), 2)
        _, out = self.run_cli("check", "--all-warnings")
        self.assertEqual(out.count("WARN  [entry-format]"), 8)


class RealDataTest(unittest.TestCase):
    def test_current_data_has_no_errors(self):
        findings, (files, tables, entries) = cd.run_checks(str(ROOT / "Data"))
        errors = [f.text() for f in findings if f.severity == "ERROR"]
        self.assertEqual(errors, [])
        self.assertEqual(files, len(list((ROOT / "Data").glob("*.lua"))))
        self.assertGreater(entries, 80000)


class SearchTest(unittest.TestCase):
    def search(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cd.main(["--data-dir", str(ROOT / "Data"), "search", *args])
        return code, out.getvalue()

    def test_finds_english_keys_swedish_values_and_spell_source_text(self):
        code, out = self.search("Accept", "--exact", "--lang", "en", "--table", "ui")
        self.assertEqual(code, 0)
        self.assertIn('ui[\'Accept\'] (key)  [en]  Accept', out)
        self.assertRegex(out, r"Data/Ui\.lua:\d+")
        code, out = self.search("Acceptera", "--exact", "--lang", "sv")
        self.assertEqual(code, 0)
        self.assertIn("[sv]  Acceptera", out)
        code, out = self.search("Backstab the target", "--lang", "en", "--table", "spell")
        self.assertEqual(code, 0)
        self.assertIn("spell[53].e", out)
        code, out = self.search("Stridsmästare", "--table", "gossip")
        self.assertIn("gossip['12_2c8ce38d']", out)

    def test_finds_comments_including_terminology_notes(self):
        code, out = self.search("Neutral, Friendly och Honored", "--lang", "comment")
        self.assertEqual(code, 0)
        self.assertIn("[comment]", out)
        code, out = self.search("alternativ", "--lang", "comment", "--table", "ui")      # trailing comment on an entry
        self.assertIn("ui['Maximum']", out)
        self.assertIn("Högsta antal", out)

    def test_case_options_limits_and_no_match(self):
        self.assertEqual(self.search("sharptalons klo", "--lang", "sv", "--table", "quest")[0], 0)
        self.assertEqual(self.search("sharptalons klo", "--case-sensitive", "--table", "quest")[0], 1)
        code, out = self.search("a", "--max", "3")
        self.assertEqual(out.count("\n"), 4)                  # 3 hits and the summary line
        self.assertRegex(out, r"\d+ match\(es\), showing the first 3")
        code, out = self.search("zzzz-not-in-any-data-file")
        self.assertEqual(code, 1)
        self.assertIn("0 match(es)", out)

    def test_gossip_key_command_and_default_command(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cd.main(["gossip-key", "Battlemaster"]), 0)
        self.assertEqual(out.getvalue().strip(), "12_2c8ce38d")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cd.main(["gossip-key", "Hi Thrall.", "--player", "Thrall"]), 0)
        self.assertEqual(out.getvalue().strip(), cd.gossip_key("Hi $N."))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cd.main(["--data-dir", str(ROOT / "Data")])      # no command: check
        self.assertEqual(code, 0)
        self.assertIn("RESULT: OK", out.getvalue())

    def test_script_runs_from_any_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, str(TOOL), "gossip-key", "Mage"], capture_output=True, text=True, cwd=tmp)
        self.assertEqual((result.returncode, result.stdout.strip()), (0, "4_7c88f2ff"))


if __name__ == "__main__":
    unittest.main()
