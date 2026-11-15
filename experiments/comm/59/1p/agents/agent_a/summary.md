I wrote `formal/agent_a.yaml`. `fcp lint` reports `lint: clean`, and I read the `fcp explain` output back: every item says what I meant it to.

**Items: 9 in total.** There are 2 assumptions, 4 properties, 1 scenario and 2 don't-cares. F-ZERO from the frame is added to the set automatically.
- **RA-ENV-1 / RA-ENV-2 (assumptions):** every call has `n > 1` and an `n` that is not prime.
- **RA-RET-1:** for any valid `n`, the call returns an integer (outcome 0).
- **RA-RET-2 and RA-RET-3:** when the call returns, `factor` divides `n` and is prime.
- **RA-RET-4:** when `n` is a prime raised to a power of 2 or more (`p^k`), `factor` must be `p`.
- **RA-ENV-2-S1 (scenario):** a call such as `n = 6`, which has several distinct prime factors, must be possible.
- **RA-ENV-3-OUTCOME / RA-ENV-3-FACTOR (don't-cares):** both outputs are left free when `n <= 1` or `n` is prime.
- **Encoding:** primality and divisibility are written as trial division by 2 to 255. That is exact for 16-bit values because 256² > 65535, and it avoids dividing by a signal, which the IR doesn't allow. "n = p^k" is written as membership in a list of all 92 such values up to 65,535.
- **Not machine-checked:** I worked out the 92-value list by hand. The Python script that would have checked it against brute force, and also checked the trial-division formulas, needed approval and didn't run. It's in the scratchpad as `pp.py` if you want to run it.

**Readings taken (`decisions`):**
- "is not a prime": reading 1, any composite `n`.
- "Assume": reading 1, a pure precondition.
- "Return": reading 1, the result must be a Python int.
- "the prime factor": reading 4, the unique prime factor, which is the literal sense of "the".

**Left unformalized (3):**
- **R-IF-1:** naming and interface only. The function section of design.yaml covers it; it isn't a property of the trace.
- **R-DEF-1:** a definition. The `n_prime` and `f_prime` defs carry it, and it lists the items that use them under `covered_by`.
- **R-FR-1:** already in the frame as F-ZERO, which frame.md says need not be restated.

**Problems in the specification:**
1. **"The prime factor" contradicts "is not a prime".** Read literally, the first phrase assumes `n` has only one prime factor. The second admits numbers like 6 = 2·3, for which "the prime factor" points to nothing. I didn't resolve this: RA-RET-4 says nothing about such `n`, no assumption excludes them, and RA-RET-1 to RA-RET-3 still apply. The prompt reads as if a word such as "largest" or "smallest" is missing, but the text supports neither, so I chose neither.
2. **Nothing says which prime factor to return** when there are several. So the output isn't fully determined for those `n`, and different correct implementations can return different values.
3. **"Assume" leaves `n <= 1` and prime `n` completely unconstrained**, including raising an exception or not finishing. It is also unclear whether a prime `n` should simply return itself.
4. **The return type is unclear.** Under the loose reading of "Return", a float such as 3.0 would count, but the trace records it only as outcome 2 and its value can't be seen.