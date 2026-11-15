I wrote `formal/agent_a.yaml`. `fcp lint` reports it clean, and the `fcp explain` output matches what each item is meant to say. I did not run `fcp check`, so I haven't confirmed that the tool actually reports the conflict described below.

**Items: 9** (the frame rule F-ZERO is added automatically on top of these)
- **Two properties for R-RET-1:**
  - RA-RET-1: when p ≠ 0, the call returns an integer (`outcome == 0`).
  - RA-RET-2: when p ≠ 0, `result == pow2n_mod_p`. FCP-PL's `%` only accepts a constant divisor, so the def picks among the constant divisors 1–127: `sum(k < 127: p == k + 1 ? (1 << n) % (k + 1) : 0)`. It uses only the base language, with no ghost state.
- **Two don't-cares for R-RET-1** (RA-RET-3, RA-RET-4): `result` and `outcome` are left free when p = 0.
- **Five scenarios** (RA-EX-1 to RA-EX-5): each docstring call returns exactly what the docstring shows, for example `n==3 && p==5 && outcome==0 && result==5`.

**Readings recorded under `decisions`:** reading 1 for every flagged phrase.
- "2^n" means 2 to the power n, not Python's XOR.
- "modulo p": the text says nothing about p = 0, so that case is left unconstrained.
- "Return 2^n modulo p": the formula applies to every call.
- "be aware of numerics" means the result must be exact.
- Each docstring example counts as written.

**Not formalized:**
- **R-IF-1:** it only defines the interface, which the adapter's function section already provides.
- **R-IF-2:** it's about the form of the code, not about trace values.
- **R-NUM-1:** RA-RET-1 and RA-RET-2 already cover it, since an exact integer result is required for every p ≥ 1. Reading it as an efficiency hint would add nothing observable for n ≤ 2047.
- **R-FR-1:** the frame rule F-ZERO covers it, and frame.md says it doesn't need restating.

**Problems in the specification:**
1. **Every docstring example contradicts the formula.** Each one returns p, but a remainder modulo p is always less than p. The correct values are 3, 2, 1, 8 and 1. I kept both statements as written rather than repairing either. As a result, all five scenarios are unreachable under RA-RET-2, and the consistency check should report that conflict. In practice, no implementation can satisfy both the formula and the examples.
2. **p = 0 is in the checked range** (the frame allows p from 0 to 127), but the spec doesn't say what should happen for it.
3. **"2^n" is XOR in Python syntax**, which is confusing inside a Python docstring. Read as XOR, the examples still don't fit.
4. **"(be aware of numerics)" is vague.** It sets no checkable obligation of its own.
5. **Possible analysis cost:** `1 << n` can be as large as 2^2047, and RA-RET-2 takes it modulo 127 different constants. Running the property against actual code should be cheap, but the analyses that work only from the spec may be slow.