I wrote `formal/variant.yaml`. `fcp lint` reports "lint: clean", and I read the `fcp explain` output back: every item says what I meant it to. I couldn't run `fcp check` (it isn't available to agents), so nothing has been checked for consistency or reachability.

**Items (9, plus 5 requirements left unformalized):**
- **6 properties:**
  - RV-OUT-1: every call returns something: `outcome == 0 || outcome == 2`.
  - RV-SUM-1 / RV-SUM-2: the answer when n can / cannot be written as such a sum.
  - RV-EX-1, RV-EX-2, RV-EX-3: one property per example.
- **3 scenarios:** RV-EX-1-S, RV-EX-2-S, RV-EX-3-S. Each requires the example's call to be possible with the bool value it shows.
- **10 decisions:** every phrase on your list takes reading 2. For R-OUT-1 "the given number n", which wasn't on your list, I took reading 1. It makes no difference here because the trace only covers n from 0 to 65,535. The note of every affected item says which forced reading it uses.

**Left unformalized:**
- **R-API-1** ("Complete this function"): it is about the code you hand in, not about any call, so it isn't a trace property.
- **R-API-2** (the name and parameter): fixed by the `function` section of design.yaml. The parameter's name can't be seen on the trace.
- **R-DEF-1, R-DEF-2:** these are definitions. They are used through the shared definition `sum4` (`covered_by` RV-SUM-1 and RV-SUM-2).
- **R-FR-1:** this is frame rule F-ZERO, which every set includes automatically (`covered_by` F-ZERO).

**Problems in the specification and in this reading:**
1. **The two forced readings change each other's numbers.** If 0 counts as positive and the four terms must be different, the smallest sum is 0 + 2 + 4 + 6 = 12, not the 20 your reading text gives. So exactly the even n ≥ 12 qualify. I wrote this as a direct formula with the reasoning in a comment. Listing every possible set of terms isn't allowed for n up to 65,535 (quantifier bounds stop at 256).
2. **Only one contradiction is real in this set.** R-EX-3 (8 gives True) conflicts with R-SUM-2, since 8 < 12. I kept the conflict as written. The R-EX-1 and R-EX-2 contradictions don't happen here: 4 + 0 + 0 + 0 and 2 + 2 + 2 + 0 repeat a term, which the distinct-terms reading forbids. So 4 and 6 give False, as the examples say.
3. **The trace hides the n = 8 contradiction from the properties.** Under the forced R-OUT-1 reading, returning 1 or 0 is allowed. The trace records any non-bool return as `outcome == 2` without its value, so the properties must accept outcome 2 whether the answer should be True or False. A call at n = 8 with outcome 2 therefore satisfies both RV-SUM-2 and RV-EX-3, even though no Python value equals both True and False. The contradiction only shows through scenario RV-EX-3-S, which should be unreachable. That is untested.
4. **This set accepts a stub that returns None.** The trace can't tell None from 1 or 0, so a body that returns None meets every item under the forced R-OUT-1 reading. A stub that raises an exception is still rejected by RV-OUT-1.