I wrote `formal/variant.yaml`. `fcp lint` reports no errors, and the `fcp explain` output matches what each item is meant to say. The set itself is inconsistent, though: two of the readings I was told to take can't hold alongside the rest.

**Items:** 21 in total: 17 properties and 4 scenarios, plus the frame rule F-EMPTY that the design file adds to every set. There are no assumptions, because R-CON-1..3 are read as checks the function must make, not as rules for the caller. I recorded 18 decisions, all reading 2, as you instructed. Every item's note names the instructed readings that affect it.

**Requirements left unformalized** (each listed with `covered_by`):
- **R-SIG-1, R-VAR-1, R-VAR-2, R-VAR-3:** these only define names. The instructed mapping is in `defs` (`number = y`, `need = x`, `remaining = x`) and is used by every item.
- **R-CTX-1:** narrative only. It's covered by the items that add `number` to the first element.
- **R-FR-1:** covered by F-EMPTY, which holds by construction.

**Problems with the instructed readings:**
- **The mapping:** `need` and `remaining` are both `x`, and `z` has no role. So `remaining == need` always holds: the "stock suffices" and "not enough carrots" conditions are always true, and the shortfall is always 0.
- **R-RET-2:** each of its three readings has its own formula for the first element, so I made one property per phrase:
  - "needed" gives `number + need` (that is, `y + x`)
  - "before" gives `number` (`y`)
  - "total number" gives `min(need, remaining)` (`x`)

  These conflict with each other. RV-RET-2-BEFORE and RV-RET-2-TOTAL also conflict with RV-RET-2-NEEDED, RV-MEAL-1, RV-HUN-1 and all four example properties. As a result, none of the four example scenarios can be reached in this set.
- **Everything else agrees:** without those two items, all other items require the answer `[y + x, 0]`. The instructed example values ([11, 0], [12, 0], [11, 0], [13, 0]) happen to fit this, because `number + need` gives the same sum either way round.
- **Examples vs. the printed docstring:** with the docstring's own order, the readings for R-RET-3 and R-HUN-3 contradict the printed examples [11, 4], [12, 1] and [7, 0]. My example items use the values the readings give, not the printed ones, and say so.
- **"An array" (R-RET-1):** the adapter reports any non-list return as outcome 2, so outcome 2 is accepted. That means a tuple can't be told apart from a wrong answer.
- **Rejecting out-of-range inputs:** I took "reject … e.g. by raising" to mean "returns no list" (`outcome != 0`), not specifically "raises". `z` is never range-checked.

**Problems in the specification itself:**
- The signature (`x, y, z`) and the docstring (`number, need, remaining`) never say which name is which.
- The phrases "no or more", "needed or eaten" and "before or after" are self-contradictory.
- "Constrain" and "thet" are typos.