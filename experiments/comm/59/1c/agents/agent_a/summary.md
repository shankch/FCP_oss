I wrote `formal/agent_a.yaml`. It has 10 formal items, and `fcp lint` reports clean. I read back the `fcp explain` output and every item says what I meant it to.

**Items** (with design.yaml's `F-ZERO` frame item added automatically):
- **2 assumptions:** `RA-ENV-1` says the caller only passes n > 1. `RA-ENV-2` says the caller never passes a prime. For both I took reading 1: these are conditions on the caller, so any outcome is acceptable for other inputs.
- **4 properties for R-FN-1**, taking the wording literally (reading 1). The call returns an integer that fits (`outcome == 0`); that integer is prime; it divides n; and no prime that divides n is larger (one quantity `q` stands for every value 2..65535).
  - The IR only allows `%` by a constant, so primality is trial division by the constants 2..255. Divisibility splits in two: either the divisor is at most 255, or the value left after dividing it out is at most 255. That split covers every case because n ≤ 65,535.
  - I wrote a brute-force Python check of these definitions, but the command needed approval and didn't run. So they are checked by reasoning only, not by testing.
- **2 scenarios:** `RA-EX-1` is the 13195 → 5 example and `RA-EX-2` is 2048 → 2. I followed the requirements' `kind: scenario`; on deterministic code, covering the call is the same as running the doctest.
- **Decisions:** reading 1 for R-FN-1, R-ENV-1 and R-ENV-2, and reading 2 for R-EX-1, meaning the example's result of 5 is taken literally.

**Not formalized:**
- **R-IF-1:** it only says the deliverable is a complete function, which constrains no call's result.
- **R-IF-2:** it defines the interface, which the function and interface sections of design.yaml already capture.
- **R-FR-1:** it is the adapter's own rule, `covered_by: [F-ZERO]`, and frame.md says it need not be restated.

**Problems in the specification:**
- **The example contradicts the description.** 13195 = 5 · 7 · 13 · 29, so its largest prime factor is 29, but the doctest shows 5, which is the *smallest* prime factor. Following the rules, I took each statement literally and didn't patch either one. As a result, `RA-EX-1` cannot be reached alongside the R-FN-1 properties, and FCP should report it as a conflict. Code that returns 29 fails the example; code that returns 5 fails R-FN-1. The notes on `RA-FN-1-MAX` and `RA-EX-1` say this explicitly.
- **The 2048 → 2 example doesn't settle it.** 2048 = 2¹¹, so 2 is both the largest and the smallest prime factor.
- **Behaviour for n ≤ 1 and for prime n is unspecified.** The text says "Assume", so I treated both as conditions on the caller. The text doesn't say whether the function should reject those inputs, or return n itself for a prime n.