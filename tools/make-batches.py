#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/make-batches.py - delar upp de okoversatta TSV-filerna i
klistra-in-tanke-omgangar (for chattpastning till Gemma).

Indata: alla numrerade worklistor i <work-dir>/untranslated/, t.ex.
  quests-001.tsv, quests-002.tsv ... (lasta i nummerordning)
Filerna andras aldrig. Nya worklistor laggs till av select-untranslated.py.

Anvandning:  python3 tools/make-batches.py --work-dir DIR [--force]

  --work-dir  external work directory (required): reads DIR/untranslated/,
              writes DIR/batches/. Nothing is written inside the repository
              unless DIR points there.
  --force     overwrite batch files that already exist. Without it the tool
              stops before writing anything: a batch number can change when a
              new worklist is added, and a finished batch must not be replaced
              by different rows.

Skapar i <work-dir>/batches/:
  quests-batch-01.tsv ... (10 rader per omgang)
  npcs-batch-01.tsv ...   (150 rader per omgang)
  gameobjects-batch-01.tsv ... (150 rader per omgang, om worklistan finns)
  pagetext-batch-01.tsv ... (10 rader per omgang, om worklistan finns)
"""
import argparse
import os
import re
import sys

QUEST_BATCH = 10
NPC_BATCH = 150
GAMEOBJECT_BATCH = 150
PAGETEXT_BATCH = 10


def numbered_files(untranslated, prefix):
    """All <prefix>-NNN.tsv worklists in the untranslated folder, in number order."""
    if not os.path.isdir(untranslated):
        return []
    pat = re.compile(r"^" + re.escape(prefix) + r"-(\d+)\.tsv$")
    found = [f for f in os.listdir(untranslated) if pat.match(f)]
    found.sort(key=lambda f: int(pat.match(f).group(1)))
    return [os.path.join(untranslated, f) for f in found]


def read_rows(paths):
    rows = []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        rows.extend(ln for ln in lines[1:] if ln.strip())
    return rows


def batch_paths(out, prefix, rows, size):
    n = (len(rows) + size - 1) // size
    return [os.path.join(out, f"{prefix}-batch-{i + 1:02d}.tsv") for i in range(n)]


def write_batches(out, rows, header, prefix, size):
    paths = batch_paths(out, prefix, rows, size)
    for i, path in enumerate(paths):
        chunk = rows[i * size:(i + 1) * size]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(header + "\n")
            fh.write("\n".join(chunk) + "\n")
    return len(paths)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Split the untranslated worklists into translation batches.")
    ap.add_argument("--work-dir", required=True,
                    help="external work directory: reads <work-dir>/untranslated/, writes <work-dir>/batches/")
    ap.add_argument("--force", action="store_true", help="overwrite batch files that already exist")
    args = ap.parse_args(argv)
    untranslated = os.path.join(args.work_dir, "untranslated")
    out = os.path.join(args.work_dir, "batches")
    specs = (
        ("quests", "id\ttext", QUEST_BATCH, False),
        ("npcs", "id\tname\ttitle", NPC_BATCH, False),
        ("gameobjects", "id\tname\ttitle", GAMEOBJECT_BATCH, True),
        ("pagetext", "id\ttext", PAGETEXT_BATCH, True),
    )
    print(f"reading worklists from {untranslated}")
    plan = []
    for prefix, header, size, optional in specs:
        sources = numbered_files(untranslated, prefix)
        if not sources:
            if optional:
                print(f"{prefix}: ingen worklista, hoppar over")
            else:
                print(f"{prefix}: ingen worklista i {untranslated}")
            continue
        rows = read_rows(sources)
        plan.append((prefix, header, size, rows))
    if not args.force:
        clash = [p for prefix, _h, size, rows in plan for p in batch_paths(out, prefix, rows, size)
                 if os.path.exists(p)]
        if clash:
            print(f"FEL: {len(clash)} batch file(s) already exist, e.g. {clash[0]}", file=sys.stderr)
            print("Nothing written. Use --force to overwrite, or move the old batches away.", file=sys.stderr)
            return 1
    if plan:
        os.makedirs(out, exist_ok=True)
    for prefix, header, size, rows in plan:
        count = write_batches(out, rows, header, prefix, size)
        print(f"{prefix}: {len(rows)} rader -> {count} batcher om {size} i {out}/{prefix}-batch-XX.tsv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
