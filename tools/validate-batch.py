#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/validate-batch.py - strukturell kontroll av en Gemma-omgang innan
den salls in.

Anvandning:
  python3 tools/validate-batch.py <in-tsv> <ut-tsv> quests
  python3 tools/validate-batch.py <in-tsv> <ut-tsv> npcs

Format:
  quests: kalla   id<TAB>text                (2 kolumner)
          utdata  id<TAB>title<TAB>objectives<TAB>description<TAB>progress<TAB>reward
                                        (6 kolumner; tomma falt ar ok)
  npcs:   kalla   id<TAB>name<TAB>title      (3 kolumner; title ar bara referens)
          utdata  id<TAB>namn                (2 kolumner)

Rubrikraden (id<TAB>...) valideras om den finns, annars hoppas den over -
bade i kallan och i utdata.

FEL (exit 1):
  - blankrader och CR-tecken i nagon av filerna
  - rader med fel kolumnantal (malformed TSV)
  - id: ej numeriska, saknade, dubbletter, okanda, fel ordning
  - utdata: en quest-rad dar alla fem falt ar tomma
  - platshallare/markup per rad som multiset: saknade, tillagda och
    felrknade $N $n $C $c $R $r $B $b $G...; $2oa $s1/$d/$t1 m.fl.,
    #/#, %s/%d och |c...|r/|H...|h rapporteras rad for rad

VARNINGAR (exit 0, mansklig titt):
  - tom titel; legitimt for ofullstandiga kallposter (t.ex. 93429/98070 i
    quests-batch-01/14). Segmenteringssteget ruttar sadana poster till
    translation/review/ via tools/verify-segmentation.py
  - utdatafalt identiskt med engelskan (promptens oforandrad-fallback)
  - npcs: namn oforandrat (personnamn SKA lamnas orandrade; varningen
    finns for att beskrivande namn inte ska smyga forbi)
  - inledande/avslutande mellanslag i utdatafalt

Obs: det har lander bara att struktur och markup stammer. Det bevisar
INTE att den svenska oversattningen ar korrekt eller bra - kvaliteten
sitter kvar i mansklig granskning och /wps fel-rapporter fran spelet.

