I wrote `formal/variant.yaml` using the readings you prescribed and noted each one in the items it affects. `fcp lint` reports no errors and `fcp explain` reads back as intended. **However, those readings contradict each other, so no implementation can satisfy this set.**

**Items: 13**, plus 3 helper definitions and 12 decisions (reading 1 for R-DEF-1 "a group of characters", reading 2 for all the others).
- **Rules (9):**
  - RV-RES-1 is the R-RES-1 rule. Under your reading of "is not a part of a word" its condition can never be met, so the rule never makes the function return True.
  - RV-RES-1-EX2: `"apple pi e"` returns False, from your reading of R-RES-1 "returns True".
  - RV-RES-2: every string except the three example strings returns False.
  - RV-RES-2-EXC: `"apple pie"`, `"apple pi e "` and `""` return True, from your R-RES-2 reading.
  - RV-RES-3: every call returns a bool.
  - RV-EX-1 to RV-EX-4: each example returns the value your reading gives it.
- **Reachability checks (4):** RV-EX-1-S to RV-EX-4-S, one per example.

**Left unformalized (4):**
- **R-IF-1:** the function name and signature are fixed by design.yaml, not by anything in a call.
- **R-IN-1:** txt is always a string by how frame.md builds the trace, so there is nothing to assume.
- **R-DEF-1:** its whitespace rule feeds the "last character" definition, but its word definition isn't used by any item. Your R-RES-1 reading says every letter at the end is part of a word, which overrides it.
- **R-FR-1:** covered by the frame rule F-ZERO.

**Problems:**
1. **Your readings contradict each other on all four example strings:**
   - `"apple pie"`, `"apple pi e "` and `""`: your R-RES-2 reading says they return True, while your R-EX-1, R-EX-3 and R-EX-4 readings say they return False.
   - `"apple pi e"`: your R-EX-2 reading says True, while your R-RES-1 "returns True" reading says False.

   The consistency check will flag all four as conflicts.
2. **Two of your readings clash:**
   - R-DEF-1 says a word is a run of letters, so the `e` in `"ab 1e"` is not part of a word.
   - R-RES-1 says a letter at the end is always part of a word.

   I followed the R-RES-1 reading for R-RES-1, so RV-RES-1 can never fire. The vacuity check will report that, and it's expected.
3. **Three of your readings have no effect** on what the set accepts: "the last character", "an alphabetical character" and "separated by space". Their definitions are written out (Python's `isalpha` and `isspace` on character codes 0 to 255), but RV-RES-1 can never fire, so they don't matter.
4. **The specification itself contradicts its examples:**
   - Its rule gives True for `"apple pi e"` and False for the other three examples.
   - The examples say the exact opposite. They look like the negation of the rule, which is reading 3 of R-RES-2 "False otherwise".