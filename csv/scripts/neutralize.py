#!/usr/bin/env python3
"""Neutralize spreadsheet formula injection in CSV text cells.

Prefixes =, +, @, and non-numeric - with a single quote.
Leaves real negative numbers alone.

Usage:
  python csv/scripts/neutralize.py --in dirty.csv --out safe.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

NUMERIC = re.compile(r"^-?\d+(\.\d+)?$")


def neutralize(val: object) -> object:
    if not isinstance(val, str) or not val:
        return val
    if val[0] in "=+@" or (val[0] == "-" and not NUMERIC.match(val)):
        return "'" + val
    return val


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--in", dest="src", required=True)
    p.add_argument("--out", dest="dst", required=True)
    args = p.parse_args()
    src = Path(args.src)
    dst = Path(args.dst)
    with src.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = [[neutralize(cell) for cell in row] for row in reader]
    with dst.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    print("wrote", dst, "rows", len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
