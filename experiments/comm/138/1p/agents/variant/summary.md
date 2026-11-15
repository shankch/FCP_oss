I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and the `fcp explain` output matches what I meant for each item.

**Items: 5** (1 assumption and 4 properties). The adapter's own rule F-ZERO is added to the set automatically.
- **RV-DOM-1** (assumption, R-DOM-1): `n >= 0`. This is always true already, because the adapter only passes values from 0 to 65,535. I kept it to record the reading.
- **RV-RET-1** (R-RET-1): `outcome != 1`, meaning every call returns, with no exception and no hang.
- **RV-RET-2** (R-RET-2): `outcome == 0 || outcome == 2`. Under the required reading, any truthy or falsy return value is acceptable, not only a bool.
- **RV-SUM-1** (R-SUM-1): if n is even and n ≥ 20, the call returns `True` or some value that isn't a bool.
- **RV-SUM-2** (R-SUM-2): otherwise, the call returns `False` or some value that isn't a bool.

The threshold of 20 comes from combining two of the required readings: four positive even summands, all different. The smallest such sum is 2 + 4 + 6 + 8 = 20, and any larger even n can be written as 2 + 4 + 6 + (n − 12). The reading choices are listed under `decisions`, and every item they affect says in its note that it follows the reading you specified.

**Left unformalized (3):**
- **R-IF-1** and **R-IF-2** are about the source code (a complete body, the function's name and its single parameter), not about what a call does. The adapter fixes the name and the argument. Under the required reading the name adds no constraint, so it doesn't affect the sum checks.
- **R-FR-1** is the adapter's rule F-ZERO, which is part of every set already, so it is marked `covered_by: [F-ZERO]` and not restated.

**Problems in the specification:**
1. **The docstring stops after "exactly 4".** It never says what kind of summand is meant, and it gives no examples, return type or allowed values of n. The summand kind comes entirely from the readings you supplied, not from the text.
2. **Two required readings pull against each other.** Reading 1 of "the sum of exactly 4" justifies even summands by pointing to the function name. Reading 2 of "is_equal_to_sum_even" says the name adds nothing. I took the even summands from the first phrase's reading alone and said so in the notes.
3. **Two other required readings disagree on the threshold.** Reading 1 of "the sum of exactly 4" says the answer is True exactly when n is even and n ≥ 8, which assumes summands can repeat. The "all different" reading of "exactly 4" pushes the threshold to 20. I used 20 because both readings must hold together. So for even n from 8 to 18 this set expects False, while a set that allows repeated summands would expect True.
4. **The checks can't see the answer when the function returns something other than a bool.** Under the truthy/falsy reading, a return like `1` or `None` is allowed, but the trace doesn't record that value. RV-SUM-1 and RV-SUM-2 can therefore only check answers given as `True` or `False`. For any other return type the answer isn't checked at all, so for example returning `None` for n = 20 would pass.