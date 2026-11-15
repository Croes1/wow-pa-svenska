#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/merge-translation.py - sammanfogar fardiga omgangar (translation/out/)
till addon-datafilerna utan att rora de genererade Data/Quest.lua / Npc.lua.

Skapar/applicerar som Tillagg (jfr Data/UiExtra.lua):
  Data/QuestExtra.lua -> nya nycklar i WPS.L.quest  ([id]={t,o,d,p,c})
  Data/NpcExtra.lua   -> nya nycklar i WPS.L.npc    ([id]="Namn")
och kopplar in dem i wow_pa_svenska.toc (Data\\QuestExtra.lua /
Data\\NpcExtra.lua laggs in efter resp. huvudfil om de saknas).

Kolumner i indata:
  quests: id<TAB>title<TAB>objectives<TAB>description<TAB>progress<TAB>reward
          -> falt t,o,d,p,c. Tomt falt far ingen nyckel: addonet byter bara
             falt som finns, sa fragmentraderna landar dar segmenteringen
             lade dem (beslut: translation/batches/review/DECISIONS-*.md).
  npcs:   id<TAB>name

Regler:
  - id som redan finns i Data/Quest.lua, Data/Npc.lua eller i extra-filen
    HOPPAS OVER och rapporteras - aldre granskat innehall skrivs aldrig over.
  - deterministiskt: id sorteras numeriskt, varje rad far batchproveniens
    som kommentar. Omkorning appendar bara nya rader; gamla rader rors ej.
  - Inga falt hittas pa: exakt det som finns i TSV:n.

Usage:
  python3 tools/merge-translation.py            # sammanfoga allt som saknas
  python3 tools/merge-translation.py --torr     # rapportera utan att skriva
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "Data")
OUT = os.path.join(ROOT, "translation", "out")
TOC = os.path.join(ROOT, "wow_pa_svenska.toc")

ID_RE = re.compile(r"\[(\d+)\]\s*=")   # matchar bde "[id]=" och "LQ[id]=" / "LN[id]="
BATCH_RE = re.compile(r"batch-(\d+)")
FIELDS = (("t", 0), ("o", 1), ("d", 2), ("p", 3), ("c", 4))  # index i falt-tuppeln (utan id)


def fail(msg):
    print(f"FEL: {msg}")
    sys.exit(1)


def lua_str(s):
    out = s.replace("\\", "\\\\").replace('"', '\\"')
    out = out.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")
    return '"' + out + '"'


def ids_from_lua(path):
    ids = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                m = ID_RE.search(line)  # search (inte match): raden kan brja med LQ[ / LN[
                if m:
                    ids.add(int(m.group(1)))
    return ids


def read_rows(kind, path):
    """Lista (id, falt-tuple, kallfil) ur en utdatafil; kolumner valideras."""
    rows, seen = [], set()
    with open(path, encoding="utf-8") as fh:
        for ln, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line:
                continue
            if ln == 1 and line.startswith("id\t"):
                continue  # eventuell rubrikrad
            parts = line.split("\t")
            want = 6 if kind == "quests" else 2
            if len(parts) != want:
                fail(f"{path} rad {ln}: {len(parts)} kolumner (vantade {want})")
            if not parts[0].isdigit():
                fail(f"{path} rad {ln}: icke-numeriskt id {parts[0]!r}")
            rid = int(parts[0])
            if rid in seen:
                fail(f"{path} rad {ln}: dubblett-id {rid}")
            seen.add(rid)
            rows.append((rid, tuple(parts[1:]), os.path.basename(path)))
    return rows


def collect(kind):
    pattern = {"quests": "quests-batch-*-sv.tsv", "npcs": "npcs-batch-*-sv.tsv"}[kind]
    files = sorted(glob.glob(os.path.join(OUT, pattern)),
                   key=lambda p: int(BATCH_RE.search(p).group(1)))
    rows = []
    for path in files:
        rows.extend(read_rows(kind, path))
    seen = {}
    for rid, _f, src in rows:
        if rid in seen:
            fail(f"id {rid} forekommer i bade {seen[rid]} och {src}")
        seen[rid] = src
    return rows


def extra_path(name):
    return os.path.join(DATA, name)


def write_file(path, header, entry_lines, merge_lines):
    """Skriver filen HELT frn grunden (idempotent): header + extra-tabell +
    in-sgningsslinga med nil-vakt. Samma TSV -> samma fil byte fr byte;
    omkorning tappar aldrig rader eftersom utgngen bygger p TSV:n."""
    text = (header
            + "local extra = {\n" + "\n".join(entry_lines) + "\n}\n\n"
            + merge_lines)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


