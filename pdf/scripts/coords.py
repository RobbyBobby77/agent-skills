#!/usr/bin/env python3
"""Convert a top-left pixel on a rendered page to PDF points (origin bottom-left).

Agents routinely stamp overlay text at the pixel coordinate they measured
and miss the field by a flipped Y-axis.

Usage:
  python pdf/scripts/coords.py --x 120 --y 80 --dpi 150 --page-height-pt 792
"""

from __future__ import annotations

import argparse
import sys


def px_to_pt(x_px: float, y_px: float, dpi: float, page_height_pt: float) -> tuple[float, float]:
    pt_x = x_px * 72.0 / dpi
    pt_y = page_height_pt - (y_px * 72.0 / dpi)
    return pt_x, pt_y


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--x", type=float, required=True, help="pixels from left")
    p.add_argument("--y", type=float, required=True, help="pixels from top")
    p.add_argument("--dpi", type=float, default=150)
    p.add_argument("--page-height-pt", type=float, default=792.0, help="US Letter 792, A4 841.89")
    args = p.parse_args()
    x, y = px_to_pt(args.x, args.y, args.dpi, args.page_height_pt)
    print(f"{x:.2f} {y:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
