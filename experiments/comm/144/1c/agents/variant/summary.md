I wrote `formal/variant.yaml` with 15 items. `fcp lint` reports no errors, and the `fcp explain` rendering matches what I meant for each item. I didn't run `fcp check`, so the conflicts listed below come from reasoning about the readings, not from the tool. All 18 flagged phrases are recorded under `decisions`, each with the reading you prescribed, and every affected item's note says so.

**Items**
- **4 assumptions:** RV-IN-2, RV-IN-3, RV-IN-4, RV-IN-5.
- **8 properties:** RV-OP-1, RV-RES-1, RV-RES-1-EX, RV-RES-2, RV-RES-2-F, RV-RES-2-INV, RV-RES-3, RV-IN-6.
- **3 scenarios:** RV-EX-1, RV-EX-2, RV-EX-3.
- **Frame rules:** R-FR-1 and R-FR-2 are covered by F-ZERO and F-CODE, which come from design.yaml and are added to every set.
- **Divisibility:** FCP-PL's `%` only accepts a constant divisor, so I tested whether the product is whole using a universally quantified constant `k` (the quotient). The numerators and denominators are read from the strings with sums over the digit positions.

**Left unformalized**
- **R-IF-1:** the function's name and argument order are set by design.yaml and can't be seen in a call trace.
- **R-IN-1:** covered by RV-IN-2 and RV-IN-4.

**Problems**
1. **The spec contradicts itself.** All three examples follow the rule with True and False swapped, not the rule as written. "Simplify the expression" doesn't fit a function that returns a bool.
2. **The prescribed readings make the set contradictory**, by design. I left the contradictions in place and named them in the notes:
   - RV-OP-1 and RV-RES-3 require a non-bool return (outcome 2) on every valid call. RV-RES-1 and RV-RES-2 require a bool.
   - RV-EX-1 (returns True) conflicts with RV-RES-1-EX (returns False). RV-EX-2 and RV-EX-3 (return False) conflict with RV-RES-2 (returns True). So no scenario can be reached.
   - RV-IN-3 bans the signs that RV-IN-2 and RV-IN-4 allow.
3. **RV-RES-2-INV and RV-IN-6 never apply.** They require False on invalid inputs, but the RV-IN-4 and RV-IN-5 assumptions already rule those inputs out.
4. **Two readings of R-RES-2 disagree on valid inputs whose product isn't whole.** The "otherwise" reading says False; the swapped "False otherwise" reading says True. I took the value from "False otherwise" and noted the conflict.
5. **FCP-PL can't express floating-point evaluation.** It only has exact integer arithmetic, so I formalized the float reading in a weaker form that never constrains a call the reading leaves free:
   - RV-RES-1 only covers calls where float evaluation is certainly exact: the first division a/b is exact in floating point.
   - RV-RES-2 uses the exact condition "the product isn't whole". For inputs that fit in 8 characters, that guarantees the float result isn't a whole number either.
   - The two calls the readings name are added as separate items: 1/5·5/1 gives 1.0 (RV-RES-1-EX) and 1/49·49/1 gives 0.9999999999999999 (RV-RES-2-F).
   - Other calls where float and exact arithmetic disagree are left unconstrained.
6. **R-RES-3's readings of "True" and "The function returns" are applied only to RV-RES-3**, since that's where they were flagged. RV-RES-1 and RV-RES-2 read True and False as Python bools.