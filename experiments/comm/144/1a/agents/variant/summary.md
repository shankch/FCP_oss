I wrote `formal/variant.yaml`. `fcp lint` reports clean, and the `fcp explain` rendering matches what I intended for every item. As instructed, the set is contradictory: on every valid call one item requires a non-bool return and others require a bool.

**Items:** 13 formal items, 3 entries under `unformalized`, and 14 `decisions`.
- **Assumptions:**
  - `RV-IN-1`: exactly one `/`, with something on each side.
  - `RV-IN-2`: every other character is a digit, and 0 is allowed.
  - `RV-IN-3`: the broader "denotes a fraction" form, which allows digits, spaces and at most one `/`.
  - `RV-IN-4`: the denominator contains a non-zero digit. Leading zeros are allowed.
- **Properties:**
  - `RV-FN-3`: on valid arguments, the function returns a value that is not a bool (outcome 2). This is the "must produce the simplified expression" reading.
  - `RV-RES-1` / `RV-RES-2`: return True or False depending on whether the floating-point value of the product x·n is a whole number.
  - `RV-EX-1..3`: the three docstring calls return the stated values.
- **Scenarios:** `RV-EX-1-S..3-S`, one per example.

Every item affected by one of the readings you gave says so in its `note`; the two `covered_by` entries say so in their `reason`. The decisions follow your list: reading 1 for "x * n, or x + n" and reading 2 for every other phrase.

**How "evaluates" (floating point) is modelled:** the reading doesn't say which float calculation is meant, so I took one double-precision division of the exact numerator product by the exact denominator product, which is what Python's `P / Q` does on integers. I worked out the whole-number test by hand and expressed it in integer arithmetic, using a rigid `m` for the integer part of the quotient. Where this differs from exact arithmetic, for example: `("99999999999999/1", "99/2")` gives 4949999999999950.5, which rounds to a whole double, so True is required. Other float calculations, such as `float(x) * float(n)`, would round differently (`1/49*49` gives 0.9999999999999999).

**The model is not tested:** I wrote a script comparing it with Python's actual division on about 300,000 calls, but the run needed approval and didn't go ahead. It's in the scratchpad (`chk.py`) if you want to run it.

**Engine cost:** the rigid ranges up to 2⁵², and the arithmetic reaches about 145 bits. That may be heavy for the engines or for replaying every rigid value.

**Not formalized:**
- **R-FN-1:** it's about the shape of the code (a function named `simplify` with two parameters), not about call results. The adapter already calls `simplify(a, b)` by that name.
- **R-FN-2:** `covered_by` `RV-RES-1`, `RV-RES-2` and `RV-FN-3`. Under the reading taken, x and n aren't tied to a and b. Only the product is used, and it is the same either way round, so no mapping is needed.
- **R-FR-1:** `covered_by` the frame rule `F-ZERO`, which frame.md says applies to every set and need not be restated.

**Problems in the specification:**
- **The set contradicts itself on every valid call:** "simplify the expression" (the function must produce the expression) conflicts with "returns True … False otherwise". I kept both and didn't repair either, so `RV-FN-3` conflicts with `RV-RES-1/2` and `RV-EX-*`. The three example scenarios should come out unreachable under the full set.
- **"x * n, or x + n":** it's unclear whether the product, the sum, either or both is meant. The examples only fit "product decides" or "either one is enough": 1/5 + 5/1 = 26/5 is not whole, yet the expected answer is True.
- **"positive whole numbers" vs "do not have zero as denominator":** the separate zero-denominator clause suggests a numerator of 0 is possible. Under the readings taken, 0 is allowed and gives True.
- **x and n vs a and b:** the docstring talks about x and n, but the parameters are named a and b.
- **"valid fractions":** this is vague, and the readings range from the strict format to any notation for a fraction.
- **"evaluates":** it doesn't say whether exact or floating-point arithmetic is meant. The two differ once the numerator product is large (about 2⁵³ or more).