QUEST_LOOP = (
    "for id, add in pairs(extra) do\n"
    "    if LQ[id] == nil then LQ[id] = add end   -- skriv aldrig over granskat innehll\n"
    "end\n"
)

NPC_LOOP = (
    "for id, namn in pairs(extra) do\n"
    "    if LN[id] == nil then LN[id] = namn end   -- skriv aldrig over granskat innehll\n"
    "end\n"
)


def quest_header():
    return (
        "-- Tillgg till WPS.L.quest: godkanda omgngar ur translation/out/,\n"
        "-- sammanfogade av tools/merge-translation.py. Gr inte handandringar hr:\n"
        "-- nsta krning regenererar filen, gamla rader rrs aldrig om.\n"
        "-- Flt t,o,d,p,c; tomt flt = ingen nyckel (addonet byter bara flt som finns).\n"
        "-- l-rader (sprarrader i trakern) saknas: tckningsbegrnsning, se PIPELINE.md;\n"
        "-- sparraderna frblir engelska till vidare, oskadligt.\n"
        "local _, WPS = ...\n"
        "local LQ = WPS.L.quest\n\n"
    )


def npc_header():
    return (
        "-- Tillgg till WPS.L.npc: godknda omgngar ur translation/out/,\n"
        "-- sammanfogade av tools/merge-translation.py. Gr inte handndringar hr:\n"
        "-- nsta krning regenererar filen, gamla rader rrs aldrig om.\n"
        "-- Personnamn str kvar orandrade med avsikt (translation/PROMPT-GEMMA.md).\n"
        "local _, WPS = ...\n"
        "local LN = WPS.L.npc\n\n"
    )


def update_toc():
    wanted = (("Data\\QuestExtra.lua", "Data\\Quest.lua"),
              ("Data\\NpcExtra.lua", "Data\\Npc.lua"))
    with open(TOC, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    changed = False
    for entry, after in wanted:
        if entry in lines:
            continue
        if after not in lines:
            fail(f".toc saknar ankarpunkten {after!r}; kan inte infoga {entry!r}")
        lines.insert(lines.index(after) + 1, entry)
        changed = True
    if changed:
        with open(TOC, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
    return changed


def main():
    dry = "--torr" in sys.argv
    qrows = collect("quests")
    nrows = collect("npcs")
    print(f"utdata-rader: quests {len(qrows)}, npcs {len(nrows)}")

    # Hoppskyddet gller bara Data-huvudfilerna: extra-filerna regenereras HELT
    # ur TSV:erna vid varje korning (idempotent inget append, inget kan tappas).
    q_existing = ids_from_lua(os.path.join(DATA, "Quest.lua"))
    n_existing = ids_from_lua(os.path.join(DATA, "Npc.lua"))

    q_new = [(rid, f, s) for rid, f, s in qrows if rid not in q_existing]
    n_new = [(rid, f, s) for rid, f, s in nrows if rid not in n_existing]
    print(f"nya quests: {len(q_new)} (hoppade {len(qrows) - len(q_new)} redan versatta)")
    print(f"nya npcs:   {len(n_new)} (hoppade {len(nrows) - len(n_new)} redan versatta)")

    q_lines = []
    for rid, fields, src in sorted(q_new, key=lambda r: r[0]):
        body = ", ".join(f"{k}={lua_str(fields[i])}" for k, i in FIELDS if fields[i])
        if not body:
            print(f"VARNING: quest {rid} har alla falt tomma - hoppar over")
            continue
        label = src[:-4] if src.endswith(".tsv") else src
        q_lines.append(f"[{rid}]={{{body}}}, -- {label}")

    n_lines = []
    for rid, fields, src in sorted(n_new, key=lambda r: r[0]):
        name = fields[0].strip()
        if not name:
            print(f"VARNING: npc {rid} har tomt namn - hoppar over")
            continue
        label = src[:-4] if src.endswith(".tsv") else src
        n_lines.append(f"[{rid}]={lua_str(name)}, -- {label}")

    if dry:
        print(f"--torr: skulle skriva {len(q_lines)} quest-rader och {len(n_lines)} npc-rader")
        return 0

    if q_lines:
        write_file(extra_path("QuestExtra.lua"), quest_header(), q_lines, QUEST_LOOP)
    if n_lines:
        write_file(extra_path("NpcExtra.lua"), npc_header(), n_lines, NPC_LOOP)

    toc_changed = update_toc()
    print(f"QuestExtra.lua: +{len(q_lines)} rader    NpcExtra.lua: +{len(n_lines)} rader")
    print(f".toc: {'uppdaterad' if toc_changed else 'redan kopplad'}")
    print("KLART - kor luac5.1 -p pd de nya filerna och testsviten innan release.")
    return 0


if __name__ == "__main__":
    sys.exit(main())