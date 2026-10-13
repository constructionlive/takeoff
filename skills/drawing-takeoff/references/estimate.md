# From quantities to a subcontractor estimate

Only do this when asked for pricing. Keep the quantity takeoff and the cost estimate as separate
workbooks so the GC can audit one without the other.

## Structure that worked
1. **Rates** tab – every wage, burden, equipment rate, material price, dump fee and markup as a yellow
   input with its source in the next cell. Include a prevailing-wage switch (`IF(pw=1, package, base×(1+burden))`)
   – public money often rides on private-looking EV projects.
2. **Crews** tab – crew build-ups (foreman fraction, operator, mason, laborers, driver) → labor $/hr and
   equipment $/hr.
3. **Estimate** tab – one line per takeoff ID: qty × (crew-hrs = qty ÷ production) → labor, equipment;
   qty × material unit → material; sub/other. Set productions low for small, congested, phased sites.
4. **Bid Summary** – division totals, sales tax on materials, GL, design-gap contingency (because of the
   missing sections), overhead, profit, bond; a **unit-price schedule** that sums back to the bid (GCs ask
   for itemized); alternates (PW, thicker walk, utility pad allowance, T&M rate for unknown utilities);
   clarifications & exclusions.

## Getting local prices
Web searches return SEO pages, not plant quotes. Use them only to bracket ready-mix, HMA, tipping fees and
rebar, cite them, and say plainly that the sub must get three quotes. State the wage basis and date.

## Reconcile
- Unit-price schedule total = direct cost; sell total = base bid. If not, something is unmapped.
- Evaluate every formula (openpyxl writes no cached values): LibreOffice `recalc.py` if available, else
  the `formulas` package; treat any `#…` result as a defect.
- Toggle the PW switch and report both numbers.
