I wrote `formal/agent_a.yaml` and checked it: `fcp lint` reports `lint: clean`, and `fcp explain` renders every item the way I meant it.

**Items (3, plus the frame rule F-ZERO, which is added to every set):**
- **RA-FN-1-RET** (property, R-FN-1): `outcome != 1`. Every call with n from 0 to 1,023 finishes and returns a value, with no exception and no hang.
- **RA-FN-1-VAL** (don't-care, R-FN-1): `result` is deliberately left unconstrained when `outcome == 0`. The request never says what the function returns.
- **RA-CAR-1-ZERO** (scenario, R-CAR-1): `n == 0 && outcome != 1` must be reachable, so `candidate(0)` is a valid call that returns. No assumption restricts n.

**Left unformalized (7):**
- **R-FN-2:** the function's signature. It is defined by the `function`/`interface` sections of design.yaml, not by anything in the trace.
- **R-RD-1, R-CAR-2, R-CAR-4:** these describe the road and the cars. No interface signal refers to them, and under the readings I took they don't affect the returned value.
- **R-CAR-3:** classed as an assumption, but it is about where the cars start. The only input is n, so there is no input signal to state it on.
- **R-COL-1:** the collision condition is never given (reading 3), so there is nothing to check.
- **R-FR-1:** `covered_by: [F-ZERO]`, since frame.md says the frame rule need not be restated.

All 9 flagged phrases have a `decisions` entry. Where a phrase was ambiguous I took the reading that adds least to the text: R-FN-1 → 2, "n cars" → 1, "simultaneously" → 1, "driving right to left" → 1, "very far from each other" → 2, "the same speed" → 1, "move in the same speed" → 2, "Two cars are said to collide" → 3, "collide" → 2.

**Problems in the specification:**
1. **The request is cut off.** The docstring stops at "Two cars are said to collide". It never says when two cars collide, what happens after a collision, or what the function returns. Read literally, the only requirement left is that the function returns something for every n. Any implementation that returns passes, so this formalization can't catch a wrong answer.
2. **The likely intended answer is not in the text.** The intent is probably the number of collisions between the two directions, which is n×n (at most 1,046,529, which fits the 21-bit `result`). Getting there needs three further readings the text doesn't support:
   - collisions are only between cars going opposite ways (R-COL-1 reading 1);
   - every left-to-right car starts to the left of every right-to-left car (R-CAR-3 reading 1);
   - cars carry on through each other after colliding ("collide" reading 1).

   If colliding cars were removed instead, the count would be n. I recorded this in the notes rather than encoding it. A formalizer who encodes n×n will disagree with this set, and that disagreement is the truncation showing up.
3. **Smaller ambiguities:** the text doesn't say whether "same speed" means speed or velocity (velocity would contradict the opposite directions), whether that speed stays constant over time, or whether n = 0 is allowed.