# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 8.

## Questions
1. **depends** (R-OUT-1, R-OUT-2, R-OUT-3, R-OUT-4): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `generate_integers(0, 0) -> raised another exception or did not finish`
2. **ambiguity** (R-OUT-1): "return the even digits" can mean: Return a Python list of int values, as the examples show. / Return the digits in another form: as digit characters (strings such as '2'), or as another sequence type such as a tuple or a generator.. Which is meant?
3. **ambiguity** (R-OUT-2, R-OUT-3): "even digits" can mean: The even single-digit numbers 0, 2, 4, 6 and 8 (0 counts as an even digit). / The even single-digit numbers 2, 4, 6 and 8 only (0 not counted). / Every even integer, of any size (as the function name generate_integers suggests). Contradicts the example generate_integers(10, 14) => [], which would then be [10, 12, 14]. / The even digits that occur in the decimal writing of the integers between a and b. Contradicts the example generate_integers(10, 14) => [], which would then contain 0, 2 and 4.. Which is meant?
4. **ambiguity** (R-OUT-2, R-OUT-3): "between a and b" can mean: The integers from min(a, b) to max(a, b), both ends included, whichever argument is larger (matches all three examples). / The integers strictly between min(a, b) and max(a, b), ends excluded. Contradicts the example generate_integers(2, 8) => [2, 4, 6, 8]. / The integers from a up to b only, none when a > b. Contradicts the example generate_integers(8, 2) => [2, 4, 6, 8].. Which is meant?
5. **ambiguity** (R-OUT-4): "ascending order" can mean: Strictly increasing: each element is smaller than the next, so no value is repeated. / Non-decreasing: each element is at most the next, so a value may repeat (matters only if the same digit can be found more than once).. Which is meant?
6. **ambiguity** (R-EX-1): "generate_integers(2, 8) => [2, 4, 6, 8]" can mean: Binding: the call (2, 8) returns [2, 4, 6, 8], so a and b themselves count as lying between a and b. / Illustrative only: it conflicts with 'between a and b' read as excluding the ends (which gives [4, 6]), and the statement prevails.. Which is meant?
7. **ambiguity** (R-EX-2): "generate_integers(8, 2) => [2, 4, 6, 8]" can mean: Binding: the call (8, 2) returns [2, 4, 6, 8], so 'between a and b' does not depend on which argument is larger. / Illustrative only: it conflicts with 'between a and b' read as from a up to b (which gives [] when a > b), and the statement prevails.. Which is meant?
8. **ambiguity** (R-EX-3): "generate_integers(10, 14) => []" can mean: Binding: the call (10, 14) returns [], so 'even digits' means even single-digit numbers and none lies between 10 and 14. / Illustrative only: it conflicts with 'even digits' read as even integers (as the name generate_integers suggests, giving [10, 12, 14]) or as the even digits written in 10 to 14 (giving 0, 2 and 4), and the statement prevails.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-IF-2, "generate_integers": both took "Only the name of the function; what it returns is fixed by the docstring (the even digits between a and b)."
- R-ENV-1, "positive integers": both took "a >= 1 and b >= 1; a call with a or b equal to 0 is outside the contract and its outcome is unconstrained."
- R-OUT-1, "return the even digits": both took "Return a Python list of int values, as the examples show."
- R-OUT-2, "even digits": both took "The even single-digit numbers 0, 2, 4, 6 and 8 (0 counts as an even digit)."
- R-OUT-2, "between a and b": both took "The integers from min(a, b) to max(a, b), both ends included, whichever argument is larger (matches all three examples)."
- R-OUT-3, "even digits": both took "The even single-digit numbers 0, 2, 4, 6 and 8 (0 counts as an even digit)."
- R-OUT-3, "between a and b": both took "The integers from min(a, b) to max(a, b), both ends included, whichever argument is larger (matches all three examples)."
- R-OUT-4, "ascending order": both took "Strictly increasing: each element is smaller than the next, so no value is repeated."
- R-EX-1, "generate_integers(2, 8) => [2, 4, 6, 8]": both took "Binding: the call (2, 8) returns [2, 4, 6, 8], so a and b themselves count as lying between a and b."
- R-EX-2, "generate_integers(8, 2) => [2, 4, 6, 8]": both took "Binding: the call (8, 2) returns [2, 4, 6, 8], so 'between a and b' does not depend on which argument is larger."
- R-EX-3, "generate_integers(10, 14) => []": both took "Binding: the call (10, 14) returns [], so 'even digits' means even single-digit numbers and none lies between 10 and 14."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-ENV-1 (R-ENV-1): every call meets `a >= 1 && b >= 1`
- agent_b, RB-ENV-1 (R-ENV-1): every call meets `valid`; `valid` is `a >= 1 && b >= 1`
- agent_b, RB-ENV-1-D1 (R-ENV-1): `outcome` is free when `!valid`; `valid` is `a >= 1 && b >= 1`
- agent_b, RB-ENV-1-D2 (R-ENV-1): `result` is free when `!valid`; `valid` is `a >= 1 && b >= 1`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the conflicts and open choices of agent_b: these searches leave out RB-OUT-2, RB-OUT-3 (rules stated for every value of a variable); 8 calls with two answers that break them are not reported
