#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Returntests for tools/validate-batch.py (stdlib unittest)."""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "validate-batch.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_batch", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


vb = load_module()


def write_file(dirpath, name, text):
    path = os.path.join(dirpath, name)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return path


def run_tool(src, dst, kind):
    return subprocess.run([sys.executable, str(SCRIPT), src, dst, kind],
                          capture_output=True, text=True)


# Fem kallrader som tacker $B/$b/$N/$n/$c/$C/$r/$2oa - identiska utdata
# validerar strukturen medan(tokens) ar ororda (varning ar ok).
QUESTS_SRC = (
    "id\ttext\n"
    "568\tThe Defense of Grom'golCommander Aggro'gosh wants you to kill 15 raptors."
    "Throm'ka, $c!$b$bReport back to me, $n.\n"
    "1107\tEncrusted Tail FinsBring 10 Encrusted Tail Fins to Wizzle Brassbolts.$B$BHave you heard of the Vile Reef, $n?\n"
    "94220\tCraftsman's Writ: Pearl-Handled DaggerAcquire the items requested. "
    "<Penned in faded ink, the note is requesting $2oa Pearl-Handled Dagger.>\n"
    "639\tSigil of StromGet the Sigil of Strom for Zengu.$b$bBut now the sons of Trollbane are weakened.\n"
    "93429\tTheir suffering must end. Someone must put them out of their misery.\n"
)


def quests_out(rows):
    """Gor 6-kolumners utdata av (id, body): allt hamnar i titeln."""
    return "".join(f"{rid}\t{body}\t\t\t\t\n" for rid, body in rows)


def pairs_from(src_text):
    rows = []
    for ln in src_text.splitlines():
        if not ln or (ln.split("\t", 1)[0] == "id"):
            continue
        rid, body = ln.split("\t", 1)
        rows.append((rid, body))
    return rows


class ValidatorQuestTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_happy_path_with_headers_exits_zero(self):
        src = write_file(self.dir, "src.tsv", QUESTS_SRC)
        dst = write_file(self.dir, "dst.tsv",
                         "id\ttitle\tobjectives\tdescription\tprogress\treward\n"
                         + quests_out(pairs_from(QUESTS_SRC)))
        res = run_tool(src, dst, "quests")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("RESULTAT: OK", res.stdout)

    def test_headers_optional(self):
        src = write_file(self.dir, "src.tsv", QUESTS_SRC.splitlines()[-1] + "\n")
        dst = write_file(self.dir, "dst.tsv",
                         "93429\tTheir suffering must end. Someone must put them out of their misery.\t\t\t\t\n")
        res = run_tool(src, dst, "quests")
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertNotIn("FEL:", res.stdout)

    def test_partial_record_shows_warning_but_exits_zero(self):
        src = write_file(self.dir, "src.tsv", QUESTS_SRC.splitlines()[-1] + "\n")
        dst = write_file(self.dir, "dst.tsv",
                         "93429\t\t\t\tTheir suffering must end. Someone must put them out of their misery.\t\n")
        res = run_tool(src, dst, "quests")
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("VARNING:", res.stdout)
        self.assertIn("titeln ar tom", res.stdout)
        self.assertIn("RESULTAT: OK", res.stdout)
    def test_missing_id_is_error_exit_one(self):
        src = write_file(self.dir, "src.tsv", QUESTS_SRC)
        rows = pairs_from(QUESTS_SRC)[:-1]
        dst = write_file(self.dir, "dst.tsv", quests_out(rows))
        res = run_tool(src, dst, "quests")
        self.assertEqual(res.returncode, 1)
        self.assertIn("SAKNAS i utdata (1): 93429", res.stdout)

    def test_duplicate_id_is_error(self):
        src = write_file(self.dir, "src.tsv", QUESTS_SRC)
        rows = pairs_from(QUESTS_SRC) + [pairs_from(QUESTS_SRC)[0]]
        dst = write_file(self.dir, "dst.tsv", quests_out(rows))
        res = run_tool(src, dst, "quests")
        self.assertEqual(res.returncode, 1)
        self.assertIn("id 568 forekommer flere ganger", res.stdout)

    def test_unexpected_id_is_error(self):
        src = write_file(self.dir, "src.tsv", QUESTS_SRC)
        dst = write_file(self.dir, "dst.tsv", quests_out(pairs_from(QUESTS_SRC))
                         + "99999\tExtra\t\t\t\t\n")
        res = run_tool(src, dst, "quests")
        self.assertEqual(res.returncode, 1)
        self.assertIn("OKANDA id i utdata (1): 99999", res.stdout)

    def test_wrong_order_is_error(self):
        src = write_file(self.dir, "src.tsv", QUESTS_SRC)
        rows = pairs_from(QUESTS_SRC)
        rows[0], rows[1] = rows[1], rows[0]
        dst = write_file(self.dir, "dst.tsv", quests_out(rows))
        res = run_tool(src, dst, "quests")
        self.assertEqual(res.returncode, 1)
        self.assertIn("ordningen avviker vid rad 1", res.stdout)

    def test_npc_column_counts(self):
        src = write_file(self.dir, "src.tsv",
                         "id\tname\ttitle\n3947\tGoblin Shipbuilder\t\n14874\tKaru\tFlight Master\n")
        dst_ok = write_file(self.dir, "dst_ok.tsv", "id\tnamn\n3947\tGoblinskeppsbyggare\n14874\tKaru\n")
        res = run_tool(src, dst_ok, "npcs")
        self.assertEqual(res.returncode, 0, res.stdout)
        dst_bad = write_file(self.dir, "dst_bad.tsv",
                             "id\tnamn\n3947\tGoblin Shipbuilder\textra kolumn\n14874\tKaru\n")
        res = run_tool(src, dst_bad, "npcs")
        self.assertEqual(res.returncode, 1)
        self.assertIn("3 kolumner (vantade 2)", res.stdout)

    def test_quest_output_wrong_column_counts_fail(self):
        src = write_file(self.dir, "src.tsv", QUESTS_SRC.splitlines()[-1] + "\n")
        bad5 = write_file(self.dir, "bad5.tsv", "93429\tTheir suffering must end.\t\t\t\n")
        res = run_tool(src, bad5, "quests")
        self.assertEqual(res.returncode, 1)
        self.assertIn("5 kolumner (vantade 6)", res.stdout)
        bad7 = write_file(self.dir, "bad7.tsv", "93429\ta\tb\tc\td\te\tf\n")
        res = run_tool(src, bad7, "quests")
        self.assertEqual(res.returncode, 1)
        self.assertIn("7 kolumner (vantade 6)", res.stdout)
    def test_blank_line_and_cr_are_errors(self):
        src = write_file(self.dir, "src.tsv", QUESTS_SRC)
        dst = write_file(self.dir, "dst.tsv",
                         quests_out(pairs_from(QUESTS_SRC)[:-1])
                         + "\n93429\tText\t\t\t\t\n")
        res = run_tool(src, dst, "quests")
        self.assertEqual(res.returncode, 1)
        self.assertIn("blank rad", res.stdout)
        dst_cr = write_file(self.dir, "dst_cr.tsv",
                            quests_out(pairs_from(QUESTS_SRC)).replace("\n", "\r\n"))
        res = run_tool(src, dst_cr, "quests")
        self.assertEqual(res.returncode, 1)
        self.assertIn("CR-tecken", res.stdout)

    def test_all_fields_empty_is_error(self):
        src = write_file(self.dir, "src.tsv", QUESTS_SRC.splitlines()[-1] + "\n")
        dst = write_file(self.dir, "dst.tsv", "93429\t\t\t\t\t\n")
        res = run_tool(src, dst, "quests")
        self.assertEqual(res.returncode, 1)
        self.assertIn("hela raden ar tom", res.stdout)

    def test_placeholder_multiset_cases(self):
        token_row = ("1\tLight a $B signal $b fire, $Gman:kvinna; guard of the $2oa $N. "
                     "Pay %s gold at #/# pace, see ${$m2$*$<frostdamage>} and $s1 in $d, "
                     "|cff00ff00loot|r with |Hquest:1|h[Seal]|h.\n")
        toks = ["$B", "$b", "$Gman:kvinna;", "$2oa", "$N", "%s", "#/#",
                "${$m2$*$<frostdamage>}", "$s1", "$d",
                "|cff00ff00loot|r", "|Hquest:1|h", "|h"]
        body_full = token_row.split("\t", 1)[1]
        for tok in toks:
            with self.subTest(tok=tok):
                src = write_file(self.dir, "src.tsv", "id\ttext\n" + token_row)
                body = body_full.replace(tok, "", 1)
                dst = write_file(self.dir, "dst.tsv", f"1\t{body.rstrip()}\t\t\t\t\n")
                res = run_tool(src, dst, "quests")
                self.assertEqual(res.returncode, 1, res.stdout)
                self.assertIn("platshallare saknas", res.stdout)
        src = write_file(self.dir, "src.tsv", "id\ttext\n" + token_row)
        dst = write_file(self.dir, "dst.tsv", f"1\t{body_full.rstrip()}\t\t\t\t\n")
        res = run_tool(src, dst, "quests")
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_repeated_placeholder_undercount_reported(self):
        src = write_file(self.dir, "src.tsv", "id\ttext\n5\tA$B$B B$B C\n")
        dst = write_file(self.dir, "dst.tsv", "5\tA$B B$B C\t\t\t\t\n")
        res = run_tool(src, dst, "quests")
        self.assertEqual(res.returncode, 1)
        self.assertIn("$B x1", res.stdout)

    def test_added_placeholder_is_error(self):
        row = QUESTS_SRC.splitlines()[1]
        rid, body = row.split("\t", 1)
        src = write_file(self.dir, "src.tsv", row + "\n")
        dst = write_file(self.dir, "dst.tsv", f"{rid}\t{body.rstrip()}$B\t\t\t\t\n")
        res = run_tool(src, dst, "quests")
        self.assertEqual(res.returncode, 1)
        self.assertIn("platshallare tillagda", res.stdout)

    def test_usage_errors_exit_two(self):
        dst = write_file(self.dir, "dst.tsv", "")
        res = run_tool(dst, dst, " Spells ")
        self.assertEqual(res.returncode, 2)
        res = run_tool(dst, os.path.join(self.dir, "saknas.tsv"), "quests")
        self.assertEqual(res.returncode, 2)
        res = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(res.returncode, 2)

    def test_real_batch_smoke(self):
        """A real 10-row quest batch (tests/fixtures/quests-batch-sample.tsv) validates, and a lost token is caught."""
        src = ROOT / "tests" / "fixtures" / "quests-batch-sample.tsv"
        rows = pairs_from(src.read_text(encoding="utf-8"))
        dst = write_file(self.dir, "dst01.tsv", quests_out(rows))
        res = run_tool(str(src), dst, "quests")
        self.assertEqual(res.returncode, 0, res.stdout)
        token_row = next((index for index, (_, body) in enumerate(rows)
                          if vb.TOKEN_RE.search(body)), None)
        self.assertIsNotNone(token_row, "the fixture must contain a placeholder to corrupt")
        rid, body = rows[token_row]
        token = vb.TOKEN_RE.search(body)
        corrupt = body[:token.start()] + body[token.end():]
        corrupted_rows = rows.copy()
        corrupted_rows[token_row] = (rid, corrupt)
        dst2 = write_file(self.dir, "dst01b.tsv", quests_out(corrupted_rows))
        res = run_tool(str(src), dst2, "quests")
        self.assertEqual(res.returncode, 1)
        self.assertIn("platshallare saknas", res.stdout)


if __name__ == "__main__":
    unittest.main()
