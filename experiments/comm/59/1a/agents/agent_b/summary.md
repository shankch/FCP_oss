I wrote `formal/agent_b.yaml`. `fcp lint` reports it clean. I read back the `fcp explain` output and every item means what I intended.

**Items: 12**, plus the frame rule F-ZERO, which the tool adds to every set.
- **2 assumptions:** `n > 1` (R-ENV-1) and `!n_prime` (R-ENV-2).
- **4 properties:** R-RET-1, R-FAC-1, R-FAC-2 and R-FAC-3. Each applies only when n > 1 and n is not prime. FAC-1/2/3 also apply only to calls that returned an integer, so they stay separate from RET-1.
- **2 scenarios:** `candidate(13195)` returns 29 (R-EX-1), and `candidate(2048)` returns 2 (R-EX-2).
- **4 dont_cares:** `outcome` and `factor` are free when n ≤ 1 and when n is prime.
- **Model:** the function keeps no state between calls, so there is no ghost state. Instead, named expressions compute from n alone whether it is prime, its smallest prime factor (`spf`), its largest prime factor up to 251 (`lpf_small`), and whether it has a prime factor of 256 or more (`big_pf`). Every output is checked against these.
- **Decisions:** all six flagged phrases take reading 1:
  - Inputs with n ≤ 1 or a prime n are entirely unconstrained.
  - Smallest and largest are both allowed, independently on each call.
  - The 13195 → 29 example is an illustration, not a required output, and doesn't contradict "smallest or largest".

**Left unformalized (2):**
- **R-GEN-1:** "complete this function" isn't a property of the trace; a missing function would just show as an exception on every call.
- **R-ARG-1:** this only defines the interface; the single argument is the input signal `n`.
- R-FR-1 is covered by the frame rule F-ZERO, which frame.md says not to restate.

**Verification gap:** I couldn't run Python here, so I didn't compare the number-theory expressions against brute force for all 65,536 values of n. I checked them by hand instead. `fcp check` isn't available to agents, so no engine has run on the set yet. The unrun script is in the session scratchpad as `check_defs.py`, if you want to run it.

**Problems in the specification:**
1. **"Smallest or largest" vs. the example.** The example returns 29, the largest prime factor of 13195. The text also allows the smallest (5). So for any n with two or more distinct prime factors, the answer isn't determined, and a determinacy analysis will report it.
2. **The example as a scenario conflicts with implementations that return the smallest.** A scenario means "this must be possible". A function that always returns the smallest prime factor obeys R-FAC-3 under my reading, yet can never produce 13195 → 29. For that reason I did not add a matching "13195 → 5" scenario: any single deterministic implementation would then fail one of the two.
3. **Precondition holes.** A prime n has an obvious correct answer (n itself), and n ≤ 1 has none, but the prompt says nothing about either. Both are left free.
4. **Earlier bad calls may hide later failures.** If the checker treats an assumption broken by one call (say n = 0) as lifting all later obligations, that call would hide failures in every later call. To keep each call's check independent, I also added the n > 1 / not-prime condition to every property.
5. **The largest-prime-factor test is large.** The rules allow no division and no `%` by a variable, so "largest prime factor" needs `big_pf`: a double quantifier of about 14,000 remainder-by-constant terms. Lint and explain handle it in about 3 s; I don't know how the solver-based analyses will cope.
6. **Limited range.** The trace only covers n from 0 to 65,535, so "for every n" is only checked in that range.