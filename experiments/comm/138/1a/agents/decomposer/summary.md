I wrote `requirements_draft.yaml` and ran `fcp anchor`, which accepted all 9 quotes on the first run and wrote `requirements.yaml`.

**Requirements**
- **R-IF-1, R-IF-2** (non_functional): the code must be a complete implementation, not a stub, of a function named `candidate` that takes one parameter, `n`.
- **R-IN-1** (assumption): `n` is "the given number". It's ambiguous whether that means a non-negative integer, any integer, or any real number.
- **R-FN-1** (guarantee): for every `n`, the function finishes without raising and returns a boolean. It's ambiguous whether it must be the bool type or just a value equal to `True`/`False`, such as `1`/`0`.
- **R-FN-2** (guarantee): returns `True` exactly when `n` "can be written as the sum of 4 numbers", otherwise `False`.
- **R-EX-1/2/3** (scenario): `candidate(4)` and `candidate(6)` return False, and `candidate(8)` returns True.
- **R-FR-1** (FRAME, guarantee): rule F-ZERO, "`result` is false unless `outcome` is 0".

**Ambiguities and contradictions**
- **What kind of numbers:** "4 numbers" doesn't say. The readings lead to different answers:
  - any integers, or non-negative integers: always True
  - positive integers: True when `n` ≥ 4
  - positive even numbers: True when `n` is even and ≥ 8
  - integers of at least 2, or primes: True when `n` ≥ 8
  - distinct positive integers: True when `n` ≥ 10
- **How many summands:** it could mean exactly four or at least four.
- **The examples contradict the most literal readings.** If the numbers can be any positive or non-negative integers, then 4 = 1+1+1+1 and 6 = 1+1+2+2, which goes against `candidate(4) == False` and `candidate(6) == False`. I recorded this on R-FN-2, R-EX-1 and R-EX-2.
- **Distinct summands would contradict the third example.** If the four numbers must differ, the smallest possible sum is 10, so `candidate(8) == True` would be wrong. I recorded this on R-FN-2 and R-EX-3.
- Only three readings fit all three examples: four positive even numbers (even `n` ≥ 8), four integers of at least 2, or four primes (both of those give `n` ≥ 8). The first two differ only on odd `n` from 9 up.

The prompt looks like a cut-down version of a known benchmark task, `is_equal_to_sum_even`, which asks for exactly 4 positive even numbers. I listed that only as one of the readings and didn't treat it as the intended meaning.