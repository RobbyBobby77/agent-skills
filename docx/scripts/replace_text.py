#!/usr/bin/env python3
"""Replace text in a .docx / .dotx, including headers and footers.

Finds matches across split <w:t> runs (Hel + lo). Puts the replacement in
the first matching run and clears the rest so formatting on that first run
survives.

Usage:
  python scripts/replace_text.py template.docx output.docx --map replacements.json
  python scripts/replace_text.py template.docx output.docx --match '[CLIENT]' --text 'Acme'
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from pathlib import Path

T_RE = re.compile(r"(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)", re.DOTALL)
P_RE = re.compile(r"<w:p[\s>].*?</w:p>", re.DOTALL)
WORD_PART = re.compile(r"^word/.+\.xml$")


def _xml_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _replace_in_paragraph(paragraph: str, old: str, new: str) -> tuple[str, int]:
    if not old:
        return paragraph, 0
    count = 0
    result = paragraph
    search_from = 0
    escaped = _xml_escape(new)
    while True:
        runs = list(T_RE.finditer(result))
        if not runs:
            break
        concat = ""
        spans = []
        for m in runs:
            start = len(concat)
            concat += m.group(2)
            spans.append((start, len(concat), m))
        found = concat.find(old, search_from)
        if found < 0:
            break
        match_end = found + len(old)
        first = last = None
        for i, (a, b, _) in enumerate(spans):
            if a < match_end and b > found:
                if first is None:
                    first = i
                last = i
        assert first is not None and last is not None
        pieces = []
        cursor = 0
        for i, (a, b, m) in enumerate(spans):
            pieces.append(result[cursor:m.start()])
            inner = m.group(2)
            if i < first or i > last:
                pieces.append(m.group(0))
            elif i == first:
                prefix_len = found - a
                suffix_len = b - match_end if i == last else 0
                prefix = inner[:prefix_len]
                suffix = inner[len(inner) - suffix_len:] if suffix_len else ""
                pieces.append(f"{m.group(1)}{prefix}{escaped}{suffix}{m.group(3)}")
            else:
                keep = inner[match_end - a:] if i == last and match_end < b else ""
                pieces.append(f"{m.group(1)}{keep}{m.group(3)}")
            cursor = m.end()
        pieces.append(result[cursor:])
        result = "".join(pieces)
        count += 1
        search_from = found + len(new)
    return result, count


def replace_in_xml(xml: str, mapping: dict[str, str]) -> tuple[str, int]:
    total = 0

    def _sub(match: re.Match[str]) -> str:
        nonlocal total
        para = match.group(0)
        for old, new in mapping.items():
            para, n = _replace_in_paragraph(para, old, new)
            total += n
        return para

    return P_RE.sub(_sub, xml), total


def replace_docx(src: Path, dst: Path, mapping: dict[str, str]) -> int:
    total = 0
    with zipfile.ZipFile(src, "r") as zin:
        out_buf = io.BytesIO()
        with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                if WORD_PART.match(info.filename) and info.filename.endswith(".xml"):
                    text = data.decode("utf-8")
                    text, n = replace_in_xml(text, mapping)
                    total += n
                    data = text.encode("utf-8")
                zout.writestr(info, data)
    dst.write_bytes(out_buf.getvalue())
    return total


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--map", dest="map_path")
    p.add_argument("--match")
    p.add_argument("--text")
    args = p.parse_args()
    mapping: dict[str, str] = {}
    if args.map_path:
        mapping.update(json.loads(Path(args.map_path).read_text()))
    if args.match is not None:
        if args.text is None:
            raise SystemExit("--text is required with --match")
        mapping[args.match] = args.text
    if not mapping:
        raise SystemExit("pass --map and/or --match/--text")
    n = replace_docx(Path(args.src), Path(args.dst), mapping)
    print(f"replaced {n} occurrence(s)")
    return 0 if n else 1


if __name__ == "__main__":
    sys.exit(main())
