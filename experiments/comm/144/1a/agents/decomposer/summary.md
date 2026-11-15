I've written `requirements_draft.yaml` with 13 requirements, and `fcp anchor` accepted every quote on the first run, so `requirements.yaml` is written with line ranges filled in.

**What it contains**
- **Function (R-FN-1 to 3):** the `simplify(a, b)` signature; that the docstring's x and n are the arguments a and b; and the stated task, "simplify the expression x * n, or x + n".
- **Inputs, all assumptions (R-IN-1 to 4):** each argument is a `<numerator>/<denominator>` string; numerator and denominator are positive whole numbers; the arguments are valid fractions; no zero denominator.
- **Result, both guarantees (R-RES-1, R-RES-2):** it returns True when the expression is a whole number, and False otherwise.
- **Examples (R-EX-1 to 3):** the three docstring examples, as scenarios.
- **Frame (R-FR-1):** F-ZERO, which says `result` is false unless `outcome` is 0.

**Ambiguities and contradictions flagged**
1. **"x * n or x + n" (R-FN-3, R-RES-1, R-RES-2, R-EX-1):** I listed four readings: product only, sum only, either one, or both. The "sum only" and "both" readings contradict example 1: 1/5 + 5/1 = 26/5 is not whole, yet the expected answer is True. That contradiction is recorded on both sides. All three examples fit "product only" and "either one".
2. **"simplify the expression" vs. returning True or False (R-FN-3 vs. R-RES-1/2):** "simplify" suggests the function returns a simplified fraction, which conflicts with returning a bool. Recorded on both sides.
3. **"positive whole numbers" vs. "do not have zero as denominator" (R-IN-2 vs. R-IN-4):** the second statement is unnecessary if both parts are positive, which hints that a numerator of 0 might be allowed. Recorded on both.
4. **Smaller ones:**
   - Whether "whole number" includes 0.
   - Whether "evaluates" means exact arithmetic or floating point.
   - Whether leading zeros are allowed in the format.
   - How broad "valid fractions" is.
   - How x and n map to a and b. This doesn't change the answer, because * and + give the same result in either order.