Exitkoder: 0 = ok (varningar ar mojliga), 1 = FEL, 2 = usage-fel.
"""
import re
import sys
from collections import Counter

KIND = {
    "quests": {"in_cols": 2, "out_cols": 6, "in_header": "id\ttext"},
    "npcs": {"in_cols": 3, "out_cols": 2, "in_header": "id\tname\ttitle"},
}
FIELDS = ("title", "objectives", "description", "progress", "reward")

# Ordningen paa alternativen matter: smalma alternativ foerst, t.ex. $B
# innan den generella bokstavsregeln sa att "$BThe" inte tolkas som
# "BThe", och sifferledade $2oa innan regeln for $[A-Za-z]+.
TOKEN_RE = re.compile(
    r"\$\{[^}\n]*\}"                          # malformlar: ${$m2$*$<frostdamage>}
    r"|\$[Gg][^;\s]*;"                        # konsbyte: $Gman:kvinna;
    r"|\$[0-9]+[A-Za-z]+"                     # sifferledad: $2oa
    r"|\$\?[A-Za-z0-9]*(?:\[[^\]\n]*\])+;?"   # $?a14748[...][...]
    r"|\$[0-9A-Za-z/]+;[0-9A-Za-z;]*"         # semikolonmall: $/10;s2
    r"|\$[BbNnCcRr]"                          # klassiska questkoder
    r"|\$[A-Za-z]+[0-9]*"                     # spellmallar: $s1 $d $t1
    r"|\|H[^|\s]*\|h"                         # lankstart: |Hplayer:%s|h
    r"|\|c[0-9A-Fa-f]{8}"                     # fargingang
    r"|\|r"                                   # fargslut
    r"|\|h"                                   # lankslut/mitten
    r"|#\d*/\d*"                              # malraknare: #/#
    r"|%[0-9]*\$?[sdf]"                       # printf: %s %d %1$s
)


def load_rows(path, label, errors):
    """Las TSV; returnera (radnr, celler, forhandstext) for icke-blanka rader."""
    try:
        with open(path, encoding="utf-8", newline="") as fh:
            raw = fh.read()
    except OSError as exc:
        print(f"FEL: kan inte lasa {label} {path}: {exc}")
        sys.exit(2)
    lines = raw.split("\n")
    rows = []
    for idx, ln in enumerate(lines, 1):
        if ln.endswith("\r"):
            ln = ln[:-1]
            errors.append(f"{label} rad {idx}: CR-tecken (fel radslut?)")
        if not ln.strip():
            if idx == len(lines) and ln == "":
                continue  # vanlig avslutande nyrad
            errors.append(f"{label} rad {idx}: ovantad blank rad i TSV")
            continue
        rows.append((idx, ln.split("\t"), ln))
    return rows


def strip_header(rows, spec, label, errors, warnings, is_source):
    """Ta bort ev. rubrikrad; kallans rubrik ska stamma, utdatafils varnas."""
    if not rows or rows[0][1][0] != "id":
        return rows
    got = "\t".join(rows[0][1]).rstrip()
    want = spec["in_header"]
    if got != want:
        msg = f"{label} rubrik {got!r} (vantad {want!r})"
        if is_source:
            errors.append(msg)
        else:
            warnings.append(msg)
    return rows[1:]
def check_ids(src_ids, dst_ids, errors):
    """id-sekvens: samma tal, i samma ordning, utan dubbletter."""

    def dup_ids(ids):
        where, dups = set(), []
        for i, rid in enumerate(ids, 1):
            if rid in where:
                dups.append(rid)
            else:
                where.add(rid)
        return dups

    for ids, label in ((src_ids, "kalla"), (dst_ids, "utdata")):
        for rid in ids:
            if not rid.isdigit():
                errors.append(f"{label}: icke-numeriskt id {rid!r}")
        for rid in dict.fromkeys(dup_ids(ids)):
            errors.append(f"{label}: id {rid} forekommer flere ganger")

    scount, dcount = Counter(src_ids), Counter(dst_ids)
    missing = [rid for rid in dict.fromkeys(src_ids) if scount[rid] > dcount.get(rid, 0)]
    unexpected = [rid for rid in dict.fromkeys(dst_ids) if dcount[rid] > scount.get(rid, 0)]
    if missing:
        text = ", ".join(missing[:20]) + (f" (+{len(missing) - 20} fler)" if len(missing) > 20 else "")
        errors.append(f"SAKNAS i utdata ({len(missing)}): {text}")
    if unexpected:
        text = ", ".join(unexpected[:20]) + (f" (+{len(unexpected) - 20} fler)" if len(unexpected) > 20 else "")
        errors.append(f"OKANDA id i utdata ({len(unexpected)}): {text}")
    if not missing and not unexpected and src_ids != dst_ids:
        for i, (a, b) in enumerate(zip(src_ids, dst_ids), 1):
            if a != b:
                errors.append(f"ordningen avviker vid rad {i}: kalla har {a}, utdata har {b}")
                break


def token_diff(src_text, dst_text):
    """Returnera (saknade, tillagda) platshallare som Counter-multimangder."""
    want = Counter(TOKEN_RE.findall(src_text))
    got = Counter(TOKEN_RE.findall(dst_text))
    return want - got, got - want


def fmt_counted(counter):
    return ", ".join(f"{name} x{n}" for name, n in sorted(counter.items()))


def check_quest_row(src_text, dst_cells, sid, errors, warnings):
    """En quest-rad: tomhet, kanter och platshallarantal."""
    vals = dst_cells[1:7]
    if not any(v.strip() for v in vals):
        errors.append(f"id {sid}: hela raden ar tom")
        return
    if not vals[0].strip():
        warnings.append(f"id {sid}: titeln ar tom (kan vara legitim partialpost - granska)")
    for name, val in zip(FIELDS, vals):
        if val != val.strip():
            warnings.append(f"id {sid}: mellanslag i kanten pa {name}-falt")
    filled = [v for v in vals if v.strip()]
    if len(filled) == 1 and filled[0].strip() == src_text.strip():
        warnings.append(f"id {sid}: oforandrad engelska i faltet (troligen fallback - granska)")
    lost, added = token_diff(src_text, "\n".join(vals))
    if lost:
        errors.append(f"id {sid}: platshallare saknas: {fmt_counted(lost)}")
    if added:
        errors.append(f"id {sid}: platshallare tillagda: {fmt_counted(added)}")


def check_npc_row(src_cells, dst_cells, sid, errors, warnings):
    """En npc-rad: utdata ar id + namn; title-kolumnen ar bara referens."""
    out_name = dst_cells[1]
    if not out_name.strip():
        errors.append(f"id {sid}: tomt namn")
        return
    if out_name != out_name.strip():
        warnings.append(f"id {sid}: mellanslag kring namnet")
    src_name = src_cells[1] if len(src_cells) > 1 else ""
    if out_name.strip() == src_name.strip():
        warnings.append(f"id {sid}: namnet oforandrat (personnamn ar ratt; kontrollera beskrivande namn)")
    lost, added = token_diff(src_name, out_name)
    if lost:
        errors.append(f"id {sid}: platshallare saknas: {fmt_counted(lost)}")
    if added:
        errors.append(f"id {sid}: platshallare tillagda: {fmt_counted(added)}")


def main():
    if len(sys.argv) != 4:
        print("usage: validate-batch.py <in-tsv> <ut-tsv> quests|npcs", file=sys.stderr)
        return 2
    inp, outp, kind = sys.argv[1], sys.argv[2], sys.argv[3]
    if kind not in KIND:
        print(f"okand sort {kind!r}: anvand quests eller npcs", file=sys.stderr)
        return 2
    spec = KIND[kind]

    errors, warnings = [], []
    src_rows = load_rows(inp, "kalla", errors)
    dst_rows = load_rows(outp, "utdata", errors)
    src_rows = strip_header(src_rows, spec, "kalla", errors, warnings, is_source=True)
    dst_rows = strip_header(dst_rows, spec, "utdata", errors, warnings, is_source=False)

    for rows, label, want_n in ((src_rows, "kalla", spec["in_cols"]),
                                (dst_rows, "utdata", spec["out_cols"])):
        for idx, parts, ln in rows:
            if len(parts) != want_n:
                errors.append(f"{label} rad {idx}: {len(parts)} kolumner (vantade {want_n}): {ln[:80]!r}")

    src_ids = [parts[0] for _, parts, _ in src_rows]
    dst_ids = [parts[0] for _, parts, _ in dst_rows]
    check_ids(src_ids, dst_ids, errors)

    pairs = 0
    for (_, sparts, _), (_, dparts, _) in zip(src_rows, dst_rows):
        if len(sparts) != spec["in_cols"] or len(dparts) != spec["out_cols"]:
            continue
        if sparts[0] != dparts[0]:
            continue  # id-avvikelsen ar redan anmald
        pairs += 1
        sid = sparts[0]
        if kind == "quests":
            check_quest_row(sparts[1], dparts, sid, errors, warnings)
        else:
            check_npc_row(sparts, dparts, sid, errors, warnings)

    print(f"indata: {len(src_rows)} rader   utdata: {len(dst_rows)} rader   jamforda: {pairs}")
    for msg in errors:
        print(f"FEL: {msg}")
    for msg in warnings:
        print(f"VARNING: {msg}")
    if errors:
        print(f"RESULTAT: {len(errors)} FEL och {len(warnings)} varningar - rakna inte in batchen")
    else:
        print(f"RESULTAT: OK ({len(warnings)} varningar) - strukturen stammer")
    print("(Strukturkontroll kan inte saga om svenska ar bra - granska och samla in /wps fel.)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())