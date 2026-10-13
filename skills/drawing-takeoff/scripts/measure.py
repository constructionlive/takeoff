#!/usr/bin/env python3
"""Turn page-point geometry into feet, square feet and cubic yards; check the scale.

  measure.py area "612.7,1298.6 617.3,1005.4 657.8,1005.8 689.9,1299.3"        # shoelace SF (+ perimeter LF)
  measure.py area "..." --depth 4                                               # + CY at 4" thick
  measure.py length "615,1420 590,992" --width 2 --depth 36                     # LF, trench SF and CY
  measure.py calibrate 621.4 1025.1 --ft 45                                     # pt distance vs. a dimension -> pt/ft
  measure.py totals shapes.json                                                 # quantities for every shape + scope totals

Points are 'x,y x,y ...' in rotated page points. --ptperft defaults to 9 (1/8"=1'-0").
"""
import argparse, json, collections
from common import parse_pts, shoelace, polyline_length, quantities, primary, load_shapes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["area", "length", "calibrate", "totals"])
    ap.add_argument("arg", nargs="*")
    ap.add_argument("--ptperft", type=float, default=9.0)
    ap.add_argument("--depth", type=float, default=0, help="inches")
    ap.add_argument("--width", type=float, default=0, help="feet (lines)")
    ap.add_argument("--ft", type=float, help="calibrate: the dimension's real length in feet")
    a = ap.parse_args(); K = a.ptperft

    if a.cmd == "area":
        pts = parse_pts(" ".join(a.arg)); sf = shoelace(pts) / K / K
        print(f"{sf:.1f} SF   perimeter {polyline_length(pts, True)/K:.1f} LF" + (f"   {sf*a.depth/12/27:.2f} CY @ {a.depth:g}\"" if a.depth else ""))
    elif a.cmd == "length":
        pts = parse_pts(" ".join(a.arg)); lf = polyline_length(pts) / K
        s = f"{lf:.1f} LF"
        if a.width:
            s += f"   {lf*a.width:.1f} SF @ {a.width:g}' wide"
            if a.depth:
                s += f"   {lf*a.width*a.depth/12/27:.2f} CY @ {a.depth:g}\" deep"
        print(s)
    elif a.cmd == "calibrate":
        d = abs(float(a.arg[1]) - float(a.arg[0])) if len(a.arg) == 2 else polyline_length(parse_pts(" ".join(a.arg)))
        print(f"{d:.1f} pt measured; at {K} pt/ft = {d/K:.2f} ft" + (f"; true scale = {d/a.ft:.3f} pt/ft ({'OK' if abs(d/a.ft-K)/K<0.02 else 'MISMATCH – set ptPerFt'})" if a.ft else ""))
    else:
        data = load_shapes(a.arg[0]); k = {s["id"]: s["ptPerFt"] for s in data["sheets"]}
        tot = collections.defaultdict(lambda: collections.defaultdict(float))
        for s in data["shapes"]:
            q = quantities(s, k[s["sheet"]]); v, u = primary(s, q)
            print(f"{s['sheet']:<6} {s['tid']:<10} {s['name'][:60]:<60} {v:9.1f} {u}" + (f"  {q['CY']:.2f} CY" if q.get("CY") else ""))
            for kk, vv in q.items():
                tot[s["scope"]][kk] += vv
        print("\nSCOPE TOTALS")
        for sc, q in tot.items():
            print(f"  {sc:<20} " + "  ".join(f"{v:,.1f} {u}" for u, v in q.items()))


if __name__ == "__main__":
    main()
