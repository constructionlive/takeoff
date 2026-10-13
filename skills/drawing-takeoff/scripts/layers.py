#!/usr/bin/env python3
"""Vector takeoff from the CAD layers embedded in a plan PDF.

  layers.py count   PLANS.pdf 6                       # drawings per layer on the page (find the DEMO-/NEW- layers)
  layers.py count   PLANS.pdf 6 --box 600 1000 700 1420   # ... only inside a pt box (which layer is this thing on?)
  layers.py cluster PLANS.pdf 6 DEMO-ASPHALT --gap 4   # group a layer's geometry into separate objects -> bbox, ft, SF
  layers.py dump    PLANS.pdf 3 BEI-CONC-NEWW --minlen 15 --box 600 990 700 1310   # boundary lines with ft lengths
  layers.py extent  PLANS.pdf 14 BEI-EQPM-XFMR         # overall extent of a layer (where is the equipment?)

Layer match is a case-insensitive substring on the short layer name (after the last '|').
--ptperft defaults to 9 (1/8" = 1'-0" on a 24x36 sheet: 72 pt/in ÷ 8 ft/in). Use --ptperft 18 for 1/4"=1'.
"""
import argparse, collections, math
from common import open_page, layer_name, drawing_rects, cluster, iter_lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["count", "cluster", "dump", "extent"])
    ap.add_argument("pdf"); ap.add_argument("page", type=int); ap.add_argument("layer", nargs="?")
    ap.add_argument("--box", nargs=4, type=float, metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--gap", type=float, default=4.0)
    ap.add_argument("--minlen", type=float, default=0.0, help="dump: ignore lines shorter than this (pt) – hides hatch")
    ap.add_argument("--min", type=float, default=0, help="cluster: hide clusters whose w+h < this (pt)")
    ap.add_argument("--ptperft", type=float, default=9.0)
    a = ap.parse_args()
    doc, p = open_page(a.pdf, a.page)
    K = a.ptperft
    pred = (lambda d: a.layer.lower() in layer_name(d).lower()) if a.layer else None

    if a.cmd == "count":
        c = collections.Counter(); ln = collections.Counter()
        for r in drawing_rects(p, None, a.box):
            pass
        M = p.rotation_matrix
        for d in p.get_drawings():
            r = d["rect"] * M; r.normalize()
            if a.box and (r.x0 < a.box[0] or r.x1 > a.box[2] or r.y0 < a.box[1] or r.y1 > a.box[3]):
                continue
            L = layer_name(d); c[L] += 1
            ln[L] += sum(math.dist(it[1] * M, it[2] * M) for it in d["items"] if it[0] == "l")
        for L, n in c.most_common():
            print(f"{n:>6}  {L or '(no layer)':<40} lines={ln[L]/K:8.1f} ft")
        return

    if a.cmd == "cluster":
        rs = cluster(drawing_rects(p, pred, a.box), a.gap)
        for o in rs:
            w, h = (o[2] - o[0]) / K, (o[3] - o[1]) / K
            if (o[2] - o[0]) + (o[3] - o[1]) < a.min:
                continue
            print(f"bbox [{o[0]:.1f},{o[1]:.1f},{o[2]:.1f},{o[3]:.1f}]  {w:.1f} x {h:.1f} ft  bboxSF={w*h:.0f}  n={o[5]}  lines={o[4]/K:.1f} ft")
        print(f"{len(rs)} clusters (bbox SF is an upper bound – trace the boundary with 'dump' for irregular shapes)")
        return

    if a.cmd == "dump":
        seen = set()
        for A, B, d in iter_lines(p, pred, a.box, a.minlen):
            key = (round(A.x, 1), round(A.y, 1), round(B.x, 1), round(B.y, 1))
            if key in seen:
                continue
            seen.add(key)
            print(f"({A.x:.1f},{A.y:.1f})-({B.x:.1f},{B.y:.1f})  len={math.dist(A,B)/K:.2f} ft  w={d.get('width')}")
        return

    if a.cmd == "extent":
        rs = drawing_rects(p, pred, a.box)
        if not rs:
            print("no drawings on that layer"); return
        x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs); x1 = max(r[2] for r in rs); y1 = max(r[3] for r in rs)
        print(f"{len(rs)} drawings  extent x {x0:.0f}-{x1:.0f}  y {y0:.0f}-{y1:.0f}  ({(x1-x0)/K:.1f} x {(y1-y0)/K:.1f} ft)")


if __name__ == "__main__":
    main()
