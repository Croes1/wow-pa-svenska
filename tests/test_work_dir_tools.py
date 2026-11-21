#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The tools take an external work directory or explicit paths and never write into translation/."""
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
LUA = shutil.which("lua5.1")


def run(script, *args, cwd=None):
    return subprocess.run([sys.executable, str(TOOLS / script), *map(str, args)],
                          capture_output=True, text=True, cwd=cwd)


def load(name, filename):
    return load_path(name, TOOLS / filename)


def load_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class WorkDirCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.work = self.root / "work"
        self.cwd = self.root / "cwd"          # a stand-in for "the repository root"
        self.cwd.mkdir()

    def write(self, path, text):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")
        return path

    def assertNothingInCwd(self):
        self.assertEqual(list(self.cwd.iterdir()), [], "a tool wrote into the working directory")


class SourceHygieneTest(unittest.TestCase):
    def test_no_tool_mentions_the_old_directory_or_the_extra_files(self):
        for path in sorted(TOOLS.iterdir()):
            if path.suffix not in (".py", ".lua"):
                continue
            text = path.read_text(encoding="utf-8")
            with self.subTest(path.name):
                self.assertNotIn("translation/", text)
                self.assertNotIn('"translation"', text)
                self.assertNotIn("UiExtra", text)
                self.assertNotIn("QuestExtra", text)
                self.assertNotIn("NpcExtra", text)


class CombineWdbTest(WorkDirCase):
    def make_wdb(self):
        helper = load_path("test_combine_wdb_helpers", ROOT / "tests" / "test_combine_wdb.py")
        quest_wdb, LONG_A = helper.quest_wdb, helper.LONG_A
        folder = self.root / "wdb"
        folder.mkdir()
        quest_wdb(str(folder / "a.wdb"), [(1, LONG_A)])
        return folder

    def test_work_dir_gets_a_cache_folder_and_nothing_is_overwritten_without_force(self):
        folder = self.make_wdb()
        first = run("combine-wdb.py", folder, "--work-dir", self.work, cwd=self.cwd)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        out = self.work / "cache" / "questcache-en.tsv"
        self.assertTrue(out.exists())
        self.assertIn(str(out), first.stdout)
        out.write_text("EDITED\n", encoding="utf-8")
        again = run("combine-wdb.py", folder, "--work-dir", self.work, cwd=self.cwd)
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("refusing to overwrite", again.stderr)
        self.assertEqual(out.read_text(encoding="utf-8"), "EDITED\n")
        forced = run("combine-wdb.py", folder, "--work-dir", self.work, "--force", cwd=self.cwd)
        self.assertEqual(forced.returncode, 0)
        self.assertNotEqual(out.read_text(encoding="utf-8"), "EDITED\n")
        self.assertNothingInCwd()

    def test_an_output_location_is_required(self):
        result = run("combine-wdb.py", self.make_wdb(), cwd=self.cwd)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--work-dir", result.stderr)
        self.assertNothingInCwd()


class SelectAndBatchTest(WorkDirCase):
    def setUp(self):
        super().setUp()
        self.data = self.root / "Data"
        head = "local _, WPS = ...\n"
        self.write(self.data / "Quest.lua", head + 'WPS.L.quest = {\n[1]={t="Gammal"},\n}\n')
        self.write(self.data / "Npc.lua", head + 'WPS.L.npc = {\n[10]="Gammal",\n}\n')
        self.quests = self.write(self.root / "q.tsv", "id\ttext\n1\tOld\n2\tNew one\n3\tNew two\n")
        self.npcs = self.write(self.root / "n.tsv", "id\tname\ttitle\n10\tOld\t\n11\tNew\tGuard\n")

    def select(self):
        return run("select-untranslated.py", self.quests, self.npcs, "--work-dir", self.work,
                   "--data-dir", self.data, cwd=self.cwd)

    def test_selector_reads_translated_ids_from_the_data_files_and_writes_to_the_work_dir(self):
        result = self.select()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.work / "untranslated" / "quests-001.tsv").read_text(encoding="utf-8"),
                         "id\ttext\n2\tNew one\n3\tNew two\n")
        self.assertEqual((self.work / "untranslated" / "npcs-001.tsv").read_text(encoding="utf-8"),
                         "id\tname\ttitle\n11\tNew\tGuard\n")
        self.assertIn(str(self.work / "untranslated"), result.stdout)
        self.assertNothingInCwd()

    def test_selector_never_overwrites_and_only_lists_new_ids_in_the_next_file(self):
        self.select()
        first = (self.work / "untranslated" / "quests-001.tsv").read_bytes()
        self.quests.write_text("id\ttext\n2\tNew one\n3\tNew two\n4\tNewer\n", encoding="utf-8")
        self.select()
        self.assertEqual((self.work / "untranslated" / "quests-001.tsv").read_bytes(), first)
        self.assertEqual((self.work / "untranslated" / "quests-002.tsv").read_text(encoding="utf-8"),
                         "id\ttext\n4\tNewer\n")

    def test_selector_needs_a_work_dir_and_fails_on_unknown_data_syntax(self):
        result = run("select-untranslated.py", self.quests, self.npcs, "--data-dir", self.data, cwd=self.cwd)
        self.assertEqual(result.returncode, 2)
        (self.data / "Quest.lua").write_text("local _, WPS = ...\nWPS.L.quest = {\n[1]=oops,\n}\n", encoding="utf-8")
        with self.assertRaises(Exception) as cm:
            load("select_untranslated", "select-untranslated.py").main(
                [str(self.quests), str(self.npcs), "--work-dir", str(self.work), "--data-dir", str(self.data)])
        self.assertIn("Quest.lua:3", str(cm.exception))
        self.assertFalse((self.work / "untranslated").exists())

    def test_batches_are_written_to_the_work_dir_and_not_overwritten_without_force(self):
        self.select()
        first = run("make-batches.py", "--work-dir", self.work, cwd=self.cwd)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        batch = self.work / "batches" / "quests-batch-01.tsv"
        self.assertEqual(batch.read_text(encoding="utf-8"), "id\ttext\n2\tNew one\n3\tNew two\n")
        batch.write_text("TRANSLATOR WAS HERE\n", encoding="utf-8")
        again = run("make-batches.py", "--work-dir", self.work, cwd=self.cwd)
        self.assertEqual(again.returncode, 1)
        self.assertIn("already exist", again.stderr)
        self.assertEqual(batch.read_text(encoding="utf-8"), "TRANSLATOR WAS HERE\n")
        forced = run("make-batches.py", "--work-dir", self.work, "--force", cwd=self.cwd)
        self.assertEqual(forced.returncode, 0)
        self.assertEqual(batch.read_text(encoding="utf-8"), "id\ttext\n2\tNew one\n3\tNew two\n")
        self.assertNothingInCwd()

    def test_batches_need_a_work_dir(self):
        result = run("make-batches.py", cwd=self.cwd)
        self.assertEqual(result.returncode, 2)
        self.assertNothingInCwd()


