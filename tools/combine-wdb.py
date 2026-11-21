#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/combine-wdb.py - combine several WDB cache files into the cache TSVs.

Give one or more folders. Each folder is scanned for *.wdb files, every file
is converted with tools/parse-wdb.py, and the results are combined per type:

  quest (WQST)       -> questcache-en.tsv       one row per id (first wins)
  creature (WMOB)    -> creaturecache-en.tsv    one row per id (first wins)
  game object (WGOB) -> gameobjectcache-en.tsv  exact duplicate rows removed
                        (entry ids repeat by design, so ids are not unique)
  page text (WPTX)   -> pagetextcache-en.tsv    one row per id (first wins)

Only the output files for types that were found are written. Existing files
for other types are left alone. An existing output file is never overwritten
unless --force is given.

Usage:
  python3 tools/combine-wdb.py <folder> [<folder> ...] [-r] (--work-dir DIR | --out-dir DIR) [--force]

  -r          also read .wdb files in all subfolders of the given folders.
  --work-dir  external work directory; the *-en.tsv files go to DIR/cache/
  --out-dir   write the *-en.tsv files straight into this folder instead
  --force     overwrite output files that already exist

Nothing is written inside the repository unless you point --work-dir or
--out-dir there. The files read and written are printed.

Example:
  python3 tools/combine-wdb.py -r .../cache_wow .../WoW/Cache/WDB/enUS --work-dir ~/wow-pa-svenska-work
"""
import argparse
import importlib.util
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PARSER = os.path.join(HERE, "parse-wdb.py")

# magic (as read from the file) -> (output file name, dedupe rule)
TYPES = {
    "WQST": ("questcache-en.tsv", "id"),
    "WMOB": ("creaturecache-en.tsv", "id"),
    "WGOB": ("gameobjectcache-en.tsv", "line"),
    "WPTX": ("pagetextcache-en.tsv", "id"),
}


def load_parser():
    spec = importlib.util.spec_from_file_location("parse_wdb", PARSER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def combine_lines(header, blocks, dedupe):
    """Merge TSV text blocks (each with its own header line).

    dedupe="id":   keep the first row seen for each id (column 1).
    dedupe="line": keep the first copy of each identical row.
    Returns (header, rows, removed_count).
    """
    seen = set()
    rows = []
    removed = 0
    for block in blocks:
        for line in block.split("\n")[1:]:
            if not line:
                continue
            key = line.split("\t", 1)[0] if dedupe == "id" else line
            if key in seen:
                removed += 1
                continue
            seen.add(key)
            rows.append(line)
    return header, rows, removed


def wdb_magic(path):
    with open(path, "rb") as fh:
        return fh.read(4)[::-1].decode("latin1", "replace")


def wdb_files(folder, recursive):
    """Yield .wdb paths in folder, in sorted order (subfolders if recursive)."""
    if not recursive:
        for name in sorted(os.listdir(folder)):
            if name.lower().endswith(".wdb"):
                yield os.path.join(folder, name)
        return
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames.sort()
        for name in sorted(filenames):
            if name.lower().endswith(".wdb"):
                yield os.path.join(dirpath, name)


def collect(folders, recursive=False):
    """Map magic -> list of .wdb file paths, in a stable order."""
    found = {}
    for folder in folders:
        if not os.path.isdir(folder):
            sys.exit(f"not a folder: {folder}")
        for path in wdb_files(folder, recursive):
            magic = wdb_magic(path)
            if magic in TYPES:
                found.setdefault(magic, []).append(path)
            else:
                print(f"skip {path}: not a supported cache type ({magic!r})")
    return found


def convert(parser, path, workdir):
    """Run parse-wdb on one file and return its TSV text."""
    out = os.path.join(workdir, os.path.basename(path) + ".tsv")
    with open(path, "rb") as fh:
        data = fh.read()
    try:
        parser.tsv_mode(data, out)
    except ValueError as exc:
        print(f"skip {path}: {exc}")
        return None
    with open(out, encoding="utf-8") as fh:
        return fh.read()


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Combine WDB cache files from one or more folders.")
    ap.add_argument("folders", nargs="+", help="folder(s) containing .wdb files")
    ap.add_argument("-r", "--recursive", action="store_true",
                    help="also read .wdb files in all subfolders")
    where = ap.add_mutually_exclusive_group(required=True)
    where.add_argument("--work-dir", help="external work directory; output goes to <work-dir>/cache/")
    where.add_argument("--out-dir", help="folder that receives the *-en.tsv files directly")
    ap.add_argument("--force", action="store_true",
                    help="overwrite output files that already exist")
    args = ap.parse_args(argv)
    out_dir = args.out_dir or os.path.join(args.work_dir, "cache")

    found = collect(args.folders, recursive=args.recursive)
    if not found:
        sys.exit("no supported .wdb files found in the given folders "
                 "(use -r to also search subfolders)")

    if not args.force:
        clash = [os.path.join(out_dir, TYPES[m][0]) for m in found
                 if os.path.exists(os.path.join(out_dir, TYPES[m][0]))]
        if clash:
            sys.exit("refusing to overwrite (use --force): " + ", ".join(clash))

    parser = load_parser()
    os.makedirs(out_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as workdir:
        for magic, paths in found.items():
            out_name, dedupe = TYPES[magic]
            blocks = []
            for path in paths:
                text = convert(parser, path, workdir)
                if text is not None:
                    blocks.append(text)
                    print(f"read {path}")
            if not blocks:
                continue
            header = blocks[0].split("\n")[0]
            header, rows, removed = combine_lines(header, blocks, dedupe)
            out_path = os.path.join(out_dir, out_name)
            with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(header + "\n")
                for row in rows:
                    fh.write(row + "\n")
            print(f"wrote {out_path}: {len(rows)} rows from {len(paths)} file(s), "
                  f"{removed} duplicate row(s) removed")


if __name__ == "__main__":
    main()
