#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/make-batches.py - delar upp de okoversatta TSV-filerna i
klistra-in-tanke-omgangar (for chattpastning till Gemma).

Indata: alla numrerade worklistor i translation/untranslated/, t.ex.
  quests-001.tsv, quests-002.tsv ... (lasta i nummerordning)
Filerna andras aldrig. Nya worklistor laggs till av select-untranslated.py.

Anvandning:  python3 tools/make-batches.py

Skapar i translation/batches/:
  quests-batch-01.tsv ... (10 rader per omgang)
  npcs-batch-01.tsv ...   (150 rader per omgang)
    gameobjects-batch-01.tsv ... (150 rader per omgang, om worklistan finns)
    pagetext-batch-01.tsv ... (10 rader per omgang, om worklistan finns)
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "translation")
UNTRANSLATED = os.path.join(SRC, "untranslated")
OUT = os.path.join(SRC, "batches")

QUEST_BATCH = 10
NPC_BATCH = 150
GAMEOBJECT_BATCH = 150
PAGETEXT_BATCH = 10


def numbered_files(prefix):
    """All <prefix>-NNN.tsv worklists in UNTRANSLATED, in number order."""
    if not os.path.isdir(UNTRANSLATED):
        return []
    pat = re.compile(r"^" + re.escape(prefix) + r"-(\d+)\.tsv$")
    found = [f for f in os.listdir(UNTRANSLATED) if pat.match(f)]
    found.sort(key=lambda f: int(pat.match(f).group(1)))
    return [os.path.join(UNTRANSLATED, f) for f in found]


def read_rows(paths):
    rows = []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        rows.extend(ln for ln in lines[1:] if ln.strip())
    return rows


def write_batches(rows, header, prefix, size):
    n = (len(rows) + size - 1) // size
    for i in range(n):
        chunk = rows[i * size:(i + 1) * size]
        path = os.path.join(OUT, f"{prefix}-batch-{i + 1:02d}.tsv")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(header + "\n")
            fh.write("\n".join(chunk) + "\n")
    return n


def main():
    os.makedirs(OUT, exist_ok=True)
    specs = (
        ("quests", "id\ttext", QUEST_BATCH, False),
        ("npcs", "id\tname\ttitle", NPC_BATCH, False),
        ("gameobjects", "id\tname\ttitle", GAMEOBJECT_BATCH, True),
        ("pagetext", "id\ttext", PAGETEXT_BATCH, True),
    )
    for prefix, header, size, optional in specs:
        sources = numbered_files(prefix)
        if not sources:
            if optional:
                print(f"{prefix}: ingen worklista, hoppar over")
            else:
                print(f"{prefix}: ingen worklista i translation/untranslated/")
            continue
        rows = read_rows(sources)
        count = write_batches(rows, header, prefix, size)
        print(f"{prefix}: {len(rows)} rader -> {count} batcher om {size} i translation/batches/{prefix}-batch-XX.tsv")


if __name__ == "__main__":
    main()