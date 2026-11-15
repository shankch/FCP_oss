I wrote `formal/variant.yaml`. `fcp lint` reports clean, and the `fcp explain` output matches what I meant for every item.

I also wrote a Python script to test the formulas on many inputs, but running it needed your approval, so it hasn't run. Instead I checked the key cases by hand: `[1,2,3,2,4]`, `[2,2,3,2]`, and how the order formula picks out kept positions.

**Items: 7**, plus 5 requirements under `unformalized`.
- **Properties (6):** RV-IF-3, RV-RM-1, RV-RM-2, RV-RM-3, RV-ORD-1, RV-EX-1.
- **Scenario (1):** RV-EX-1-S, the doctest call is possible.
- I added one universally quantified value `v` (0–255) and three named expressions: `dup` is the adjacent-run definition from your reading of R-DEF-1, and `n_in` and `n_out` count occurrences of `v` in `numbers` and `result`. I used no other ghost state.
- `decisions` records: R-IF-3 → 2, R-DEF-1 → 2, R-RM-1 → 2, R-EX-1 → 1 (all as you instructed), R-RM-3 → 1, R-ORD-1 → 1.
- Every item affected by your four readings says so in its note. Because raising is allowed under your R-IF-3 reading, the requirements about the returned list only apply when `outcome == 0`. RV-IF-3 rules out only `outcome == 2`.

**Not formalized:**
- **R-FR-1:** the frame rule F-EMPTY already covers it.
- **R-IF-1:** this is about the deliverable, not about what any call does.
- **R-IF-2:** the function name and argument are fixed in `design.yaml`.
- **R-IN-1:** the interface already guarantees `numbers` is a list of integers, so an assumption would constrain nothing.
- **R-DEF-1:** it's a definition, captured as `dup` and used by RV-RM-1 and RV-RM-2.

**Problems in the specification:**
1. **Under your readings, the example contradicts the docstring.** With the adjacent-run reading of "occur more than once", the two 2s in `[1, 2, 3, 2, 4]` aren't next to each other, so 2 doesn't count as occurring more than once. Nothing should then be removed, and RV-RM-2 requires `[1, 2, 3, 2, 4]`. But RV-EX-1, with the example taken as authoritative, requires `[1, 2, 3, 4]`. As written, the set can't satisfy RV-RM-2 and RV-EX-1 on that call, and RV-EX-1-S should be unreachable. I left the conflict in place and noted it in both items. The example's own explanation treats 2 as a repeated value, which only makes sense if any two positions count, not just adjacent ones.
2. **Your R-RM-1 reading doesn't give Unix uniq's output.** That reading says "of each value … one occurrence of it", which I took as a count per value. A value that has an adjacent run is kept once even if it appears again later: `[2, 2, 3, 2]` gives `[2, 3]`, where uniq gives `[2, 3, 2]`.
3. **Some cases can't be seen in the trace.** It can't tell an exception from a call that never finishes (both are outcome 1), or show whether the argument was changed in place (the R-RM-3 ambiguity). Outcome 2 covers both a wrong return type and a list of integers too big for the result signal. RV-IF-3 rules out all of outcome 2, so it also blocks oversized lists, which strictly break R-RM-3 rather than the type annotation.
4. **RV-ORD-1 is a little stronger than R-ORD-1 alone.** It requires the kept copies of each value to be its earliest ones. Combined with RV-RM-1 and RV-RM-2 it means exactly "keep the first occurrence"; the extra strength only matters for keep counts those items already forbid.