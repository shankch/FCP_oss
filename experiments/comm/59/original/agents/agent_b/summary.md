I wrote `formal/agent_b.yaml`. `fcp lint` reports clean, and the `fcp explain` output matches what I meant for every item.

**Items (8):**
- **2 assumptions:** `n > 1` (RB-ENV-1, for R-ENV-1) and "n is not prime" (RB-ENV-2, for R-ENV-2).
- **4 properties:**
  - RB-FN-1-RET: a call with a valid n returns normally (`outcome == 0`).
  - RB-FN-1-VAL: the returned value equals the model's largest prime factor.
  - RB-EX-1-P and RB-EX-2-P: the two docstring examples as checks that always hold (13195 → 29, 2048 → 2).
- **2 scenarios:** RB-EX-1 and RB-EX-2, the same two examples as reachable behaviours (R-EX-1, R-EX-2 are scenario-kind requirements).
- **Model:** the function keeps no state between calls, so there is nothing for ghost state to track. Instead the model is a set of defs computed from `n` (`primes`, `n_prime`, `cq`, `small_lpf`, `lpf_ok`), and the outputs are checked against them.
  - `%` only accepts constant divisors, so the model uses two facts about 16-bit numbers. Every composite n ≤ 65535 has a prime factor ≤ 251. And since 257² > 65535, n has at most one prime factor above 255.
  - If n has such a factor, the answer is n/cq for a unique cq ≤ 255, written as `factor * cq == n`. Otherwise the answer is the largest of the 54 primes below 256 that divides n.

**Not verified by running:** running Python needed approval, so I couldn't do the exhaustive check over all 65,536 values of n. The model rests on a written argument (in the file's comments) and hand checks of edge cases: 514, 65535, 53841 = 3·131·137, 63001 = 251², 65522 = 2·181², and both examples. The example properties will also show up as a conflict if the model is wrong at those two inputs.

**Left unformalized (3):**
- **R-IF-1:** the function's name and parameter are how the adapter binds to the code, not something visible in the trace of calls.
- **R-DEF-1:** a definition; covered by the defs and by RB-FN-1-VAL and RB-ENV-2.
- **R-FR-1:** already in every set as frame rule F-ZERO, and frame.md says not to restate it.

**Decisions:** I took reading 1 for all three flagged phrases:
- "Return": the value must be an int. The docstring examples expect `29` and `2`, which a float like `29.0` would not match.
- "Assume n > 1": a precondition only; anything goes for n ≤ 1.
- "is not a prime": a precondition only; anything goes for prime n.

**Problems in the specification and frame:**
1. **Behaviour outside the precondition is undefined.** For n ≤ 1 and for prime n, nothing is said. Excluding primes is odd, because their largest prime factor (n itself) is well defined.
2. **No return type.** The signature has no annotation; only the docstring examples suggest an int.
3. **The frame can't tell "raised" from "hung".** Outcome 1 means both "raised an exception" and "did not finish". So the other readings of R-ENV-1 ("must raise", "must finish") can't be stated exactly on this trace.
4. **One call outside the precondition switches off checking for the rest of its trace.** That is how assumptions work in FCP. I repeated the precondition as the trigger in RB-FN-1-RET and RB-FN-1-VAL, but the assumptions still apply. If the code checker runs n = 0, 1, 2, … as one long trace, everything after n = 0 would go unchecked. Whether it does depends on the tool, which I couldn't check.
5. **The model only works for 16-bit n.** It depends on n ≤ 65535, the limit frame.md sets, so it must be redone if that width changes.