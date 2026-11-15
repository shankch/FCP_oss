I wrote `formal/variant.yaml` with 13 properties, all of type `implies`. `fcp lint` reports clean, and `fcp explain` reads back as I meant each item. I tried to run a brute-force Python check of the `hit` definition, but that command was declined, so it was not run. I worked out by hand that all six examples count as hits.

**How the instructed readings combine.** A shared definition `hit` captures "b or one of its rotations is in a" under your readings: rotations are any rearrangement, "substring" means subsequence, letters ignore case (Python `str.lower()` on Latin-1), and an empty b is never a hit. "Some rearrangement of b is a subsequence of a" is stated as "every character appears in a at least as often as in b". The two say the same thing, and the second is easier to write.

**The items:**
- **R-RES-1:**
  - `RV-RES-1`: a hit returns False. The examples win, so the reversed rule applies.
  - `RV-RES-1-EMPTY`: when b is empty, the call does not return True. That reading says so in as many words, so I formalized it.
- **R-RES-2:**
  - `RV-RES-2`: a non-hit returns True. This is the reversed rule. Because only the True case is specified, R-RES-2 says nothing when there is a hit.
  - `RV-RES-2-EX1/EX3/EX5`: each of these example calls returns True, as the readings state.
- **R-EX-1 to R-EX-6:** `RV-EX-1` to `RV-EX-6`. Because each reading takes the rule as right, examples 1, 3 and 5 return False, and 2, 4 and 6 return True.
- **"Returns True":** wherever True is required, any truthy value counts. The trace can't tell whether a returned value that isn't a bool is truthy, so it is accepted where True is required and rejected where True is forbidden. "Returns False" means the bool False.

Every item's note names the instructed readings that affect it.

**Left unformalized (6), with reasons:**
- **R-NF-1:** it is about delivering Python code, not about any call's result.
- **R-DEF-1, R-DEF-2, R-DEF-3:** these are definitions, built into `hit` and marked as covered by the R-RES items.
- **R-IN-1:** with reading 1 (any string is allowed), there is no assumption to make. It is covered by the R-RES items, which hold for every input.
- **R-FR-1:** this is frame rule F-ZERO, which `frame.md` says is part of every set automatically.

**Problems in the specification and the readings:**
1. **The original prompt contradicts itself.** "ell" is literally inside "hello", yet the example says False. The decomposer flagged this contradiction.
2. **The instructed readings contradict each other, so no answer satisfies every item:**
   - Under the instructed definitions, all six examples are hits. So the claim in the readings that "all six examples fit the negated rule" is false: examples 1, 3 and 5 (True) break `RV-RES-1`.
   - For the calls in examples 1, 3 and 5, `RV-RES-2-EXn` requires True, while `RV-RES-1` and `RV-EX-n` require False.
   - For the calls in examples 2, 4 and 6, `RV-EX-n` requires True, while `RV-RES-1` requires False.
   - For an empty b, `RV-RES-2` requires True, while `RV-RES-1-EMPTY` forbids it.

   That is seven kinds of call with no valid answer. I expect the consistency check to report them.
3. **Some readings rest on the default definitions.** The rule-is-right readings (R-EX-1/3/5) and the example-wins readings (R-RES-2) argue from cyclic shifts and contiguous substrings. Under the variant definitions, R-RES-2's condition doesn't even apply to those calls.
4. **The trace can't fully show truthiness.** Telling a truthy non-bool return from a falsy one isn't possible, so that reading is only approximated.