I wrote `formal/agent_b.yaml`. `fcp lint` reports clean, and the `fcp explain` output says what I meant for each item.

**Items (3, plus the adapter's frame item F-ZERO, which is added automatically):**
- **The model:** these are named expressions over `n`, not ghost state. The function keeps nothing between calls, so a ghost would carry the previous call's value into the next one. The expressions are `lr_cars = n`, `rl_cars = n`, `meets_per_pair = 1`, and `expected = lr_cars * rl_cars * meets_per_pair`, which works out to n·n.
- `RB-OUT-1-RET` (R-OUT-1): `outcome == 0` on every call. The largest answer, 1023·1023 = 1,046,529, fits the 20-bit `collisions` output, so every call must return an integer.
- `RB-OUT-1-VAL` (R-OUT-1): `collisions == expected` on every call.
- `RB-OUT-1-MAX` (R-OUT-1, scenario): a call with n = 1023 can return 1,046,529. This checks that the requirement fits both the output width and F-ZERO.

**Requirements left unformalized (10 of 11), each with a reason and the items that cover it:**
- **R-FN-1** is a requirement on the deliverable, not on behaviour. The only part a trace can check is that every call returns an integer, and `RB-OUT-1-RET` covers that.
- **R-FN-2, R-ROAD-1, R-CAR-1 to R-CAR-4, R-COL-1, R-COL-2** are definitions. They have no behaviour of their own; each one feeds one of the model expressions, so `RB-OUT-1-VAL` covers them (and `RET` as well for R-FN-2).
- **R-FR-1** is the adapter's frame rule, and F-ZERO already covers it. frame.md says it need not be restated.

**Readings recorded under `decisions` (reading 1 in all five cases):** the name `is_prime` is only a name; the left-to-right cars all start to the left of the others ("start out far" implies they get closer); "outputs" means the return value; and collisions are counted per pair, giving n·n.

**Problems in the specification:**
1. **The name contradicts the docstring.** `is_prime(n)` describes a collision count, not a primality test. Under reading 2 the function would return a bool, which conflicts with the docstring and with the 20-bit integer output.
2. **"Very far from each other" doesn't say which set is on which side.** If the sets could be moving apart, both 0 and n·n would be allowed answers.
3. **"Outputs" could mean printing**, which would leave the return value unspecified.
4. **Simultaneous meetings are left open.** If several cars meeting at one point and time count as one collision, the answer depends on starting positions that the spec never gives.
5. **Negative n is not defined by the spec.** It falls outside the trace, so this doesn't affect the formalization.