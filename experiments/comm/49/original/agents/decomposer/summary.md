I wrote 11 requirements to `requirements_draft.yaml`, and `fcp anchor` accepted every quote on the first run, writing `requirements.yaml`. I spot-checked the line numbers on the examples and the frame rule, and they point to the right source lines.

**Requirements**
- **R-TASK-1** (non_functional): write a complete body for `modp`.
- **R-SIG-1** (definition): the function is `modp(n: int, p: int)`.
- **R-RES-1** (guarantee): for p ≥ 1, it returns 2ⁿ mod p, meaning the value r with 0 ≤ r < p.
- **R-RES-2** (dont_care): the prompt doesn't say what happens when p = 0, because "modulo 0" is undefined.
- **R-NUM-1** (non_functional): "be aware of numerics".
- **R-EX-1…5** (scenario): the five doctests. Each quote spans the `>>>` line and its output line. All five agree with 2ⁿ mod p.
- **R-FR-1** (FRAME, guarantee): F-ZERO, which says `result` is 0 unless `outcome` is 0.

**Ambiguities flagged**
- **"2^n"** (R-RES-1): it could mean 2 to the power n, or 2 XOR n, which is what `^` means in Python. The XOR reading contradicts four of the five examples.
- **"modulo p" when n = 0 and p = 1**: this is a contradiction, so it's recorded on both R-RES-1 and R-EX-3.
  - If the result is always reduced, `modp(0, 1)` is 0.
  - If you treat the example `modp(0, 101) = 1` as meaning "n = 0 always gives 1", `modp(0, 1)` is 1. A common loop that starts at 1 and only reduces when it multiplies gives that answer too.
- **"Return"** (R-RES-1): the result must be an `int`, or a float like `3.0` might also be acceptable.
- **p = 0** (R-RES-2): three readings:
  - anything is acceptable;
  - the call must raise an exception, as Python's `%` and `pow` do;
  - it returns 2ⁿ unreduced.
- **"be aware of numerics"** (R-NUM-1): three readings:
  - be efficient: a call that never finishes counts as outcome 1;
  - use exact integers, not floating point;
  - guard against overflow, which Python integers can't have, so this reading changes nothing you can observe.