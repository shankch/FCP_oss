I've written `formal/variant.yaml`. `fcp lint` reports clean, and I read the `fcp explain` output back: each item says what I meant it to say.

**Items: 11.** Eight properties (RV-FN-1, RV-RET-1, RV-RET-2, RV-IN-2 to RV-IN-6) and three scenarios (RV-EX-1 to RV-EX-3). There are no assumptions, no don't-cares and no ghosts. All 15 flagged phrases are recorded under `decisions` as reading 2, and every item a forced reading affects says so in its note.

**Unformalized (4), each with a reason:**
- **R-IF-1:** the function's name and argument order are fixed by the adapter, so there's no trace property to state.
- **R-DEF-1:** a definition. It's covered by RV-RET-1 and RV-RET-2 through the def `xn_whole`.
- **R-IN-1:** the trace carries x and n as strings by construction. What remains is covered by RV-IN-2 and RV-IN-5.
- **R-FR-1:** this is frame rule F-ZERO, which is already part of every set.

**Decisions you should check:**
- **R-DEF-1 overrides R-RET-1/R-RET-2.** Both depend on R-DEF-1, so I applied its reading to them. If x * n means `str * str`, it raises TypeError and never evaluates to a whole number. So RV-RET-1 never triggers and constrains nothing. RV-RET-2 then applies to every call: every call must return a falsy value and must not raise. As a result, the forced readings of "whole number", "evaluates to" and "returns True" have no effect. They're still written into the items and explained in the notes.
- **No assumptions.** Under "have the following format" (R-IN-2) and "You can assume" (R-IN-5), the input clauses become obligations on the function: reject the input, or return False. If I'd kept R-IN-1/3/4/6 as assumptions, the calls those readings constrain would be skipped by every check.
- **Truthy and falsy are only partly observable.** When the function returns something that isn't a bool, the trace records that (outcome 2) but not the value. So "any truthy value" and "any falsy value" are written to allow outcome 2, which is looser than the readings.

**Problems in the specification:**
1. Under the R-DEF-1 reading, RV-RET-2 contradicts R-EX-1 (`simplify("1/5","5/1") = True`).
2. The R-FN-1 reading (the function returns the simplified product, not a bool) contradicts all three examples. Its notes record that it also contradicts R-RET-1 and R-RET-2 in the prose. That doesn't show in the formal items, because the trace can't tell a truthy non-bool return from a falsy one.
3. A zero numerator such as "0/1" is a valid fraction under the R-IN-5 reading, so RV-FN-1 requires a non-bool result. RV-IN-3 requires rejecting the same call.
4. The R-IN-2 format allows no signs or spaces, but the R-IN-3/R-IN-4 reading counts "+3" and " 3" as positive whole numbers. Since RV-IN-2 rejects those strings anyway, the int() reading changes nothing you can observe.
5. The floating-point reading of "evaluates to" can't be stated exactly in FCP-PL, because the IEEE rounding and the order of operations aren't specified. That doesn't matter here, since R-RET-1 never applies.