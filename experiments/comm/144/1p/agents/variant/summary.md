I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and I read the `fcp explain` output back to check each item says what I meant.

**Items: 6 formal items**, plus the adapter's frame rule F-ZERO, which is added to every set automatically.
- **4 assumptions**
  - RV-A-IN-1 and RV-A-IN-2: x and n are each valid fractions, meaning exactly one `/`, digits everywhere else, and both parts contain a digit other than `0`.
  - RV-A-IN-3 and RV-A-IN-4: neither x nor n ends in `/0`.
- **2 properties**
  - RV-P-OUT-1 (R-OUT-1): if both inputs are valid and the product (a·c)/(b·d) is not yet in lowest terms, the call must not raise or hang (`outcome != 1`).
  - RV-P-OUT-2 (R-OUT-2): if both inputs are valid and the call ends without raising or hanging, it must return something other than a boolean (`outcome == 2`).
- **Decisions:** all 12 flagged phrases have an entry. The nine instructed phrases use the given readings, and every affected item's note says so.
- **My own choices** for the phrases the instructions left open: I took reading 2 for "simplify" and for "simplify the expression" in both R-OUT-1 and R-OUT-2. That means the function returns the reduced fraction as a string, not a boolean. It is the literal sense of the words, and the only reading that fits the instructed `'2/1'` form.

**Unformalized**
- R-FN-1 has no property: it asks for a complete implementation, which is not something a single call can show.
- R-FN-2 has no property: the function's name and parameters are already fixed by `design.yaml`.
- R-FR-1 is covered by F-ZERO.

**Limits of what I could express**
- **Common factors are only searched up to 49.** FCP-PL has no modulo by a variable, so "the product can be simplified" can only be checked over a fixed range of factors. The full range 2..255 went over lint's 1 GB memory limit. On inputs whose only shared factors are primes of 53 or more (e.g. `'53/2'`, `'1/53'`), RV-P-OUT-1 is weaker than the reading requires.
- **Raising and hanging can't be told apart.** Outcome 1 means either. The instructed R-OUT-1 reading allows raising on inputs that can't be simplified, but not hanging, and no property can separate the two.
- **The returned fraction is invisible.** The adapter records any non-boolean return only as outcome 2. Which fraction comes back (e.g. `'1/2'`) and the `'2/1'` form for whole numbers can't be checked; this is noted in RV-P-OUT-2.
- **Leading zeros count as valid.** The instructed "valid fractions" wording doesn't exclude them, so `'01/2'` is valid, even though the decomposer's third reading suggests they meant to exclude them.

**Problems in the specification**
- **No operation is named.** "Simplify the expression" never says what the expression is (product? quotient?) or what form the result takes.
- **The request conflicts with the adapter.** The adapter assumes a boolean result. Read literally, the request asks for a simplified expression, so under my reading every correct answer is recorded as outcome 2, and an implementation that returns True/False breaks RV-P-OUT-2. I recorded this in the notes rather than working around it.
- **The zero-denominator clause adds nothing.** Under the instructed readings, "valid" already excludes a zero denominator. RV-A-IN-3 and RV-A-IN-4 are implied by RV-A-IN-1 and RV-A-IN-2.