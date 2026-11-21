#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/fix-empty-columns.py - lagger tappade tomma slutkolumner i Gemma-utdata.

Gemma tar ibland bort de avslutande tomma kolumnerna (progress/reward) nar de
ar tomma och skriver t.ex. 4 kolumner stallen for 6. Detta verktyg fyller pa
dem - men ENDAST om den engelska referensfilen visar att de saknade
kolumnerna ska vara tomma. Nar engelskan har text saknas sadant innehall
tyst - den raden ska skickas till Gemma igen, inte lappas.

Anvandning:
  python3 tools/fix-empty-columns.py <engelsk-referens-tsv> <ut-tsv>

  quests: referens = <arbetskatalog>/segmented/quests-batch-XX-en-segmented.tsv
          utdata   = <arbetskatalog>/out/quests-batch-XX-sv.tsv

Bada filerna anges med explicita sokvagar (arbetskatalogen ligger utanfor
repot). Verktyget skriver ENDAST over <ut-tsv>, och bara om alla rader gar att
reparera; vid FEL andras ingenting.

FEL (exit 1): saknad rad, fel id/ordning, referensrad utan 6 kolumner eller
en saknad kolumn vars engelska motsvarighet INTE ar tom.
"""
import sys


def load(path, label):
    try:
        with open(path, encoding="utf-8", newline="") as fh:
            raw = fh.read()
    except OSError as exc:
        print(f"FEL: kan inte lasa {label} {path}: {exc}")
        sys.exit(2)
    if "\r" in raw:
        print(f"FEL: {label} {path} innehaller CR-tecken - spara som LF")
        sys.exit(2)
    lines = raw.split("\n")
    rows = []
    for idx, ln in enumerate(lines, 1):
        if not ln.strip():
            if idx == len(lines) and ln == "":
                continue
            print(f"FEL: {label} rad {idx}: ovantad blank rad i TSV")
            sys.exit(2)
        cells = ln.split("\t")
        if idx == 1 and cells[0] == "id":
            continue  # ev. rubrikrad
        rows.append((idx, cells))
    return rows


def main():
    if len(sys.argv) != 3:
        print("usage: fix-empty-columns.py <engelsk-referens-tsv> <ut-tsv>", file=sys.stderr)
        return 2
    ref_rows = load(sys.argv[1], "referens")
    ut_rows = load(sys.argv[2], "utdata")

    if len(ref_rows) != len(ut_rows):
        print(f"FEL: referensen har {len(ref_rows)} rader men utdatan {len(ut_rows)} "
              f"- hela omgangen maste ligga i utdatan")
        return 1

    fixed = 0
    for (ri, rcells), (_, ucells) in zip(ref_rows, ut_rows):
        if rcells[0] != ucells[0]:
            print(f"FEL: referensens id {rcells[0]} matchar inte utdatans {ucells[0]} ")
            return 1
        if len(rcells) != 6:
            print(f"FEL: referensrad id {rcells[0]} har {len(rcells)} kolumner (vantade 6)")
            return 1
        if len(ucells) == 6:
            continue
        if len(ucells) > 6:
            print(f"FEL: utdatarad id {ucells[0]} har {len(ucells)} kolumner - for manga")
            return 1
        missing = list(range(len(ucells), 6))
        if all(rcells[j] == "" for j in missing):
            ucells.extend([""] * len(missing))
            fixed += 1
            print(f"reparerar id {ucells[0]}: lagger till {len(missing)} tom(a) slutkolumner "
                  f"(engelskan ar tom dar)")
        else:
            print(f"FEL: id {ucells[0]} saknar kolumner {missing} men ENGELSKAN har text dar - "
                  f"svenskt innehall kan vara tappat: skicka raden till Gemma igen")
            return 1

    with open(sys.argv[2], "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join("\t".join(cells) for _, cells in ut_rows) + "\n")
    print(f"RESULTAT: OK - {fixed} rad(er) fick sina tomma slutkolumner tillbaka; "
          f"kor validern igen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
