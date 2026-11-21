#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/select-untranslated.py - steg 2: jamfor cacheinnehallet mot det som
redan ar oversatt i Data/Quest.lua och Data/Npc.lua, och skriv TSV-filer
med bara det som saknas.

Usage:
  python3 tools/select-untranslated.py <quest-en.tsv> <creature-en.tsv> --work-dir DIR
  python3 tools/select-untranslated.py <quest-en.tsv> <creature-en.tsv> \\
      <gameobject-en.tsv> <pagetext-en.tsv> --work-dir DIR

  --work-dir  external work directory (required); worklists go to DIR/untranslated/
  --data-dir  folder with Quest.lua and Npc.lua (default: Data/ in this repository)

What counts as translated is read from the real Data files (the quest table in
Data/Quest.lua and the npc table in Data/Npc.lua); no TSV export is used.

Outputs (in <work-dir>/untranslated/), one new numbered file per kind per run:
    quests-001.tsv, quests-002.tsv ...        id, text         quests not translated yet
    npcs-001.tsv, ...                         id, name, title  creatures not translated yet
    gameobjects-001.tsv, ...                  id, name, title  game objects
    pagetext-001.tsv, ...                     id, text         page text

Pass the first two caches for quests and creatures. Add both optional caches
to also write game-object and page-text worklists.
Existing files are NEVER overwritten or modified: they grow over time and are
worked separately. Each run writes the next free number, and only contains IDs
that are not already in an earlier numbered file of the same kind. Nothing is
written when there is nothing new. Nothing is written inside the repository
unless --work-dir points there.
Console summary shows coverage + overlap validation.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import datalua  # noqa: E402


def ids_from_lua(path, table):
    """Integer keys of one table in a Data file (parsed with datalua; fails on unknown syntax)."""
    return {k for k in datalua.DataFile.read(path).table(table).keys() if isinstance(k, int)}


def read_tsv(path, wide):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if i == 0 and line.startswith("id\t"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                name = parts[1]
                extra = parts[2] if len(parts) > 2 else ""
                rows.append((int(parts[0]), name, extra))
    return rows


def clean(text, cr=False):
    text = text.replace("\t", " ")
    if cr:
        text = text.replace("\r", "\\r")
    return text.replace("\n", "\\n")


def existing_ids(out, prefix):
    """IDs already present in earlier numbered files of this kind."""
    ids = set()
    for path in numbered_files(out, prefix):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                head = line.split("\t", 1)[0]
                if head.isdigit():
                    ids.add(int(head))
    return ids


def numbered_files(out, prefix):
    pat = re.compile(r"^" + re.escape(prefix) + r"-(\d+)\.tsv$")
    if not os.path.isdir(out):
        return []
    return sorted(os.path.join(out, f) for f in os.listdir(out) if pat.match(f))


def write_new(out, prefix, header, rows):
    """Write rows (id, line) not seen in earlier files to the next free
    <prefix>-NNN.tsv. Never overwrites. Returns (path or None, count)."""
    seen = existing_ids(out, prefix)
    lines = [line for rid, line in rows if rid not in seen]
    if not lines:
        print(f"inget nytt for {prefix}: ingen fil skapad")
        return None, 0
    os.makedirs(out, exist_ok=True)
    n = 1
    nums = [int(re.search(r"-(\d+)\.tsv$", f).group(1)) for f in numbered_files(out, prefix)]
    if nums:
        n = max(nums) + 1
    while True:
        path = os.path.join(out, f"{prefix}-{n:03d}.tsv")
        try:
            # "x" = exclusive create: fails instead of overwriting.
            fh = open(path, "x", encoding="utf-8")
            break
        except FileExistsError:
            n += 1
    with fh:
        fh.write(header)
        fh.writelines(lines)
    print(f"skapade {path}: {len(lines)} rader")
    return path, len(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Write worklists of the quests, creatures, game objects and page texts "
                    "that are not yet translated in Data/*.lua.")
    ap.add_argument("caches", nargs="+",
                    help="<quest-en.tsv> <creature-en.tsv> [<gameobject-en.tsv> <pagetext-en.tsv>]")
    ap.add_argument("--work-dir", required=True,
                    help="external work directory; worklists are written to <work-dir>/untranslated/")
    ap.add_argument("--data-dir", default=os.path.join(ROOT, "Data"),
                    help="folder with Quest.lua and Npc.lua (default: Data/ of this repository)")
    args = ap.parse_args(argv)
    if len(args.caches) not in (2, 4):
        ap.error("give 2 caches (quest, creature) or 4 (quest, creature, gameobject, pagetext)")
    quest_tsv, npc_tsv = args.caches[:2]
    out = os.path.join(args.work_dir, "untranslated")
    quest_lua = os.path.join(args.data_dir, "Quest.lua")
    npc_lua = os.path.join(args.data_dir, "Npc.lua")
    translated_q = ids_from_lua(quest_lua, "quest")
    translated_n = ids_from_lua(npc_lua, "npc")
    print(f"{quest_lua}: {len(translated_q)} oversatta quests")
    print(f"{npc_lua}:   {len(translated_n)} oversatta npc-namn")
    print(f"worklists go to {out}")

    cached_q = read_tsv(quest_tsv, wide=False)
    cached_n = read_tsv(npc_tsv, wide=True)
    print(f"{quest_tsv}: {len(cached_q)} quests i cachen")

    # ID-semantik-validering: skall cache-id:natera traden i Data-filerna?
    overlap_q = sum(1 for rid, _, _ in cached_q if rid in translated_q)
    overlap_n = sum(1 for rid, _, _ in cached_n if rid in translated_n)
    print(f"overlapp: {overlap_q} quest-id i bada (validerar id-semantiken)")
    print(f"overlapp: {overlap_n} npc-id i bada")

    new_q = [(rid, text) for rid, text, _ in cached_q if rid not in translated_q]
    new_n = [(rid, name, extra) for rid, name, extra in cached_n
             if rid not in translated_n]

    write_new(out, "quests", "id\ttext\n",
              [(rid, f"{rid}\t{clean(text)}\n") for rid, text in new_q])
    write_new(out, "npcs", "id\tname\ttitle\n",
              [(rid, f"{rid}\t{name}\t{extra}\n") for rid, name, extra in new_n])
    print(f"\nkandidater: {len(new_q)} quests, {len(new_n)} npc-namn utan oversattning")
    if new_q:
        rid, text = new_q[0]
        print(f"forsta: {rid} -> {text[:90]}")
    if new_n:
        print(f"forsta npc: {new_n[0]}")

    if len(args.caches) == 4:
        gameobject_tsv, pagetext_tsv = args.caches[2:4]
        gameobjects = read_tsv(gameobject_tsv, wide=True)
        pagetext = read_tsv(pagetext_tsv, wide=False)
        write_new(out, "gameobjects", "id\tname\ttitle\n",
                  [(rid, f"{rid}\t{name}\t{extra}\n") for rid, name, extra in gameobjects])
        write_new(out, "pagetext", "id\ttext\n",
                  [(rid, f"{rid}\t{clean(text, cr=True)}\n") for rid, text, _ in pagetext])
    return 0


if __name__ == "__main__":
    sys.exit(main())
