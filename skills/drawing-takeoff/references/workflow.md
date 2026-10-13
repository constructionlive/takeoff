# Drawing takeoff – detailed workflow and pitfalls

Everything below was learned doing a real civil/EV-charging takeoff (demo, concrete pads, ADA walk, curb, asphalt,
trench) from a 22-sheet Blymyer set. Read it when you hit a step that isn't obvious from SKILL.md.

## 0. Why vectors beat vision
A 24x36 sheet needs ~100 megapixels to read; the model sees <1. But most engineer-issued PDFs are plotted
from CAD and still carry the CAD **layers** (PDF optional content groups) and exact **vector geometry**.
`pdfinfo.py PLANS.pdf --layers` tells you in one call. Layer names like `DEMO-ASPHALT`, `REMOVE-CURB`,
`BEI-CONC-NEWW`, `BEI-CURB-NEWW`, `E-BEI-CIRC-AC`, `C-SITE-BOLL` are the takeoff done for you – you only
have to read them out and verify. Fall back to tiling + reading only when the set is scanned/flattened
(0 layers, drawings are one big image).

## 1. Inventory (5 minutes)
- `pdfinfo.py set.pdf` → page index ↔ sheet number, declared scales, drawing counts. Note that title-block
  text is unreliable for sheet IDs (the most frequent match is often a cross-reference) – confirm by
  rendering the lower-right corner at 60 dpi once.
- `tile.py set.pdf N --dpi 60 -o ovN.png` for every civil/electrical sheet you were asked about. Look at
  them. Decide which sheet is the *source of truth* for each scope (demo plan for removals, site plan for
  new work, dimensioned plan for lengths, electrical for trench routes, detail sheets for sections).
- Read notes, legends and schedules at 140–160 dpi tiles (`--region 0.66 0.02 0.25 0.6` is the usual
  right-hand notes column). Pull schedules with `pdfinfo.py --text N` – counts in the equipment schedule
  are a free cross-check for your counts.

## 2. Scale
`page.rect` is in points; at 1/8"=1'-0" one foot is 9.0 pt. Always verify on a dimensioned string:
`measure.py calibrate 621.4 1025.1 --ft 45` (5 stalls @ 9' = 45'-0"). Record `ptPerFt` per sheet.
Detail sheets are a different scale per detail – never measure on them, read their dimension strings.

## 3. Find the geometry
- `layers.py count set.pdf N` → which layers exist on this page and how much line length each carries.
  Suffixes tell you a lot: `-NEWW`/`-NEW` new work, `DEMO-`/`REMOVE-` removals, `HATCH`/`PATT` fills.
- `layers.py cluster set.pdf N LAYER --gap 4` → separate objects with bbox size in ft. Good for counts
  and rectangles (pads, patches, striping).
- `layers.py dump set.pdf N LAYER --minlen 15 --box x0 y0 x1 y1` → boundary lines only (minlen hides
  hatch), which you chain into a polygon and feed to `measure.py area`.
- `layers.py extent set.pdf N LAYER` → where is the transformer / switchboard / dispensers.
- When something isn't on an obvious layer, box it: `layers.py count set.pdf N --box …` lists only what
  is drawn inside that box.

## 4. Record every item as a shape
Append to `shapes.json` (see shapes-schema.md) as you go – polygon vertices from `dump`, rects from
`cluster`, counts from `extent`/cluster centres, polylines traced off a `tile.py --grid 50` render for
dashed conduit runs. Give every shape the takeoff ID you will use in the estimate and a scope.

## 5. Verify before you report (the loop that catches errors)
1. `markup.py set.pdf shapes.json -o Markup.pdf --png previews/` and **look at the previews**. Every
   shape should sit on the linework it claims to measure. Misplaced = wrong.
2. Zoom-check anything that was clustered: in one real case a 5th demo square (EV-2A pad) was
   merged into the big walkway polygon by the clustering gap and only appeared when the box was
   restricted (`--box` with y < pad row). Clusters hide neighbours – restrict the box or lower `--gap`.
3. Re-trace dashed/polyline runs on a gridded tile. Summing dashed segments undercounts; bbox extents
   over-count on diagonals; the grid read is the honest number (trench to EV-4B went 113 → 126 LF).
4. Cross-check against written dimensions (C-110 style "dimensioned site plan") and schedules.
5. Check that sheets share one coordinate frame before reusing coordinates across them (the equipment
   extents on C-100 and E-100 matched to the point; they usually do when plotted from one model, but
   verify with `layers.py extent` on both).

## 6. Deliver
- `build_xlsx.py shapes.json -o Takeoff.xlsx --rfis rfis.json` (priceable workbook).
- `build_html.py set.pdf shapes.json -o Takeoff.html` (the reviewer edits shapes, exports CSV/JSON; load
  the JSON back into `shapes.json` to round-trip).
- Report: quantities table per scope with sheet/detail references, dimensions and thicknesses *as
  written*, separate demo vs new, and a numbered **RFI / discrepancy list** (see below). Mark every
  number that rests on an assumption with (A) and say what the assumption is.

## 7. Things the drawings routinely do not tell you – flag, don't assume
- Pavement, sidewalk and curb **sections** (thickness, base, reinforcement, curb profile).
- Trench width/depth ("varies"), surface restoration limits, sawcut for trenches.
- Equipment pads that are referenced to a detail but never outlined on the plan (draw them at detail
  size on the equipment centre and say so).
- Items on one sheet but not another (pergola "to be demolished" on the site plan, absent from demo plan).
- Schedule vs plan count mismatches; detail references that point to the wrong detail; details that don't exist.
- Utility-company items (transformer pad, bollards) with no detail – scope ownership question, not an exclusion.
- Survey/title-block address mismatches; no geotech.

## PyMuPDF gotchas
- `page.rect` is the rotated page; `get_drawings()` coordinates are **not** – multiply by
  `page.rotation_matrix` (common.py does). `get_pixmap(clip=…)` takes rotated coords directly.
- `fitz` import name is deprecated – `import pymupdf as fitz`.
- Layer names repeat per xref (`Fresno CA CAD File|EXCON1`); match on the part after the last `|`.
- Hatch patterns live on the same layer as their boundary; filter by `--minlen` or stroke width, or
  cluster and take the bbox.
- Large text dumps: write to a file and grep; don't print 80 KB into context.
- Renders: 60 dpi for overview, 110–150 for notes, 200+ only for a small `--region`. A full sheet at
  200 dpi is 7,200 px wide – fine for markup output, wasteful to look at.
