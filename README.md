# drawing-takeoff – a Claude skill for construction quantity takeoffs

Turns a plan-set PDF into verified quantities, a marked-up drawing, a priceable Excel takeoff, an
interactive HTML takeoff page and an RFI list. It measures from the CAD layers most engineer-issued
PDFs still carry, instead of guessing from a downscaled image, then verifies every item visually.

## Install (Claude Code)
```
/plugin marketplace add constructionlive/takeoff
/plugin install drawing-takeoff@drawing-takeoff
```
or copy `skills/drawing-takeoff` into `~/.claude/skills/` (personal) or `.claude/skills/` (project).

Python deps: `pip install -r skills/drawing-takeoff/scripts/requirements.txt` (pymupdf, pillow, openpyxl).

## Use
Attach or point at the PDF and ask for a takeoff, e.g. *"Take off demo, concrete, curb, asphalt and trenching
from sheets C-100, C-101, C-110 and E-100 of this set; flag anything that needs an RFI."*

## What you get
- `shapes.json` – every measured item (polygons, lines, counts) with takeoff IDs
- `Markup.pdf` – the sheets with the takeoff burned on, scale bar and legend, for checking
- `Takeoff.xlsx` – quantities with live SF/LF/EA/CY formulas and a unit-cost column
- `Takeoff.html` – single-file editor: drag/reshape/add items, scope totals, CSV/JSON export
- An RFI / discrepancy list in the reply

## Layout
```
skills/drawing-takeoff/
  SKILL.md                 workflow the model follows
  scripts/                 pdfinfo · tile · layers · measure · markup · build_xlsx · build_html
  assets/template.html     the interactive page
  references/              workflow details & pitfalls, shapes schema, estimating notes
```
Scanned/flattened sets (no layers) still work, but only through the tile-and-read path; expect lower precision.
