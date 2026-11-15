I wrote 16 requirements to `requirements_draft.yaml`, and `fcp anchor` accepted every quote on the first run, writing `requirements.yaml`.

**The main finding is that all three examples contradict the stated rule.** The examples match a rule with True and False swapped (True only when the product is *not* a whole number):
- `simplify("1/5", "5/1") = False`, but the product is 1, a whole number.
- `simplify("1/6", "2/1") = True`, but the product is 1/3.
- `simplify("7/10", "10/2") = True`, but the product is 7/2.

I recorded each of these as an ambiguity on both sides: on the rule (R-RES-1 for the first, R-RES-2 for the other two) and on its example (R-EX-1 to R-EX-3). In every case, reading 1 trusts the sentence and reading 2 trusts the examples.

**Breakdown:**
- **Interface (R-IF-1, non_functional):** the function is `simplify(x, n)`.
- **Purpose (R-OP-1):** "simplify the expression x * n".
- **Result (R-RES-1..3):** returns True when the product is whole, returns False when it isn't, and returns a bool (no exception, no other type).
- **Inputs (R-IN-1..5, assumptions):** both arguments are strings, in the format `<numerator>/<denominator>`, with positive whole numbers, valid fractions and no zero denominator.
- **Invalid inputs (R-IN-6, dont_care):** behaviour is left open when the input assumptions are broken.
- **Examples (R-EX-1..3, scenarios).**
- **Frame rules (R-FR-1 F-ZERO, R-FR-2 F-CODE):** these use the IDs that `design.yaml` already refers to.

**Other ambiguities and tensions I flagged:**
- **"simplify" vs. returning a bool** (R-OP-1 ↔ R-RES-3): the opening sentence could mean the function must return the simplified product, which clashes with returning True/False.
- **"False otherwise" vs. "You can assume"** (R-RES-2 ↔ R-IN-6): it's unclear whether invalid inputs must return False or are unconstrained.
- **"positive" vs. "do not have zero as denominator"** (R-IN-3 ↔ R-IN-5): it's unclear whether a zero numerator is allowed.
- **"evaluates to"**: exact fraction arithmetic or floating point. These give different answers, e.g. 1/49 × 49/1 comes out just below 1 in floats. I didn't get to run Python to confirm that value; it's standard IEEE double behaviour.
- **Smaller ones:** what "whole number" covers (it makes no difference for valid inputs), the bool `True` vs. any truthy value, whether the format tolerates spaces or signs, whether leading zeros are allowed, and what counts as a "valid fraction".