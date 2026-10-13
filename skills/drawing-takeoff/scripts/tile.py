#!/usr/bin/env python3
"""Render a page (or a region of it) at a chosen DPI so the model can actually read it.

  tile.py PLANS.pdf 3 --dpi 60 -o overview.png                 # whole sheet, cheap overview
  tile.py PLANS.pdf 3 --region 0.66 0.02 0.25 0.6 --dpi 150 -o notes.png   # fractions x y w h of the page
  tile.py PLANS.pdf 14 --clip 500 80 1320 1560 --dpi 110 --grid 50 -o grid.png  # pt box + coordinate grid

Coordinates are in rotated page points (page.rect), the same frame get_drawings()*rotation_matrix and
the shapes JSON use, so anything read off a --grid render can be typed straight into a shape.
"""
import argparse
import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("page", type=int)
    ap.add_argument("--region", nargs=4, type=float, metavar=("X", "Y", "W", "H"), help="fractions of the page")
    ap.add_argument("--clip", nargs=4, type=float, metavar=("X0", "Y0", "X1", "Y1"), help="page points")
    ap.add_argument("--dpi", type=int, default=100)
    ap.add_argument("--grid", type=float, default=0, help="draw a labelled grid every N pt (e.g. 50)")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    doc = fitz.open(a.pdf); p = doc[a.page]; R = p.rect
    if a.region:
        x, y, w, h = a.region
        clip = fitz.Rect(R.x0 + x * R.width, R.y0 + y * R.height, R.x0 + (x + w) * R.width, R.y0 + (y + h) * R.height)
    elif a.clip:
        clip = fitz.Rect(*a.clip)
    else:
        clip = R
    pix = p.get_pixmap(dpi=a.dpi, clip=clip)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    if a.grid:
        k = a.dpi / 72.0
        d = ImageDraw.Draw(im)
        try:
            f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
        except Exception:
            f = ImageFont.load_default()
        g = a.grid
        gx = (int(clip.x0 // g) + 1) * g
        while gx < clip.x1:
            X = (gx - clip.x0) * k
            d.line([(X, 0), (X, im.height)], fill=(0, 170, 255), width=1); d.text((X + 2, 2), f"{gx:.0f}", fill=(0, 0, 255), font=f)
            gx += g
        gy = (int(clip.y0 // g) + 1) * g
        while gy < clip.y1:
            Y = (gy - clip.y0) * k
            d.line([(0, Y), (im.width, Y)], fill=(0, 170, 255), width=1); d.text((2, Y + 2), f"{gy:.0f}", fill=(0, 0, 255), font=f)
            gy += g
    im.save(a.out)
    print(f"wrote {a.out} {im.width}x{im.height}px  clip={[round(v,1) for v in clip]}  ({a.dpi} dpi)")


if __name__ == "__main__":
    main()
