#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/make-batches.py - delar upp de okoversatta TSV-filerna i
klistra-in-tanke-omgangar (for chattpastning till Gemma).

Anvandning:  python3 tools/make-batches.py

Skapar i translation/batches/:
  quests-batch-01.tsv ... (10 rader per omgang)
  npcs-batch-01.tsv ...   (150 rader per omgang)
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "translation")
OUT = os.path.join(SRC, "batches")

QUEST_BATCH = 10
NPC_BATCH = 150


def read_rows(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    return [ln for ln in lines[1:] if ln.strip()]


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
    q = read_rows(os.path.join(SRC, "quest-not-translated.tsv"))
    nq = write_batches(q, "id\ttext", "quests", QUEST_BATCH)
    n = read_rows(os.path.join(SRC, "npcs-not-translated.tsv"))
    nn = write_batches(n, "id\tname\ttitle", "npcs", NPC_BATCH)
    print(f"quests: {len(q)} rader -> {nq} batcher om {QUEST_BATCH} i translation/batches/quests-batch-XX.tsv")
    print(f"npcs:   {len(n)} rader -> {nn} batcher om {NPC_BATCH} i translation/batches/npcs-batch-XX.tsv")


if __name__ == "__main__":
    main()