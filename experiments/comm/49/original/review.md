# FCP review

Before any code: the request alone.

Settled: 4 requirements. Questions: 7.

## Settled (the two readings agree on them; no conflict; nothing flagged)
- R-EX-1: modp(3, 5) returns 3.
- R-EX-2: modp(1101, 101) returns 2.
- R-EX-4: modp(3, 11) returns 8.
- R-EX-5: modp(100, 101) returns 1.

## Questions
1. **open** (result, outcome, R-RES-2): the request allows `result` to be 0 or 1 (the reading leaves this free on purpose: RA-RES-2-RESULT) and lets this call end in two ways, "returned" or "returned something else" (the reading leaves this free on purpose: RA-RES-2-OUTCOME): is any answer acceptable, or which is meant?
   - `modp(0, 0)`
2. **depends** (R-EX-3, R-RES-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `modp(1, 2) -> 0`
3. **readings** (R-RES-1): the two readings of this requirement disagree on these calls: which is meant?
   - `modp(1, 2) -> 1`
4. **ambiguity** (R-RES-1): "2^n" can mean: 2 raised to the power n (mathematical notation); every example agrees with this reading / 2 XOR n, which is what 2 ^ n means in Python code; this reading contradicts the examples modp(3, 5) = 3, modp(1101, 101) = 2, modp(0, 101) = 1 and modp(3, 11) = 8. Which is meant?
5. **ambiguity** (R-RES-1): "modulo p" can mean: the result is always reduced into 0 .. p-1, so modp(0, 1) is 0 (2^0 mod 1 = 0) / for n = 0 the value 2^0 = 1 is returned as is, as the example modp(0, 101) = 1 may be generalized to modp(0, p) = 1 for every p, so modp(0, 1) is 1; this contradicts the first reading at p = 1. Which is meant?
6. **ambiguity** (R-RES-1): "Return" can mean: the returned value is a Python int / any number equal to the residue is acceptable, such as the float 3.0 (the doctest output 3 and the frame's outcome 2 for other types argue against this). Which is meant?
7. **ambiguity** (R-EX-3): "modp(0, 101)" can mean: a single data point: only modp(0, 101) = 1 is required, consistent with reducing 2^0 = 1 modulo 101 / an illustration that modp(0, p) is 1 for every p, which contradicts R-RES-1's reduced result 2^0 mod 1 = 0 at p = 1. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-RES-1, "2^n": both took "2 raised to the power n (mathematical notation); every example agrees with this reading"
- R-RES-1, "modulo p": both took "the result is always reduced into 0 .. p-1, so modp(0, 1) is 0 (2^0 mod 1 = 0)"
- R-RES-1, "Return": both took "the returned value is a Python int"
- R-RES-2, "modulo p": both took "p = 0 is outside the function's contract: any outcome (a value, an exception, no answer) is acceptable"
- R-EX-3, "modp(0, 101)": both took "a single data point: only modp(0, 101) = 1 is required, consistent with reducing 2^0 = 1 modulo 101"

## Taken as given
The readings leave these outputs free on purpose. Where a call shows two answers, a question above asks about it:
- agent_a, RA-RES-2-OUTCOME (R-RES-2): `outcome` is free when `p == 0`
- agent_a, RA-RES-2-RESULT (R-RES-2): `result` is free when `p == 0`
- agent_b, RB-RES-2-RES (R-RES-2): `result` is free when `p == 0`
- agent_b, RB-RES-2-OUT (R-RES-2): `outcome` is free when `p == 0`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the comparison of agent_a and variant
- the comparison of agent_a and variant: it cannot assume RV-RES1-VAL (rules stated for every value of a variable), and requirements they bear on stay undecided
- the comparison of agent_b and variant
- the comparison of agent_b and variant: it cannot assume RV-RES1-VAL (rules stated for every value of a variable), and requirements they bear on stay undecided
