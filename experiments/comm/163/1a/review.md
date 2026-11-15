# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 10.

## Questions
1. **open** (result): the request allows [] or [1]: which is meant?
   - `generate_integers(1, 1)`
2. **depends** (R-ORD-1, R-OUT-1, R-SEL-1, R-SEL-2, R-SEL-3, R-SEL-4, R-SEL-5): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
3. **ambiguity** (R-SEL-1): "digits" can mean: The single-digit integers 0 to 9 that lie in the range between a and b (consistent with generate_integers(10, 14) => []). / The decimal digits that occur in the integers between a and b (for 10..14 this would include 0, 2 and 4, contradicting generate_integers(10, 14) => []). / Loosely, the integers between a and b of any size (for 10..14 this would include 10, 12 and 14 or 11 and 13, contradicting generate_integers(10, 14) => []).. Which is meant?
4. **ambiguity** (R-SEL-2): "between a and b" can mean: Inclusive: a and b themselves count as between a and b (consistent with generate_integers(2, 8) => [2, 4, 6, 8]). / Exclusive: only values strictly greater than the smaller and strictly less than the larger argument (contradicts generate_integers(2, 8) => [2, 4, 6, 8], which contains 2 and 8).. Which is meant?
5. **ambiguity** (R-SEL-2): "between a and b" can mean: Order-independent: the range from min(a, b) to max(a, b) (consistent with generate_integers(8, 2) => [2, 4, 6, 8]). / Directed: the values from a up to b, empty when a > b (contradicts generate_integers(8, 2) => [2, 4, 6, 8]).. Which is meant?
6. **ambiguity** (R-SEL-3): "odd or even" can mean: Even digits only (the parity every example shows). / Odd digits only (contradicts generate_integers(2, 8) => [2, 4, 6, 8] and generate_integers(8, 2) => [2, 4, 6, 8]). / Both odd and even digits, i.e. every digit regardless of parity (contradicts generate_integers(2, 8) => [2, 4, 6, 8], which omits 3, 5 and 7). / The implementer chooses one parity, odd or even, and uses it for every call (the examples then bind only an implementation that chose even). / The parity may be chosen per call, e.g. odd digits when a is odd and even digits when a is even (consistent with all three examples, whose first argument is even).. Which is meant?
7. **ambiguity** (R-ORD-1): "in descending or ascending order" can mean: Always ascending (the order every example shows). / Always descending (contradicts generate_integers(2, 8) => [2, 4, 6, 8] and generate_integers(8, 2) => [2, 4, 6, 8]). / The implementer chooses one order and uses it for every call (the examples then bind only an implementation that chose ascending). / Following the argument order: ascending when a <= b and descending when a > b (contradicts generate_integers(8, 2) => [2, 4, 6, 8]). / Paired with the parity respectively: odd digits in descending order, even digits in ascending order. / Either order on any call, as long as the list is sorted one way or the other.. Which is meant?
8. **ambiguity** (R-EX-1): "generate_integers(2, 8) => [2, 4, 6, 8]" can mean: Binding: the call must return exactly [2, 4, 6, 8], which fixes even parity and ascending order and contradicts the odd and descending options of 'odd or even digits' and 'in descending or ascending order' (R-SEL-3, R-ORD-1). / Illustrative: one admissible answer for an implementation that chose even digits in ascending order; an implementation that chose odd digits or descending order may return another list.. Which is meant?
9. **ambiguity** (R-EX-2): "generate_integers(8, 2) => [2, 4, 6, 8]" can mean: Binding: the call must return exactly [2, 4, 6, 8], which fixes even parity and ascending order even when a > b, contradicting the odd and descending options of 'odd or even digits' and 'in descending or ascending order' (R-SEL-3, R-ORD-1) and the reading that descending order applies when a > b. / Illustrative: one admissible answer for an implementation that chose even digits in ascending order; an implementation that chose odd digits or descending order may return another list.. Which is meant?
10. **ambiguity** (R-EX-3): "generate_integers(10, 14) => []" can mean: Consistent with 'digits' meaning the single-digit integers 0 to 9 in the range: no digit lies between 10 and 14. / Contradicts 'digits' read as the digits occurring in the numbers 10 to 14 (0, 2, 4 even; 1, 3 odd) or as the integers 10 to 14 themselves (R-SEL-1).. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "positive integers": both took "An environment obligation: calls with a = 0 never happen, so the result for a = 0 is unconstrained (don't care)."
- R-IN-2, "positive integers": both took "An environment obligation: calls with b = 0 never happen, so the result for b = 0 is unconstrained (don't care)."
- R-SEL-1, "digits": both took "The single-digit integers 0 to 9 that lie in the range between a and b (consistent with generate_integers(10, 14) => [])."
- R-SEL-2, "between a and b": both took "Inclusive: a and b themselves count as between a and b (consistent with generate_integers(2, 8) => [2, 4, 6, 8])."
- R-SEL-3, "odd or even": both took "The parity may be chosen per call, e.g. odd digits when a is odd and even digits when a is even (consistent with all three examples, whose first argument is even)."
- R-ORD-1, "in descending or ascending order": both took "Either order on any call, as long as the list is sorted one way or the other."
- R-EX-1, "generate_integers(2, 8) => [2, 4, 6, 8]": both took "Binding: the call must return exactly [2, 4, 6, 8], which fixes even parity and ascending order and contradicts the odd and descending options of 'odd or even digits' and 'in descending or ascending order' (R-SEL-3, R-ORD-1)."
- R-EX-2, "generate_integers(8, 2) => [2, 4, 6, 8]": both took "Binding: the call must return exactly [2, 4, 6, 8], which fixes even parity and ascending order even when a > b, contradicting the odd and descending options of 'odd or even digits' and 'in descending or ascending order' (R-SEL-3, R-ORD-1) and the reading that descending order applies when a > b."
- R-EX-3, "generate_integers(10, 14) => []": both took "Consistent with 'digits' meaning the single-digit integers 0 to 9 in the range: no digit lies between 10 and 14."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `a >= 1`
- agent_a, RA-IN-2 (R-IN-2): every call meets `b >= 1`
- agent_b, RB-IN-1 (R-IN-1): every call meets `a >= 1`
- agent_b, RB-IN-2 (R-IN-2): every call meets `b >= 1`

## Limits of this review
These searches stopped at their time budget. What they found stands; what lies beyond the budget was not searched:
- request points of agent_a, variant
- request points of agent_a, agent_b, variant
- the comparison of agent_a and variant
