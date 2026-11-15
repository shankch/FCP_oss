# FCP review

Before any code: the request alone.

Settled: 1 requirements. Questions: 16.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-RES-1: Every number in the returned list is even.

## Questions
1. **conflict** (R-EX-1, R-RES-4): no implementation can meet these requirements on these calls: which one gives way?
   - `generate_integers(2, 8)`
2. **conflict** (R-EX-2, R-RES-4): no implementation can meet these requirements on these calls: which one gives way?
   - `generate_integers(8, 2)`
3. **conflict** (R-EX-3, R-RES-2): no implementation can meet these requirements on these calls: which one gives way?
   - `generate_integers(10, 14)`
4. **open** (result): the request allows [2] or [2, 2]: which is meant?
   - `generate_integers(2, 1)`
5. **depends** (R-EX-1, R-EX-3, R-OUT-1, R-RES-2, R-RES-4, R-SYM-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `generate_integers(0, 1) -> raised another exception or did not finish`
   - `generate_integers(1, 1) -> []`
6. **readings** (R-ORD-1): the two readings of this requirement disagree on these calls: which is meant?
   - `generate_integers(2, 3) -> [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]`
   - `generate_integers(3, 1) -> [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]`
7. **ambiguity** (R-RES-2): "digits" can mean: single decimal digits: every returned number is from 0 to 9, so no number above 9 is ever returned; this contradicts the example generate_integers(10, 14) => [14] (R-EX-3) / integers: 'digits' is used loosely for numbers (the function is named generate_integers), so this places no limit on the returned numbers; this agrees with the example generate_integers(10, 14) => [14] (R-EX-3) / numbers written only with even digits: every decimal digit of every returned number is even (2, 4, 20, 46, ...); this contradicts the example generate_integers(10, 14) => [14] (R-EX-3), since 14 contains the digit 1. Which is meant?
8. **ambiguity** (R-RES-3): "between a and b" can mean: inclusive: min(a, b) <= x <= max(a, b), so a and b themselves may be returned; this agrees with every example, each of which returns an endpoint (8 or 14) / exclusive: min(a, b) < x < max(a, b), so a and b themselves are never returned; this contradicts every example (generate_integers(2, 8) => [8], generate_integers(8, 2) => [8], generate_integers(10, 14) => [14]). Which is meant?
9. **ambiguity** (R-RES-4): "even digits" can mean: the even decimal digits 0, 2, 4, 6 and 8: each of them that lies between a and b must appear, and nothing is required when a and b are both above 8 / even integers: every even integer that lies between a and b must appear / numbers written only with even digits (2, 4, 20, 46, ...): each such number that lies between a and b must appear. Which is meant?
10. **ambiguity** (R-RES-4): "between a and b" can mean: inclusive: the range is min(a, b) to max(a, b) including both ends / exclusive: the range is strictly between min(a, b) and max(a, b), excluding both ends. Which is meant?
11. **ambiguity** (R-RES-4): "the even digits between a and b" can mean: the description governs: the list holds every even digit between a and b, so generate_integers(2, 8) and generate_integers(8, 2) return [2, 4, 6, 8] (inclusive) or [4, 6] (exclusive), contradicting the examples that give [8] (R-EX-1, R-EX-2); with 'digits' read as integers, generate_integers(10, 14) must also contain 12, contradicting the example that gives [14] (R-EX-3) / the examples govern: only the largest even number between a and b is returned (generate_integers(2, 8) => [8], generate_integers(10, 14) => [14]), so the list need not contain the other even digits between a and b. Which is meant?
12. **ambiguity** (R-SYM-1): "between a and b" can mean: either order: the range runs from the smaller to the larger argument, so swapping a and b does not change the result (as generate_integers(2, 8) => [8] and generate_integers(8, 2) => [8] show) / ordered: the range runs from a up to b, so nothing lies between a and b when a > b and the list is then empty; this contradicts the example generate_integers(8, 2) => [8] (R-EX-2). Which is meant?
13. **ambiguity** (R-ORD-1): "ascending order" can mean: strictly ascending: each number is smaller than the next, so no number appears twice / non-decreasing: each number is at most the next, so a number may be repeated. Which is meant?
14. **ambiguity** (R-EX-1): "generate_integers(2, 8) => [8]" can mean: the example holds: generate_integers(2, 8) returns exactly [8], so the list does not hold every even digit between a and b, contradicting 'return the even digits between a and b' (R-RES-4) / the description governs and the example is wrong: the call returns [2, 4, 6, 8], every even digit from 2 to 8 inclusive / the description governs and the example is wrong: the call returns [4, 6], the even digits strictly between 2 and 8. Which is meant?
15. **ambiguity** (R-EX-2): "generate_integers(8, 2) => [8]" can mean: the example holds: generate_integers(8, 2) returns exactly [8], so the list does not hold every even digit between a and b, contradicting 'return the even digits between a and b' (R-RES-4) / the description governs and the example is wrong: the call returns [2, 4, 6, 8], every even digit from 2 to 8 inclusive / the description governs and the example is wrong: the call returns [4, 6], the even digits strictly between 2 and 8. Which is meant?
16. **ambiguity** (R-EX-3): "generate_integers(10, 14) => [14]" can mean: the example holds: generate_integers(10, 14) returns exactly [14], so a number above 9 can be returned, contradicting 'even digits' read as the digits 0 to 9 (R-RES-2), and 10 and 12 are left out, contradicting 'the even digits between a and b' read as every even integer in the range (R-RES-4) / the description governs and the example is wrong: no even digit (0 to 9) lies between 10 and 14, so the call returns [] / the description governs and the example is wrong: 'digits' means integers, so the call returns [10, 12, 14] (inclusive) or [12] (exclusive). Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IN-1, "positive": both took "strictly positive: a >= 1 and b >= 1, so a call with a = 0 or b = 0 is outside the request and its result is unconstrained"
- R-RES-2, "digits": both took "single decimal digits: every returned number is from 0 to 9, so no number above 9 is ever returned; this contradicts the example generate_integers(10, 14) => [14] (R-EX-3)"
- R-RES-3, "between a and b": both took "inclusive: min(a, b) <= x <= max(a, b), so a and b themselves may be returned; this agrees with every example, each of which returns an endpoint (8 or 14)"
- R-RES-4, "even digits": both took "the even decimal digits 0, 2, 4, 6 and 8: each of them that lies between a and b must appear, and nothing is required when a and b are both above 8"
- R-RES-4, "between a and b": both took "inclusive: the range is min(a, b) to max(a, b) including both ends"
- R-RES-4, "the even digits between a and b": both took "the description governs: the list holds every even digit between a and b, so generate_integers(2, 8) and generate_integers(8, 2) return [2, 4, 6, 8] (inclusive) or [4, 6] (exclusive), contradicting the examples that give [8] (R-EX-1, R-EX-2); with 'digits' read as integers, generate_integers(10, 14) must also contain 12, contradicting the example that gives [14] (R-EX-3)"
- R-SYM-1, "between a and b": both took "either order: the range runs from the smaller to the larger argument, so swapping a and b does not change the result (as generate_integers(2, 8) => [8] and generate_integers(8, 2) => [8] show)"
- R-EX-1, "generate_integers(2, 8) => [8]": both took "the example holds: generate_integers(2, 8) returns exactly [8], so the list does not hold every even digit between a and b, contradicting 'return the even digits between a and b' (R-RES-4)"
- R-EX-2, "generate_integers(8, 2) => [8]": both took "the example holds: generate_integers(8, 2) returns exactly [8], so the list does not hold every even digit between a and b, contradicting 'return the even digits between a and b' (R-RES-4)"
- R-EX-3, "generate_integers(10, 14) => [14]": both took "the example holds: generate_integers(10, 14) returns exactly [14], so a number above 9 can be returned, contradicting 'even digits' read as the digits 0 to 9 (R-RES-2), and 10 and 12 are left out, contradicting 'the even digits between a and b' read as every even integer in the range (R-RES-4)"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-IN-1 (R-IN-1): every call meets `a >= 1 && b >= 1`
- agent_b, RB-IN-1 (R-IN-1): every call meets `a >= 1 && b >= 1`
- agent_b, RB-IN-1-DO (R-IN-1): `outcome` is free when `!in_req`; `in_req` is `a >= 1 && b >= 1`
- agent_b, RB-IN-1-DR (R-IN-1): `result` is free when `!in_req`; `in_req` is `a >= 1 && b >= 1`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the comparison of agent_a and variant
- the comparison of agent_b and variant
