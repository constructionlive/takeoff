#!/usr/bin/env python3
"""Burn the takeoff shapes onto the sheets so a human (or the model) can verify them.

  markup.py PLANS.pdf shapes.json -o Takeoff_Markup.pdf [--dpi 200] [--png previews/]

For every sheet in shapes.json: one full-sheet page and one page cropped to the work area, with every
shape drawn in its scope colour, labelled "ID  qty unit", a graphic scale bar and a legend.
"""
import argparse, io, math, os
import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont
from common import load_shapes, quantities, primary

FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"; FONTB = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def font(sz, b=False):
    try:
        return ImageFont.truetype(FONTB if b else FONT, sz)
    except Exception:
        return ImageFont.load_default()


def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("shapes"); ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--dpi", type=int, default=200); ap.add_argument("--png", help="also save 1/4-size PNG previews here")
    a = ap.parse_args()
    data = load_shapes(a.shapes); doc = fitz.open(a.pdf); K = a.dpi / 72.0
    pages = []
    for sh in data["sheets"]:
        shapes = [s for s in data["shapes"] if s["sheet"] == sh["id"]]
        if not shapes:
            continue
        p = doc[sh["page"]]; pix = p.get_pixmap(dpi=a.dpi)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).convert("RGBA")
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        P = lambda pts: [(x * K, y * K) for x, y in pts]
        xs, ys = [], []
        for s in shapes:
            c = hexrgb(s.get("color") or data["scopes"].get(s["scope"], "#000000")); pts = s["pts"]
            xs += [q[0] for q in pts]; ys += [q[1] for q in pts]
            if s["type"] == "area":
                d.polygon(P(pts), fill=c + (60,)); d.line(P(pts) + [P(pts)[0]], fill=c + (255,), width=5)
            elif s["type"] == "line":
                w = int(max(s.get("width", 0) * sh["ptPerFt"] * K, 6))
                d.line(P(pts), fill=c + (90 if s.get("width") else 255,), width=w, joint="curve")
                if s.get("width"):
                    d.line(P(pts), fill=c + (255,), width=4, joint="curve")
            else:
                for i, (x, y) in enumerate(P(pts)):
                    r = 9 * K / 2.8
                    d.ellipse([x - r, y - r, x + r, y + r], fill=c + (230,), outline=(255, 255, 255, 255), width=3)
                    d.text((x, y), str(i + 1), fill="white", font=font(18, True), anchor="mm")
            q = quantities(s, sh["ptPerFt"]); v, u = primary(s, q)
            txt = f"{s['tid']}  {v:,.1f} {u}" + (f" / {q['CY']:.2f} CY" if q.get("CY") else "")
            cx = sum(q_[0] for q_ in pts) / len(pts); cy = sum(q_[1] for q_ in pts) / len(pts)
            if s["type"] == "count":
                cx = pts[0][0] + 4; cy = pts[0][1] - 6
            f = font(24, True); X, Y = cx * K, cy * K; bb = d.textbbox((X, Y), txt, font=f)
            d.rectangle([bb[0] - 6, bb[1] - 5, bb[2] + 6, bb[3] + 5], fill=(255, 255, 255, 235), outline=c + (255,), width=3)
            d.text((X, Y), txt, fill=c + (255,), font=f)
        # scale bar + legend
        fb = font(26, True); X0, Y0 = 60, img.height - 160; seg = 10 * sh["ptPerFt"] * K
        scale_note = '1/8" = 1\'-0"' if abs(sh["ptPerFt"] - 9) < .05 else "custom"
        d.text((X0, Y0 - 40), f"GRAPHIC SCALE  {sh['ptPerFt']:.2f} pt/ft  ({scale_note})", fill=(0, 0, 0, 255), font=fb)
        for i in range(4):
            d.rectangle([X0 + i * seg, Y0, X0 + (i + 1) * seg, Y0 + 20], fill=(0, 0, 0, 255) if i % 2 == 0 else (255, 255, 255, 255), outline=(0, 0, 0, 255), width=2)
            d.text((X0 + i * seg - 8, Y0 + 26), f"{i*10}'", fill=(0, 0, 0, 255), font=fb)
        d.text((X0 + 4 * seg - 8, Y0 + 26), "40'", fill=(0, 0, 0, 255), font=fb)
        used = sorted({s["scope"] for s in shapes}); LX, LY = img.width - 820, 60; lh = 42
        d.rectangle([LX, LY, img.width - 40, LY + 70 + lh * len(used)], fill=(255, 255, 255, 240), outline=(0, 0, 0, 255), width=4)
        d.text((LX + 16, LY + 14), f"TAKEOFF MARKUP – {sh['name']}", fill=(0, 0, 0, 255), font=font(30, True))
        for i, sc in enumerate(used):
            c = hexrgb(data["scopes"].get(sc, "#000")); yy = LY + 66 + i * lh
            tot = {}
            for s in shapes:
                if s["scope"] == sc:
                    for kk, vv in quantities(s, sh["ptPerFt"]).items():
                        tot[kk] = tot.get(kk, 0) + vv
            d.rectangle([LX + 16, yy, LX + 60, yy + 26], fill=c + (110,), outline=c + (255,), width=4)
            d.text((LX + 74, yy - 2), f"{sc}: " + "  ".join(f"{v:,.1f} {u}" for u, v in tot.items()), fill=(0, 0, 0, 255), font=font(24))
        out = Image.alpha_composite(img, ov).convert("RGB")
        pages.append((f"{sh['name']} – full sheet", out))
        m = 60
        crop = (max(0, (min(xs) - m) * K), max(0, (min(ys) - m) * K), min(out.width, (max(xs) + m) * K), min(out.height, (max(ys) + m) * K))
        pages.append((f"{sh['name']} – work area", out.crop(tuple(int(v) for v in crop))))

    pdf = fitz.open()
    for i, (title, im) in enumerate(pages):
        band = Image.new("RGB", (im.width, 90), (31, 56, 100)); ImageDraw.Draw(band).text((24, 22), f"{i+1}/{len(pages)}  {title}", fill="white", font=font(40, True))
        page_im = Image.new("RGB", (im.width, im.height + 90), "white"); page_im.paste(band, (0, 0)); page_im.paste(im, (0, 90))
        pg = pdf.new_page(width=page_im.width / a.dpi * 72, height=page_im.height / a.dpi * 72)
        buf = io.BytesIO(); page_im.save(buf, format="JPEG", quality=82); pg.insert_image(pg.rect, stream=buf.getvalue())
        if a.png:
            os.makedirs(a.png, exist_ok=True); page_im.resize((page_im.width // 4, page_im.height // 4)).save(os.path.join(a.png, f"markup_{i+1}.png"))
    pdf.save(a.out, deflate=True)
    print(f"wrote {a.out}: {len(pages)} pages")


if __name__ == "__main__":
    main()
