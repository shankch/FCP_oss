I wrote `formal/agent_b.yaml`. `fcp lint` reports no errors, and the `fcp explain` output matches what I meant for every item.

**Items: 9 written by me, plus the adapter's frame rule F-ZERO**
- **Reference model (defs):** `in_domain = p >= 1` and `want = sum(k < 127: p == k + 1 ? (1 << n) % (k + 1) : 0)`. Each call is independent and keeps no state, so the model is a calculation on the current arguments rather than a ghost register. FCP-PL only allows `%` with a constant divisor, so `want` picks one term per possible value of p (1 to 127), each an exact `2**n % (k+1)`.
- **2 properties (R-RET-1):** when p ≥ 1, `outcome == 0` (the call returns an integer) and `result == want`.
- **2 don't-cares (R-RET-1):** `outcome` and `result` are left free when p = 0.
- **5 scenarios (R-EX-1 to R-EX-5):** each docstring example, taken literally as "this call returns this value".
- **Decisions:** reading 1 for "2^n" (power, not XOR), "modulo p" (p = 0 is a don't-care), "Return 2^n modulo p" (the formula governs) and all five examples (the example is authoritative). Reading 3 for "be aware of numerics" (a general caution).

**Requirements left unformalized**
- **R-IF-1 and R-IF-2:** the function's name and parameters, and the instruction to complete it. Neither says anything about what a call returns; the adapter's `function` section covers them.
- **R-NUM-1:** covered by the two R-RET-1 properties. Its only checkable effect, an exact integer result, is already required: a float return counts as outcome 2, and the result must equal `2**n % p` exactly. The efficiency sense can't be seen in the trace, except as "did not finish", which the outcome property already forbids.
- **R-FR-1:** covered by F-ZERO. frame.md says frame rules are added to every set and need not be restated.

**Problems in the specification**
1. **The examples contradict the formula.** Every docstring example returns `p` itself. A remainder modulo p is always below p, so no example can hold if the formula does. Under the formula the answers would be 3, 2, 1, 8 and 1, which are the original HumanEval values. I kept both sides literally, so the set is inconsistent on purpose: all five scenarios are unreachable under the `result == want` property. FCP's consistency check should report each scenario conflicting with that property. Each item's note says so.
2. **p = 0 is not specified.** The text doesn't define "modulo 0", but the adapter includes p = 0 in the trace. I left both outputs free there; I did not add an assumption that callers avoid p = 0.
3. **"2^n" is ambiguous inside Python code**, where `^` means XOR. None of the examples fits the XOR reading either.

**Possible cost in later analyses:** `1 << n` builds numbers up to 2^2047. That passes lint and is cheap when checking the code with Python integers, but the solver-based spec-only analyses may be slow on it.