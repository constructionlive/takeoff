#!/usr/bin/env python3
"""shapes.json + plans PDF -> single-file interactive takeoff page (Takeoff Studio).

  build_html.py PLANS.pdf shapes.json -o Takeoff.html [--dpi 130] [--title "Project"]

The page embeds each referenced sheet as JPEG and every shape as an editable vector: move, reshape,
add/delete, change scope/depth/width, live SF/LF/EA/CY totals, CSV/JSON export, autosave in the browser.
"""
import argparse, base64, io, json, os
import pymupdf as fitz
from PIL import Image
from common import load_shapes

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "template.html")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("shapes"); ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--dpi", type=int, default=130); ap.add_argument("--quality", type=int, default=72)
    ap.add_argument("--title", default="Takeoff Studio")
    a = ap.parse_args()
    data = load_shapes(a.shapes); doc = fitz.open(a.pdf)
    for s in data["sheets"]:
        p = doc[s["page"]]; pix = p.get_pixmap(dpi=a.dpi)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        buf = io.BytesIO(); im.save(buf, format="JPEG", quality=a.quality, optimize=True)
        s["img"] = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
        s["w"], s["h"] = p.rect.width, p.rect.height
        print(f"  {s['id']}: {pix.width}x{pix.height}px {len(buf.getvalue())//1024} KB")
    for i, sh in enumerate(data["shapes"]):
        sh.setdefault("id", f"S{i+1}")
    html = open(TEMPLATE).read().replace("__DATA__", json.dumps(data)).replace("__TITLE__", a.title)
    open(a.out, "w").write(html)
    print(f"wrote {a.out} ({len(html)//1024} KB, {len(data['shapes'])} shapes, {len(data['sheets'])} sheets)")


if __name__ == "__main__":
    main()
