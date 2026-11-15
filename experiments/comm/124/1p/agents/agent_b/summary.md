I've written `formal/agent_b.yaml`. `fcp lint` reports it clean, and `fcp explain` shows each item means what I intended.

**Items: 5 formal items** (3 properties, 2 scenarios). The frame rule F-ZERO is added to the set automatically.
- `RB-RET-1` (R-RET-1): every call returns a bool, i.e. `outcome == 0`. This takes the "total" reading.
- `RB-RET-2` (R-RET-2): whenever the date is valid, the call returns True.
- `RB-RET-3` (R-RET-3): whenever the date is invalid, the call returns False. This can never trigger, because no string is invalid (see below).
- `RB-S-RET-2` and `RB-S-RET-2-EMPTY` (R-RET-2): returning True must be possible, including for the empty string.
- The model of the expected answer is defs rather than ghost state, because the function keeps nothing between calls. `rules_ok` combines all the listed rules, and since the list is empty it is simply `true`. `date_valid` is defined as `rules_ok`.

**Not formalized (6):**
- R-API-1 and R-API-2 describe the deliverable and the function's name and parameter, not behaviour. The adapter already fixes the name and parameter.
- R-IN-1: the encoding already guarantees every argument is a string, and I took the "any string" reading, so no assumption is needed.
- R-VAL-1 and R-VAL-2 are definitions. The defs above realize them, so they are marked `covered_by: [RB-RET-2, RB-RET-3]`.
- R-FR-1 is covered by the frame item F-ZERO.

**Decisions:** I took the most literal reading of every flagged phrase. That is reading 1 for all of them, except the third phrase of R-VAL-1, where I took reading 2: an empty rule list does not logically contradict "otherwise False"; it just means the False case never happens.

**Problems in the specification:**
1. **The rule list is empty.** Line 8 is just "1." with nothing after it, and the docstring ends there. The prompt looks truncated. Read literally, every string is a valid date, so the only correct function is one that always returns True. That also rules out False entirely.
2. **The prompt contradicts itself in intent.** It asks the function to "validate" the date and to return False for invalid ones, which assumes some strings are invalid. No stated rule makes any string invalid. I noted this on `RB-RET-3` rather than inventing the missing date rules (month range, day range, format). As a result `RB-RET-3` will be reported as never triggering, and it should be.
3. **Implementations will split.** Any implementation written to the intended (missing) rules will return False on some strings, and this set will fail it. Another formalizer who reads the list as "rules omitted, result unspecified" would leave the result free, so comparing our two sets should show the disagreement.