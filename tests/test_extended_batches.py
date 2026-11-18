#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for optional game-object and page-text batch inputs."""
import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_script(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class ExtendedBatchTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def test_selector_creates_gameobject_and_pagetext_worklists(self):
        selector = load_script("select_untranslated", "select-untranslated.py")
        data_dir = self.root / "Data"
        out_dir = self.root / "translation" / "untranslated"
        write(data_dir / "Quest.lua", "[1]={t=\"Old quest\"},\n")
        write(data_dir / "Npc.lua", "[10]=\"Old NPC\",\n")
        quest = write(self.root / "quest.tsv", "id\ttext\n1\tOld quest\n2\tNew quest\n")
        npc = write(self.root / "npc.tsv", "id\tname\ttitle\n10\tOld NPC\t\n11\tNew NPC\tGuard\n")
        gameobject = write(self.root / "gameobject.tsv", "id\tname\textra\n20\tOld Iron Gate\t\n")
        pagetext = write(self.root / "pagetext.tsv", "id\ttext\n2013\tA book page.\n")

        with patch.object(selector, "ROOT", str(self.root)), \
             patch.object(selector, "OUT", str(out_dir)), \
             patch.object(selector.sys, "argv", ["select-untranslated.py", str(quest), str(npc), str(gameobject), str(pagetext)]), \
             contextlib.redirect_stdout(io.StringIO()):
            selector.main()

        self.assertEqual((out_dir / "quests-001.tsv").read_text(encoding="utf-8"),
                         "id\ttext\n2\tNew quest\n")
        self.assertEqual((out_dir / "npcs-001.tsv").read_text(encoding="utf-8"),
                         "id\tname\ttitle\n11\tNew NPC\tGuard\n")
        self.assertEqual((out_dir / "gameobjects-001.tsv").read_text(encoding="utf-8"),
                         "id\tname\ttitle\n20\tOld Iron Gate\t\n")
        self.assertEqual((out_dir / "pagetext-001.tsv").read_text(encoding="utf-8"),
                         "id\ttext\n2013\tA book page.\n")

    def test_batch_generator_reads_optional_worklists(self):
        generator = load_script("make_batches", "make-batches.py")
        source = self.root / "translation"
        worklists = source / "untranslated"
        output = source / "batches"
        write(worklists / "quests-001.tsv", "id\ttext\n1\tQuest\n")
        write(worklists / "npcs-001.tsv", "id\tname\ttitle\n2\tNPC\t\n")
        write(worklists / "gameobjects-001.tsv",
              "id\tname\ttitle\n10\tGate\t\n11\tChair\n")
        write(worklists / "gameobjects-002.tsv",
              "id\tname\ttitle\n12\tCrate\t\n")
        write(worklists / "pagetext-001.tsv",
              "id\ttext\n20\tPage one.\n21\tPage two.\n")

        with patch.object(generator, "SRC", str(source)), \
             patch.object(generator, "UNTRANSLATED", str(worklists)), \
             patch.object(generator, "OUT", str(output)), \
             patch.object(generator, "GAMEOBJECT_BATCH", 2), \
             patch.object(generator, "PAGETEXT_BATCH", 1), \
             contextlib.redirect_stdout(io.StringIO()):
            generator.main()

        self.assertTrue((output / "gameobjects-batch-01.tsv").exists())
        self.assertEqual((output / "gameobjects-batch-01.tsv").read_text(encoding="utf-8"),
                         "id\tname\ttitle\n10\tGate\t\n11\tChair\n")
        self.assertEqual((output / "gameobjects-batch-02.tsv").read_text(encoding="utf-8"),
                         "id\tname\ttitle\n12\tCrate\t\n")
        self.assertEqual((output / "pagetext-batch-02.tsv").read_text(encoding="utf-8"),
                         "id\ttext\n21\tPage two.\n")

    def test_validator_accepts_gameobject_and_pagetext_rows(self):
        validator = ROOT / "tools" / "validate-batch.py"
        cases = (
            ("gameobjects", "id\tname\ttitle\n1\tWooden Chair\t\n",
             "id\tnamn\n1\tTrästol\n"),
            ("pagetext", "id\ttext\n2\tRead the $B old page.\n",
             "id\ttext\n2\tLäs den $B gamla sidan.\n"),
        )
        for kind, source_text, output_text in cases:
            with self.subTest(kind=kind):
                source = write(self.root / f"{kind}-source.tsv", source_text)
                output = write(self.root / f"{kind}-output.tsv", output_text)
                result = subprocess.run(
                    [sys.executable, str(validator), str(source), str(output), kind],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("RESULTAT: OK", result.stdout)

    def test_pagetext_validator_rejects_lost_tokens(self):
        validator = ROOT / "tools" / "validate-batch.py"
        source = write(self.root / "page-source.tsv", "id\ttext\n2\tRead the $B old page.\n")
        output = write(self.root / "page-output.tsv", "id\ttext\n2\tLäs den gamla sidan.\n")
        result = subprocess.run(
            [sys.executable, str(validator), str(source), str(output), "pagetext"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("platshallare saknas", result.stdout)


if __name__ == "__main__":
    unittest.main()