#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/check-data.py - search and validate the addon's Data/*.lua files. Read-only, offline.

  python3 tools/check-data.py [check]            validate everything (the default command)
  python3 tools/check-data.py search TEXT        find English or Swedish text, or a comment
  python3 tools/check-data.py gossip-key TEXT    print the Data/Gossip.lua key of an English text

Common option: --data-dir DIR (default: Data/ in this repository).

check
  Prints every ERROR, then a summary of the WARNINGs (a few examples per kind; --examples N
  or --all-warnings for more). Exit status 1 if there is at least one error, 0 otherwise.
  Errors are things that must block a merge; warnings are for a human to look at and never
  change the exit status.

  Errors
    parse-error         a file or line is not in the format tools/datalua.py understands
    duplicate-key       the same key twice in one table (Lua keeps the last one)
    bad-key             wrong key type or shape: ids must be positive integers, name tables need
                        non-empty strings, gossip keys must be <length>_<8 hex digits>
    bad-value           wrong value type for the table, an empty string/list/entry, an unknown
                        field, a field of the wrong type, or Item h outside 0..2^32-1
    missing-field       quest without any of t/d/o/p/c; item without n; item d without h (the
                        description is only used when h matches); spell a without ea (auras need
                        both); spell without any of n/d/a/c
    literal-escape      a value contains a backslash followed by r or n: a line break that was
                        escaped twice and shows up in game as "\\r\\n"
    control-char        a value contains a control character other than a line break
    token-lost          the English source has a placeholder the Swedish text lacks
                        (spell e->d and ea->a, and key->value in ui, zone, names_*, qtext)
    gossip-key          see "gossip keys" below

  Warnings
    token-added         the Swedish text has a placeholder the English source lacks
    colour-changed      same number of colour codes, but other colours (for example a named
                        colour written as the equivalent hex code)
    unused-field        item h without d; spell e without d; spell ea without a
    entry-format        an entry line that is not written the way datalua writes it (spacing,
                        trailing whitespace, escapes)
    field-order         fields not in the table's usual order (quest t,d,o,p,c,l; item h,n,d;
                        spell e,ea,n,d,a,c)
    edge-whitespace     leading/trailing whitespace of the Swedish value differs from the key's
    inconsistent        the same English term (ignoring case) has different Swedish translations
                        in different entries or tables; a hint, never an instruction to rewrite.
                        Silenced for a term by an intentional-difference marker (see below)
    marker-no-reason    a wps:skillnad marker without a reason; it does not silence anything
    marker-ignored      a wps:skillnad marker on an entry of a table that is not checked for
                        consistency (quest, item, spell, npc, gossip), so it has no effect

  Placeholders ($N, $B, $s1, ${formula}, $?a123[..][..], $lword:words; and $gm:f;, |c..|r, |H..|h,
  %s, #/#) are compared as multisets. The words inside $l..;/$g..; and the text inside a
  $?cond[..][..] are translatable and are not compared; the condition itself is.

intentional differences
  A term that is deliberately translated differently in different places (for example a creature
  name that stays English in a quest but is a spell name elsewhere) is marked with a trailing
  comment on one of its entries:

      ["Carnage"]="Carnage", -- wps:skillnad creature name, kept English; the spell is "Blodbad"

  The marker is "wps:skillnad" followed by a reason, which is required. It silences the
  "inconsistent" warning for that English term (case-insensitive) wherever its entries are, so it
  is enough to put it on one of them. It is a note for the next maintainer, so say why. Markers are
  ordinary comments: tools/datalua.py keeps them when it rewrites a file, and
  "search skillnad --lang comment" lists them all.

gossip keys
  Data/Gossip.lua is keyed by "<byte length>_<djb2 as 8 hex digits>" of the English text after
  normalisation: \\r\\n becomes \\n, and the player's name becomes $N. gossip_key() below is a port of
  Key() and Lookup() in GossipText.lua (WPS.Hash in Core.lua is the same djb2); tests compare it
  with the real Lua code. The English text itself is not stored, so check can only verify the shape
  of a key, not that it belongs to a given text. Use the gossip-key command to compute a key and
  compare it with an existing entry. --player NAME applies the $N substitution for that name.

search
  Looks in keys, values, the English source fields of spells (e, ea), quest tracker lines, trailing
  comments and comment lines (terminology notes) of every Data file. Case-insensitive substring by
  default. Options: --exact, --case-sensitive, --lang en|sv|comment|any, --table NAME, --max N.
  Each hit is printed as file:line table[key].field and the matching text. A hit on a key also
  shows the Swedish value after "  ->  ", so the translation can be read without opening the file.
  Exit status: 0 if something was found, 1 if nothing was, 2 on a usage error.
"""
import argparse
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import datalua  # noqa: E402

ID_TABLES = {"quest", "item", "spell", "npc"}
STRUCTURED = {
    "quest": ("t", "d", "o", "p", "c", "l"),
    "item": ("h", "n", "d"),
    "spell": ("e", "ea", "n", "d", "a", "c"),
}
GOSSIP_KEY_RE = re.compile(r"^[0-9]+_[0-9a-f]{8}$")
MAX_U32 = 2 ** 32 - 1
LITERAL_ESCAPE_RE = re.compile(r"\\[rn]")
CONTROL_RE = re.compile(r"[\x00-\x09\x0b-\x1f\x7f]")


# --------------------------------------------------------------------------
# Hash and gossip key: a port of Core.lua WPS.Hash and GossipText.lua Key()/Lookup()
# --------------------------------------------------------------------------

def wps_hash(text):
    """djb2 over the UTF-8 bytes, modulo 2^32 (WPS.Hash in Core.lua, Key in GossipText.lua)."""
    h = 5381
    for b in text.encode("utf-8"):
        h = (h * 33 + b) % 4294967296
    return h


def gossip_key(text, player_name=None):
    """The Data/Gossip.lua key for the English text as the game shows it.

    Same steps as Lookup() in GossipText.lua: "\\r\\n" -> "\\n" first, then the player's name
    -> "$N" (every occurrence, literally), then Key(): ("%d_%08x"):format(#s, hash) where #s is
    the byte length. A lone "\\r" is not touched, exactly as in Lua."""
    norm = text.replace("\r\n", "\n")
    if player_name:
        norm = norm.replace(player_name, "$N")
    data = norm.encode("utf-8")
    return "%d_%08x" % (len(data), wps_hash(norm))


# --------------------------------------------------------------------------
# Placeholders
# --------------------------------------------------------------------------

TOKEN_RE = re.compile(r"""
    \$\{[^}\n]*\}                    # ${formula}
  | \$\?[^\[\s\]]*                   # $?a12792 $?s17245 $?$pN: the condition; the [..] text is free
  | \$<[^>\n]*>                      # $<variable>
  | \$@[A-Za-z]+[0-9]*               # $@spelldesc123
  | \$[lLgG][^:;\n]*:[^;\n]*;         # $lpoint:points;  $lcinnamon roll:cinnamon rolls;  $ghis:her;
  | \$[lL];                          # $l;
  | \$/[0-9]+;[A-Za-z]*[0-9]*        # $/10;s2
  | \$[BbNnCcRr]                     # quest codes win over the generic form: $B$BText is $B $B
  | \$[0-9]*[A-Za-z]+[0-9]*          # $s1 $d $t1 $1oa
  | \|H[^|\s]*\|h                    # link start
  | \|c[0-9A-Fa-f]{8}                # colour start
  | \|cn[A-Z_]+:?                    # named colour
  | \|r | \|h
  | \|T[^|]*\|t | \|A[^|]*\|a        # textures, atlases
  | \#\d*/\d*                        # #/# objective counters
  | %[0-9]*\$?[sdfi]                 # printf
""", re.VERBOSE)


def normalise_token(tok):
    if tok[:2] in ("$l", "$L") and ":" in tok:
        return "$l;"
    if tok[:2] in ("$g", "$G") and ":" in tok:
        return "$g;"
    if tok in ("$b", "$B"):
        return "$B"
    if tok in ("$n", "$N"):
        return "$N"
    if tok.startswith("|c"):
        return "|c"             # any colour start; the exact colours are compared by colours()
    return tok


def tokens(text):
    return Counter(normalise_token(t) for t in TOKEN_RE.findall(text))


def colours(text):
    """The exact colour starts, case-folded: |cffd200.. and named |cnNAME: ones."""
    return Counter(t.lower() if len(t) == 10 else t for t in TOKEN_RE.findall(text) if t.startswith("|c"))


def token_diff(source, translation):
    """(lost, added): placeholders only in the source / only in the translation. Colour starts
    count as one kind here; use colour_change() for which colours they are."""
    want, got = tokens(source), tokens(translation)
    return want - got, got - want


def colour_change(source, translation):
    """(old, new) colours if the number of colour starts is equal but the colours differ."""
    a, b = colours(source), colours(translation)
    if sum(a.values()) == sum(b.values()) and a != b:
        return a - b, b - a
    return None


def fmt_tokens(counter):
    return ", ".join(f"{t} x{n}" if n > 1 else t for t, n in sorted(counter.items()))


# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------

ERROR, WARNING = "ERROR", "WARN"


class Finding:
    __slots__ = ("severity", "code", "file", "line", "where", "message")

    def __init__(self, severity, code, file, line, where, message):
        self.severity, self.code, self.file, self.line = severity, code, file, line
        self.where, self.message = where, message

    def text(self):
        loc = f"{self.file}:{self.line}" if self.line else self.file
        return f"{self.severity:5} [{self.code}] {loc} {self.where}: {self.message}"


def where(table, key, field=None):
    k = repr(key) if isinstance(key, str) else str(key)
    return f"{table}[{k}]" + (f".{field}" if field else "")


def short(text, width=70):
    text = text.replace("\n", "\\n")
    return text if len(text) <= width else text[:width - 3] + "..."


# --------------------------------------------------------------------------
# The checks
# --------------------------------------------------------------------------

def check_key(table, key):
    """Problem with a key, or None."""
    name = table.name
    if name in ID_TABLES:
        if not isinstance(key, int) or key < 1:
            return "ids must be positive integers"
    elif name == "gossip":
        if not isinstance(key, str) or not GOSSIP_KEY_RE.match(key):
            return "gossip keys look like <length>_<8 hex digits>"
        length = int(key.split("_", 1)[0])
        if length < 1:
            return "gossip key with length 0"
    else:
        if not isinstance(key, str) or not key.strip():
            return "name tables need a non-empty string key"
    return None


def string_values(value):
    """(field, text) for every string inside an entry value; l items as l[1], l[2], ..."""
    if isinstance(value, str):
        yield None, value
    elif isinstance(value, dict):
        for field, v in value.items():
            if isinstance(v, str):
                yield field, v
            elif isinstance(v, list):
                for i, item in enumerate(v, 1):
                    if isinstance(item, str):
                        yield f"{field}[{i}]", item


def check_structure(path, table, node, out):
    """Value shape, required fields and text hygiene of one entry."""
    entry, key = node.entry, node.entry.key
    value, name, line = entry.value, table.name, node.lineno

    def add(sev, code, msg, field=None):
        out.append(Finding(sev, code, path, line, where(name, key, field), msg))

    problem = check_key(table, key)
    if problem:
        add(ERROR, "bad-key", problem)

    if name in STRUCTURED:
        allowed = STRUCTURED[name]
        if not isinstance(value, dict):
            add(ERROR, "bad-value", f"{name} entries must be {{field=...}} tables")
            return
        if not value:
            add(ERROR, "bad-value", "empty entry")
            return
        for field, v in value.items():
            if field not in allowed:
                add(ERROR, "bad-value", f"unknown field {field!r} (known: {', '.join(allowed)})", field)
            elif field == "h":
                if not isinstance(v, int) or not 0 <= v <= MAX_U32:
                    add(ERROR, "bad-value", "h must be an integer between 0 and 4294967295", field)
            elif field == "l":
                if not isinstance(v, list) or not v:
                    add(ERROR, "bad-value", "l must be a non-empty list of strings", field)
                elif any(not isinstance(x, str) or not x.strip() for x in v):
                    add(ERROR, "bad-value", "l contains an empty or non-string line", field)
            elif not isinstance(v, str):
                add(ERROR, "bad-value", f"{field} must be a string", field)
            elif not v.strip():
                add(ERROR, "bad-value", f"{field} is empty; leave the field out instead", field)
        if name == "quest" and not any(isinstance(value.get(f), str) and value[f].strip() for f in "tdopc"):
            add(ERROR, "missing-field", "a quest needs at least one of t, d, o, p, c")
        if name == "item":
            if "n" not in value:
                add(ERROR, "missing-field", "an item needs a name (n)")
            if "d" in value and "h" not in value:
                add(ERROR, "missing-field", "d without h: the description is only applied when h matches the English line")
            if "h" in value and "d" not in value:
                add(WARNING, "unused-field", "h without d is never used")
        if name == "spell":
            if "a" in value and "ea" not in value:
                add(ERROR, "missing-field", "a without ea: aura descriptions need both")
            if not any(f in value for f in ("n", "d", "a", "c")):
                add(ERROR, "missing-field", "a spell needs at least one of n, d, a, c")
            if "e" in value and "d" not in value:
                add(WARNING, "unused-field", "e without d is never used")
            if "ea" in value and "a" not in value:
                add(WARNING, "unused-field", "ea without a is never used")
        order = [f for f in allowed if f in value]
        if [f for f in value if f in allowed] != order:
            add(WARNING, "field-order", f"fields are {','.join(value)}; the usual order is {','.join(order)}")
    elif not isinstance(value, str):
        add(ERROR, "bad-value", "this table holds plain strings")
        return
    elif not value.strip():
        add(ERROR, "bad-value", "empty Swedish text")

    for field, text in string_values(value):
        if LITERAL_ESCAPE_RE.search(text):
            add(ERROR, "literal-escape", f"contains a literal backslash-r or backslash-n: {short(text, 50)!r}", field)
        if CONTROL_RE.search(text):
            add(ERROR, "control-char", f"contains a control character: {short(text, 50)!r}", field)

    # entry written the way datalua writes it?
    try:
        canonical = entry.format()
    except datalua.DataError:
        canonical = None
    if canonical is not None and node.text != canonical:
        col = next((i for i, (a, b) in enumerate(zip(node.text, canonical)) if a != b),
                   min(len(node.text), len(canonical)))
        add(WARNING, "entry-format", f"not written in the canonical form (first difference at column {col + 1}): "
                                     f"spacing, trailing whitespace or escapes")


def check_pair(path, table, node, source, translation, field, out):
    lost, added = token_diff(source, translation)
    key, line = node.entry.key, node.lineno
    if lost:
        out.append(Finding(ERROR, "token-lost", path, line, where(table.name, key, field),
                           f"placeholder missing in the Swedish text: {fmt_tokens(lost)}  [{short(source, 50)!r}]"))
    if added:
        out.append(Finding(WARNING, "token-added", path, line, where(table.name, key, field),
                           f"placeholder only in the Swedish text: {fmt_tokens(added)}  [{short(source, 50)!r}]"))
    changed = None if (lost or added) else colour_change(source, translation)
    if changed:
        out.append(Finding(WARNING, "colour-changed", path, line, where(table.name, key, field),
                           f"colour codes differ: {fmt_tokens(changed[0])} -> {fmt_tokens(changed[1])}"))


def check_table(path, table, out):
    for key, lines in table.duplicates:
        out.append(Finding(ERROR, "duplicate-key", path, lines[0], where(table.name, key),
                           f"defined {len(lines)} times (lines {', '.join(map(str, lines))}); Lua keeps the last"))
    for node in table.nodes:
        check_structure(path, table, node, out)
        key, value = node.entry.key, node.entry.value
        if table.name == "spell" and isinstance(value, dict):
            for src, dst in (("e", "d"), ("ea", "a")):
                if isinstance(value.get(src), str) and isinstance(value.get(dst), str):
                    check_pair(path, table, node, value[src], value[dst], f"{src}>{dst}", out)
        elif table.name not in ID_TABLES and table.name != "gossip" and isinstance(key, str) and isinstance(value, str):
            check_pair(path, table, node, key, value, None, out)
            if key.strip() and value.strip():
                if (key[:1].isspace(), key[-1:].isspace()) != (value[:1].isspace(), value[-1:].isspace()):
                    out.append(Finding(WARNING, "edge-whitespace", path, node.lineno, where(table.name, key),
                                       f"leading/trailing whitespace differs: {key!r} -> {value!r}"))


MARKER = "wps:skillnad"


def marker_reason(comment):
    """None if the trailing comment is not an intentional-difference marker, otherwise its reason
    ("" when the reason is missing). "wps:skillnadX" is not a marker."""
    m = re.match(re.escape(MARKER) + r"(?=\s|$)(.*)$", comment or "")
    return m.group(1).strip() if m else None


def check_consistency(parsed, out):
    """Same English term (ignoring case) with different Swedish across entries and tables.
    A wps:skillnad marker with a reason on any entry of the term silences the warning."""
    seen = defaultdict(dict)    # english -> {swedish: (file, line, table, key)}
    marked = set()              # casefolded English terms with an intentional-difference marker
    for path, df in parsed:
        for table in df.tables.values():
            checked = table.name not in ID_TABLES and table.name != "gossip"
            for node in table.nodes:
                key, value = node.entry.key, node.entry.value
                reason = marker_reason(node.entry.comment)
                if reason is not None:
                    if not checked:
                        out.append(Finding(WARNING, "marker-ignored", path, node.lineno, where(table.name, key),
                                           f"{MARKER} has no effect in the {table.name} table"))
                    elif not reason:
                        out.append(Finding(WARNING, "marker-no-reason", path, node.lineno, where(table.name, key),
                                           f"{MARKER} needs a reason after it, e.g. '-- {MARKER} creature name, kept English'"))
                    elif isinstance(key, str) and key.strip():
                        marked.add(key.strip().casefold())
                if not checked:
                    continue
                if not (isinstance(key, str) and isinstance(value, str)) or not key.strip() or not value.strip():
                    continue
                seen[key.strip().casefold()].setdefault(value.strip().casefold(), []).append(
                    (path, node.lineno, table.name, key, value))
    for english, variants in sorted(seen.items()):
        if len(variants) < 2 or english in marked:
            continue
        first = [v[0] for v in variants.values()]
        parts = "; ".join(f"{where(t, k)} -> {sv!r}" for _p, _l, t, k, sv in first[:4])
        more = f" (+{len(first) - 4} more)" if len(first) > 4 else ""
        path, line = first[0][0], first[0][1]
        out.append(Finding(WARNING, "inconsistent", path, line, repr(english),
                           f"{len(variants)} different translations: {parts}{more}"))


def load_files(data_dir, out):
    """Parse every Data/*.lua; a file that cannot be read is an error and is skipped."""
    parsed = []
    names = sorted(n for n in os.listdir(data_dir) if n.endswith(".lua"))
    if not names:
        raise SystemExit(f"no .lua files in {data_dir}")
    for name in names:
        path = os.path.join(data_dir, name)
        try:
            parsed.append((path, datalua.DataFile.read(path)))
        except datalua.DataError as exc:
            out.append(Finding(ERROR, "parse-error", path, exc.line, "", exc.message))
    return parsed


def run_checks(data_dir):
    findings = []
    parsed = load_files(data_dir, findings)
    for path, df in parsed:
        for table in df.tables.values():
            check_table(path, table, findings)
    check_consistency(parsed, findings)
    counts = (len(parsed), sum(len(df.tables) for _p, df in parsed),
              sum(len(t) for _p, df in parsed for t in df.tables.values()))
    return findings, counts


def cmd_check(args):
    findings, (files, tables, entries) = run_checks(args.data_dir)
    errors = [f for f in findings if f.severity == ERROR]
    warnings = [f for f in findings if f.severity == WARNING]
    print(f"checked {files} files, {tables} tables, {entries} entries in {args.data_dir}")
    for f in errors:
        print(f.text())
    by_code = defaultdict(list)
    for f in warnings:
        by_code[f.code].append(f)
    for code in sorted(by_code):
        items = by_code[code]
        shown = items if args.all_warnings else items[:args.examples]
        print(f"\n{len(items)} warning(s) [{code}]" + ("" if len(shown) == len(items) else f", first {len(shown)}:"))
        for f in shown:
            print("  " + f.text())
    print()
    print(f"errors:   {len(errors)}" + "".join(f"  {c}={n}" for c, n in sorted(Counter(f.code for f in errors).items())))
    print(f"warnings: {len(warnings)}" + "".join(f"  {c}={len(v)}" for c, v in sorted(by_code.items())))
    print("RESULT: " + ("ERRORS - do not merge" if errors else "OK (no errors)"))
    return 1 if errors else 0


# --------------------------------------------------------------------------
# search
# --------------------------------------------------------------------------

ENGLISH_FIELDS = {"e", "ea"}


def searchable(path, df):
    """(lang, line, table, key, field, text) for everything a person might look for."""
    for node in df.nodes:
        if node.kind == "comment":
            yield "comment", node.lineno, None, None, None, node.text.strip().lstrip("-").strip()
            continue
        if node.kind != "entry":
            continue
        entry, table = node.entry, node.table
        if isinstance(entry.key, str):
            yield "en" if table != "gossip" else "key", node.lineno, table, entry.key, "key", entry.key
        for field, text in string_values(entry.value):
            base = (field or "").split("[", 1)[0]
            lang = "en" if base in ENGLISH_FIELDS else "sv"
            yield lang, node.lineno, table, entry.key, field, text
        if entry.comment:
            yield "comment", node.lineno, table, entry.key, "comment", entry.comment


def cmd_search(args):
    if not args.text:
        print("search: give some text to look for", file=sys.stderr)
        return 2
    needle = args.text if args.case_sensitive else args.text.casefold()
    hits = total = 0
    for name in sorted(n for n in os.listdir(args.data_dir) if n.endswith(".lua")):
        path = os.path.join(args.data_dir, name)
        try:
            df = datalua.DataFile.read(path)
        except datalua.DataError as exc:
            print(f"ERROR cannot read {exc}", file=sys.stderr)
            return 2
        for lang, line, table, key, field, text in searchable(path, df):
            if args.table and table != args.table:
                continue
            if args.lang != "any" and lang != args.lang:
                continue
            hay = text if args.case_sensitive else text.casefold()
            if (hay == needle) if args.exact else (needle in hay):
                total += 1
                if hits < args.max:
                    hits += 1
                    ref = f"{path}:{line}"
                    what = where(table, key, field if field not in (None, "key") else None) if table else "comment"
                    shown = short(text, 100)
                    if field == "key":
                        what = where(table, key) + " (key)"
                        value = df.table(table).get(key)             # show what the key is translated to
                        if isinstance(value, str):
                            shown += "  ->  " + short(value, 100)
                    print(f"{ref}  {what}  [{lang}]  {shown}")
    print(f"{total} match(es)" + (f", showing the first {hits}" if total > hits else ""))
    return 0 if total else 1


def cmd_gossip_key(args):
    print(gossip_key(args.text, args.player))
    return 0


# --------------------------------------------------------------------------

def build_parser():
    ap = argparse.ArgumentParser(description="Search and validate Data/*.lua (read-only). "
                                             "Without a command, 'check' is run.")
    ap.add_argument("--data-dir", default=os.path.join(ROOT, "Data"), help="directory with the Data files")
    sub = ap.add_subparsers(dest="command")
    p = sub.add_parser("check", help="validate everything; exit 1 on errors")
    p.add_argument("--examples", type=int, default=3, help="warnings shown per kind (default 3)")
    p.add_argument("--all-warnings", action="store_true", help="show every warning")
    p = sub.add_parser("search", help="find text in keys, values, English source fields and comments")
    p.add_argument("text")
    p.add_argument("--exact", action="store_true", help="the whole text must equal TEXT")
    p.add_argument("--case-sensitive", action="store_true")
    p.add_argument("--lang", choices=("any", "en", "sv", "comment", "key"), default="any")
    p.add_argument("--table", help="only this table, e.g. quest, ui, names_item")
    p.add_argument("--max", type=int, default=50, help="results shown (default 50)")
    p = sub.add_parser("gossip-key", help="print the Data/Gossip.lua key of an English text")
    p.add_argument("text")
    p.add_argument("--player", metavar="NAME", help="replace this player name with $N first")
    return ap


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    commands = ("check", "search", "gossip-key")
    if not any(a in commands for a in argv):
        argv.append("check")                     # check is the default command
    args = build_parser().parse_args(argv)
    if args.command == "check":
        return cmd_check(args)
    if args.command == "search":
        return cmd_search(args)
    return cmd_gossip_key(args)


if __name__ == "__main__":
    sys.exit(main())
