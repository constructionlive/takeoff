#!/usr/bin/env python3
"""Inventory a plan set: pages, sheet numbers, scales, CAD layers, and text search.

  pdfinfo.py PLANS.pdf                      # one line per page: size, rotation, sheet no., scales, #layers
  pdfinfo.py PLANS.pdf --layers             # unique layer (OCG) names – tells you whether vector takeoff is possible
  pdfinfo.py PLANS.pdf --text 3             # full text of page index 3 (schedules, notes, legends)
  pdfinfo.py PLANS.pdf --grep "curb|asphalt|thick" # search all pages for spec words (case-insensitive)
"""
import argparse, re, collections
import pymupdf as fitz
from common import SCALE_RE

SHEET_RE = re.compile(r'\b([A-Z]{1,2}-\d{1,3}(?:\.\d{1,2})?)\b')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--layers", action="store_true")
    ap.add_argument("--text", type=int)
    ap.add_argument("--grep")
    a = ap.parse_args()
    doc = fitz.open(a.pdf)

    if a.layers:
        names = collections.Counter(v["name"].split("|")[-1] for v in doc.get_ocgs().values())
        print(f"{len(names)} unique layer names across {len(doc.get_ocgs())} OCGs")
        for n, c in sorted(names.items()):
            print(f"  {n}  (x{c})")
        return
    if a.text is not None:
        print(doc[a.text].get_text())
        return
    if a.grep:
        rx = re.compile(a.grep, re.I)
        for i, p in enumerate(doc):
            for line in p.get_text().splitlines():
                if rx.search(line):
                    print(f"p{i}: {line.strip()}")
        return

    print(f"{len(doc)} pages, {len(doc.get_ocgs())} OCG layers")
    for i, p in enumerate(doc):
        t = p.get_text()
        sheets = collections.Counter(SHEET_RE.findall(t))
        # the sheet's own number is usually the one that appears in the title block; heuristically the
        # most common match is often a cross-reference, so show the top 3 and let the reader decide
        top = ", ".join(f"{k}" for k, _ in sheets.most_common(3))
        scales = sorted(set(m.group(0) for m in SCALE_RE.finditer(t)))
        ndraw = len(p.get_drawings())
        print(f"p{i:>2} {p.rect.width:.0f}x{p.rect.height:.0f}pt rot={p.rotation:<3} sheets≈[{top}] scales={scales} drawings={ndraw} chars={len(t)}")


if __name__ == "__main__":
    main()
