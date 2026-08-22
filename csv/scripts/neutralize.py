#!/usr/bin/env python3
"""Neutralize spreadsheet formula injection in CSV text cells.

Prefixes =, +, @, and non-numeric - with a single quote, including when those
characters are preceded by tab, CR, LF, or space. Leaves real negative
numbers alone.

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
    args = p.parse_args()
    src = Path(args.src)
    dst = Path(args.dst)
    encoding = args.encoding
    raw = src.read_bytes()
    if encoding.lower() in {"utf-8", "utf8"} and raw.startswith(b"\xef\xbb\xbf"):
        encoding = "utf-8-sig"
    text = raw.decode(encoding)
    delimiter = detect_delimiter(text[:8192], args.delimiter)
    rows = [
        [neutralize(cell) for cell in row]
        for row in csv.reader(io.StringIO(text), delimiter=delimiter)
    ]
    with dst.open("w", newline="", encoding=encoding) as f:
        csv.writer(f, delimiter=delimiter).writerows(rows)
    print("wrote", dst, "rows", len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
