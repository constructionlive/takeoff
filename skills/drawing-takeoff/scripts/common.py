"""Shared helpers for the drawing-takeoff scripts (PyMuPDF based)."""
import json, math, re
import pymupdf as fitz

SCOPE_COLORS = {
    "Demo": "#e60000", "Demo-Landscape": "#009600", "Refinish": "#ff8c00", "Striping": "#a000c8", "Sawcut": "#c80078",
    "Misc": "#555555", "Sidewalk": "#006ee6", "Sidewalk-DWS": "#ffcc00", "Curb": "#001e8c", "Concrete-Footing": "#dc0000",
    "Concrete-Pad": "#ff7800", "Concrete-Misc": "#785000", "Excluded": "#808080", "Trench-Landscape": "#00a050",
    "Trench-Asphalt": "#ff00a0", "Earthwork": "#8b4513", "Asphalt": "#303030", "Other": "#000000",
}

SCALE_RE = re.compile(r'(\d+(?:/\d+)?)"\s*=\s*(\d+)\'(?:-(\d+)")?', re.I)


def open_page(pdf, page):
    doc = fitz.open(pdf)
    return doc, doc[int(page)]


def layer_name(drawing):
    """Short layer name: last segment of 'xref|LAYER'. Empty string if the PDF has no OCGs."""
    return (drawing.get("layer") or "").split("|")[-1]


def iter_lines(page, pred=None, box=None, minlen=0.0):
    """Yield (a, b, drawing) for every straight line item on the page, in *rotated* page coords.

    page.get_drawings() returns unrotated coords; multiply by page.rotation_matrix so that
    they match page.rect, get_pixmap() clips and anything the model reads off a render.
    """
    M = page.rotation_matrix
    for d in page.get_drawings():
        if pred and not pred(d):
            continue
        for it in d["items"]:
            if it[0] != "l":
                continue
            a, b = it[1] * M, it[2] * M
            if box and not (box[0] <= min(a.x, b.x) and max(a.x, b.x) <= box[2]
                            and box[1] <= min(a.y, b.y) and max(a.y, b.y) <= box[3]):
                continue
            if math.dist(a, b) >= minlen:
                yield a, b, d


def drawing_rects(page, pred=None, box=None):
    """Rotated bounding rects (+ summed line length) of drawings matching pred."""
    M = page.rotation_matrix
    out = []
    for d in page.get_drawings():
        if pred and not pred(d):
            continue
        r = d["rect"] * M
        r.normalize()
        if box and (r.x0 < box[0] or r.x1 > box[2] or r.y0 < box[1] or r.y1 > box[3]):
            continue
        ln = sum(math.dist(it[1] * M, it[2] * M) for it in d["items"] if it[0] == "l")
        out.append([r.x0, r.y0, r.x1, r.y1, ln, 1])
    return out


def cluster(rects, gap):
    """Greedy merge of [x0,y0,x1,y1,len,n] rects whose boxes come within `gap` pt."""
    rs = [r[:] for r in rects]
    changed = True
    while changed:
        changed = False
        out = []
        for r in rs:
            for o in out:
                if r[0] <= o[2] + gap and r[2] >= o[0] - gap and r[1] <= o[3] + gap and r[3] >= o[1] - gap:
                    o[0] = min(o[0], r[0]); o[1] = min(o[1], r[1]); o[2] = max(o[2], r[2]); o[3] = max(o[3], r[3])
                    o[4] += r[4]; o[5] += r[5]
                    changed = True
                    break
            else:
                out.append(r)
        rs = out
    return sorted(rs, key=lambda o: (o[1], o[0]))


def shoelace(pts):
    a = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def polyline_length(pts, closed=False):
    p = list(pts) + ([pts[0]] if closed else [])
    return sum(math.dist(p[i], p[i + 1]) for i in range(len(p) - 1))


def parse_pts(s):
    """'x,y x,y ...' or JSON [[x,y],...] -> list of [x,y]."""
    s = s.strip()
    if s.startswith("["):
        return [[float(a), float(b)] for a, b in json.loads(s)]
    return [[float(v) for v in tok.split(",")] for tok in s.split()]


def quantities(shape, pt_per_ft):
    """SF / LF / EA / CY for one shape dict (see references/shapes-schema.md)."""
    k = pt_per_ft
    c = shape.get("count") or 1
    t = shape["type"]
    pts = shape["pts"]
    q = {}
    if t == "area":
        sf = shoelace(pts) / (k * k) * c
        q["SF"] = sf
        if shape.get("depth"):
            q["CY"] = sf * shape["depth"] / 12 / 27
    elif t == "line":
        lf = polyline_length(pts) / k * c
        q["LF"] = lf
        if shape.get("width"):
            q["SF"] = lf * shape["width"]
            if shape.get("depth"):
                q["CY"] = q["SF"] * shape["depth"] / 12 / 27
    else:
        q["EA"] = len(pts) * c
    return q


def primary(shape, q):
    t = shape["type"]
    if t == "area":
        return q.get("SF", 0), "SF"
    if t == "line":
        return q.get("LF", 0), "LF"
    return q.get("EA", 0), "EA"


def load_shapes(path):
    data = json.load(open(path))
    data.setdefault("scopes", {})
    for k, v in SCOPE_COLORS.items():
        data["scopes"].setdefault(k, v)
    for s in data["sheets"]:
        s.setdefault("ptPerFt", 9.0)
    return data
