# shapes.json – the takeoff record

One file holds the whole takeoff. Every script reads it; `build_html.py` lets a human edit it and export it back.

```json
{
  "sheets": [
    {"id": "C101", "name": "C-101 Demolition", "page": 6, "ptPerFt": 9.0}
  ],
  "scopes": {"Demo": "#e60000", "Curb": "#001e8c"},
  "shapes": [
    {"sheet": "C101", "type": "area",  "tid": "D-01", "name": "Demo (E) hardscape at new walkway",
     "scope": "Demo", "pts": [[612.7,1298.6],[617.3,1005.4],[657.8,1005.8],[689.9,1299.3]],
     "depth": 4, "count": 1, "note": "Traced from DEMO-ASPHALT layer"},
    {"sheet": "C100", "type": "line",  "tid": "K-01", "name": "New 6\" curb – west edge",
     "scope": "Curb", "pts": [[614.6,1063.9],[613.1,1249.1]], "width": 0.5, "depth": 18},
    {"sheet": "C100", "type": "count", "tid": "C-08", "name": "Light pole foundation 18\"Ø x 7'-6\"",
     "scope": "Concrete-Footing", "pts": [[606,702.5],[604,908.5],[603,1105.5]], "note": "0.49 CY ea"}
  ]
}
```

| field | meaning |
|---|---|
| `sheets[].page` | 0-based page index in the PDF |
| `sheets[].ptPerFt` | page points per foot. 9.0 = 1/8"=1'-0" (72 pt/in ÷ 8 ft/in); 18.0 = 1/4"; 4.5 = 1/16". Confirm with `measure.py calibrate` |
| `pts` | **rotated page points** – the frame of `page.rect`, of `tile.py --grid` renders, and of `get_drawings()` × `page.rotation_matrix` |
| `type` | `area` → SF (+ `depth` in → CY) · `line` → LF (+ `width` ft → SF, + `depth` → CY) · `count` → EA (one point per item) |
| `count` | multiplier (6 identical laterals drawn once = `count: 6`) |
| `tid` | takeoff ID the estimate refers to (D-01, C-03, E-06…). Several shapes may share one ID |
| `scope` | bucket for totals and colour; add your own keys to `scopes` for new colours |
| `color` | optional per-shape override |

Quantities are computed, never stored: `common.quantities(shape, ptPerFt)`.
