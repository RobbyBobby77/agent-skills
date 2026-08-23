#!/usr/bin/env python3
"""Neutralize spreadsheet formula injection in CSV text cells.

Prefixes =, +, @, and non-numeric - with a single quote, including when those
characters are preceded by tab, CR, LF, or space. Leaves real negative
numbers alone.

Preserves the source file's line terminator. When the delimiter was sniffed
rather than given and the parse comes out ragged, refuses to write instead of
silently reshaping every row.

Usage:
  python scripts/neutralize.py --in dirty.csv --out safe.csv
  python scripts/neutralize.py --in dirty.csv --out safe.csv --encoding latin-1 --delimiter ';'
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from pathlib import Path

NUMERIC = re.compile(r"^-?\d+(\.\d+)?$")
INJECT_PREFIX = "\t\r\n "


def neutralize(val: object) -> object:
    if not isinstance(val, str) or not val:
        return val
    stripped = val.lstrip(INJECT_PREFIX)
    if not stripped:
        return val
    if stripped[0] in "=+@" or (stripped[0] == "-" and not NUMERIC.match(stripped)):
        return "'" + val
    return val


def detect_delimiter(sample: str, delimiter: str | None) -> str:
    if delimiter:
        return delimiter
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def detect_newline(raw: bytes) -> str:
    """The source file's line terminator. CRLF only when it already uses CRLF."""
    idx = raw.find(b"\n")
    if idx == -1:
        return "\r\n"  # single line, no terminator observed: RFC 4180 default
    if idx == 0:
        return "\n"
    return "\r\n" if raw[idx - 1] == 0x0D else "\n"


def ragged_rows(rows: list[list[str]]) -> list[int]:
    """1-indexed rows whose field count differs from the header's. Blank lines ignored."""
    if not rows:
        return []
    width = len(rows[0])
    return [i for i, row in enumerate(rows, 1) if row and len(row) != width]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--in", dest="src", required=True)
    p.add_argument("--out", dest="dst", required=True)
    p.add_argument("--encoding", default="utf-8", help="Text encoding (default utf-8)")
    p.add_argument(
        "--delimiter",
        default=None,
        help="Field delimiter; sniffed from the sample when omitted",
    )
    p.add_argument(
        "--allow-ragged",
        action="store_true",
        help="Write even when rows disagree on field count (the file really is ragged)",
    )
    args = p.parse_args()
    src = Path(args.src)
    dst = Path(args.dst)
    encoding = args.encoding
    raw = src.read_bytes()
    if encoding.lower() in {"utf-8", "utf8"} and raw.startswith(b"\xef\xbb\xbf"):
        encoding = "utf-8-sig"
    text = raw.decode(encoding)
    delimiter = detect_delimiter(text[:8192], args.delimiter)
    newline = detect_newline(raw)
    rows = [
        [neutralize(cell) for cell in row]
        for row in csv.reader(io.StringIO(text), delimiter=delimiter)
    ]

    ragged = ragged_rows(rows)
    if ragged:
        shown = ", ".join(str(n) for n in ragged[:5])
        more = f" (+{len(ragged) - 5} more)" if len(ragged) > 5 else ""
        print(
            f"warning: {len(ragged)} row(s) disagree with the header's "
            f"{len(rows[0])} field(s) under delimiter {delimiter!r}: rows {shown}{more}",
            file=sys.stderr,
        )
        if args.delimiter is None and not args.allow_ragged:
            print(
                "refusing to write: the delimiter was sniffed, not given, so it is "
                "probably wrong and writing would reshape every row. Re-run with "
                "--delimiter, or --allow-ragged if the file really is ragged.",
                file=sys.stderr,
            )
            return 2

    with dst.open("w", newline="", encoding=encoding) as f:
        csv.writer(f, delimiter=delimiter, lineterminator=newline).writerows(rows)
    print("wrote", dst, "rows", len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
