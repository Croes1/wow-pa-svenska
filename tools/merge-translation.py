#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/merge-translation.py - insert new, approved translation rows into the real
Data/*.lua files.

Nothing is regenerated. The rows of the explicit input are compared with the
target table, rows whose key is new are inserted, everything else in the target is
left byte for byte as it was. No Extra file is created and the .toc is never edited.

  quests  Data/Quest.lua  table quest   [id]={t,d,o,p,c}
  npcs    Data/Npc.lua    table npc     [id]="Name"
  ui      Data/Ui.lua     table ui      ["English"]="Svenska"

gameobjects and pagetext have no runtime table in the addon and are refused.

Input (--input is required; a file, or a directory of batch outputs):
  quests  id<TAB>title<TAB>objectives<TAB>description<TAB>progress<TAB>reward
          A directory means every quests-batch-NN-sv.tsv in it, in batch order.
          An empty field gets no key: the addon only replaces fields that exist.
  npcs    id<TAB>name        (a directory means npcs-batch-NN-sv.tsv)
  ui      --input is the English dump (id<TAB>area<TAB>en, as written by
          parse-uidump.py) and --sv the Swedish file (id<TAB>sv); rows are paired by id.
An optional header line (first column "id") is skipped.

Line breaks in a cell are written as escapes because a TSV row is one line: \\r\\n,
\\n and \\r all mean one real line break (stored as a Lua \\n, the form the other quests
use), and \\t means a tab (for ui only \\n and \\t are decoded, as in
check-ui-translation.lua). Every other character, including quotes and a lone backslash,
is taken literally and escaped for Lua on the way out. Placeholders such as $B, $N, %s
and |c...|r are never touched.

Rules:
  - Structural problems abort the whole run and nothing is written: wrong column count,
    non-numeric or duplicate id, ids that differ between the ui files.
  - Rows that are well formed but unusable (a quest with every field empty, an empty npc
    name or ui text, control characters) are rejected: reported and skipped.
  - A key that already exists in the target is never overwritten: it is skipped and
    reported with the target file and key. --overwrite replaces such entries instead and
    lists every old and new value; use it only for a deliberate correction.
  - New entries go in deterministically (see datalua.py): in id order, in place in sorted
    tables, appended in Ui.lua.
  - The target is replaced atomically after the result has been re-parsed and, if
    luac5.1 is installed, syntax checked. A failed check leaves the target untouched.

Usage:
  python3 tools/merge-translation.py quests --input DIR_OR_FILE [--dry-run]
  python3 tools/merge-translation.py npcs --input DIR_OR_FILE [--dry-run]
  python3 tools/merge-translation.py ui --input dump-en.tsv --sv dump-sv.tsv [--dry-run]

  --dry-run    report additions, collisions and rejections; write nothing
  --data-dir   directory holding the Data files (default: Data/ in this repository)
  --overwrite  replace existing entries instead of skipping them

Exit status: 0 on success (also when rows were skipped or rejected), 1 on a structural
error or a failed check, 2 on a usage error.
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import datalua  # noqa: E402

BATCH_RE = re.compile(r"batch-(\d+)")
# Quest fields in the order Data/Quest.lua uses for most entries; the TSV columns are title, objectives,
# description, progress, reward (t, o, d, p, c).
QUEST_COLUMNS = (("t", 1), ("d", 3), ("o", 2), ("p", 4), ("c", 5))
QUEST_BREAKS = re.compile(r"\\r\\n|\\n|\\r|\\t")
UI_BREAKS = re.compile(r"\\n|\\t")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")

KINDS = {
    "quests": {"file": "Quest.lua", "table": "quest", "pattern": "quests-batch-*-sv.tsv"},
    "npcs": {"file": "Npc.lua", "table": "npc", "pattern": "npcs-batch-*-sv.tsv"},
    "ui": {"file": "Ui.lua", "table": "ui", "pattern": None},
}
NO_RUNTIME_TABLE = ("gameobjects", "pagetext")
SHOW = 10   # how many collisions/rejections to list before summarising


class MergeError(Exception):
    pass


def decode_cell(text, ui=False):
    """Turn the TSV escapes for line breaks and tabs into the real characters."""
    pattern = UI_BREAKS if ui else QUEST_BREAKS
    return pattern.sub(lambda m: "\t" if m.group() == "\\t" else "\n", text)


def input_files(path, kind):
    if os.path.isdir(path):
        pattern = KINDS[kind]["pattern"]
        if not pattern:
            raise MergeError(f"--input for {kind} must be a file, not a directory: {path}")
        files = sorted(glob.glob(os.path.join(path, pattern)),
                       key=lambda p: int(BATCH_RE.search(os.path.basename(p)).group(1)))
        if not files:
            raise MergeError(f"no {pattern} files in {path}")
        return files
    if not os.path.isfile(path):
        raise MergeError(f"input not found: {path}")
    return [path]


def read_tsv(path, columns):
    """Rows as (lineno, cells); the header line is skipped. Structural errors raise MergeError."""
    try:
        with open(path, encoding="utf-8", newline="") as fh:
            raw = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise MergeError(f"cannot read {path}: {exc}")
    if "\r" in raw:
        raise MergeError(f"{path}: contains CR characters; save the file with LF line endings")
    lines = raw.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    rows = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            raise MergeError(f"{path}:{number}: unexpected blank line")
        cells = line.split("\t")
        if number == 1 and cells[0] == "id":
            continue
        if len(cells) != columns:
            raise MergeError(f"{path}:{number}: {len(cells)} columns, expected {columns}")
        if not cells[0].isdigit():
            raise MergeError(f"{path}:{number}: non-numeric id {cells[0]!r}")
        rows.append((number, cells))
    return rows


def check_text(text, label):
    """Why a decoded text cannot be stored, or None."""
    if CONTROL_RE.search(text):
        return f"{label} contains a control character"
    return None


def quest_rows(path):
    out, rejected = [], []
    for number, cells in read_tsv(path, 6):
        key = int(cells[0])
        value = {}
        problem = None
        for field, col in QUEST_COLUMNS:
            text = decode_cell(cells[col])
            if text == "":
                continue            # empty field: no key
            problem = problem or check_text(text, f"field {field}")
            value[field] = text
        if problem:
            rejected.append((path, number, key, problem))
        elif not value:
            rejected.append((path, number, key, "every field is empty"))
        else:
            out.append((key, value, path, number))
    return out, rejected


def npc_rows(path):
    out, rejected = [], []
    for number, cells in read_tsv(path, 2):
        key = int(cells[0])
        name = decode_cell(cells[1]).strip()
        problem = ("the name is empty" if not name else check_text(name, "the name"))
        if problem:
            rejected.append((path, number, key, problem))
        else:
            out.append((key, name, path, number))
    return out, rejected


def ui_rows(en_path, sv_path):
    en = {}
    for number, cells in read_tsv(en_path, 3 if _has_area(en_path) else 2):
        if cells[0] in en:
            raise MergeError(f"{en_path}:{number}: duplicate id {cells[0]}")
        en[cells[0]] = (number, cells[-1])
    sv = {}
    for number, cells in read_tsv(sv_path, 2):
        if cells[0] in sv:
            raise MergeError(f"{sv_path}:{number}: duplicate id {cells[0]}")
        sv[cells[0]] = (number, cells[1])
    if set(en) != set(sv):
        missing = sorted(set(en) - set(sv))[:5]
        extra = sorted(set(sv) - set(en))[:5]
        raise MergeError(f"ids differ between {en_path} and {sv_path}: only in English {missing}, only in Swedish {extra}")
    out, rejected, seen = [], [], {}
    for rid in sorted(en, key=int):
        number, en_text = en[rid]
        en_text, sv_text = decode_cell(en_text, ui=True), decode_cell(sv[rid][1], ui=True)
        problem = None
        if not en_text.strip():
            problem = "the English text is empty"
        elif not sv_text.strip():
            problem = "the Swedish text is empty"
        else:
            problem = check_text(en_text, "the English text") or check_text(sv_text, "the Swedish text")
        if problem:
            rejected.append((en_path, number, rid, problem))
            continue
        if en_text in seen:
            raise MergeError(f"{en_path}: ids {seen[en_text]} and {rid} have the same English text {en_text!r}")
        seen[en_text] = rid
        out.append((en_text, sv_text, en_path, number))
    return out, rejected


def _has_area(path):
    with open(path, encoding="utf-8") as fh:
        first = fh.readline().rstrip("\n").split("\t")
    return len(first) == 3


def collect(kind, inputs, sv):
    """All usable rows of the input as (key, value, path, line) plus the rejected ones."""
    rows, rejected = [], []
    if kind == "ui":
        if len(inputs) != 1 or not sv:
            raise MergeError("ui needs exactly one --input (English file) and --sv (Swedish file)")
        en_path = input_files(inputs[0], kind)[0]
        if not os.path.isfile(sv):
            raise MergeError(f"input not found: {sv}")
        print(f"reading {en_path}")
        print(f"reading {sv}")
        return ui_rows(en_path, sv)
    if sv:
        raise MergeError("--sv is only used with ui")
    reader = quest_rows if kind == "quests" else npc_rows
    files = []
    for item in inputs:
        files.extend(input_files(item, kind))
    seen = {}
    for path in files:
        print(f"reading {path}")
        part, bad = reader(path)
        # a rejected row still occupies its id: a repeated id is a structural error either way
        for key, src, number in ([(k, s_, n) for k, _v, s_, n in part] + [(k, p, n) for p, n, k, _why in bad]):
            if key in seen:
                raise MergeError(f"id {key} appears in both {seen[key]} and {src}:{number}")
            seen[key] = f"{src}:{number}"
        rows.extend(part)
        rejected.extend(bad)
    return rows, rejected


def short(value, width=60):
    text = repr(value)
    return text if len(text) <= width else text[:width - 3] + "..."


def luac_check(tmp):
    luac = shutil.which("luac5.1")
    if luac is None:
        return
    result = subprocess.run([luac, "-p", tmp], capture_output=True, text=True)
    if result.returncode != 0:
        raise datalua.DataError("luac5.1 rejected the result: " + result.stderr.strip())


def merge(kind, inputs, sv, data_dir, dry_run, overwrite):
    spec = KINDS[kind]
    target = os.path.join(data_dir, spec["file"])
    rows, rejected = collect(kind, inputs, sv)
    print(f"target {target} (table {spec['table']})")
    df = datalua.DataFile.read(target)
    table = df.table(spec["table"])

    added, collisions = [], []
    for key, value, src, number in sorted(rows, key=lambda r: r[0]):
        if key in table:
            collisions.append((key, value, src, number))
        else:
            added.append((key, value))
    replaced = collisions if overwrite else []
    skipped = [] if overwrite else collisions

    for key, value, src, number in skipped[:SHOW]:
        print(f"SKIP  {spec['file']} {datalua.key_text(key)} already exists: {short(table.get(key))}  (input {src}:{number})")
    if len(skipped) > SHOW:
        print(f"SKIP  ... and {len(skipped) - SHOW} more existing keys")
    for key, value, src, number in replaced[:SHOW]:
        print(f"REPLACE {spec['file']} {datalua.key_text(key)}\n    old: {short(table.get(key), 100)}\n    new: {short(value, 100)}")
    if len(replaced) > SHOW:
        print(f"REPLACE ... and {len(replaced) - SHOW} more")
    for path, number, key, why in rejected[:SHOW]:
        print(f"REJECT {path}:{number} id {key}: {why}")
    if len(rejected) > SHOW:
        print(f"REJECT ... and {len(rejected) - SHOW} more")

    verb = "would add" if dry_run else "added"
    print(f"{verb}: {len(added)}   skipped (already in {spec['file']}): {len(skipped)}   "
          f"rejected: {len(rejected)}" + (f"   replaced: {len(replaced)}" if overwrite else ""))
    if dry_run:
        print("--dry-run: nothing written")
        return 0
    if not added and not replaced:
        print("nothing to write")
        return 0

    df.insert(spec["table"], added)
    for key, value, _src, _n in replaced:
        df.replace(spec["table"], key, value)
    df.write(check=luac_check)
    if shutil.which("luac5.1") is None:
        print("note: luac5.1 not found; the result was checked by datalua.py only")

    # Post-condition: read the file back and compare every row with the input.
    again = datalua.DataFile.read(target).table(spec["table"])
    wanted = dict(added)
    wanted.update({k: v for k, v, _s, _n in replaced})
    bad = [k for k, v in wanted.items() if again.get(k) != v]
    if bad:
        raise MergeError(f"verification failed for {len(bad)} entries after writing {target}, e.g. {bad[:3]}")
    print(f"wrote {target}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Insert new approved translation rows into Data/*.lua (see the module docstring).")
    ap.add_argument("kind", choices=sorted(KINDS) + list(NO_RUNTIME_TABLE))
    ap.add_argument("--input", action="append", required=True, metavar="PATH",
                    help="TSV file or directory of batch outputs (repeatable except for ui)")
    ap.add_argument("--sv", metavar="FILE", help="ui only: the Swedish file (id<TAB>sv)")
    ap.add_argument("--data-dir", default=os.path.join(ROOT, "Data"), help="directory with the Data files")
    ap.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    ap.add_argument("--overwrite", action="store_true",
                    help="replace existing entries instead of skipping them (deliberate corrections only)")
    args = ap.parse_args(argv)
    if args.kind in NO_RUNTIME_TABLE:
        ap.error(f"{args.kind} has no runtime table in the addon; keep those batches in the work directory")
    try:
        return merge(args.kind, args.input, args.sv, args.data_dir, args.dry_run, args.overwrite)
    except (MergeError, datalua.DataError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("nothing was written", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