class ParseUidumpTest(WorkDirCase):
    SAVED = ('WPSDB = {\n["uiDump"] = {\n'
             '["New Window"] = "Frame",\n'
             '["Acceptera"] = "Frame",\n'
             '["Skräp"] = "Frame",\n'
             '["Tooltip noise"] = "GameTooltip",\n'
             '["Two\\nLines"] = "Frame",\n'
             '},\n}\n')

    def setUp(self):
        super().setUp()
        self.repo = self.root / "repo"
        head = "local _, WPS = ...\n"
        self.write(self.repo / "Data" / "Ui.lua", head + 'WPS.L.ui = {\n["Accept"]="Acceptera",\n}\n')
        self.write(self.repo / "Data" / "Glossary.lua", head + 'WPS.L.names_general = {\n["Horde"]="Horden",\n}\n')
        self.saved = self.write(self.root / "wow_pa_svenska.lua", self.SAVED)

    def test_extracts_untranslated_texts_to_the_given_file_and_reads_ui_and_glossary(self):
        out = self.work / "ui" / "dump-en.tsv"
        result = run("parse-uidump.py", self.saved, "-o", out, "--repo", self.repo, cwd=self.cwd)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rows = out.read_text(encoding="utf-8").splitlines()
        self.assertEqual(rows[0], "id\tarea\ten")
        # The dump holds what the game displayed: "Acceptera" is a Swedish value already in Ui.lua,
        # "Skräp" contains å/ä/ö so it is taken for Swedish, and the GameTooltip entry is noise
        self.assertEqual([r.split("\t")[2] for r in rows[1:]], ["New Window", "Two\\nLines"])
        self.assertNothingInCwd()

    def test_output_is_required_and_never_overwritten_without_force(self):
        self.assertEqual(run("parse-uidump.py", self.saved, "--repo", self.repo, cwd=self.cwd).returncode, 2)
        out = self.write(self.work / "dump-en.tsv", "KEEP\n")
        result = run("parse-uidump.py", self.saved, "-o", out, "--repo", self.repo, cwd=self.cwd)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(out.read_text(encoding="utf-8"), "KEEP\n")
        self.assertEqual(run("parse-uidump.py", self.saved, "-o", out, "--repo", self.repo, "--force",
                             cwd=self.cwd).returncode, 0)

    def test_it_reads_the_real_data_files_without_error(self):
        out = self.work / "dump-real.tsv"
        result = run("parse-uidump.py", self.saved, "-o", out, cwd=self.cwd)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("Acceptera", out.read_text(encoding="utf-8"))   # a Swedish value in the real Data/Ui.lua


@unittest.skipUnless(LUA, "lua5.1 is not installed; check-ui-translation.lua cannot run")
class CheckUiTranslationTest(WorkDirCase):
    def lua(self, *args):
        return subprocess.run([LUA, str(TOOLS / "check-ui-translation.lua"), *map(str, args)],
                              capture_output=True, text=True, cwd=self.cwd)

    def test_checks_a_pair_against_the_given_ui_file(self):
        ui = self.write(self.root / "Ui.lua",
                        'local _, WPS = ...\nWPS.L.ui = {\n["Accept"]="Acceptera",\n["Level %d"]="Nivå %d",\n}\n')
        en = self.write(self.work / "en.tsv", "id\tarea\ten\n001\tF\tAccept\n002\tF\tLevel 7\n")
        good = self.write(self.work / "sv-good.tsv", "id\tsv\n001\tAcceptera\n002\tNivå 7\n")
        bad = self.write(self.work / "sv-bad.tsv", "id\tsv\n001\tGodkänn\n002\tNivå 7\n")
        ok = self.lua(en, good, ui)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertIn("RESULTAT: OK", ok.stdout)
        nok = self.lua(en, bad, ui)
        self.assertEqual(nok.returncode, 1)
        self.assertIn("FEL: 001", nok.stdout)
        self.assertNothingInCwd()

    def test_defaults_to_the_data_ui_file_of_the_repository_from_any_directory(self):
        en = self.write(self.work / "en.tsv", "id\tarea\ten\n001\tF\tAccept\n")
        sv = self.write(self.work / "sv.tsv", "id\tsv\n001\tAcceptera\n")
        result = self.lua(en, sv)             # cwd is an unrelated directory
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
