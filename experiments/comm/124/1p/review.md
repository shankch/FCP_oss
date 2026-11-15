# FCP review

Before any code: the request alone.

Settled: 1 requirements. Questions: 2.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-RET-2: If the date string is valid (per the validity definition R-VAL-1), valid_date returns True.

## Questions
1. **ambiguity** (R-RET-1): "returns True if the date is valid otherwise False" can mean: Total: every string argument, however malformed, yields True or False and never an exception. / Only for date-shaped strings (see R-IN-1); for other strings the function may raise or return anything.. Which is meant?
2. **ambiguity** (R-RET-3): "otherwise False" can mean: Contradiction with R-VAL-1/R-VAL-2: the function is said to validate and to return False for invalid dates, which presumes some strings are invalid; but the rule list that defines validity is empty, so under a literal reading no string is ever invalid and False is never returned. / False is required for strings that break validity rules which the prompt intended but omitted; which strings those are is unspecified.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "a given date string": both took "Any string may be passed, whatever its content (including the empty string and strings that look nothing like a date); the function must classify every one."
- R-RET-1, "returns True if the date is valid otherwise False": both took "Total: every string argument, however malformed, yields True or False and never an exception."
- R-RET-3, "otherwise False": both took "Contradiction with R-VAL-1/R-VAL-2: the function is said to validate and to return False for invalid dates, which presumes some strings are invalid; but the rule list that defines validity is empty, so under a literal reading no string is ever invalid and False is never returned."
- R-VAL-1, "is valid if": both took "If and only if: a date string is valid exactly when every listed rule is satisfied (consistent with 'otherwise False')."
- R-VAL-1, "all of the following rules": both took "The list is empty, so the conjunction is vacuously true: every string is valid and the function always returns True."
- R-VAL-1, "The date is valid if all of the following rules are satisfied": both took "No contradiction: the function validly returns True for every string and the False branch is simply unreachable."
- R-VAL-2, "1.": both took "There is no rule: the list is intentionally or effectively empty, imposing no constraint on validity."
