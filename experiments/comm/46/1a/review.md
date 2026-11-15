# FCP review

Before any code: the request alone.

Settled: 4 requirements. Questions: 10.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-BASE-1: fib4(0) returns 0.
- R-BASE-2: fib4(1) returns 0.
- R-BASE-3: fib4(2) returns 2.
- R-BASE-4: fib4(3) returns 0.

## Questions
1. **open** (result, outcome): the request allows `result` to be 0 or 1 and lets this call end in two ways, "returned" or "returned something else": which is meant?
   - `fib4(4)`
2. **scenario** (R-EX-1): the behaviour RB-EX-1 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
3. **depends** (R-FUN-1, R-REC-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `fib4(2) -> 2`
4. **readings** (R-REC-1): the two readings of this requirement disagree on these calls: which is meant?
   - `fib4(5) -> 124615124604835863084731911095975935`
5. **ambiguity** (R-REC-1): "+/-" can mean: Every '+/-' is '+': fib4(n) = fib4(n-1) + fib4(n-2) + fib4(n-3) + fib4(n-4), as 'similar to the Fibonacci sequence' suggests (0, 0, 2, 0, 2, 4, 8, 14, ...). / The signs alternate: fib4(n) = fib4(n-1) - fib4(n-2) + fib4(n-3) - fib4(n-4) (0, 0, 2, 0, -2, 0, 0, -2, ...; some elements are negative). / Each '+/-' is a fixed sign, + or -, that the prompt leaves to the implementation; any one fixed combination of the three signs is acceptable. / Each '+/-' may be + or - independently for every n; any value obtained by some choice of signs is acceptable.. Which is meant?
6. **ambiguity** (R-REC-1): "fib4(n) -> fib4(n-1) +/- fib4(n-2) +/- fib4(n-3) +/- fib4(n-4)" can mean: Contradiction with the examples fib4(5) = 2, fib4(6) = 4, fib4(7) = 6: the base values and this recurrence define the sequence and the examples are wrong. From the base values the recurrence gives fib4(4) = 2 or -2 and fib4(5) = -4, 0 or 4 under every choice of signs, never 2; with all '+' it gives fib4(5) = 4, fib4(6) = 8, fib4(7) = 14. / Contradiction with the examples fib4(5) = 2, fib4(6) = 4, fib4(7) = 6: the examples are right and the definition is wrong as stated. The examples fit the all-'+' recurrence only if fib4(4) = 0, which no choice of signs gives from the base values.. Which is meant?
7. **ambiguity** (R-FUN-1): "n-th element" can mean: The element with index n, counting fib4(0) as element 0: fib4(n) returns the value the definition gives for fib4(n). / The n-th element counting from 1: fib4(n) returns the value the definition gives for index n-1 (with all '+' this matches fib4(5) = 2 and fib4(6) = 4 but not fib4(7) = 6, and leaves fib4(0) undefined).. Which is meant?
8. **ambiguity** (R-EX-1): ">>> fib4(5)" can mean: Contradiction with the recurrence and base values: fib4(5) must return 2 as the example shows, although the base values and the recurrence give -4, 0 or 4 under every choice of signs (4 with all '+'). / Contradiction with the recurrence and base values: the example is wrong, and fib4(5) returns the value the base values and the recurrence give, not 2.. Which is meant?
9. **ambiguity** (R-EX-2): ">>> fib4(6)" can mean: Contradiction with the recurrence and base values: fib4(6) must return 4 as the example shows, although the recurrence gives 8 with all '+' and 0 with alternating signs, and no fixed choice of signs gives both fib4(6) = 4 and fib4(7) = 6. / Contradiction with the recurrence and base values: the example is wrong, and fib4(6) returns the value the base values and the recurrence give.. Which is meant?
10. **ambiguity** (R-EX-3): ">>> fib4(7)" can mean: Contradiction with the recurrence and base values: fib4(7) must return 6 as the example shows, although the recurrence gives 14 with all '+' and -2 with alternating signs; the only fixed signs that give 6 (fib4(n-1) - fib4(n-2) - fib4(n-3) + fib4(n-4)) give fib4(5) = -4 and fib4(6) = 0. / Contradiction with the recurrence and base values: the example is wrong, and fib4(7) returns the value the base values and the recurrence give.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IF-1, "n: int": both took "n may be any int; the prompt does not say what fib4 does for a negative n."
- R-REC-1, "+/-": both took "Each '+/-' may be + or - independently for every n; any value obtained by some choice of signs is acceptable."
- R-REC-1, "fib4(n) -> fib4(n-1) +/- fib4(n-2) +/- fib4(n-3) +/- fib4(n-4)": both took "Contradiction with the examples fib4(5) = 2, fib4(6) = 4, fib4(7) = 6: the base values and this recurrence define the sequence and the examples are wrong. From the base values the recurrence gives fib4(4) = 2 or -2 and fib4(5) = -4, 0 or 4 under every choice of signs, never 2; with all '+' it gives fib4(5) = 4, fib4(6) = 8, fib4(7) = 14."
- R-FUN-1, "n-th element": both took "The element with index n, counting fib4(0) as element 0: fib4(n) returns the value the definition gives for fib4(n)."
- R-NF-1, "efficiently": both took "No particular bound; only exponential-time computation (naive recursion) is excluded."
- R-NF-2, "recursion": both took "No function of the implementation may be recursive, including helpers and memoized (for example lru_cache) recursion."

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the scenarios of agent_b: RB-EX-2, RB-EX-3
- the comparison of agent_a and agent_b
