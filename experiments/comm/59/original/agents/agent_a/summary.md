I wrote `formal/agent_a.yaml`. `fcp lint` reports no errors, and the `fcp explain` output says what I intended for every item.

**Items: 8, all prefixed `RA-`**
- **Assumptions (2):** `RA-ENV-1` (`n > 1`) and `RA-ENV-2` (`!n_prime`). Both are caller-only preconditions (reading 1): if `n` is 0, 1 or a prime, the function may do anything.
- **Properties (4):**
  - `RA-FN-1-OK`: when `n > 1` and `n` is not prime, the call returns an int (`outcome == 0`).
  - `RA-FN-1-VAL`: in the same case, `factor` is the largest prime factor of `n`.
  - `RA-EX-1-VAL` and `RA-EX-2-VAL`: calling with 13195 returns 29, and calling with 2048 returns 2. These go further than the "scenario" label, because a doctest says what the call returns, not just that it can happen. Both inputs meet the assumptions, so this agrees with R-FN-1.
- **Scenarios (2):** `RA-EX-1` and `RA-EX-2` cover the two doctest calls.
- **Decisions:** reading 1 for "Return" (must be a Python int; the doctests show `29` and `2`), for "Assume n > 1" and for "is not a prime".

No ghost state is used. FCP-PL has no division and `%` only accepts a constant divisor, so "largest prime factor" is built from quantified constants up to 255. This works because 65535 < 256², so any composite 16-bit number has a divisor of at most 255. A prime factor of 256 or more is detected as `n/q` for some `q` of at most 255, by checking that no `d·q` divides `n`. The YAML comments explain each step.

**Not verified:** the Python brute-force check of these definitions against a sieve for all 16-bit `n` was blocked by the permission prompt, so it never ran. I checked them by hand only, on the two doctests and on the edge cases 514 = 2·257, 256 and 257. If you allow `python3`, the script is ready at `scratchpad/check_defs.py`.

**Left unformalized (3)**
- **R-IF-1:** the function name and signature are fixed by the adapter and can't be seen in a trace of calls.
- **R-DEF-1:** a definition, carried by the defs and `covered_by: [RA-FN-1-VAL, RA-ENV-2]`.
- **R-FR-1:** this is the frame rule `F-ZERO`, which is added to every set and doesn't need restating (`covered_by: [F-ZERO]`).

**Problems in the specification**
- **Undefined behaviour outside the precondition:** nothing is said for `n` ≤ 1 or for a prime `n`. Requiring "not a prime" is unnecessary, since the largest prime factor of a prime is the prime itself. The precondition may just be there to excuse slow or wrong code on primes.
- **No return type:** the signature has no annotation, so whether returning 29.0 counts is decided only by the doctest output.
- **Assumptions can switch off later checks:** an assumption only protects properties while it has held on every earlier cycle. If one trace contains several calls and an invalid one (say `n = 0`) comes early, every later call would go unchecked. Since calls are independent, I also put the precondition into the trigger of the R-FN-1 properties, but that can't undo the global effect.
- **Doctests:** both are consistent with the definition (13195 = 5·7·13·29, 2048 = 2¹¹).