#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One small translation round from source files to a direct merge, using an external work directory."""
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


def run(script, *args, cwd):
    result = subprocess.run([sys.executable, str(TOOLS / script), *map(str, args)],
                            capture_output=True, text=True, cwd=cwd)
    return result


def load_wdb_helper():
    spec = importlib.util.spec_from_file_location("combine_helper", ROOT / "tests" / "test_combine_wdb.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


HEAD = "local _, WPS = ...\n"
ENGLISH = ("Wolf Hunt" + "Kill the wolves." + "Go and kill 5 wolves, $N.$B$BReturn to me when done." + "Well done, $N.")


class WorkflowRoundTest(unittest.TestCase):
    def test_round_from_wdb_to_merged_lua_without_creating_translation_or_extra_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"                      # stand-in for the repository: must stay clean
            data = repo / "Data"
            data.mkdir(parents=True)
            (data / "Quest.lua").write_text(HEAD + 'WPS.L.quest = {\n[1]={t="Redan klar"},\n}\n', encoding="utf-8")
            (data / "Npc.lua").write_text(HEAD + 'WPS.L.npc = {\n[10]="Redan klar",\n}\n', encoding="utf-8")
            before = {str(p.relative_to(repo)): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
            work = root / "work"

            # 1. source: a WDB cache with one translated and two new quests
            wdb = root / "wdb"
            wdb.mkdir()
            helper = load_wdb_helper()
            helper.quest_wdb(str(wdb / "a.wdb"), [(1, helper.LONG_A), (2, ENGLISH), (3, helper.LONG_B)])
            r = run("combine-wdb.py", wdb, "--work-dir", work, cwd=repo)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            quest_cache = work / "cache" / "questcache-en.tsv"
            creature_cache = root / "creaturecache-en.tsv"
            creature_cache.write_text("id\tname\ttitle\n10\tDone\t\n11\tWolf Scout\tHunter\n", encoding="utf-8")

            # 2. select what is missing from Data/*.lua
            r = run("select-untranslated.py", quest_cache, creature_cache, "--work-dir", work, "--data-dir", data, cwd=repo)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            worklist = (work / "untranslated" / "quests-001.tsv").read_text(encoding="utf-8")
            self.assertEqual([l.split("\t")[0] for l in worklist.splitlines()[1:]], ["2", "3"])

            # 3. batches
            r = run("make-batches.py", "--work-dir", work, cwd=repo)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            src = work / "batches" / "quests-batch-01.tsv"
            npc_src = work / "batches" / "npcs-batch-01.tsv"
            self.assertTrue(src.exists() and npc_src.exists())

            # 4. "translate" (by hand: the tools only validate), then validate the output
            out = work / "out"
            out.mkdir()
            rows = ["id\ttitle\tobjectives\tdescription\tprogress\treward"]
            for line in src.read_text(encoding="utf-8").splitlines()[1:]:
                rid, text = line.split("\t")
                if rid == "2":
                    rows.append("2\tVargjakt\tDöda vargarna.\tGå och döda 5 vargar, $N.$B$BÅtervänd när du är klar.\\r\\n\\r\\nSnart.\t\tBra jobbat, $N.")
                else:
                    rows.append(f'{rid}\tTitel\t\tText med "citat" och C:\\dir.\t\t')
            (out / "quests-batch-01-sv.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
            (out / "npcs-batch-01-sv.tsv").write_text("id\tnamn\n11\tVargspejare\n", encoding="utf-8")
            r = run("validate-batch.py", src, out / "quests-batch-01-sv.tsv", "quests", cwd=repo)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

            # 5. dry run, then the real merge into the main files
            r = run("merge-translation.py", "quests", "--input", out, "--data-dir", data, "--dry-run", cwd=repo)
            self.assertIn("would add: 2", r.stdout)
            self.assertEqual(r.returncode, 0)
            self.assertEqual((data / "Quest.lua").read_text(encoding="utf-8"), HEAD + 'WPS.L.quest = {\n[1]={t="Redan klar"},\n}\n')
            for kind in ("quests", "npcs"):
                r = run("merge-translation.py", kind, "--input", out, "--data-dir", data, cwd=repo)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

            quest = (data / "Quest.lua").read_text(encoding="utf-8")
            self.assertIn('[2]={t="Vargjakt",d="Gå och döda 5 vargar, $N.$B$BÅtervänd när du är klar.\\n\\nSnart.",o="Döda vargarna.",c="Bra jobbat, $N."},', quest)
            self.assertIn('[1]={t="Redan klar"},', quest)
            self.assertNotIn("\\\\r", quest)
            self.assertIn('[11]="Vargspejare",', (data / "Npc.lua").read_text(encoding="utf-8"))

            # 6. nothing but the two data files changed; no translation/ and no Extra file anywhere
            after = {str(p.relative_to(repo)): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
            self.assertEqual(sorted(after), sorted(before))
            self.assertEqual([k for k in after if after[k] != before[k]], ["Data/Npc.lua", "Data/Quest.lua"])
            self.assertFalse(any("translation" in k or "Extra" in k for k in after))
            self.assertFalse((repo / "translation").exists())
            self.assertTrue((work / "cache").is_dir() and (work / "batches").is_dir() and (work / "out").is_dir())

            if shutil.which("luac5.1"):
                subprocess.run(["luac5.1", "-p", str(data / "Quest.lua"), str(data / "Npc.lua")], check=True)


if __name__ == "__main__":
    unittest.main()
