I've written `formal/variant.yaml`. It has 7 items: 5 properties and 2 scenarios. `fcp lint` reports clean, and the `fcp explain` output reads as intended. I also tried to run a brute-force check that the `RV-FN-1` formula picks out exactly the smallest prime factor for every 16-bit `n`, but the command needed approval and didn't run. That formula has only been checked by hand.

**Items**
- **`RV-FN-1` (R-FN-1, reading 2 as you instructed):** for n ≥ 2, the call returns the smallest number ≥ 2 that divides n, which is always prime. The `%` operator only takes constant divisors, so the formula tests divisors 2..255 one by one. That is enough because 65,535 < 256², so any composite n has a divisor of at most 255. Prime n is included, since R-ENV-1 and R-ENV-2 are no longer conditions on the caller.
- **`RV-ENV-1` (R-ENV-1, reading 2 as you instructed):** n ≤ 1 → outcome 1. This is a guarantee rather than an assumption, so the set has no assumptions. The adapter gives "raised an exception" and "did not finish" the same outcome, 1, and names no exception, so the property can't tell those apart or require a particular exception.
- **`RV-ENV-2` (R-ENV-2, reading 2 as you instructed):** for prime n, the call returns n.
- **`RV-EX-1` + scenario `RV-EX-1-S` (R-EX-1, reading 1 as you instructed):** the call with 13195 returns 29.
- **`RV-EX-2` + scenario `RV-EX-2-S`:** the call with 2048 returns 2.
- **Decisions** are recorded for all four flagged phrases (2, 2, 2, 1). Each affected item's `note` says the reading came from your instructions.

**Unformalized (3)**
- **R-IF-1:** it describes the deliverable, not how a call behaves. Marked as covered by `RV-FN-1` and `RV-ENV-1`.
- **R-IF-2:** the function name and argument are already fixed by the `function` section of `design.yaml`.
- **R-FR-1:** it is the adapter's frame rule F-ZERO, which is part of every set automatically. Marked as covered by `F-ZERO`.

**Problems**
- **The instructed readings contradict each other at n = 13195.** Reading R-FN-1 as "smallest prime factor" makes `RV-FN-1` require 5. Reading R-EX-1 as "the example is wrong" makes `RV-EX-1` require 29. That second reading's own reasoning only works if "largest" means largest. I formalized both as instructed and didn't resolve the conflict, so the set has no valid answer at n = 13195, and `RV-EX-1-S` should come out unreachable. Both notes say this.
- **The spec contradicts itself.** It says "largest prime factor", but its first example (13195 → 5) gives the smallest; 2048 → 2 fits either meaning. "Assume n > 1 and is not a prime" also leaves open what should happen for n ≤ 1 or a prime n.