---
name: drawing-takeoff
description: Quantity takeoff and bid support from construction drawings (PDF plan sets) – demolition, concrete pads/footings/flatwork, curbs, sidewalks/ADA ramps, asphalt, earthwork and trenching, counts of equipment/bollards/signs. Measures from the CAD vector layers embedded in the PDF instead of guessing from a low-res image, verifies with zoomed tiles and a marked-up drawing, and delivers a priceable Excel takeoff, an interactive HTML takeoff page the reviewer can edit, an RFI/discrepancy list and, if asked, a full crew-based estimate. Use this whenever someone shares civil, site, electrical or architectural drawings and wants quantities, SF/LF/CY/EA, a takeoff, an estimate, a bid, "how much concrete/asphalt", to check an estimator's numbers, or to mark up the plans – even if they only say "review these plans" or "what's the scope on sheet C-100".
---

# Drawing takeoff

You are the digital estimator. The person asking is bidding or checking a bid; wrong quantities cost
them money, and quantities invented from a blurry overview are wrong. The method here is: read the
drawing's own geometry, verify it visually, record every item as a shape, and show your work so a human
can check it in minutes.

## Setup
Scripts live in `scripts/` (Python, `pymupdf pillow openpyxl` – `pip install -r scripts/requirements.txt`
into a venv if `import pymupdf` fails). Run them from any directory; they take the PDF path as an argument.
Work in a scratch folder; keep one `shapes.json` as the single record of the takeoff.

## Workflow

1. **Inventory the set** – `pdfinfo.py SET.pdf` (pages ↔ sheets, scales), then `pdfinfo.py SET.pdf --layers`.
   Layers present → vector takeoff (fast, exact). No layers → tile-and-read takeoff (slower; say so in the report).
   Render a 60-dpi overview of each sheet the request names (`tile.py SET.pdf N --dpi 60 -o ovN.png`) and look at
   it; read notes/legends/schedules at 140–160 dpi tiles or `pdfinfo.py --text N`.

2. **Fix the scale** – 1/8"=1'-0" is 9.0 pt/ft. Prove it on a dimensioned string with
   `measure.py calibrate x1 x2 --ft 45` before measuring anything; record `ptPerFt` per sheet.

3. **Measure from the layers** – `layers.py count` (what's drawn), `cluster` (separate objects, bbox ft),
   `dump --minlen 15` (boundary lines to chain into polygons), `extent` (where equipment sits). Compute with
   `measure.py area|length`. Trace dashed runs (conduit, trench) off a `tile.py --grid 50` render instead of
   summing dashes. Read written dimensions and details for thicknesses, depths and reinforcement – never
   invent a section.

4. **Record** every item in `shapes.json` (schema: `references/shapes-schema.md`): takeoff ID, name,
   scope, points, depth/width/count, note on how it was measured. Separate demo from new work by scope.

5. **Verify** – `markup.py SET.pdf shapes.json -o Markup.pdf --png prev/` and look at the previews: every
   shape must sit on the linework it measures. Re-check clustered items with a tighter `--box`
   (clusters swallow neighbours), re-trace polylines on the grid, compare to schedules and dimension
   strings. Fix, re-render, repeat. This loop is where the real errors get caught – don't skip it.

6. **Deliver** – `build_xlsx.py shapes.json -o Takeoff.xlsx --rfis rfis.json` and
   `build_html.py SET.pdf shapes.json -o Takeoff.html` (the reviewer can move/reshape/add items and export
   CSV/JSON). In the reply give: quantities per scope with sheet/detail references, dimensions as written,
   concrete volumes and reinforcement, demo vs new separated, then the **RFI list**. Mark assumption-based
   numbers with (A) and state the assumption. Pricing only on request – see `references/estimate.md`.

## Flag, don't assume
The drawings usually omit pavement/sidewalk/curb sections, trench width and depth, restoration limits,
utility-company pads, and sometimes items referenced on one sheet but missing from another. Count mismatches
between schedules and plans, wrong detail references and non-existent details are common. Each of these is
an RFI line with a sheet reference and the takeoff impact, not a guess.

## Where to read more
- `references/workflow.md` – step-by-step detail, PyMuPDF gotchas, the verification loop and the specific
  mistakes it catches. Read it the first time you run the skill on a set.
- `references/shapes-schema.md` – the JSON the scripts share.
- `references/estimate.md` – crew-based estimate structure, local-price sourcing, reconciliation checks.
