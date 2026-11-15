#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Returntests for tools/verify-segmentation.py (stdlib unittest)."""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "verify-segmentation.py"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_segmentation", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


vs = load_module()


def write_file(dirpath, name, text):
    path = os.path.join(dirpath, name)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return path


def run_tool(src, seg, review=None):
    cmd = [sys.executable, str(SCRIPT), src, seg]
    if review:
        cmd.append(review)
    return subprocess.run(cmd, capture_output=True, text=True)


SRC = (
    "id\ttext\n"
    "568\tThe Defense of Grom'golCommander Aggro'gosh wants you to kill 15 raptors."
    "Throm'ka, $c!$b$bReport back to me.\n"
    "1205\tDeadmireBring Deadmire's Tooth to Melor.$B$BHis time to die.\n"
    "62036\t WANTED: Stonesplitter RockRockjaw raid our herds.Take 4 Rocks as proof.\n"
)
SEG_OK = (
    "568\tThe Defense of Grom'gol\tCommander Aggro'gosh wants you to kill 15 raptors.\t"
    "Throm'ka, $c!$b$bReport back to me.\t\t\n"
    "1205\tDeadmire\tBring Deadmire's Tooth to Melor.\t$B$BHis time to die.\t\t\n"
    "62036\tWANTED: Stonesplitter Rock\tRockjaw raid our herds.\t\t\tTake 4 Rocks as proof.\n"
)


class SegmentationToolTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_exact_partition_passes_without_review_file(self):
        src = write_file(self.dir, "src.tsv", SRC)
        seg = write_file(self.dir, "seg.tsv", SEG_OK)
        res = run_tool(src, seg, review=os.path.join(self.dir, "rev.tsv"))
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("RESULTAT: OK", res.stdout)
        self.assertIn("ingen review-fil behovdes", res.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "rev.tsv")))

    def test_documented_leading_whitespace_normalization(self):
        src = write_file(self.dir, "src.tsv", SRC.splitlines()[-1] + "\n")
        seg = write_file(self.dir, "seg.tsv",
                         "62036\tWANTED: Stonesplitter Rock\tRockjaw raid our herds.\t\t\tTake 4 Rocks as proof.\n")
        res = run_tool(src, seg)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("RESULTAT: OK", res.stdout)
        self.assertIn("ruttade till granskning: 0", res.stdout)

    def test_empty_title_row_routed_to_review(self):
        src = write_file(self.dir, "src.tsv", SRC.splitlines()[-1] + "\n")
        seg = write_file(self.dir, "seg.tsv",
                         "62036\t\tWANTED: Stonesplitter RockRockjaw raid our herds.Take 4 Rocks as proof.\t\t\t\n")
        res = run_tool(src, seg)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("ruttade till granskning: 1", res.stdout)
        review = os.path.join(os.path.dirname(src), "review", "src-en-review.tsv")
        with open(review, encoding="utf-8") as fh:
            self.assertIn("titeln ar tom", fh.read())
    def test_concat_mismatch_is_error_and_routed(self):
        src = write_file(self.dir, "src.tsv", SRC.splitlines()[1] + "\n")
        seg = write_file(self.dir, "seg.tsv",
                         "568\tThe Defense of Grom'gol\tCommander Aggro'gosh wants you to kill 15 raptors. "
                         "Throm'ka, $c!$b$bReport back to me.\t\t\t\n")
        res = run_tool(src, seg)
        self.assertEqual(res.returncode, 1)
        self.assertIn("sammanfogningen stammer inte", res.stdout)
        review = os.path.join(os.path.dirname(src), "review", "src-en-review.tsv")
        self.assertTrue(os.path.exists(review))
        with open(review, encoding="utf-8") as fh:
            self.assertIn("568", fh.read())

    def test_added_space_between_fields_is_error(self):
        src = write_file(self.dir, "src.tsv", SRC.splitlines()[1] + "\n")
        seg = write_file(self.dir, "seg.tsv",
                         "568\tThe Defense of Grom'gol \tCommander Aggro'gosh wants you to kill 15 raptors.\t\t\t\n")
        res = run_tool(src, seg)
        self.assertEqual(res.returncode, 1)

    def test_missing_unexpected_and_optional_header(self):
        src = write_file(self.dir, "src.tsv", SRC)
        seg = write_file(self.dir, "seg.tsv", SEG_OK.splitlines()[0] + "\n")
        res = run_tool(src, seg)
        self.assertEqual(res.returncode, 1)
        self.assertIn("SAKNAS i segmentering", res.stdout)
        seg2 = write_file(self.dir, "seg2.tsv", SEG_OK + "9999\tX\t\t\t\t\n")
        res = run_tool(src, seg2)
        self.assertEqual(res.returncode, 1)
        self.assertIn("OKANDA id", res.stdout)
        seg3 = write_file(self.dir, "seg3.tsv",
                          "id\ttitle\tobjectives\tdescription\tprogress\treward\n" + SEG_OK)
        res = run_tool(src, seg3)
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_blank_line_is_error(self):
        src = write_file(self.dir, "src.tsv", SRC)
        seg = write_file(self.dir, "seg.tsv", SEG_OK.splitlines()[0] + "\n\n" + "\n".join(SEG_OK.splitlines()[1:]) + "\n")
        res = run_tool(src, seg)
        self.assertEqual(res.returncode, 1)
        self.assertIn("blank rad", res.stdout)

    def test_fragment_rows_routed_to_review(self):
        src = write_file(self.dir, "src.tsv",
                         "id\ttext\n"
                         "95534\t< The rest of the note is singed. >\n"
                         "97539\t$C, bring me some from the spiders.\n")
        seg = write_file(self.dir, "seg.tsv",
                         "95534\t\t< The rest of the note is singed. >\t\t\t\n"
                         "97539\t\t$C, bring me some from the spiders.\t\t\t\n")
        res = run_tool(src, seg)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("ruttade till granskning: 2", res.stdout)
        review = os.path.join(os.path.dirname(src), "review", "src-en-review.tsv")
        self.assertTrue(os.path.exists(review))
        with open(review, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        self.assertEqual(lines[0].split("\t")[:2], ["id", "orsak"])
        self.assertIn("95534", lines[1])
        self.assertIn("fragment", lines[1])
        self.assertIn("97539", lines[2])
    def test_review_file_has_reason_and_kalla_columns(self):
        src = write_file(self.dir, "src.tsv", "id\ttext\n11\tPlain text here.\n")
        seg = write_file(self.dir, "seg.tsv", "11\t\tPlain text here.\t\t\t\n")
        res = run_tool(src, seg)
        self.assertEqual(res.returncode, 0, res.stdout)
        review = os.path.join(os.path.dirname(src), "review", "src-en-review.tsv")
        with open(review, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("kalla", lines[0])
        self.assertIn("titeln ar tom", lines[1])

    def test_column_count_is_error(self):
        src = write_file(self.dir, "src.tsv", SRC.splitlines()[1] + "\n")
        seg = write_file(self.dir, "seg.tsv", "568\ttitle only five columns\t\t\t\n")
        res = run_tool(src, seg)
        self.assertEqual(res.returncode, 1)
        self.assertIn("5 kolumner (vantade 6)", res.stdout)

    def test_real_batch14_roundtrip_routes_only_98070(self):
        src = ROOT / "translation" / "batches" / "quests-batch-14.tsv"
        if not src.exists():
            self.skipTest("quests-batch-14.tsv saknas")
        seg = write_file(self.dir, "seg14.tsv",
                         "1482\tThe Corrupter\tBring an Oracle Crystal to Maurin Bonesplitter in Desolace.\t"
                         "An oracle crystal would do nicely. They are crafted by the naga for their oracles to use."
                         "$B$BNorthwest of here, along the coast, is a vast coral reef that the naga have taken as "
                         "their home when this close to the shore. You can find their oracles there. The Slitherblade "
                         "are deadly and will not react kindly to your intrusions, so be careful and make haste.$B$B"
                         "When you return, we shall see about finding this demon lord Azrethoc.\t\t\n"
                         "98070\t\t\tGo, slay as many of these harpies as you are able. Return to me once the deed "
                         "has been done, and I will reward you well for your efforts.\t\t\n"
                         "639\tSigil of Strom\tGet the Sigil of Strom for Zengu in Hammerfall.\t"
                         "In ancient times, trolls fought against the Arathorian Empire and our most capable "
                         "adversary, Lord Ignaeus of Strom, named Trollbane. He rode into battle wielding "
                         "Trol'kalar--troll slayer, in their ancient tongue.$b$bBut now the sons of Trollbane are "
                         "weakened, their stronghold brought to ruin.$b$bThe sword is protected by several sigils "
                         "that were divided among the survivors of Stromgarde, and we must retrieve them.$b$b"
                         "The first was taken by the Syndicate, one of their men in Stromgarde should have it.\t\t\n")
        res = run_tool(str(src), seg, review=os.path.join(self.dir, "rev14.tsv"))
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("RESULTAT: OK", res.stdout)
        with open(os.path.join(self.dir, "rev14.tsv"), encoding="utf-8") as fh:
            body = fh.read()
        self.assertIn("98070", body)
        self.assertIn("titeln ar tom", body)
        self.assertNotIn("1482\tThe Corrupter\t", body)
        self.assertNotIn("639\tSigil of Strom\t", body)


if __name__ == "__main__":
    unittest.main()
