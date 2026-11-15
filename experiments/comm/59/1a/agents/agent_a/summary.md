I wrote `formal/agent_a.yaml`. `fcp lint` reports it clean, and the `fcp explain` rendering of every item matches what I intended. The number-theory definitions are only checked by hand: `fcp check` isn't available to agents, and Python and awk needed approval, so I couldn't brute-force them.

**Items: 12** (plus the frame rule F-ZERO, which is added to every set automatically)
- **6 properties:** RA-RET-1, RA-FAC-1, RA-FAC-2, RA-FAC-3, RA-EX-1, RA-EX-2. Each guarantee applies only to calls where n > 1 and n is not prime. FAC-1/2/3 also apply only when the call returned an integer, so a call that raises counts against R-RET-1 alone.
- **2 scenarios:** the two examples, candidate(13195) → 29 and candidate(2048) → 2, must be possible.
- **4 don't-cares:** `outcome` and `factor` are free when n ≤ 1 (R-ENV-1) and when n is prime (R-ENV-2).
- **6 decisions** recorded. I took reading 1 for "Assume n > 1", "is not a prime", "the smallest or largest prime factor" and R-EX-1's second phrase. I took reading 2 for R-FAC-3's contradiction phrase and for the doctest `>>> candidate(13195) 29`. Taken literally, the doctest says what that call returns, so I made it a required output.

**Left unformalized**
- **R-GEN-1:** it describes the deliverable, not behaviour across calls.
- **R-ARG-1:** it only defines the interface (the input signal `n`).
- **R-FR-1:** covered by F-ZERO.

**Encoding choices you should know about**
- **Domain rules as don't-cares, not assumptions.** frame.md lets the checker call any n in any order. Under the IR's rules, one failed assumption would switch off the guarantees for every later call too. The requirement only limits the guarantees to calls with n > 1, so a per-call condition fits it better. Each note explains this.
- **Divisibility built from literal tests.** FCP-PL only allows `%` by a literal number, so `n % factor` and even `n % d` inside a quantifier are rejected. I used three workarounds:
  - a 255-bit table of which numbers c ≤ 255 divide n;
  - `q * factor == n` with q ≤ 255;
  - a test for "n has a prime factor above 255", which compares how many small prime factors (with repeats) n has against a divisor s ≤ 255.

  Each relies on n < 256², so in any n = a·b one of a, b is at most 255. I argued all of them hand-checked as exact over 0..65535; the definitions are long but generated mechanically.

**Problems in the specification**
1. **The example contradicts the rule.** "Smallest or largest" allows 5 for 13195, but the doctest requires 29. In this set the doctest wins, for n = 13195 only.
2. **Most answers aren't determined.** Any composite n that isn't a prime power has two allowed answers, and no convention picks one.
3. **Edge inputs are unspecified.** Nothing says what happens for n ≤ 1 or prime n, even though the checker will call them. Another reading would require prime n to return n itself.