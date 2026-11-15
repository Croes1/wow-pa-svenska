#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/parse-wdb.py - parser for the WoW client cache files in Cache/WDB
(questcache.wdb = WQST, creaturecache.wdb = WMOB, gameobjectcache.wdb = WGOB).

Verified layout (Forever client build 70938):
  header   = 24 bytes: magic, build, locale('enUS'), u32, u32, 0
  records  = [u32 id][u32 blobSize][blob...]  (no padding)
  trailer  = 8 bytes

  WMOB blob  = numerics..., name (c-string), ..., subtitle (c-string)
  WGOB blob  = [u32 ?][u32 entryId], name (c-string), numerics
  WQST blob  = numerics, then ONE long text:
               " <Title><Description>$B...<OfferText>"
               (title/description/reward are glued, no separators!)
               -> reported as `body`; per-field split happens later.

Read-only. Usage:
  python3 tools/parse-wdb.py <file.wdb> probe              diagnostics
  python3 tools/parse-wdb.py <file.wdb> scan               layout hypotheses
  python3 tools/parse-wdb.py <file.wdb> find <needle>      hexdump around needle
  python3 tools/parse-wdb.py <file.wdb> blob 0,1           blob diagnostics
  python3 tools/parse-wdb.py <file.wdb> tsv <out.tsv>      id + extracted text/name
