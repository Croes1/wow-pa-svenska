#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/datalua.py - read and edit the addon's Data/*.lua files without damaging them.

The Data files are the addon's source data and are edited directly. This module
is deliberately narrow: it understands the formats that actually occur in
Data/*.lua, not Lua in general. Anything else raises DataError and nothing is
written. Unmodified lines are kept byte for byte, so reading and writing a file
unchanged gives a zero diff, and a tool run changes only the lines it touches.

Supported file shape (one entry per physical line, UTF-8, LF line endings):

    -- comment lines and blank lines anywhere
    local _, WPS = ...
    local ui = WPS.L.ui                 -- optional alias for assignment style
    WPS.L.quest = {                     -- one block per table
    [123]={t="Title",d="Text",l={"a","b"}},          -- numeric key, structured value
    [25]={h=3305331836,n="Name",d="Text"},           -- number field (Item.h)
    [3]="Name",                                      -- numeric key, string value
    ["Some English"]="Svensk text", -- trailing comment  -- string key
    }
    ui["Some English"] = "Svensk text"  -- assignment style

Values are Python str (Lua string), int (non-negative integer), list of str
(l={...}) or dict of field -> str | int | list. Numeric and string keys stay
different (123 is not "123"), exactly as in Lua.

Only double-quoted strings with the escapes \\\\ \\" \\' \\n \\r \\t \\a \\b \\f \\v and
\\ddd (below 128) are read. Multi-line strings, long brackets, single quotes, floats,
negative numbers, nested tables below l={...}, entries sharing a line and block
comments are rejected with the line number.

Command line (read-only unless --rewrite):

  python3 tools/datalua.py Data/*.lua            parse, verify exact round trip, summarise
  python3 tools/datalua.py --rewrite Data/*.lua  also rewrite each file atomically
                                                 (an unchanged file must give no git diff)
"""
import bisect
import os
import re
import shutil
import sys
import tempfile

SIMPLE_ESCAPES = {"\\": "\\", '"': '"', "'": "'", "n": "\n", "r": "\r", "t": "\t",
                  "a": "\a", "b": "\b", "f": "\f", "v": "\v"}
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
INT_RE = re.compile(r"[0-9]+")
OPEN_RE = re.compile(r"^WPS\.L\.([A-Za-z_][A-Za-z0-9_]*) = \{$")
ALIAS_RE = re.compile(r"^local ([A-Za-z_][A-Za-z0-9_]*) = WPS\.L\.([A-Za-z_][A-Za-z0-9_]*)$")
HEADER_LINE = "local _, WPS = ..."


class DataError(Exception):
    """Unknown or damaged syntax. Carries the file and line when known."""

    def __init__(self, message, path=None, line=None):
        self.message, self.path, self.line = message, path, line
        where = ""
        if path:
            where = f"{path}:{line}: " if line else f"{path}: "
        elif line:
            where = f"line {line}: "
        super().__init__(where + message)


class _LineError(ValueError):
    """Raised inside one line; the caller adds file and line number."""


# --------------------------------------------------------------------------
# Lua strings
# --------------------------------------------------------------------------

def lua_string(s):
    """Quote s as a Lua string literal. Only \\ " and control characters are escaped;
    UTF-8 text is written as is. \\r is written as \\r (data should not contain it)."""
    out = ['"']
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif ord(ch) < 32 or ord(ch) == 127:
            out.append("\\%03d" % ord(ch))
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def key_text(key):
    """Source text of a key: [123] or ["text"]."""
    if isinstance(key, bool) or not isinstance(key, (int, str)):
        raise DataError(f"unsupported key type {type(key).__name__}")
    if isinstance(key, int):
        if key < 0:
            raise DataError(f"negative key {key} is not supported")
        return f"[{key}]"
    return f"[{lua_string(key)}]"


def value_text(value):
    """Source text of a value, compact (no spaces), fields in the dict's own order."""
    if isinstance(value, bool):
        raise DataError("booleans are not supported")
    if isinstance(value, str):
        return lua_string(value)
    if isinstance(value, int):
        if value < 0:
            raise DataError(f"negative number {value} is not supported")
        return str(value)
    if isinstance(value, list):
        if not all(isinstance(v, str) for v in value):
            raise DataError("a list may only contain strings")
        return "{" + ",".join(lua_string(v) for v in value) + "}"
    if isinstance(value, dict):
        parts = []
        for field, v in value.items():
            if not isinstance(field, str) or not IDENT_RE.fullmatch(field):
                raise DataError(f"invalid field name {field!r}")
            if isinstance(v, dict):
                raise DataError(f"field {field!r}: nested tables below a list are not supported")
            parts.append(f"{field}={value_text(v)}")
        return "{" + ",".join(parts) + "}"
    raise DataError(f"unsupported value type {type(value).__name__}")


# --------------------------------------------------------------------------
# One-line parser
# --------------------------------------------------------------------------

class _Cursor:
    def __init__(self, text):
        self.s, self.i = text, 0

    def fail(self, msg):
        raise _LineError(f"{msg} (column {self.i + 1})")

    def ws(self):
        while self.i < len(self.s) and self.s[self.i] in " \t":
            self.i += 1

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else ""

    def eat(self, ch):
        if self.peek() != ch:
            self.fail(f"expected {ch!r}, found {self.peek()!r}" if self.peek() else f"expected {ch!r}, found end of line")
        self.i += 1

    def string(self):
        s = self.s
        if self.peek() != '"':
            self.fail("expected a double-quoted string")
        self.i += 1
        out = []
        while True:
            if self.i >= len(s):
                self.fail("unterminated string (multi-line strings are not supported)")
            ch = s[self.i]
            if ch == '"':
                self.i += 1
                return "".join(out)
            if ch != "\\":
                out.append(ch)
                self.i += 1
                continue
            self.i += 1
            if self.i >= len(s):
                self.fail("backslash at end of line (line continuation is not supported)")
            esc = s[self.i]
            if esc in SIMPLE_ESCAPES:
                out.append(SIMPLE_ESCAPES[esc])
                self.i += 1
            elif esc.isdigit():
                m = re.compile(r"[0-9]{1,3}").match(s, self.i)
                n = int(m.group())
                if n >= 128:
                    self.fail(f"decimal escape \\{m.group()} is not ASCII")
                out.append(chr(n))
                self.i = m.end()
            else:
                self.fail(f"unsupported escape \\{esc}")

    def integer(self):
        m = INT_RE.match(self.s, self.i)
        if not m:
            self.fail("expected a non-negative integer")
        end = m.end()
        if end < len(self.s) and (self.s[end].isalnum() or self.s[end] in "._"):
            self.fail("unsupported number syntax")
        self.i = end
        return int(m.group())

    def ident(self):
        m = IDENT_RE.match(self.s, self.i)
        if not m:
            self.fail("expected a field name")
        self.i = m.end()
        return m.group()

    def key(self):
        self.eat("[")
        self.ws()
        key = self.string() if self.peek() == '"' else self.integer()
        self.ws()
        self.eat("]")
        return key

    def list_value(self):
        self.eat("{")
        items = []
        self.ws()
        while self.peek() != "}":
            items.append(self.string())
            self.ws()
            if self.peek() == ",":
                self.i += 1
                self.ws()
            elif self.peek() != "}":
                self.fail("expected ',' or '}' in list")
        self.eat("}")
        return items

    def field_value(self):
        c = self.peek()
        if c == '"':
            return self.string()
        if c == "{":
            self.ws()
            return self.list_value()
        return self.integer()

    def value(self):
        """A string, or a {field=...} table (not a bare list: l={...} only occurs as a field)."""
        c = self.peek()
        if c == '"':
            return self.string()
        if c != "{":
            self.fail("expected a string or a {field=value} table")
        self.i += 1
        fields = {}
        self.ws()
        while self.peek() != "}":
            name = self.ident()
            if name in fields:
                self.fail(f"duplicate field {name!r}")
            self.ws()
            self.eat("=")
            self.ws()
            fields[name] = self.field_value()
            self.ws()
            if self.peek() == ",":
                self.i += 1
                self.ws()
            elif self.peek() != "}":
                self.fail("expected ',' or '}' after field")
        self.eat("}")
        return fields

    def trailing_comment(self):
        """After the entry: only whitespace or a '-- comment' may follow."""
        self.ws()
        rest = self.s[self.i:]
        if not rest:
            return None
        if rest.startswith("--") and not rest.startswith("--["):
            self.i = len(self.s)
            return rest[2:].strip()
        self.fail(f"unexpected text after the entry: {rest[:30]!r}")


def parse_block_entry(text):
    """'[key]=value,' with optional trailing comment -> (key, value, comment)."""
    c = _Cursor(text)
    c.ws()
    key = c.key()
    c.ws()
    c.eat("=")
    c.ws()
    value = c.value()
    c.ws()
    c.eat(",")
    return key, value, c.trailing_comment()


def parse_assign_entry(text, alias):
    """'alias[key] = value' with optional trailing comment -> (key, value, comment)."""
    c = _Cursor(text)
    c.ws()
    if c.ident() != alias:
        raise _LineError(f"expected assignment to {alias}[...]")
    c.ws()
    key = c.key()
    c.ws()
    c.eat("=")
    c.ws()
    value = c.value()
    return key, value, c.trailing_comment()


# --------------------------------------------------------------------------
# File model
# --------------------------------------------------------------------------

class Entry:
    __slots__ = ("key", "value", "comment", "style", "alias")

    def __init__(self, key, value, comment=None, style="block", alias=None):
        self.key, self.value, self.comment = key, value, comment
        self.style, self.alias = style, alias

    def format(self):
        """Canonical source text of this entry (compact; comment kept)."""
        if self.style == "assign":
            text = f"{self.alias}{key_text(self.key)} = {value_text(self.value)}"
        else:
            text = f"{key_text(self.key)}={value_text(self.value)},"
        return text + (f" -- {self.comment}" if self.comment else "")


class Node:
    """One physical line. kind: blank, comment, header, alias, open, close, entry."""
    __slots__ = ("kind", "text", "table", "entry", "lineno")

    def __init__(self, kind, text, table=None, entry=None, lineno=0):
        self.kind, self.text, self.table, self.entry, self.lineno = kind, text, table, entry, lineno


class Table:
    """One WPS.L.<name> table. Entries are in file order; the last one wins for a repeated key,
    as in Lua, and every repeat is listed in .duplicates."""

    def __init__(self, name, style, alias=None):
        self.name, self.style, self.alias = name, style, alias
        self.nodes = []        # entry nodes in file order
        self.index = {}        # key -> node (last wins)
        self.duplicates = []   # (key, [line numbers])
        self.anchor = None     # node after which a first entry goes (open or alias line)

    def reindex(self):
        self.index, seen = {}, {}
        self.duplicates = []
        for n in self.nodes:
            seen.setdefault(n.entry.key, []).append(n.lineno)
            self.index[n.entry.key] = n
        self.duplicates = [(k, v) for k, v in seen.items() if len(v) > 1]

    def keys(self):
        return [n.entry.key for n in self.nodes]

    def __contains__(self, key):
        return key in self.index

    def __len__(self):
        return len(self.nodes)

    def get(self, key, default=None):
        n = self.index.get(key)
        return n.entry.value if n else default

    def items(self):
        return [(n.entry.key, n.entry.value) for n in self.nodes]

    def is_sorted(self):
        """True if keys are all one type and strictly increasing (ints numerically,
        strings by code point = UTF-8 byte order)."""
        keys = self.keys()
        if len({type(k) for k in keys}) > 1:
            return False
        return all(a < b for a, b in zip(keys, keys[1:]))


class DataFile:
    def __init__(self, nodes, final_newline, path=None):
        self.nodes, self.final_newline, self.path = nodes, final_newline, path
        self.tables = {}
        self._build_tables()

    # ---- reading ----

    @classmethod
    def parse(cls, text, path=None):
        if "\r" in text:
            raise DataError("contains CR characters (CRLF line endings?); the Data files use LF", path)
        if text.startswith("﻿"):
            raise DataError("starts with a byte order mark", path)
        raw_lines = text.split("\n")
        final_newline = raw_lines[-1] == ""
        if final_newline:
            raw_lines.pop()
        nodes = []
        aliases = {}       # alias -> table name
        blocks = set()     # table names that have a WPS.L.x = { block
        current = None
        for lineno, line in enumerate(raw_lines, 1):
            try:
                node = cls._classify(line, lineno, current, aliases, blocks)
            except _LineError as exc:
                raise DataError(str(exc), path, lineno) from None
            if node.kind == "open":
                current = node.table
            elif node.kind == "close":
                current = None
            elif node.kind == "alias":
                aliases[ALIAS_RE.match(node.text).group(1)] = node.table
            nodes.append(node)
        if current is not None:
            raise DataError(f"table {current!r} is not closed before the end of the file", path, len(raw_lines))
        return cls(nodes, final_newline, path)

    @staticmethod
    def _classify(line, lineno, current, aliases, blocks):
        stripped = line.strip()
        if not stripped:
            return Node("blank", line, lineno=lineno)
        if stripped.startswith("--"):
            if stripped.startswith("--["):
                raise _LineError("block comments are not supported")
            return Node("comment", line, lineno=lineno)
        if current is not None:
            if line == "}":
                return Node("close", line, table=current, lineno=lineno)
            key, value, comment = parse_block_entry(line)
            return Node("entry", line, table=current, lineno=lineno,
                        entry=Entry(key, value, comment))
        if line == HEADER_LINE:
            return Node("header", line, lineno=lineno)
        m = ALIAS_RE.match(line)
        if m:
            return Node("alias", line, table=m.group(2), lineno=lineno)
        m = OPEN_RE.match(line)
        if m:
            if m.group(1) in blocks:
                raise _LineError(f"table {m.group(1)!r} is defined twice")
            blocks.add(m.group(1))
            return Node("open", line, table=m.group(1), lineno=lineno)
        m = IDENT_RE.match(line)
        if m and m.group() in aliases:
            alias = m.group()
            key, value, comment = parse_assign_entry(line, alias)
            return Node("entry", line, table=aliases[alias], lineno=lineno,
                        entry=Entry(key, value, comment, "assign", alias))
        raise _LineError(f"unknown syntax: {line[:60]!r}")

    def _build_tables(self):
        self.tables = {}
        for node in self.nodes:
            if node.kind == "open":
                old = self.tables.get(node.table)
                if old is not None and old.style == "assign" and not old.nodes:
                    del self.tables[node.table]   # alias line came first; no assignments yet
                if node.table in self.tables:
                    raise DataError(f"table {node.table!r} is defined as a block and by assignments", self.path, node.lineno)
                t = Table(node.table, "block")
                t.anchor = node
                self.tables[node.table] = t
            elif node.kind == "alias":
                t = self.tables.get(node.table)
                if t is None:
                    t = Table(node.table, "assign", alias=ALIAS_RE.match(node.text).group(1))
                    self.tables[node.table] = t
                    t.anchor = node
            elif node.kind == "entry":
                t = self.tables[node.table]
                if node.entry.style != t.style:
                    raise DataError(f"table {t.name!r} mixes block entries and assignments", self.path, node.lineno)
                t.nodes.append(node)
        for t in self.tables.values():
            t.reindex()

    @classmethod
    def read(cls, path):
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
        except OSError as exc:
            raise DataError(f"cannot read: {exc.strerror}", str(path)) from None
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DataError(f"not valid UTF-8 (byte offset {exc.start})", str(path)) from None
        df = cls.parse(text, str(path))
        return df

    # ---- access ----

    def table(self, name):
        t = self.tables.get(name)
        if t is None:
            raise DataError(f"no table WPS.L.{name} in this file", self.path)
        return t

    def text(self):
        out = "\n".join(n.text for n in self.nodes)
        return out + ("\n" if self.final_newline and self.nodes else "")

    # ---- editing ----

    def insert(self, table_name, items, comment=None):
        """Add new keys. items: iterable of (key, value). Existing keys are an error (callers check
        `key in table` first and decide what a collision means).

        Placement is deterministic. In a table whose keys are strictly increasing, each new key goes
        before the first larger existing key (after the last entry if none is larger). In any other
        table (for example Ui, with its thematic sections) new keys are appended after the last
        entry, in key order. Comments and blank lines around existing entries are never moved.
        Returns the number of entries inserted."""
        t = self.table(table_name)
        new = {}
        for key, value in items:
            if key in t.index or key in new:
                raise DataError(f"key {key!r} already exists in {table_name}", self.path)
            new[key] = value
        if not new:
            return 0
        existing_types = {type(k) for k in t.keys()}
        new_types = {type(k) for k in new}
        if len(new_types) > 1 or (existing_types and new_types != existing_types):
            raise DataError(f"new keys do not have the same type as the keys in {table_name}", self.path)

        def make(key, value):
            entry = Entry(key, value, comment, t.style, t.alias)
            return Node("entry", entry.format(), table=t.name, entry=entry)

        ordered = sorted(new)
        sorted_table = t.is_sorted()
        position_of = {id(n): i for i, n in enumerate(self.nodes)}
        before = {}  # node index -> nodes to put in front of it
        if t.nodes:
            tail = position_of[id(t.nodes[-1])] + 1
        else:
            tail = position_of[id(t.anchor)] + 1
        keys = t.keys()
        for key in ordered:
            at = tail
            if sorted_table and t.nodes:
                i = bisect.bisect_left(keys, key)
                if i < len(keys):
                    at = position_of[id(t.nodes[i])]
            before.setdefault(at, []).append(make(key, new[key]))
        rebuilt = []
        for i, node in enumerate(self.nodes):
            rebuilt.extend(before.get(i, ()))
            rebuilt.append(node)
        rebuilt.extend(before.get(len(self.nodes), ()))
        self.nodes = rebuilt
        t.nodes = [n for n in rebuilt if n.kind == "entry" and n.table == t.name]
        if not self.final_newline:
            self.final_newline = True
        t.reindex()
        return len(new)

    def replace(self, table_name, key, value):
        """Replace the value of an existing key; the entry's line is rewritten in canonical form
        (a trailing comment is kept). Only for an explicit, reported overwrite."""
        t = self.table(table_name)
        node = t.index.get(key)
        if node is None:
            raise DataError(f"key {key!r} does not exist in {table_name}", self.path)
        if t.duplicates and any(k == key for k, _ in t.duplicates):
            raise DataError(f"key {key!r} occurs more than once in {table_name}; fix that first", self.path)
        node.entry = Entry(key, value, node.entry.comment, node.entry.style, node.entry.alias)
        node.text = node.entry.format()

    # ---- writing ----

    def write(self, path=None, check=None):
        """Write atomically: a temporary file next to the target is written, re-parsed and must
        give the same tables as this object (and pass `check(tmp_path)` if given), then it replaces
        the target. The target is never left half-written."""
        path = path or self.path
        if not path:
            raise DataError("no path to write to")
        text = self.text()
        try:
            again = DataFile.parse(text, str(path))
        except DataError as exc:
            raise DataError(f"refusing to write: the result does not parse ({exc})") from None
        if _summary(again) != _summary(self):
            raise DataError("refusing to write: the result differs from the in-memory tables", str(path))
        directory = os.path.dirname(os.path.abspath(path))
        fd, tmp = tempfile.mkstemp(prefix=".datalua-", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(text.encode("utf-8"))
            if os.path.exists(path):
                shutil.copymode(path, tmp)
            else:
                os.chmod(tmp, 0o644)
            if check:
                check(tmp)
            os.replace(tmp, path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
        self.path = str(path)


def _summary(df):
    return {name: t.items() for name, t in df.tables.items()}


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------

def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(
        description="Parse Data/*.lua files, verify that rewriting is lossless, and summarise them. "
                    "Writes nothing unless --rewrite is given.")
    ap.add_argument("files", nargs="+", help="Data/*.lua files")
    ap.add_argument("--rewrite", action="store_true",
                    help="also rewrite each file atomically (an unchanged file must give no git diff)")
    args = ap.parse_args(argv)
    status = 0
    for path in args.files:
        try:
            df = DataFile.read(path)
            with open(path, "rb") as fh:
                original = fh.read()
            if df.text().encode("utf-8") != original:
                raise DataError("rewriting would change the file (round trip is not lossless)", path)
            if args.rewrite:
                df.write()
        except DataError as exc:
            print(f"ERROR {exc}")
            status = 1
            continue
        parts = ", ".join(f"{t.name}={len(t)}" for t in df.tables.values())
        print(f"ok {path}: {len(df.nodes)} lines, {parts}" + (" (rewritten)" if args.rewrite else ""))
    return status


if __name__ == "__main__":
    sys.exit(main())
