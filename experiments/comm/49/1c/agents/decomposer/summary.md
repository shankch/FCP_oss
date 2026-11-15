I wrote `requirements_draft.yaml` with 10 requirements. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`.

**The requirements**
- **R-IF-1** (definition): the function is `modp(n: int, p: int)`.
- **R-IF-2** (non_functional): "Complete this function", meaning keep the given name and parameters and supply the body.
- **R-RET-1** (guarantee): return (2^n) mod p.
- **R-NUM-1** (non_functional): "be aware of numerics".
- **R-EX-1 to R-EX-5** (scenarios): the five docstring examples.
- **R-FR-1** (FRAME, guarantee): F-ZERO, `result` is 0 unless `outcome` is 0. It matches `req: R-FR-1` in `design.yaml`.

**Ambiguities and contradictions flagged**
- **Every example contradicts the formula.** Each example's expected answer is p itself, but 2^n mod p is always less than p. The correct values are 3, 2, 1, 8 and 1, against the stated 5, 101, 101, 11 and 101. I recorded this on R-RET-1 ("the formula governs" vs. "the examples govern") and on each of R-EX-1 to R-EX-5 ("the example is authoritative" vs. "the example is an error").
- **"2^n"** could mean exponentiation, or the Python expression `2 ^ n`, which is bitwise XOR. The examples don't match the XOR reading either.
- **"modulo p" when p = 0**: the request doesn't say what should happen, and the trace includes p = 0. The readings are "don't care", "raises an exception (ZeroDivisionError)", or "returns some integer".
- **"be aware of numerics"** could mean the result must be an exact integer, or that the code should be efficient (modular exponentiation), or it's just a general caution with nothing to check.

The main problem is that the examples and the formula can't both be right. Whoever writes the formalization will need to decide which one to follow.