"""
import re
import struct
import sys

NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9'\"()\-. ]{2,}$")


def u32(d, off):
    return struct.unpack_from("<I", d, off)[0]


def cstrings(data, lo, hi, min_len=1):
    """All NUL-terminated strings in data[lo:hi] with their offsets."""
    out = []
    i = lo
    while i < hi:
        j = i
        while j < hi and j - i < 65536:
            b = data[j]
            if b == 0 or not (32 <= b < 127 or b == 9 or b >= 0x80):
                break
            j += 1
        terminated = j < hi and data[j] == 0
        if terminated:
            if j - i >= min_len:
                out.append((i, data[i:j].decode("utf-8", "replace")))
            i = j + 1
        elif j == hi and j - i >= min_len:
            # segmentet fyller blob-slutet utan nullterminering
            # (sa serialiserar klienten questtexten)
            out.append((i, data[i:j].decode("utf-8", "replace")))
            i = j
        else:
            i = j + 1
    return out


def textish(s):
    """True if the string looks like real text, not binary noise."""
    if not NAME_RE.match(s):
        return False
    return sum(ch.isalpha() for ch in s) >= 3


def try_records(data, start):
    pos, recs = start, []
    n = len(data)
    while pos + 8 <= n:
        rid = u32(data, pos)
        size = u32(data, pos + 4)
        if size == 0 or pos + 8 + size > n:
            break
        recs.append((rid, data[pos + 8:pos + 8 + size]))
        pos += 8 + size
    return recs, n - pos


def extract_row(magic, rid, blob):
    """(id, col1, col2) per cache type, or None for junk records."""
    strings = [s for _, s in cstrings(blob, 0, len(blob), min_len=1)]
    if magic == "WQST":
        longs = [s for s in strings if len(s) >= 50]
        if not longs:
            return None
        body = max(longs, key=len).strip()
        return (rid, body, "") if body else None
    if magic == "WMOB":
        names = [s for s in strings if textish(s)]
        if not names:
            return None
        name = names[0].strip()
        title = names[1].strip() if len(names) > 1 else ""
        return (rid, name, title)
    if magic == "WGOB":
        inner = u32(blob, 4) if len(blob) >= 8 else 0
        names = [s for s in strings if textish(s)]
        if not names:
            return None
        key = inner if 0 < inner < 1000000 else rid
        return (key, names[0].strip(), "")
    return None

def hexdump(data, lo, hi):
    for off in range(lo, hi, 16):
        chunk = data[off:off + 16]
        hexpart = "|".join(f"{b:02x}" for b in chunk)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"  {off:06x}  {hexpart:<48}  |{asc}|")


def find_mode(data, needle):
    raw = needle.encode("latin1", "replace")
    pos, hits = 0, 0
    while True:
        i = data.find(raw, pos)
        if i < 0:
            break
        hits += 1
        lo = max(0, i - 0x50)
        hi = min(len(data), i + len(raw) + 0x50)
        print(f"\n--- hit {hits} at file offset {i:#x} ({i}) ---")
        hexdump(data, lo, hi)
        pos = i + 1
        if hits >= 3:
            print("(more hits hidden)")
            break
    if hits == 0:
        print("no hits")


def blob_mode(data):
    recs, trailer = try_records(data, 0x18)
    print(f"records={len(recs)}  trailer={trailer}")
    for idx in [int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else "0").split(",")]:
        rid, blob = recs[idx]
        print(f"\n=== record #{idx}  id={rid}  blobSize={len(blob)} ===")
        for off in range(0, min(len(blob), 0x60), 4):
            print(f"    +{off:04x}: {u32(blob, off):>12}   {blob[off:off+4].hex(' ')}")
        hexdump(blob, 0, min(len(blob), 0x180))
        for off, s in cstrings(blob, 0, len(blob), min_len=1):
            print(f"  +{off:04x}: {s!r}")


def scan(data):
    print("record-layout scan ([u32 id][u32 size][data]):")
    for hsize in (16, 20, 24, 28, 32, 40, 48):
        recs, trailer = try_records(data, hsize)
        if len(recs) < 4:
            print(f"  hsize={hsize:#04x}: only {len(recs)} records, trailer={trailer}")
            continue
        sizes = [len(b) for _, b in recs]
        print(f"  hsize={hsize:#04x}: recs={len(recs)}  trailer={trailer}  "
              f"ids[:5]={[r[0] for r in recs[:5]]}  sizes[:8]={sizes[:8]}")


def tsv_mode(data, outpath):
    magic = data[:4][::-1].decode("latin1")
    recs, trailer = try_records(data, 0x18)
    rows, skipped = [], 0
    for rid, blob in recs:
        row = extract_row(magic, rid, blob)
        if row:
            rows.append(row)
        else:
            skipped += 1
    wide = magic in ("WMOB", "WGOB")
    with open(outpath, "w", encoding="utf-8") as fh:
        fh.write("id\tname\textra\n" if wide else "id\ttext\n")
        for rid, a, b in rows:
            b = b.replace("\t", " ").replace("\n", "\\n")
            fh.write(f"{rid}\t{a}\t{b}\n" if b else f"{rid}\t{a}\n")
    print(f"tsv: wrote {len(rows)} rows to {outpath} (skipped {skipped})")
    if magic == "WQST" and rows:
        sample = max(rows, key=lambda r: len(r[1]))
        print("sample body:", sample[0], "->", sample[1][:100])


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    path, mode = sys.argv[1], sys.argv[2]
    with open(path, "rb") as fh:
        data = fh.read()
    magic = data[:4][::-1].decode("latin1")
    build = u32(data, 4)
    locale = data[8:12][::-1].decode("latin1")
    print(f"{path}: magic={magic} build={build} locale={locale!r} size={len(data)}")
    if mode == "probe":
        print("  u32 map of first 0x40:")
        for off in range(0, 0x40, 4):
            print(f"    {off:04x}: {u32(data, off):>12}   {data[off:off+4].hex(' ')}")
        hexdump(data, 0x18, 0x138)
        print("c-strings in the first 0x800:")
        for off, s in cstrings(data, 0x18, 0x800):
            print(f"  {off:06x}: {s!r}")
    elif mode == "scan":
        scan(data)
    elif mode == "find":
        find_mode(data, sys.argv[3])
    elif mode == "blob":
        blob_mode(data)
    elif mode == "tsv":
        if len(sys.argv) < 4:
            sys.exit(__doc__)
        tsv_mode(data, sys.argv[3])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
