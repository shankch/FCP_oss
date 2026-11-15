# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 14.

## This review is partial
3 of the 11 steps of the check did not end. What the other steps found stands; no requirement is settled that rests on one of these:
- the conflicts of agent_a: the translation of the monitors for the solver (yosys) did not end in 300 s
- the open choices of agent_a: the translation of the monitors for the solver (yosys) did not end in 300 s
- the scenarios of agent_b: passed the memory limit of 6.8 GB, also with one task at a time

What the checking process printed about it is in check_errors.txt.

## Questions
1. **open** (result, outcome, R-MOD-1): the request allows `result` to be 0 or 1 (the reading leaves this free on purpose: RB-MOD-1-Y0-RESULT) and lets this call end in two ways, "returned" or "raised another exception or did not finish" (the reading leaves this free on purpose: RB-MOD-1-Y0-OUTCOME): is any answer acceptable, or which is meant?
   - `candidate(0, 0)`
2. **depends** (R-MOD-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
   - `candidate(0, 2) -> 1`
3. **readings** (R-EX-1): the two readings of this requirement were not shown to agree, and no call that separates them was found: do they mean the same?
4. **readings** (R-EX-2): the two readings of this requirement were not shown to agree, and no call that separates them was found: do they mean the same?
5. **readings** (R-EX-3): the two readings of this requirement were not shown to agree, and no call that separates them was found: do they mean the same?
6. **readings** (R-EX-4): the two readings of this requirement were not shown to agree, and no call that separates them was found: do they mean the same?
7. **readings** (R-EX-5): the two readings of this requirement were not shown to agree, and no call that separates them was found: do they mean the same?
8. **readings** (R-MOD-1): the two readings of this requirement were not shown to agree, and no call that separates them was found: do they mean the same?
9. **ambiguity** (R-MOD-1): "2^n modulo p" can mean: n is the first argument x and p is the second argument y (all five examples agree with this) / n is the second argument y and p is the first argument x. Which is meant?
10. **ambiguity** (R-MOD-1): "2^n" can mean: 2 raised to the power n / 2 XOR n, which is what the operator ^ means in Python. Which is meant?
11. **ambiguity** (R-MOD-1): "modulo p" can mean: the least non-negative residue, a value in 0..p-1; for example candidate(0, 1) returns 0 / any integer congruent to 2^n modulo p; for example candidate(0, 1) may return 1 instead of 0. Which is meant?
12. **ambiguity** (R-MOD-1): "modulo p, when p is 0" can mean: modulo 0 is undefined, so for y = 0 the call may end in any way / for y = 0 the call must raise an exception, as division by zero does in Python / for y = 0 the call returns 2^n unreduced, by the convention that a modulo 0 is a. Which is meant?
13. **ambiguity** (R-MOD-1): "p" can mean: p is any positive integer modulus / p denotes a prime (every example uses one of the primes 5, 11, 101), so calls with a non-prime y are outside the contract. Which is meant?
14. **ambiguity** (R-MOD-1): "Return" can mean: the returned value must be a Python int (the examples print 3, not 3.0) / any value numerically equal to the residue is acceptable, for example the float 3.0. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-SIG-2, "x: int, y: int": both took "x is the exponent the docstring calls n, and y is the modulus it calls p (all five examples agree with this)"
- R-MOD-1, "2^n modulo p": both took "n is the first argument x and p is the second argument y (all five examples agree with this)"
- R-MOD-1, "2^n": both took "2 raised to the power n"
- R-MOD-1, "modulo p": both took "the least non-negative residue, a value in 0..p-1; for example candidate(0, 1) returns 0"
- R-MOD-1, "modulo p, when p is 0": both took "modulo 0 is undefined, so for y = 0 the call may end in any way"
- R-MOD-1, "p": both took "p is any positive integer modulus"
- R-MOD-1, "Return": both took "the returned value must be a Python int (the examples print 3, not 3.0)"
- R-NUM-1, "be aware of numerics": both took "the result must be exact: no floating-point arithmetic (such as math.pow) that loses precision for large n"

## Taken as given
The readings leave these outputs free on purpose. Where a call shows two answers, a question above asks about it:
- agent_a, RA-MOD-Z1 (R-MOD-1): `outcome` is free when `y == 0`
- agent_a, RA-MOD-Z2 (R-MOD-1): `result` is free when `y == 0`
- agent_b, RB-MOD-1-Y0-OUTCOME (R-MOD-1): `outcome` is free when `y == 0`
- agent_b, RB-MOD-1-Y0-RESULT (R-MOD-1): `result` is free when `y == 0`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the scenarios of agent_a: RA-EX-1C, RA-EX-2C, RA-EX-3C, RA-EX-4C, RA-EX-5C
- conflict search of agent_b
- the comparison of agent_a and agent_b: the translation of the monitors for the solver (yosys) did not end in 300 s; what the integer encoding left open stays undecided
- the comparison of agent_a and agent_b
- the comparison of agent_a and variant: the translation of the monitors for the solver (yosys) did not end in 300 s; what the integer encoding left open stays undecided
- the comparison of agent_a and variant
