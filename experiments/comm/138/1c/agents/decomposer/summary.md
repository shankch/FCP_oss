I wrote 8 requirements to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run and produced `requirements.yaml` ("anchored 8 requirements").

**Requirements**
- **R-IF-1** (non_functional): the deliverable is a Python function `is_equal_to_sum_even(n)`.
- **R-RET-1** (guarantee): every call finishes and returns True or False, with no exception and no other type.
- **R-SUM-1 / R-SUM-2** (guarantee): the function returns True if n can be written as the sum of exactly 4 positive even numbers, and False if it can't. These are split so each direction can be checked separately.
- **R-EX-1..3** (scenario): the three examples, `f(4)==True`, `f(6)==True` and `f(8)==False`.
- **R-FR-1** (FRAME, guarantee): F-ZERO, "`result` is false unless `outcome` is 0". This is the ID that `design.yaml` already refers to.

**Contradictions, each recorded as an ambiguity on both requirements in the pair**
- The examples conflict with the description. The smallest possible sum is 2+2+2+2 = 8. So 4 and 6 should give False, which contradicts R-EX-1 and R-EX-2 against R-SUM-2. And 8 should give True, which contradicts R-EX-3 against R-SUM-1.
- I recorded two readings for each pair: either the description is right and the example is wrong, or the description is inverted. Under the inverted reading the function returns True when n *cannot* be written that way, and that is the only reading that fits all three examples.

**Other ambiguities**
- **"exactly 4 positive even numbers"** (R-SUM-1/2): if the numbers may repeat, the valid n are the even numbers from 8 up. If they must be different, the valid n are the even numbers from 20 up. Under the different-numbers reading, R-EX-3 (`f(8)==False`) no longer conflicts, but R-EX-1 and R-EX-2 still do.
- **"Evaluate whether"** (R-RET-1): this may require a real Python True/False, or accept any value equal to them, such as 1 or 0. The examples only test `== True` and `== False`, so they can't tell the two apart.