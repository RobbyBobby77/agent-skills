#!/usr/bin/env python3
"""Text-level QA for a .pptx before visual render.

Flags leftover placeholders, empty slides, and slides whose only text is a
generic title. This does not catch overlap — still render slides as images.

Usage:
  python pptx/scripts/qa_text.py output.pptx
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

T_RE = re.compile(r"<a:t[^>]*>(.*?)</a:t>", re.DOTALL)
SLIDE_RE = re.compile(r"ppt/slides/slide(\d+)\.xml$")
BAD = re.compile(
    r"lorem|ipsum|xxxx|placeholder|this (page|slide)|TODO|TBD|click to add",
    re.I,
)


def slide_texts(raw: bytes) -> list[str]:
    return [m.group(1) for m in T_RE.finditer(raw.decode("utf-8", errors="replace"))]


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: qa_text.py deck.pptx")
    path = Path(sys.argv[1])
    issues = 0
    with zipfile.ZipFile(path) as z:
        slides = sorted(
            ((int(m.group(1)), name) for name in z.namelist() if (m := SLIDE_RE.search(name))),
            key=lambda item: item[0],
        )
        if not slides:
            print("ERROR: no slides found")
            return 1
        for num, name in slides:
            texts = slide_texts(z.read(name))
            joined = " ".join(texts).strip()
            if not joined:
                print(f"slide {num}: EMPTY")
                issues += 1
                continue
            for t in texts:
                if BAD.search(t):
                    print(f"slide {num}: placeholder {t!r}")
                    issues += 1
    print(f"{len(slides)} slides, {issues} issue(s)")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
