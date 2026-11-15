I split spec.md into 11 requirements and wrote them to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run ("anchored 11 requirements") and wrote `requirements.yaml` with the computed line numbers.

**Requirements**
- **R-API-1 / R-API-2** (non_functional): the function must be fully implemented, not a stub, and keep the name `is_equal_to_sum_even` with one parameter `n`.
- **R-OUT-1** (guarantee): every call returns a bool (True or False). It doesn't raise, hang, or return some other type.
- **R-SUM-1 / R-SUM-2** (guarantee): return True if `n` is the sum of exactly 4 positive even numbers, and False otherwise.
- **R-DEF-1** (definition): a positive even number is 2k with k ≥ 1.
- **R-DEF-2** (definition): the sum has exactly four terms, and a value may repeat.
- **R-EX-1..3** (scenario): the examples 4 → False, 6 → False, 8 → True.
- **R-FR-1** (FRAME, guarantee): the frame rule F-ZERO, which says `result` is false unless `outcome` is 0. This matches `req: R-FR-1` in design.yaml.

**Ambiguities and contradictions flagged**
- **"positive"**: if it means non-negative (so 0 counts), it contradicts the examples, because 4 = 4+0+0+0 and 6 = 2+2+2+0 would give True. This is recorded on R-DEF-1 and on R-EX-1 and R-EX-2.
- **"exactly 4 positive even numbers"**: if the four numbers must be distinct, the smallest possible sum is 20, which contradicts 8 → True. This is recorded on R-DEF-2 and R-EX-3.
- **"Evaluate whether" / "== True" / "== False"**: these could mean returning the bool True or False, or any value that compares equal to it, such as 1 or 0. The adapter scores an int as outcome 2, so the choice matters. This is recorded on R-OUT-1 and all three examples.
- **"the given number n"**: the input range isn't stated. It could be non-negative integers, all integers, or non-integers too. This is recorded on R-OUT-1.

Under the readings that agree with the examples, the answer is True exactly when `n` is even and at least 8. I didn't add that as a requirement because the spec never states it.