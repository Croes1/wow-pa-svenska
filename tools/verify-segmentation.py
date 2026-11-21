#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/verify-segmentation.py - deterministisk kontroll av den engelska
segmenteringsfilen (Task A i prompten for segmenteringssteget).

Anvandning (explicita sokvagar; ingen hardkodad katalog):
  python3 tools/verify-segmentation.py <kalla-batch-tsv> <segmenterad-en-tsv> [review-tsv]

Enda fil som skrivs ar review-filen, och bara om nagon rad ruttas dit. Utan
tredje argumentet hamnar den i review/ bredvid kallfilen (i arbetskatalogen).

Regeln: de fem faltene title+objectives+description+progress+reward,
sammanfogade utan mellanrum, ska vara EN exakt partition av kalltexten.
Enda normalisering som ar tillaten (dokumenterad i PROMPT-GEMMA.md):
kallradens inledande och avslutande blanka tecken far tappas (t.ex.
mellanslaget fore titeln i " WANTED: ..."). Allt annat gar byte for byte:
inga ord far tillkomma, forsvinna, ordnas om eller fa nytt mellanrum.

FEL (exit 1): saknad/okant/dublett id, fel kolumnantal, blankrader, helt
tom rad och sammanfogning som inte stammer kallan.

GRANSKNING (review-fil, exit 0): rader som ar sannolikt ofullstandiga
eller tvetydiga ruttas till review-filen for mansklig titt och ska inte
automatoversattas vidare som om ingenting hade varit:
  - tom titel (ingen framsida - fragmentposter t.ex. 93429/98070)
  - kalltexten borjar med gemen, '<' eller en $-token (fragment som
    95534/97539 - inledningen saknas redan i kallan)

Obs: kontrollen bevisar bara att segmenten AR en partition av kallan. Den
kan inte saga om en text hamnat i ratt falt (progress eller description
pa en fragment-post) - det avgor mansklig granskning i review-filen.
Hittar pa ALDRIG text: falt som saknas lamnas tomma.
"""
import re
import sys
import os
from collections import Counter

FIELDS = ("title", "objectives", "description", "progress", "reward")
REVIEW_HEADER = ("id", "orsak", "title", "objectives", "description",
                 "progress", "reward", "kalla")

# En kallrad som borjar med gemen, '<' eller $-token saknar framsidan
# (titel) i kallan: det ar ett fragment och rutts alltid till granskning.
FRAGMENT_RE = re.compile(r"^[a-z<]|^\$[A-Za-z0-9]")


def load_rows(path, label, errors):
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
                continue
            errors.append(f"{label} rad {idx}: ovantad blank rad i TSV")
            continue
        rows.append((idx, ln.split("\t"), ln))
    return rows


def strip_header(rows):
    if rows and rows[0][1][0] == "id":
        return rows[1:]
    return rows


def esc(value):
    """TSV-saker text for review-filen (lassbart, inte for masining)."""
    return (value.replace("\\", "\\\\").replace("\t", "\\t")
                 .replace("\n", "\\n"))


def dup_ids(ids):
    where, dups = set(), []
    for rid in ids:
        if rid in where:
            dups.append(rid)
        else:
            where.add(rid)
    return dups
def main():
    if len(sys.argv) not in (3, 4):
        print("usage: verify-segmentation.py <kalla-tsv> <segmenterad-tsv> [review-tsv]",
              file=sys.stderr)
        return 2
    src_path, seg_path = sys.argv[1], sys.argv[2]
    if len(sys.argv) == 4:
        review_path = sys.argv[3]
    else:
        stem = os.path.splitext(os.path.basename(src_path))[0]
        review_path = os.path.join(os.path.dirname(src_path) or ".", "review",
                                   f"{stem}-en-review.tsv")

    errors, review_rows = [], []
    src_rows = strip_header(load_rows(src_path, "kalla", errors))
    seg_rows = strip_header(load_rows(seg_path, "segment", errors))

    for rows, label, want in ((src_rows, "kalla", 2), (seg_rows, "segment", 6)):
        for idx, parts, ln in rows:
            if len(parts) != want:
                errors.append(
                    f"{label} rad {idx}: {len(parts)} kolumner (vantade {want}): {ln[:80]!r}")
            elif not parts[0].isdigit():
                errors.append(f"{label} rad {idx}: icke-numeriskt id {parts[0]!r}")

    src_ids = [parts[0] for _, parts, _ in src_rows if len(parts) >= 2]
    seg_ids = [parts[0] for _, parts, _ in seg_rows if len(parts) >= 2]
    for rid in dict.fromkeys(dup_ids(src_ids) + dup_ids(seg_ids)):
        errors.append(f"id {rid} forekommer flera ganger")

    scount, gcount = Counter(src_ids), Counter(seg_ids)
    missing = [rid for rid in dict.fromkeys(src_ids) if scount[rid] > gcount.get(rid, 0)]
    unexpected = [rid for rid in dict.fromkeys(seg_ids) if gcount[rid] > scount.get(rid, 0)]
    if missing:
        errors.append(f"SAKNAS i segmentering ({len(missing)}): {', '.join(missing[:20])}")
    if unexpected:
        errors.append(f"OKANDA id ({len(unexpected)}): {', '.join(unexpected[:20])}")

    src_map = {parts[0]: parts[1] for _, parts, _ in src_rows if len(parts) == 2}
    segmented, routed = 0, 0
    for (_, sparts, _), (_, gparts, _) in zip(src_rows, seg_rows):
        if sparts[0] != gparts[0]:
            continue
        sid, body = sparts[0], sparts[1]
        fields = gparts[1:7]
        segmented += 1
        reasons = []
        if "".join(fields) != body.strip():
            errors.append(
                f"id {sid}: sammanfogningen stammer inte kallan "
                f"(segment {len(''.join(fields))} tecken, kallan {len(body.strip())} efter trimning)")
            reasons.append("sammanfogningen stammer inte kallan")
        elif not any(f.strip() for f in fields):
            errors.append(f"id {sid}: hela raden ar tom")
            reasons.append("hela raden ar tom")
        if not fields[0].strip():
            reasons.append("titeln ar tom (ofullstandig eller fragmentpost)")
        if FRAGMENT_RE.match((body.strip() or "") + "\n"):
            reasons.append("kalltexten borjar som fragment (gemen/'<'/$-token)")
        if reasons:
            routed += 1
            review_rows.append((sid, "; ".join(reasons), fields, body))

    os.makedirs(os.path.dirname(review_path) or ".", exist_ok=True)
    if review_rows:
        with open(review_path, "w", encoding="utf-8") as fh:
            fh.write("\t".join(REVIEW_HEADER) + "\n")
            for sid, reasons, fields, body in review_rows:
                cells = [sid, reasons] + [esc(f) for f in fields] + [esc(body)]
                fh.write("\t".join(cells) + "\n")

    print(f"kalla: {len(src_rows)} rader   segment: {len(seg_rows)} rader   jamforda: {segmented}")
    for msg in errors:
        print(f"FEL: {msg}")
    print(f"ruttade till granskning: {routed}"
          + (f" -> {review_path}" if review_rows else " (ingen review-fil behovdes)"))
    if errors:
        print(f"RESULTAT: {len(errors)} FEL - rakna inte in segmenteringen")
        return 1
    print("RESULTAT: OK - samtliga segment bygger samman till kallan (utom radens trimning)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
