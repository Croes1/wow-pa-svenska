#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/merge-translation.py: insert new rows into Data/*.lua, never regenerate."""
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "merge-translation.py"
DUMP = ROOT / "tools" / "dump-runtime.lua"
LUA = shutil.which("lua5.1")
LUAC = shutil.which("luac5.1")

HEAD = "-- header\nlocal _, WPS = ...\n"
QUEST = (HEAD + "WPS.L.quest = {\n"
         '[10]={t="Gammal",d="Behåll mig.",o="Mål",l={"Rad"}},\n'
         '[30]={t="Också gammal"},\n'
         "}\n")
NPC = HEAD + 'WPS.L.npc = {\n[3]="Köttätare",\n[30]="Skogsspindel",\n}\n'
UI = HEAD + 'WPS.L.ui = {\n["Zebra"]="Sebra",\n["Apple"]="Äpple",\n}\n'
CORE = 'local ADDON, WPS = ...\nWPS.L = { quest = {}, npc = {}, ui = {} }\n'
TOC = "## Interface: 16001\n\nCore.lua\nData\\Quest.lua\nData\\Npc.lua\nData\\Ui.lua\n"


def load_tool():
    spec = importlib.util.spec_from_file_location("merge_translation", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class MergeTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addon = Path(self.tmp.name) / "addon"
        self.data = self.addon / "Data"
        self.data.mkdir(parents=True)
        self.work = Path(self.tmp.name) / "work"
        self.work.mkdir()
        (self.data / "Quest.lua").write_text(QUEST, encoding="utf-8")
        (self.data / "Npc.lua").write_text(NPC, encoding="utf-8")
        (self.data / "Ui.lua").write_text(UI, encoding="utf-8")
        (self.addon / "Core.lua").write_text(CORE, encoding="utf-8")
        (self.addon / "wow_pa_svenska.toc").write_text(TOC, encoding="utf-8")

    def tsv(self, name, text):
        path = self.work / name
        path.write_text(text, encoding="utf-8", newline="")
        return path

    def run_tool(self, *args, expect=None):
        result = subprocess.run([sys.executable, str(TOOL), *args, "--data-dir", str(self.data)],
                                capture_output=True, text=True)
        if expect is not None:
            self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def read(self, name):
        return (self.data / name).read_text(encoding="utf-8")

    def snapshot(self):
        return {str(p.relative_to(self.addon)): p.read_bytes() for p in self.addon.rglob("*") if p.is_file()}

    def dump(self):
        out = subprocess.run([LUA, str(DUMP), str(self.addon)], capture_output=True, check=True).stdout
        return [line.split("\t") for line in out.decode("utf-8").splitlines()]


class EscapedLineBreakTest(MergeTestCase):
    """Regression: a line break written as \\r\\n in a batch row must become a real line break."""

    def quest_row(self, qid, title, objectives, description, progress="", reward=""):
        return "\t".join([str(qid), title, objectives, description, progress, reward])

    def test_escaped_crlf_becomes_a_real_line_break_not_a_literal_backslash_sequence(self):
        src = self.tsv("quests-batch-01-sv.tsv", self.quest_row(
            99051, "Titel", "Hitta saken.", "Första raden.\\r\\n\\r\\nAndra raden.\\nTredje.$B$BFjärde.") + "\n")
        self.run_tool("quests", "--input", str(src), expect=0)
        text = self.read("Quest.lua")
        self.assertIn('d="Första raden.\\n\\nAndra raden.\\nTredje.$B$BFjärde."', text)   # Lua \n escapes in the source
        self.assertNotIn("\\\\r", text)
        self.assertNotIn("\\\\n", text)
        self.assertNotIn("\\r", text)
        from_parse = load_datalua().DataFile.read(self.data / "Quest.lua").table("quest").get(99051)
        self.assertEqual(from_parse["d"], "Första raden.\n\nAndra raden.\nTredje.$B$BFjärde.")

    @unittest.skipUnless(LUA, "lua5.1 is not installed; the runtime dump cannot run")
    def test_runtime_dump_has_real_line_breaks_and_no_literal_backslash_r_or_n(self):
        src = self.tsv("quests-batch-01-sv.tsv", self.quest_row(
            99051, "Titel", "Mål\\r\\n", "A\\r\\n\\r\\nB") + "\n")
        self.run_tool("quests", "--input", str(src), expect=0)
        rows = {(r[2], r[3]): r[5] for r in self.dump() if r[0] == "quest"}
        # dump-runtime writes a real line break as \n (two characters) and a literal
        # backslash+n as \\n (three characters), so these two strings are different on purpose.
        self.assertEqual(rows[("99051", "d")], "A\\n\\nB")
        self.assertEqual(rows[("99051", "o")], "Mål\\n")
        for (_key, _field), value in rows.items():
            self.assertNotIn("\\\\r", value)
            self.assertNotIn("\\\\n", value)
            self.assertNotIn("\\r", value)

    def test_quotes_backslashes_and_placeholders_round_trip(self):
        text = 'Han sa "hej" till $N på C:\\dir, %s |cffff0000röd|r $2oa $B'
        src = self.tsv("quests-batch-01-sv.tsv", self.quest_row(5, "T", "", text) + "\n")
        self.run_tool("quests", "--input", str(src), expect=0)
        value = load_datalua().DataFile.read(self.data / "Quest.lua").table("quest").get(5)
        self.assertEqual(value, {"t": "T", "d": text})
        if LUAC:
            subprocess.run([LUAC, "-p", str(self.data / "Quest.lua")], check=True)
        if LUA:
            rows = {(r[2], r[3]): r[5] for r in self.dump() if r[0] == "quest"}
            self.assertEqual(rows[("5", "d")], text.replace("\\", "\\\\"))     # dump escapes the backslash

    def test_npc_name_with_quote_and_ui_text_with_escapes(self):
        npc = self.tsv("npcs-batch-01-sv.tsv", 'id\tnamn\n5\tDen "Store" Ogern\n')
        self.run_tool("npcs", "--input", str(npc), expect=0)
        self.assertIn('[5]="Den \\"Store\\" Ogern",', self.read("Npc.lua"))
        en = self.tsv("dump-en.tsv", "id\tarea\ten\n001\t?\tLine one\\nLine two\n")
        sv = self.tsv("dump-sv.tsv", "id\tsv\n001\tRad ett\\nRad två\n")
        self.run_tool("ui", "--input", str(en), "--sv", str(sv), expect=0)
        value = load_datalua().DataFile.read(self.data / "Ui.lua").table("ui").get("Line one\nLine two")
        self.assertEqual(value, "Rad ett\nRad två")


class MergeBehaviourTest(MergeTestCase):
    def test_new_quests_are_inserted_in_place_and_old_lines_are_untouched(self):
        src = self.tsv("quests-batch-01-sv.tsv",
                       "id\ttitle\tobjectives\tdescription\tprogress\treward\n"
                       "40\tSist\t\tText\t\t\n"
                       "5\tFörst\tMål\tBeskrivning\tFramsteg\tBelöning\n"
                       "20\tMitt\t\t\t\tBara belöning\n")
        result = self.run_tool("quests", "--input", str(src), expect=0)
        self.assertIn("added: 3", result.stdout)
        new = self.read("Quest.lua")
        self.assertEqual(new.split("\n"), [
            "-- header", "local _, WPS = ...", "WPS.L.quest = {",
            '[5]={t="Först",d="Beskrivning",o="Mål",p="Framsteg",c="Belöning"},',
            '[10]={t="Gammal",d="Behåll mig.",o="Mål",l={"Rad"}},',
            '[20]={t="Mitt",c="Bara belöning"},',
            '[30]={t="Också gammal"},',
            '[40]={t="Sist",d="Text"},',
            "}", ""])

    def test_directory_input_reads_batches_in_numeric_order_and_ignores_other_files(self):
        self.tsv("quests-batch-02-sv.tsv", "2\tB\t\t\t\t\n")
        self.tsv("quests-batch-10-sv.tsv", "3\tC\t\t\t\t\n")
        self.tsv("quests-batch-01-sv.tsv", "1\tA\t\t\t\t\n")
        self.tsv("quests-batch-01.tsv", "9\tEnglish source\n")        # not an -sv output
        self.tsv("npcs-batch-01-sv.tsv", "50\tNpc\n")
        result = self.run_tool("quests", "--input", str(self.work), expect=0)
        reads = [l for l in result.stdout.splitlines() if l.startswith("reading")]
        self.assertEqual([Path(l.split(" ", 1)[1]).name for l in reads],
                         ["quests-batch-01-sv.tsv", "quests-batch-02-sv.tsv", "quests-batch-10-sv.tsv"])
        self.assertEqual(load_datalua().DataFile.read(self.data / "Quest.lua").table("quest").keys(), [1, 2, 3, 10, 30])

    def test_running_twice_is_idempotent(self):
        src = self.tsv("quests-batch-01-sv.tsv", "1\tA\t\t\t\t\n")
        self.run_tool("quests", "--input", str(src), expect=0)
        first = self.snapshot()
        result = self.run_tool("quests", "--input", str(src), expect=0)
        self.assertIn("added: 0", result.stdout)
        self.assertIn("skipped (already in Quest.lua): 1", result.stdout)
        self.assertEqual(self.snapshot(), first)

    def test_existing_translations_are_never_overwritten_by_default(self):
        src = self.tsv("quests-batch-01-sv.tsv", "10\tNY TITEL\t\tNY TEXT\t\t\n2\tNy\t\t\t\t\n")
        result = self.run_tool("quests", "--input", str(src), expect=0)
        self.assertIn("added: 1   skipped (already in Quest.lua): 1", result.stdout)
        self.assertIn("SKIP  Quest.lua [10] already exists", result.stdout)
        text = self.read("Quest.lua")
        self.assertIn('[10]={t="Gammal",d="Behåll mig.",o="Mål",l={"Rad"}},', text)
        self.assertNotIn("NY TITEL", text)

    def test_overwrite_replaces_only_the_colliding_entry_and_reports_old_and_new(self):
        src = self.tsv("npcs-batch-01-sv.tsv", "3\tNy kötätare\n7\tNy\n")
        result = self.run_tool("npcs", "--input", str(src), "--overwrite", expect=0)
        self.assertIn("old: 'Köttätare'", result.stdout)
        self.assertIn("new: 'Ny kötätare'", result.stdout)
        self.assertEqual(self.read("Npc.lua").split("\n")[3:7],
                         ['[3]="Ny kötätare",', '[7]="Ny",', '[30]="Skogsspindel",', "}"])

    def test_dry_run_writes_nothing_and_still_reports_collisions(self):
        src = self.tsv("quests-batch-01-sv.tsv", "10\tx\t\t\t\t\n2\tNy\t\t\t\t\n")
        before = self.snapshot()
        result = self.run_tool("quests", "--input", str(src), "--dry-run", expect=0)
        self.assertIn("would add: 1   skipped (already in Quest.lua): 1", result.stdout)
        self.assertIn("nothing written", result.stdout)
        self.assertEqual(self.snapshot(), before)

    def test_no_extra_file_is_created_and_the_toc_is_untouched(self):
        for kind, name, row in (("quests", "quests-batch-01-sv.tsv", "1\tA\t\t\t\t\n"),
                                ("npcs", "npcs-batch-01-sv.tsv", "1\tNpc\n")):
            self.run_tool(kind, "--input", str(self.tsv(name, row)), expect=0)
        after = self.snapshot()
        self.assertEqual(sorted(after), ["Core.lua", "Data/Npc.lua", "Data/Quest.lua", "Data/Ui.lua", "wow_pa_svenska.toc"])
        self.assertEqual(after["wow_pa_svenska.toc"], TOC.encode("utf-8"))
        self.assertEqual(after["Data/Ui.lua"], UI.encode("utf-8"))
        self.assertFalse(list(self.data.glob("*Extra*")))
        self.assertFalse((self.addon / "translation").exists())

    def test_ui_rows_are_paired_by_id_and_appended_after_the_existing_entries(self):
        en = self.tsv("dump-en.tsv", "id\tarea\ten\n001\tA\tMango\n002\tB\tBanana\n003\tC\tApple\n")
        sv = self.tsv("dump-sv.tsv", "id\tsv\n003\tÄpple (ny)\n001\tMango\n002\tBanan\n")
        result = self.run_tool("ui", "--input", str(en), "--sv", str(sv), expect=0)
        self.assertIn("added: 2   skipped (already in Ui.lua): 1", result.stdout)
        self.assertEqual(self.read("Ui.lua").split("\n")[3:8],
                         ['["Zebra"]="Sebra",', '["Apple"]="Äpple",', '["Banana"]="Banan",', '["Mango"]="Mango",', "}"])


class RejectionTest(MergeTestCase):
    def assertAborted(self, kind, name, text, fragment, *extra):
        before = self.snapshot()
        result = self.run_tool(kind, "--input", str(self.tsv(name, text)), *extra)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(fragment, result.stderr)
        self.assertIn("nothing was written", result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_structural_errors_abort_the_whole_run(self):
        self.assertAborted("quests", "a.tsv", "1\tA\t\t\t\t\n2\tB\tonly three\n", "3 columns, expected 6")
        self.assertAborted("quests", "b.tsv", "x\tA\t\t\t\t\n", "non-numeric id")
        self.assertAborted("quests", "c.tsv", "1\tA\t\t\t\t\n1\tB\t\t\t\t\n", "id 1 appears in both")
        self.assertAborted("npcs", "d.tsv", "1\tA\textra\n", "3 columns, expected 2")
        self.assertAborted("npcs", "e.tsv", "1\tA\n\n2\tB\n", "blank line")
        self.assertAborted("npcs", "f.tsv", "1\tA\r\n", "CR characters")

    def test_id_repeated_across_batch_files_aborts(self):
        self.tsv("quests-batch-01-sv.tsv", "7\tA\t\t\t\t\n")
        self.tsv("quests-batch-02-sv.tsv", "7\tB\t\t\t\t\n")
        before = self.snapshot()
        result = self.run_tool("quests", "--input", str(self.work))
        self.assertEqual(result.returncode, 1)
        self.assertIn("id 7 appears in both", result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_ui_files_must_have_the_same_ids(self):
        en = self.tsv("dump-en.tsv", "id\tarea\ten\n001\tA\tOne\n002\tA\tTwo\n")
        sv = self.tsv("dump-sv.tsv", "id\tsv\n001\tEtt\n")
        before = self.snapshot()
        result = self.run_tool("ui", "--input", str(en), "--sv", str(sv))
        self.assertEqual(result.returncode, 1)
        self.assertIn("ids differ", result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_unusable_rows_are_rejected_and_skipped_while_the_rest_is_merged(self):
        src = self.tsv("quests-batch-01-sv.tsv", "1\t\t\t\t\t\n2\tFin\t\t\t\t\n3\tTitel\t\tTecken\x01\t\t\n")
        result = self.run_tool("quests", "--input", str(src), expect=0)
        self.assertIn("added: 1   skipped (already in Quest.lua): 0   rejected: 2", result.stdout)
        self.assertIn("REJECT", result.stdout)
        self.assertIn("every field is empty", result.stdout)
        self.assertIn("control character", result.stdout)
        self.assertEqual(load_datalua().DataFile.read(self.data / "Quest.lua").table("quest").keys(), [2, 10, 30])
        npc = self.tsv("npcs-batch-01-sv.tsv", "8\t \n9\tNamn\n")
        result = self.run_tool("npcs", "--input", str(npc), expect=0)
        self.assertIn("added: 1   skipped (already in Npc.lua): 0   rejected: 1", result.stdout)

    def test_unparseable_target_is_never_touched(self):
        (self.data / "Npc.lua").write_text(HEAD + 'WPS.L.npc = {\n[3]=weird,\n}\n', encoding="utf-8")
        self.assertAborted("npcs", "n.tsv", "5\tNy\n", "Npc.lua:4:")

    def test_types_without_a_runtime_table_are_refused(self):
        for kind in ("gameobjects", "pagetext"):
            result = self.run_tool(kind, "--input", str(self.tsv("x.tsv", "1\tx\n")))
            self.assertEqual(result.returncode, 2)
            self.assertIn("no runtime table", result.stderr)

    def test_input_is_required(self):
        result = subprocess.run([sys.executable, str(TOOL), "quests"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--input", result.stderr)

    def test_a_failing_syntax_check_leaves_the_target_untouched(self):
        tool = load_tool()
        src = self.tsv("quests-batch-01-sv.tsv", "1\tA\t\t\t\t\n")
        before = self.snapshot()

        def refuse(_tmp):
            raise tool.datalua.DataError("luac5.1 rejected the result")

        with mock.patch.object(tool, "luac_check", refuse), \
                mock.patch("sys.stderr"), mock.patch("sys.stdout"):
            code = tool.main(["quests", "--input", str(src), "--data-dir", str(self.data)])
        self.assertEqual(code, 1)
        self.assertEqual(self.snapshot(), before)          # no changed file, no leftover temp file


_datalua = None


def load_datalua():
    global _datalua
    if _datalua is None:
        spec = importlib.util.spec_from_file_location("datalua", ROOT / "tools" / "datalua.py")
        _datalua = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_datalua)
    return _datalua


if __name__ == "__main__":
    unittest.main()
