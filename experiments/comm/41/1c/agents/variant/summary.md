I wrote `formal/variant.yaml`. `fcp lint` reports "lint: clean", and the `fcp explain` output matches what I meant for each item. I also tried to check the primality definition `n_prime` by brute force over every n from 0 to 1023, but that command wasn't approved, so the definition is checked by hand only. It tests divisors 2 to 31, which is enough because 31² = 961 ≤ 1023 < 32².

**Items: 3 properties**, plus the adapter's frame rule F-ZERO.
- **R-FN-2** has two properties: `RV-FN-2-RET` says the call always returns (`outcome != 1`), and `RV-FN-2-VAL` says that when `outcome == 0`, `collisions` is 1 if n is prime and 0 otherwise.
- **R-OUT-1** has one property, `RV-OUT-1-RESULT`. It says the same thing in one expression.
- All five ambiguous phrases are recorded under `decisions` with reading 2, as you asked. Every affected item's `note` (or `reason`) says I took that reading even where reading 1 seems more natural.

**Left unformalized (9 requirements):**
- **R-FN-1**: it's non-functional (deliver a completed body). The observable behaviour it requires is stated by the three properties.
- **R-ROAD-1, R-CAR-1 to R-CAR-4, R-COL-1, R-COL-2**: these define the collision scenario. Under the readings taken, the collision count is printed rather than returned. The trace records only the returned value and the outcome, not printed output, so these constrain no signal. R-CAR-3's reason also says the count isn't even determined: it is 0 if the two sets are moving apart.
- **R-FR-1**: covered by F-ZERO, which is already part of every set.

**Problems in the specification:**
1. **Name vs. docstring:** the function name `is_prime` contradicts the docstring's "outputs the number of such collisions". Under these readings, the name decides the return value and the docstring only governs printed output, which nothing checks.
2. **Undetermined count:** R-CAR-3 doesn't say which side each set starts on. Combined with counting distinct events, the collision count could be anything from 0 to n·n.
3. **How the adapter records a bool:** `frame.md` doesn't say whether a returned Python bool counts as "an integer that fits" (outcome 0, True = 1) or as "another type" (outcome 2). I allowed both. The cost is that if bools come out as outcome 2, the trace can't tell True from False, or a primality answer from any other non-integer return such as `None` from an empty body. `RV-FN-2-VAL` would then never trigger, and the vacuity check should flag that.