# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 11.

## Questions
1. **open** (result, R-RET-6): the request allows [6, 8] or [8, 6] (the reading leaves this free on purpose: RA-RET-6): is any answer acceptable, or which is meant?
   - `generate_integers(25, 6)`
2. **depends** (R-RET-1, R-RET-2, R-RET-3, R-RET-4): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `generate_integers(0, 0) -> raised another exception or did not finish`
3. **ambiguity** (R-RET-1): "return" can mean: The function returns a Python list. / Any collection of the values is acceptable (a list, tuple, set, generator, ...).. Which is meant?
4. **ambiguity** (R-RET-2): "even digits" can mean: Even decimal digits: every element is a single-digit even number, one of 0, 2, 4, 6, 8 (the docstring wins over the function name). / 'Digits' is used loosely for numbers: every element is an even integer of any size, as the function name generate_integers suggests (contradiction with R-IF-2). / Even digits that occur in the decimal writing of the numbers between a and b: every element is one of 0, 2, 4, 6, 8, taken from those numbers' digits.. Which is meant?
5. **ambiguity** (R-RET-3): "between" can mean: Inclusive: a and b themselves count as lying between a and b. / Exclusive: only values strictly greater than the lower bound and strictly less than the upper bound lie between a and b.. Which is meant?
6. **ambiguity** (R-RET-3): "a and b" can mean: Either order: the range runs from min(a, b) to max(a, b), so swapping a and b does not change which values lie between them. / Ordered: the range runs from a up to b, so nothing lies between them when a > b and the list is empty.. Which is meant?
7. **ambiguity** (R-RET-3): "even digits" can mean: Even single digits (0, 2, 4, 6, 8): each element itself lies between a and b. / Even integers of any size, as the function name generate_integers suggests: each element itself lies between a and b. / Even digits occurring in the decimal writing of the numbers between a and b: each element is a digit of some number between a and b, and need not itself lie between a and b.. Which is meant?
8. **ambiguity** (R-RET-4): "between" can mean: Inclusive: a or b itself must appear when it is an even digit. / Exclusive: a and b themselves never appear; only values strictly between them are required.. Which is meant?
9. **ambiguity** (R-RET-4): "a and b" can mean: Either order: the even digits from min(a, b) to max(a, b) must appear, whichever of a and b is larger. / Ordered: the even digits from a up to b must appear; nothing is required when a > b.. Which is meant?
10. **ambiguity** (R-RET-4): "even digits" can mean: Every even single digit (0, 2, 4, 6, 8) between a and b must appear; nothing is required when the range lies above 9. / Every even integer of any size between a and b must appear, as the function name generate_integers suggests (contradiction with R-IF-2). / Every even digit occurring in the decimal writing of some number between a and b must appear.. Which is meant?
11. **ambiguity** (R-RET-5): "the even digits" can mean: The set of qualifying values: each appears exactly once, without duplicates. / One entry per occurrence (for instance per occurrence of a digit in the decimal writing of the numbers between a and b): duplicates are allowed or required.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IF-2, "generate_integers": both took "The name is only a label; the returned values are even digits (single digits 0-9) as the docstring says, so the name and the docstring do not conflict."
- R-IN-1, "positive": both took "Strictly positive: a >= 1 and b >= 1; a call with a == 0 or b == 0 is outside the precondition and its behaviour is unconstrained."
- R-IN-1, "a and b": both took "No order between a and b is assumed: a call with a > b is a valid call and must be answered."
- R-RET-1, "return": both took "The function returns a Python list."
- R-RET-2, "even digits": both took "Even decimal digits: every element is a single-digit even number, one of 0, 2, 4, 6, 8 (the docstring wins over the function name)."
- R-RET-3, "between": both took "Inclusive: a and b themselves count as lying between a and b."
- R-RET-3, "a and b": both took "Either order: the range runs from min(a, b) to max(a, b), so swapping a and b does not change which values lie between them."
- R-RET-3, "even digits": both took "Even single digits (0, 2, 4, 6, 8): each element itself lies between a and b."
- R-RET-4, "between": both took "Inclusive: a or b itself must appear when it is an even digit."
- R-RET-4, "a and b": both took "Either order: the even digits from min(a, b) to max(a, b) must appear, whichever of a and b is larger."
- R-RET-4, "even digits": both took "Every even single digit (0, 2, 4, 6, 8) between a and b must appear; nothing is required when the range lies above 9."
- R-RET-5, "the even digits": both took "The set of qualifying values: each appears exactly once, without duplicates."
- R-RET-6, "return the even digits": both took "The order is unconstrained: any order of the required elements is acceptable."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `a >= 1 && b >= 1`
- agent_b, RB-A-POS (R-IN-1): every call meets `a >= 1 && b >= 1`
- agent_b, RB-D-OUTSIDE-RESULT (R-IN-1): `result` is free when `!pre`; `pre` is `a >= 1 && b >= 1`
- agent_b, RB-D-OUTSIDE-OUTCOME (R-IN-1): `outcome` is free when `!pre`; `pre` is `a >= 1 && b >= 1`
The readings leave these outputs free on purpose. Where a call shows two answers, a question above asks about it:
- agent_a, RA-RET-6 (R-RET-6): `result` is free when `ndig >= 2`; `ndig` is `count(d < 10: d % 2 == 0 && lo <= d && d <= hi)`
- agent_b, RB-D-ORDER (R-RET-6): `result` is free when `pre && nexp >= 2`; `pre` is `a >= 1 && b >= 1`; `nexp` is `count(d < 10: d % 2 == 0 && lo <= d && d <= hi)`

## Limits of this review
These searches stopped at their time budget. What they found stands; what lies beyond the budget was not searched:
- the comparison of agent_a and variant
