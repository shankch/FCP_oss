I wrote `formal/agent_b.yaml`. `fcp lint` reports no errors, and the `fcp explain` output matches what I meant for every item.

**Items (6):**
- **4 properties:**
  - `RB-RET-1`: every call ends normally (`outcome != 1`).
  - `RB-RET-2`: when a call returns, it returns a bool (`outcome == 0`).
  - `RB-SUM-1`: if n is a sum of 4 even numbers, the call returns True.
  - `RB-SUM-2`: if it isn't, the call returns False.
- **2 scenarios:** one call answered True and one answered False.
- **Model:** frame.md says calls are independent, so the reference model is a set of `defs` that depend only on n, with no ghost state. The central one is `sum4_even = n % 2 == 0`.

**Unformalized (4):**
- **R-IF-1 and R-IF-2** don't describe behaviour: they fix the function's name, signature and that it's complete. None of that is a value on the trace. The observable effects are caught by the behavioural items: an unfinished stub returns None and fails `RB-RET-2`; a wrong number of parameters makes every call raise and fails `RB-RET-1`. R-IF-1 lists those items under `covered_by`.
- **R-DOM-1:** the frame only allows n from 0 to 65,535, and every such value is a "given number" under all three readings. The assumption would just be `true`.
- **R-FR-1:** already covered by the frame rule `F-ZERO`, which frame.md says need not be restated.

**Problems in the specification:**
1. **The request is cut off mid-sentence.** It ends at "the sum of exactly 4" and never says what the four numbers are. The only clue is the word "even" in the function name, so I treated the name as part of the text.
2. **I read the summands as even integers of any sign, with repeats allowed.** Nothing in the workspace says "positive" or "distinct", so this is the most literal reading. It means 0, 2, 4 and 6 must return True. Under the usual "positive even numbers" reading those four return False and the threshold is n ≥ 8. Code written to that reading will fail `RB-SUM-1` on those four values, and a formalizer who took the "positive" reading will disagree with me there.
3. **"Exactly" does nothing under my reading,** because zeros can pad any sum out to four terms. That hints the author meant positive summands, but the text doesn't say so, and I didn't fill that in. The notes on `RB-SUM-1`/`RB-SUM-2` explain this.
4. **The domain is unclear.** "The given number n" could include negative numbers or floats. I took the literal "any number" reading, but the frame restricts the trace to 0–65,535, so it changes nothing here.

**Decisions:** I recorded a reading for all 9 flagged phrases. R-IF-2 name → 1. R-DOM-1 → 3. R-RET-2 → 1 (must be a real bool). For R-SUM-1 and R-SUM-2: "the sum of exactly 4" → 3, "exactly 4" → 1 (repeats allowed), name → 1.