# FCP review

Before any code: the request alone.

Settled: 5 requirements. Questions: 7.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-BASE-1: fib4(0) returns 0.
- R-BASE-2: fib4(1) returns 0.
- R-EX-1: fib4(5) returns 4.
- R-EX-2: fib4(6) returns 8.
- R-EX-3: fib4(7) returns 14.

## Questions
1. **readings** (R-FN-1): the two readings of this requirement disagree (no separating call was found within the budget): which is meant?
2. **ambiguity** (R-BASE-3): "fib4(2) -> 2" can mean: a base value that overrides the recurrence; the recurrence applies only from n = 4 / apparent contradiction with the recurrence read for every n: fib4(2) would be fib4(1) + fib4(0) + fib4(-1) + fib4(-2) = 0 + 0 + 0 + 0 = 0 if terms before the start are 0, not 2. Which is meant?
3. **ambiguity** (R-BASE-4): "fib4(3) -> 0" can mean: a base value that overrides the recurrence; the recurrence applies only from n = 4 / apparent contradiction with the recurrence read for every n: fib4(3) would be fib4(2) + fib4(1) + fib4(0) + fib4(-1) = 2 + 0 + 0 + 0 = 2 if terms before the start are 0, not 0. Which is meant?
4. **ambiguity** (R-REC-1): "fib4(n)" can mean: the recurrence holds only for n >= 4, where the four earlier terms are base values or computed terms / the recurrence holds for every n, which seems to contradict the base values fib4(2) -> 2 and fib4(3) -> 0 (and defines values at negative n). Which is meant?
5. **ambiguity** (R-FN-1): "the n-th element" can mean: counting from 0: the n-th element is fib4(n) as defined (the examples fib4(5) -> 4, fib4(6) -> 8, fib4(7) -> 14 agree with this) / counting from 1: the n-th element is the value the definition gives for index n-1 (this disagrees with the examples). Which is meant?
6. **ambiguity** (R-FN-1): "compute" can mean: return the element as the function's result / print the element (the doctest output would look the same). Which is meant?
7. **ambiguity** (R-FN-1): "compute the n-th element" can mean: the returned value is a Python int / any value numerically equal to the element is acceptable, such as a float. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "n: int": both took "n may be any integer, including negative ones"
- R-IN-2, "the n-th element": both took "the sequence has no element at a negative index, so the behaviour for negative n is free"
- R-DEF-1, "that's defined as follows": both took "the rules that follow define the Fib4 sequence"
- R-DEF-1, "similar to the Fibbonacci sequnece": both took "informative only; the listed rules are the complete definition"
- R-BASE-3, "fib4(2) -> 2": both took "a base value that overrides the recurrence; the recurrence applies only from n = 4"
- R-BASE-4, "fib4(3) -> 0": both took "a base value that overrides the recurrence; the recurrence applies only from n = 4"
- R-REC-1, "fib4(n)": both took "the recurrence holds only for n >= 4, where the four earlier terms are base values or computed terms"
- R-FN-1, "the n-th element": both took "counting from 0: the n-th element is fib4(n) as defined (the examples fib4(5) -> 4, fib4(6) -> 8, fib4(7) -> 14 agree with this)"
- R-FN-1, "compute": both took "return the element as the function's result"
- R-FN-1, "compute the n-th element": both took "the returned value is a Python int"
- R-NF-1, "efficiently": both took "anything better than the exponential naive recursion, such as linear time with a table of all values"
- R-NF-2, "Do not use recursion.": both took "no recursion anywhere, including recursive helper functions, mutual recursion and memoized recursion"

## Limits of this review
These searches stopped at their time budget. What they found stands; what lies beyond the budget was not searched:
- the comparison of agent_a and agent_b
