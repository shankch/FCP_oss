I wrote `formal/agent_b.yaml`. `fcp lint` reports clean, and `fcp explain` shows each item means what I intended. I couldn't test the model on actual calls: agents only get lint, explain and anchor, not `fcp monitor`. I checked the arithmetic by hand.

**Items: 5** (plus the frame rule F-ZERO, which the tool adds to every set)
- **Reference model:** `expected` is 2^n mod p, computed from `n` and `p`. The function keeps no state between calls, so a counter or phase would mean nothing here. `%` only accepts a constant divisor, so `expected` adds up one term for each possible modulus 1–1024, and exactly one term matches any p from 1 to 1023.
- **RB-RES-1-ret / RB-RES-1-val (R-RES-1):** when p ≥ 1, the call must return an integer (`outcome == 0`) and `result == expected`.
- **RB-SIG-2-p0 (R-SIG-2):** a scenario saying a call with p = 0 must be possible. No assumption is needed, because the trace's inputs are always integers.
- **RB-RES-2-outcome / RB-RES-2-result (R-RES-2):** both outputs are left free when p = 0.

**Readings chosen** (all recorded under `decisions`): reading 1 for every flagged phrase except R-RES-2 "modulo", where I took reading 3 (unconstrained).

**Left unformalized (3)**
- **R-FR-1:** this is the frame rule itself, so it's marked as covered by F-ZERO.
- **R-TASK-1:** a statement about the deliverable, not about any call.
- **R-SIG-1:** the function name and argument order are fixed by the adapter. Its one checkable point, that p is the modulus, is covered by RB-RES-1-val.

**Problems in the specification**
1. **The docstring is cut off:** "Return 2^n modulo." never says modulo what, and never mentions p. I took p as the modulus because the function is named modp and p has no other role. That fills a gap in the text, and the notes say so. The literal alternative leaves the result unconstrained.
2. **`2^n` is XOR in Python.** I read it as the power 2ⁿ, as the notation means in prose.
3. **p = 0 is never defined.** Python raises an exception, and one mathematical convention says x mod 0 = x. The text supports neither, so I left the answer free. This conflicts with reading "p: int" as any int: a p = 0 call is allowed, but nothing says what it should return. requirements.yaml also lists R-RES-2 as a guarantee even though its own text says the behaviour is undefined.
4. **Negative n or p is never addressed** (for negative n, 2^n isn't even an integer). Those calls can't appear in the trace, so this choice doesn't change any check.