#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/select-untranslated.py - steg 2: jamfor cacheinnehallet mot det som
redan ar oversatt i Data/Quest.lua och Data/Npc.lua, och skriv TSV-filer
med bara det som saknas (klara att mata till Gemma 4 31B).

Usage:
  python3 tools/select-untranslated.py <quest-en.tsv> <creature-en.tsv>

Outputs (in translation/):
  quest-not-translated.tsv     id, text          quests w/o translation yet
  npcs-not-translated.tsv      id, name, title   creatures w/o translation yet
Console summary shows coverage + overlap validation.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "translation")

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


def main():
    quest_tsv, npc_tsv = sys.argv[1], sys.argv[2]
    os.makedirs(OUT, exist_ok=True)

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

    q_out = os.path.join(OUT, "quest-not-translated.tsv")
    with open(q_out, "w", encoding="utf-8") as fh:
        fh.write("id\ttext\n")
        for rid, text in new_q:
            t = text.replace("\t", " ").replace("\n", "\\n")
            fh.write(f"{rid}\t{t}\n")
    n_out = os.path.join(OUT, "npcs-not-translated.tsv")
    with open(n_out, "w", encoding="utf-8") as fh:
        fh.write("id\tname\ttitle\n")
        for rid, name, extra in new_n:
            fh.write(f"{rid}\t{name}\t{extra}\n")

    print(f"\nskriv {q_out}: {len(new_q)} quests utan oversattning")
    print(f"skriv {n_out}: {len(new_n)} npc-namn utan oversattning")
    if new_q:
        rid, text = new_q[0]
        print(f"forsta: {rid} -> {text[:90]}")
    if new_n:
        print(f"forsta npc: {new_n[0]}")


if __name__ == "__main__":
    main()