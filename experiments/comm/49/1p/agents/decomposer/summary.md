I split spec.md into 6 requirements and wrote them to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run ("anchored 6 requirements") and wrote `requirements.yaml`.

The request is only a function signature plus a one-line docstring, "Return 2^n modulo.", which is cut off before it says what to take the modulo by.

| ID | Kind | Content |
|---|---|---|
| R-FR-1 (FRAME) | guarantee | F-ZERO: `result` is 0 unless `outcome` is 0 (the only frame rule in frame.md) |
| R-TASK-1 | non_functional | Deliver a complete `modp` and keep the given signature |
| R-SIG-1 | definition | The function is named `modp` and takes `n` then `p` |
| R-SIG-2 | assumption | Callers pass integers for `n` and `p` |
| R-RES-1 | guarantee | When p ≥ 1, it returns `(2**n) % p` |
| R-RES-2 | guarantee | When p = 0, the request doesn't define the behaviour |

**Ambiguities flagged:**
- **What the modulus is:** the docstring stops at "modulo". One reading is modulo `p`; the other is that the modulus is unstated, so the value isn't constrained. The signature declares `p` but the docstring never mentions it. I recorded that conflict on both R-SIG-1 and R-RES-1.
- **`2^n`:** it could mean 2 to the power n, or 2 XOR n (what `^` means in Python).
- **What value modulo returns:** either the least non-negative remainder (0 to p − 1) or any integer congruent to 2^n mod p.
- **Return type:** it's not stated whether the result must be an `int` or whether an equal float counts. The trace records a float as outcome 2.
- **p = 0:** the signature `p: int` allows zero, but 2^n modulo 0 is undefined. I recorded this on both R-SIG-2 and R-RES-2. The readings are:
  - raise `ZeroDivisionError` (outcome 1)
  - return 2^n unchanged (outcome 2 once 2^n exceeds 1,023)
  - don't care, if `p` is meant to be a positive modulus
- **Negative `n` or `p`:** flagged on R-SIG-2. These values can't appear in a trace, because frame.md excludes negative arguments.

The request has no examples, so there are no scenario requirements.