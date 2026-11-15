I wrote `formal/variant1.yaml`. `fcp lint` reports it clean, and I read the `fcp explain` output for every item; each one means what I intended.

**Items: 11, all starting with V1-.** There are 10 properties and 1 scenario. The frame rule F-ZERO is added to the set automatically.
- **R-RET-1:** any call that rule 1 doesn't reject ends with `outcome == 0` (V1-RET-1).
- **R-ERR-1:** no items, or any item with quantity 0, ends with `outcome == 1` (V1-ERR-1).
- **R-LINES-1:** `len(lines) == len(price)` (V1-LINES-1), and every line without a rule-3 discount equals price × qty (V1-LINES-2).
- **R-MEM-1:** reading 1, so each line's discount is ⌊price·qty/10⌋ (V1-MEM-1). FCP-PL has no division, so this is written as the bound `10d ≤ x < 10d+10`.
- **R-DISC-1:** for members, reading 1, so discount = ⌊(sum of price·qty over items not on sale)/10⌋ (V1-DISC-1). For non-members, discount is 0 (V1-DISC-2).
- **R-SUM-1 / R-TOT-1:** total = sum of lines (V1-SUM-1); total = summed price·qty − discount (V1-TOT-1).
- **R-EX-1:** a scenario that the example call can happen (V1-EX-1), plus a property that this call returns exactly the stated result (V1-EX-2).
- **Ghost state:** none. Three defs (`valid`, `gross`, `gross_ns`) keep the formulas short.
- **Decisions:** R-MEM-1 reading 1 and R-DISC-1 reading 1, as you instructed. The notes of the affected items say so.

**Left unformalized:**
- **R-SIG-1 and R-IN-1:** these are definitions, and the interface and function section of `design.yaml` already express them. R-SIG-1 points to V1-RET-1 for its "returns a dict" part.
- **R-FR-1:** this is the adapter's own definition, already the frame rule F-ZERO.

**Problems in the specification:**
1. **Rules 5 and 6 contradict each other under the readings taken.** Rounding each line's discount down separately (rule 3) can give less than rounding the summed discount down (rule 4). Example: a member buys two items, each price 5, qty 1, not on sale. The lines must be [5, 5], so total is 10 by rule 5. But the discount must be 1, so total is 9 by rule 6. Because R-RET-1 says such a call must return, no answer satisfies every rule. I found this by working it out by hand and didn't run `fcp check`. I wrote it down in the notes and did not repair it. Reading 2 of R-DISC-1 (round each item, then sum) would remove the conflict.
2. **R-RET-1 says "returns a dict" without any condition, but rule 1 says some calls raise.** I applied it only to calls that rule 1 accepts, as the requirement's own text does ("for a valid call"), and said so in the note.
3. **The example only fits reading 1 of R-MEM-1.** Reading 2 would give a line of 3598, not 3599. With a single item, the example can't tell the two readings of R-DISC-1 apart.
4. **The spec never says lines without a member discount have zero discount.** Rule 2 says "minus that line's discount", but only rule 3 defines one. I took it as zero for every other line (V1-LINES-2), as the requirement text does.