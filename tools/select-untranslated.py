#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/select-untranslated.py - steg 2: jamfor cacheinnehallet mot det som
redan ar oversatt i Data/Quest.lua och Data/Npc.lua, och skriv TSV-filer
med bara det som saknas.

Usage:
  python3 tools/select-untranslated.py <quest-en.tsv> <creature-en.tsv>
    python3 tools/select-untranslated.py <quest-en.tsv> <creature-en.tsv> \
        <gameobject-en.tsv> <pagetext-en.tsv>

Outputs (in translation/untranslated/), one new numbered file per kind per run:
    quests-001.tsv, quests-002.tsv ...        id, text         quests not translated yet
    npcs-001.tsv, ...                         id, name, title  creatures not translated yet
    gameobjects-001.tsv, ...                  id, name, title  game objects
    pagetext-001.tsv, ...                     id, text         page text

Pass the first two caches for quests and creatures. Add both optional caches
to also write game-object and page-text worklists.
Existing files are NEVER overwritten or modified: they grow over time and are
worked separately. Each run writes the next free number, and only contains IDs
that are not already in an earlier numbered file of the same kind. Nothing is
written when there is nothing new.
Console summary shows coverage + overlap validation.
"""
HELP_TEXT = (
    "Usage:\n"
    "  python3 tools/select-untranslated.py <quest-en.tsv> <creature-en.tsv>\n"
    "  python3 tools/select-untranslated.py <quest-en.tsv> <creature-en.tsv> \\\n"
    "    <gameobject-en.tsv> <pagetext-en.tsv>\n"
    "\n"
    "Outputs in translation/untranslated/ (new numbered file per run, never overwritten):\n"
    "  quests-NNN.tsv       quest IDs and text\n"
    "  npcs-NNN.tsv         creature IDs, names, and titles\n"
    "  gameobjects-NNN.tsv  game-object IDs, names, and titles\n"
    "  pagetext-NNN.tsv     page-text IDs and text\n"
)
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "translation", "untranslated")

ID_RE = re.compile(r"^\[(\d+)\]=")


def ids_from_lua(path):
    ids = set()
    if not os.path.exists(path):
        return ids
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = ID_RE.match(line)
            if m:
                ids.add(int(m.group(1)))
    return ids


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


def existing_ids(prefix):
    """IDs already present in earlier numbered files of this kind."""
    ids = set()
    for path in numbered_files(prefix):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                head = line.split("\t", 1)[0]
                if head.isdigit():
                    ids.add(int(head))
    return ids


def numbered_files(prefix):
    pat = re.compile(r"^" + re.escape(prefix) + r"-(\d+)\.tsv$")
    if not os.path.isdir(OUT):
        return []
    return sorted(os.path.join(OUT, f) for f in os.listdir(OUT) if pat.match(f))


def write_new(prefix, header, rows):
    """Write rows (id, line) not seen in earlier files to the next free
    <prefix>-NNN.tsv. Never overwrites. Returns (path or None, count)."""
    seen = existing_ids(prefix)
    lines = [line for rid, line in rows if rid not in seen]
    if not lines:
        print(f"inget nytt for {prefix}: ingen fil skapad")
        return None, 0
    os.makedirs(OUT, exist_ok=True)
    n = 1
    nums = [int(re.search(r"-(\d+)\.tsv$", f).group(1)) for f in numbered_files(prefix)]
    if nums:
        n = max(nums) + 1
    while True:
        path = os.path.join(OUT, f"{prefix}-{n:03d}.tsv")
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


def main():
    if len(sys.argv) not in (3, 5):
        print(HELP_TEXT, file=sys.stderr)
        return 2
    quest_tsv, npc_tsv = sys.argv[1:3]
    translated_q = ids_from_lua(os.path.join(ROOT, "Data", "Quest.lua"))
    translated_n = ids_from_lua(os.path.join(ROOT, "Data", "Npc.lua"))
    print(f"Data/Quest.lua: {len(translated_q)} oversatta quests")
    print(f"Data/Npc.lua:   {len(translated_n)} oversatta npc-namn")

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

    write_new("quests", "id\ttext\n",
              [(rid, f"{rid}\t{clean(text)}\n") for rid, text in new_q])
    write_new("npcs", "id\tname\ttitle\n",
              [(rid, f"{rid}\t{name}\t{extra}\n") for rid, name, extra in new_n])
    print(f"\nkandidater: {len(new_q)} quests, {len(new_n)} npc-namn utan oversattning")
    if new_q:
        rid, text = new_q[0]
        print(f"forsta: {rid} -> {text[:90]}")
    if new_n:
        print(f"forsta npc: {new_n[0]}")

    if len(sys.argv) == 5:
        gameobject_tsv, pagetext_tsv = sys.argv[3:5]
        gameobjects = read_tsv(gameobject_tsv, wide=True)
        pagetext = read_tsv(pagetext_tsv, wide=False)
        write_new("gameobjects", "id\tname\ttitle\n",
                  [(rid, f"{rid}\t{name}\t{extra}\n") for rid, name, extra in gameobjects])
        write_new("pagetext", "id\ttext\n",
                  [(rid, f"{rid}\t{clean(text, cr=True)}\n") for rid, text, _ in pagetext])
    return 0


if __name__ == "__main__":
    sys.exit(main())