I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and the `fcp explain` rendering of every item reads as I intended. I tried to brute-force check the arithmetic encodings (divisibility, primality, smallest and largest prime factor) against ground truth with a Python script, but the run needed approval and didn't happen. Those encodings rest only on the reasoning in the defs' comments; the script is in the scratchpad if you want to run it.

**Items: 11**
- **8 properties:**
  - n ≤ 1 still ends with a defined outcome.
  - A prime n returns n.
  - In scope (n > 1, not prime), the call returns an integer.
  - That integer divides n.
  - That integer is prime.
  - One convention is kept across all calls (R-FAC-3).
  - `candidate(13195)` returns 29.
  - `candidate(2048)` returns 2.
- **2 scenarios:** each example behaviour must be possible.
- **1 dont_care:** `factor` is free when n ≤ 1.
- **0 assumptions:** under the readings you gave, n > 1 and "not a prime" are not environment obligations. The value guarantees are scoped by their triggers instead.

R-FAC-3 is written as "either every in-scope call so far returned the smallest prime factor, or every one returned the largest." It uses one rigid `p` (2 to 65535) to say "no prime factor of n is larger than the returned one." I needed it because `%` only takes a constant divisor and a largest prime factor can exceed 255. The rigid's range is large, which may make runtime replay against code slow.

**Not formalized: 3**
- **R-GEN-1:** it's about the deliverable (complete the function), not a property of the calls.
- **R-ARG-1:** it's an interface definition, already realized by the input signal `n`.
- **R-FR-1:** covered by the frame item F-ZERO, which is added to every set.

**Decisions:** all four phrases you specified use your readings, with a note on every item they affect. The two unflagged-by-you phrases:
- **R-EX-1 ">>> candidate(13195) 29":** reading 2. I read the doctest literally, as a required output.
- **R-FAC-3 "smallest or largest (contradiction…)":** reading 2, because it's the only one consistent with your contradiction reading for R-EX-1.

**Problems in the specification**
1. **Contradiction.** "smallest or largest" allows the smallest-factor convention, but the doctest requires 13195 → 29, and 13195's smallest prime factor is 5. Combined with the one-convention reading, this rules out the smallest convention for every n. I kept both statements as written and recorded the conflict in the notes.
2. **Unobservable termination.** "End in a defined way" for n ≤ 1 can't be fully checked: the adapter reports "raised an exception" and "did not finish" as the same outcome (1). The trace can only check that the outcome is one of the defined codes 0–2.
3. **Return or raise is not fixed for n ≤ 1.** The reading says "for example raise an exception" but doesn't require it. So the outcome for n ≤ 1 is undetermined, and determinacy analysis will flag it. I didn't declare it a dont_care, because the reading says only the returned value is free.