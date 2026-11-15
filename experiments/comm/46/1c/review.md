# FCP review

Before any code: the request alone.

Settled: 4 requirements. Questions: 8.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-BASE-1: fib4(0) returns 0.
- R-BASE-2: fib4(1) returns 0.
- R-BASE-3: fib4(2) returns 2.
- R-BASE-4: fib4(3) returns 0.

## Questions
1. **depends** (R-FN-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `fib4(3) -> 0`
2. **ambiguity** (R-REC-1): "fib4(n)" can mean: The recurrence applies to every n >= 4 only; the base values cover 0 to 3. / The recurrence applies to every integer n not listed as a base value, including negative n, where it extends the sequence backwards.. Which is meant?
3. **ambiguity** (R-REC-1): "fib4(n) -> fib4(n-1) + fib4(n-2) + fib4(n-3) + fib4(n-4)" can mean: Contradiction with the docstring examples (R-EX-1, R-EX-2, R-EX-3): the recurrence and base values are authoritative, so fib4(5) = 4, fib4(6) = 8 and fib4(7) = 14, and the examples fib4(5) -> 0, fib4(6) -> 0, fib4(7) -> 2 are wrong. / Contradiction with the docstring examples (R-EX-1, R-EX-2, R-EX-3): the examples are authoritative, so fib4(5) = 0, fib4(6) = 0 and fib4(7) = 2, and the recurrence does not hold at n = 5 and n = 6 (its meaning for larger n is then unclear).. Which is meant?
4. **ambiguity** (R-FN-1): "the n-th element" can mean: The element at index n counting from 0, so fib4(n) is the sequence value labelled fib4(n) in the definition. / The n-th element counting from 1, so fib4(n) is the value at index n - 1 (and fib4(0) has no meaning).. Which is meant?
5. **ambiguity** (R-FN-1): "compute" can mean: fib4 returns the element as a Python int. / fib4 only has to produce the value somehow (for instance print it, or return it as a float); the form of the answer is not fixed.. Which is meant?
6. **ambiguity** (R-EX-1): ">>> fib4(5) 0" can mean: Contradiction with the recurrence (R-REC-1) and base values: these give fib4(5) = fib4(4) + fib4(3) + fib4(2) + fib4(1) = 2 + 0 + 2 + 0 = 4, so the example is wrong and fib4(5) returns 4. / Contradiction with the recurrence (R-REC-1) and base values: the example is authoritative, fib4(5) returns 0, and the recurrence does not hold at n = 5.. Which is meant?
7. **ambiguity** (R-EX-2): ">>> fib4(6) 0" can mean: Contradiction with the recurrence (R-REC-1) and base values: these give fib4(6) = fib4(5) + fib4(4) + fib4(3) + fib4(2) = 4 + 2 + 0 + 2 = 8, so the example is wrong and fib4(6) returns 8. / Contradiction with the recurrence (R-REC-1) and base values: the example is authoritative, fib4(6) returns 0, and the recurrence does not hold at n = 6.. Which is meant?
8. **ambiguity** (R-EX-3): ">>> fib4(7) 2" can mean: Contradiction with the recurrence (R-REC-1) and base values: these give fib4(7) = fib4(6) + fib4(5) + fib4(4) + fib4(3) = 8 + 4 + 2 + 0 = 14, so the example is wrong and fib4(7) returns 14. / Contradiction with the recurrence (R-REC-1) and base values: the example is authoritative, fib4(7) returns 2 (which is what the recurrence gives at n = 7 if fib4(5) = fib4(6) = 0 as R-EX-1 and R-EX-2 say), and the recurrence's value 14 is wrong.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-ENV-1, "n: int": both took "n may be any Python int, including negative values; the prompt leaves the result for negative n unstated."
- R-REC-1, "fib4(n)": both took "The recurrence applies to every n >= 4 only; the base values cover 0 to 3."
- R-REC-1, "fib4(n) -> fib4(n-1) + fib4(n-2) + fib4(n-3) + fib4(n-4)": both took "Contradiction with the docstring examples (R-EX-1, R-EX-2, R-EX-3): the recurrence and base values are authoritative, so fib4(5) = 4, fib4(6) = 8 and fib4(7) = 14, and the examples fib4(5) -> 0, fib4(6) -> 0, fib4(7) -> 2 are wrong."
- R-FN-1, "the n-th element": both took "The element at index n counting from 0, so fib4(n) is the sequence value labelled fib4(n) in the definition."
- R-FN-1, "compute": both took "fib4 returns the element as a Python int."
- R-NF-1, "efficiently": both took "Time linear in n with any amount of memory (for instance a table of all elements up to n)."
- R-NF-2, "recursion": both took "Any recursion is forbidden, including recursive helpers, mutual recursion and memoized recursion (such as functools.lru_cache on a recursive function)."
- R-EX-1, ">>> fib4(5) 0": both took "Contradiction with the recurrence (R-REC-1) and base values: these give fib4(5) = fib4(4) + fib4(3) + fib4(2) + fib4(1) = 2 + 0 + 2 + 0 = 4, so the example is wrong and fib4(5) returns 4."
- R-EX-2, ">>> fib4(6) 0": both took "Contradiction with the recurrence (R-REC-1) and base values: these give fib4(6) = fib4(5) + fib4(4) + fib4(3) + fib4(2) = 4 + 2 + 0 + 2 = 8, so the example is wrong and fib4(6) returns 8."
- R-EX-3, ">>> fib4(7) 2": both took "Contradiction with the recurrence (R-REC-1) and base values: these give fib4(7) = fib4(6) + fib4(5) + fib4(4) + fib4(3) = 8 + 4 + 2 + 0 = 14, so the example is wrong and fib4(7) returns 14."
