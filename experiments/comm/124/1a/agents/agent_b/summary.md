Lint is clean and the English rendering matches what I intended, so I'm writing up the summary now.

## Summary

I wrote `formal/agent_b.yaml` (set `agent_b`). `fcp lint` reports it clean, and I read back the `fcp explain` rendering for every item. I did not run `fcp check`, so the set is not yet proved against any code.

**Items: 24 in total, 17 properties and 7 scenarios.**
- **Model:** `valid_date` keeps no state between calls, so there is no ghost. The model is a set of definitions computed from the argument: `shape` (the exact 10-character `dd-mm-yyyy` layout), the field values `f1`/`f2`, a day/month check for each field order (`okA` for dd-mm, `okB` for mm-dd), and `ok`, which is the full definition of a valid date.
- **Return value:** RB-RET-1 says a valid date returns True. RB-RET-2 says anything else returns False and never raises.
- **One property per rule:** EMP-1, DAY-1/2/3, MON-1, FMT-1, FMT-2, plus FMT-3 split into one property per field order. Because both orders are accepted, a day or month rule that fails in one order only rules out that order.
- **Examples:** each of the five examples is a property (the call must give that answer) and also a scenario (that answer must be possible). Two more scenarios show that each field order on its own is accepted.

**Not formalized (4):**
- **R-API-1:** the function name and its one parameter are fixed by the adapter, so there is nothing to check in a trace.
- **R-IN-1:** the encoding already guarantees the argument is a string; calls with anything else are not part of the trace.
- **R-VAL-1:** this is a definition. It is the model's `ok`, and RB-RET-1 and RB-RET-2 cover it.
- **R-FR-1:** this is the frame rule F-ZERO, which is added to every set automatically.

**Decisions:** I took reading 1 for all 12 flagged phrases. That means the four rules are the whole definition (no leap-year or year check), "not less than 1 or higher than N" means the value is between 1 and N, two digits are required for day and month, surrounding spaces are not stripped, the year can be any four digits including 0000, both field orders are accepted, and invalid strings return False.

**Problems in the specification:**
1. **The prompt contradicts itself.** Rule 4 accepts `dd-mm-yyyy`, which makes `'15-01-2012'` a valid date (15 January 2012). But the example says `valid_date('15-01-2012') => False`. Following the most literal reading of each, RB-FMT-3-DM and RB-RET-1 conflict with RB-EX-2, and scenario RB-EX-2-S can never happen. No implementation can satisfy the whole set; I left this conflict in rather than repairing it.
2. **"Not less than 1 or higher than N"** could be parsed as "(at least 1) or (above N)", which leaves no upper limit. I took the normal English meaning, a range from 1 to N, and say so in the notes.
3. **Under "either order", the day rules do almost nothing alone.** Any day out of range (0, or above 29/30/31) can never be a valid month. So a day-rule failure in one order always means the other order is invalid too. I kept the "other order is not valid" condition in RB-DAY-1/2/3 to show the structure, but it is always true there.
4. **Unanswered questions:** the prompt says nothing about leap years, the range of the year, one-digit fields or surrounding spaces. Each one is a recorded decision.