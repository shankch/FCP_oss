I wrote `formal/variant2.yaml`. `fcp lint` reports clean, and the `fcp explain` output matches what I intended for every item. I did not run `fcp check`, so the conflicts below come from working the arithmetic by hand, not from a tool run.

**Items: 10** (9 properties, 1 scenario), all ids starting `V2-`. There is no ghost state; every item relates the inputs directly to the outputs.
- **R-RET-1:** a call with at least one item and no quantity of 0 returns a dict (`outcome == 0`).
- **R-ERR-1:** a call with no items, or with any quantity of 0, raises ValueError (`outcome == 1`).
- **R-LINES-1:** there is one line per item, and a line with no rule-3 discount is price × qty.
- **R-MEM-1:** for a member, a line not on sale is ⌊0.9·price·qty⌋.
- **R-DISC-1:** for a member, `discount` is the sum over items not on sale of ⌊price·qty/10⌋; for everyone else it is 0.
- **R-SUM-1 and R-TOT-1:** both definitions of `total` are stated as written.
- **R-EX-1:** the example is a scenario (a behaviour that must be possible).

FCP-PL has no division operator, so the rounding is written with floor-modulo, for example `10*lines[i] == 9*p*q - (9*p*q) % 10`.

**Decisions:** R-MEM-1 takes reading 2 and R-DISC-1 takes reading 2, as you instructed. The note of each affected item says so.

**Left unformalized: 3**
- **R-SIG-1 and R-IN-1:** these are definitions, already captured by the `function` and interface sections of design.yaml.
- **R-FR-1:** this is frame rule F-ZERO, which is added to every set automatically.

**Problems in the specification**
1. **The required readings contradict the spec's own example.** Under R-MEM-1 reading 2, the example's line is ⌊0.9·3998⌋ = 3598, but the prompt says `lines: [3599]`. The example follows reading 1. I kept the scenario as written, so it should be unreachable in this set.
2. **The two readings round in opposite directions.** With R-MEM-1 reading 2, each line's discount is effectively rounded up; with R-DISC-1 reading 2, `discount` rounds each item down. So rule 5 (`total` = sum of lines) and rule 6 (`total` = gross − `discount`) disagree for any member with an item not on sale whose price × qty is not a multiple of 10. In the example they give 3598 and 3599. Since R-RET-1 makes such valid calls return a dict, the set cannot be satisfied on those inputs. I did not repair this.
3. **`total` is defined twice (rules 5 and 6), which is fragile even without the forced readings.** The two definitions agree only if the line discounts add up to `discount`. That holds under R-MEM-1 reading 1 with R-DISC-1 reading 2. It fails under reading 1 for both: two items with price × qty of 5 each give line discounts of 0 + 0, but `discount` = ⌊1.0⌋ = 1.