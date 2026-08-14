#!/usr/bin/env python3
"""Find LibreOffice and convert a document. Works with PATH and Flatpak.

Copied into docx, pptx, xlsx, and pdf — skills install independently.
Keep the four copies identical.

Usage:
  python scripts/soffice.py --convert-to pdf --outdir out file.docx
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

FLATPAK_ID = "org.libreoffice.LibreOffice"


def find_soffice(*visible: Path) -> list[str]:
    for name in ("soffice", "libreoffice"):
        path = shutil.which(name)
        if path:
            return [path]
    if shutil.which("flatpak"):
        probe = subprocess.run(
            ["flatpak", "info", FLATPAK_ID],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if probe.returncode == 0:
            # Flatpak --filesystem=host does not see tmpfs /tmp.
            cmd = ["flatpak", "run", "--filesystem=host", "--filesystem=/tmp"]
            for path in visible:
                cmd.append(f"--filesystem={path.resolve()}")
            cmd.append(FLATPAK_ID)
            return cmd
    raise SystemExit(
        "LibreOffice not found (soffice/libreoffice on PATH, or "
        f"flatpak {FLATPAK_ID})"
    )


def convert(src: Path, outdir: Path, fmt: str) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = find_soffice(src.parent, outdir) + [
        "--headless",
        "--norestore",
        "--convert-to",
        fmt,
        "--outdir",
        str(outdir),
        str(src),
    ]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout + proc.stderr)
        raise SystemExit(proc.returncode)
    produced = outdir / (src.stem + "." + fmt.split(":", 1)[0])
    if not produced.is_file():
        raise SystemExit(f"conversion produced no file: {produced}")
    return produced


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--convert-to", dest="fmt", required=True)
    p.add_argument("--outdir", required=True)
    p.add_argument("src")
    args = p.parse_args()
    out = convert(Path(args.src).resolve(), Path(args.outdir).resolve(), args.fmt)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
