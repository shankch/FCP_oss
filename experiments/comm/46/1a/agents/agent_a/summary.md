I wrote `formal/agent_a.yaml`. `fcp lint` reports clean, and the `fcp explain` output matches what I intended for each item.

**7 properties:**
- **`RA-BASE-1`…`RA-BASE-4`:** for n = 0, 1, 2, 3 the call returns normally (`outcome == 0`) with result 0, 0, 2, 0.
- **`RA-REC-1` and `RA-REC-2`:** the recurrence, checked against earlier calls. It only applies when the four previous calls were n-1, n-2, n-3, n-4, in that order, and all returned values `result` can hold. Then this call's result must equal one of the 8 sign combinations of those four values. `outcome == 2` (a value `result` can't hold) is accepted only if some combination is negative or above 2^118 − 1.
- **`RA-FUN-1`:** every call returns: no exception and no timeout, so `outcome` is 0 or 2.

**Readings I took (all recorded under `decisions`):**
- **`+/-`:** reading 4, each sign chosen freely for every n. That is the plainest reading of ±; reading it as all '+' would be a repair.
- **Definition vs. examples:** the base values and the recurrence govern, so the three examples are wrong (reading 2 for each).
- **Other phrases:**
  - "n-th element": counting from 0.
  - `n: int`: any int.
  - "efficiently": no specific bound, only exponential time is ruled out.
  - "recursion": no recursion anywhere, helpers included.

**Not formalized:**
- **`R-TASK-1`, `R-NF-2`:** they're about the code itself, which a call trace can't show.
- **`R-NF-1`:** speed isn't visible either. The one visible consequence, that every call finishes, is part of `RA-FUN-1`.
- **`R-IF-1`:** the interface already guarantees it, since n is the only argument and is always 0–127 in the trace.
- **`R-DEF-1`:** it's the definition itself, so the base and recurrence items cover it.
- **`R-EX-1`…`R-EX-3`:** they contradict the definition. Under my reading the examples are wrong, so I pointed them at the base and recurrence items with the reason stated.
- **`R-FR-1`:** already covered by the frame rule F-ZERO.

**Problems in the specification:**
1. **The examples contradict the definition for every choice of signs.** From the base values, fib4(4) is ±2 and fib4(5) is −4, 0 or 4, never 2. The examples 2, 4, 6 only fit all '+' signs if fib4(4) = 0, which the definition can't produce. With all '+' you get 4, 8, 14.
2. **The values aren't pinned down.** With `+/-`, "the" sequence isn't unique, and some sign choices give negative elements. The trace can't hold a negative value (it shows as `outcome 2`), so any recurrence check that passes through one is lost.
3. **The recurrence check has a blind spot.** Calls don't remember anything, so fib4(n) for n ≥ 4 is only checked when the checker calls n-4 … n-1 just before n, as in an ascending sweep. A single call such as fib4(5) = 2 is not ruled out, so analyses that work from the specification alone won't see the conflict with the examples.
4. **The result width is tight.** By my estimate, all-'+' fib4(127) is about 2^117.5, so it just fits in the 118-bit `result`. I worked this out by hand because the Python check needed approval, so it isn't machine-checked.
5. **Minor:** the prompt misspells "Fibbonacci sequnece", which has no effect.