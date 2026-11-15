# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 10.

## This review is partial
4 of the 10 steps of the check did not end. What the other steps found stands; no requirement is settled that rests on one of these:
- the conflicts of agent_a: the translation of the monitors for the solver (yosys) did not end in 300 s
- the open choices of agent_a: the translation of the monitors for the solver (yosys) did not end in 300 s
- the conflicts of agent_b: the translation of the monitors for the solver (yosys) did not end in 300 s
- the open choices of agent_b: the translation of the monitors for the solver (yosys) did not end in 300 s

What the checking process printed about it is in check_errors.txt.

## Questions
1. **depends** (R-RET-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
2. **readings** (R-RET-1): the two readings of this requirement were not shown to agree, and no call that separates them was found: do they mean the same?
3. **ambiguity** (R-RET-1): "2^n" can mean: 2 raised to the power n (Python 2 ** n) / the Python expression 2 ^ n, i.e. bitwise XOR of 2 and n. Which is meant?
4. **ambiguity** (R-RET-1): "modulo p" can mean: p = 0 is outside the intended domain; the result for p = 0 is unconstrained (don't care) / for p = 0 the call fails with an exception, as Python's 2 ** n % 0 raises ZeroDivisionError / for p = 0 the call returns some integer (for example 2 ** n unreduced, or 0). Which is meant?
5. **ambiguity** (R-RET-1): "Return 2^n modulo p" can mean: the formula governs: the result is (2 ** n) % p, which is always below p and therefore contradicts every docstring example (each shows the result p) / the docstring examples govern: modp(3, 5) is 5, modp(1101, 101) is 101, modp(0, 101) is 101, modp(3, 11) is 11 and modp(100, 101) is 101, so the formula does not describe the intended result (at least on those calls). Which is meant?
6. **ambiguity** (R-EX-1): ">>> modp(3, 5) 5" can mean: the example is authoritative: modp(3, 5) returns 5 (contradicts R-RET-1, since 2^3 modulo 5 is 3) / the example is erroneous and R-RET-1 governs: modp(3, 5) returns 3. Which is meant?
7. **ambiguity** (R-EX-2): ">>> modp(1101, 101) 101" can mean: the example is authoritative: modp(1101, 101) returns 101 (contradicts R-RET-1, since 2^1101 modulo 101 is 2) / the example is erroneous and R-RET-1 governs: modp(1101, 101) returns 2. Which is meant?
8. **ambiguity** (R-EX-3): ">>> modp(0, 101) 101" can mean: the example is authoritative: modp(0, 101) returns 101 (contradicts R-RET-1, since 2^0 modulo 101 is 1) / the example is erroneous and R-RET-1 governs: modp(0, 101) returns 1. Which is meant?
9. **ambiguity** (R-EX-4): ">>> modp(3, 11) 11" can mean: the example is authoritative: modp(3, 11) returns 11 (contradicts R-RET-1, since 2^3 modulo 11 is 8) / the example is erroneous and R-RET-1 governs: modp(3, 11) returns 8. Which is meant?
10. **ambiguity** (R-EX-5): ">>> modp(100, 101) 101" can mean: the example is authoritative: modp(100, 101) returns 101 (contradicts R-RET-1, since 2^100 modulo 101 is 1) / the example is erroneous and R-RET-1 governs: modp(100, 101) returns 1. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-RET-1, "2^n": both took "2 raised to the power n (Python 2 ** n)"
- R-RET-1, "modulo p": both took "p = 0 is outside the intended domain; the result for p = 0 is unconstrained (don't care)"
- R-RET-1, "Return 2^n modulo p": both took "the formula governs: the result is (2 ** n) % p, which is always below p and therefore contradicts every docstring example (each shows the result p)"
- R-EX-1, ">>> modp(3, 5) 5": both took "the example is authoritative: modp(3, 5) returns 5 (contradicts R-RET-1, since 2^3 modulo 5 is 3)"
- R-EX-2, ">>> modp(1101, 101) 101": both took "the example is authoritative: modp(1101, 101) returns 101 (contradicts R-RET-1, since 2^1101 modulo 101 is 2)"
- R-EX-3, ">>> modp(0, 101) 101": both took "the example is authoritative: modp(0, 101) returns 101 (contradicts R-RET-1, since 2^0 modulo 101 is 1)"
- R-EX-4, ">>> modp(3, 11) 11": both took "the example is authoritative: modp(3, 11) returns 11 (contradicts R-RET-1, since 2^3 modulo 11 is 8)"
- R-EX-5, ">>> modp(100, 101) 101": both took "the example is authoritative: modp(100, 101) returns 101 (contradicts R-RET-1, since 2^100 modulo 101 is 1)"

## Taken as given
The readings leave these outputs free on purpose. Where a call shows two answers, a question above asks about it:
- agent_a, RA-RET-3 (R-RET-1): `result` is free when `p == 0`
- agent_a, RA-RET-4 (R-RET-1): `outcome` is free when `p == 0`
- agent_b, RB-RET-1-P0-OUT (R-RET-1): `outcome` is free when `p == 0`
- agent_b, RB-RET-1-P0-RES (R-RET-1): `result` is free when `p == 0`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the scenarios of agent_a: RA-EX-1, RA-EX-2, RA-EX-3, RA-EX-4, RA-EX-5
- the scenarios of agent_b: RB-EX-1, RB-EX-2, RB-EX-3, RB-EX-4, RB-EX-5
- the comparison of agent_a and agent_b: the translation of the monitors for the solver (yosys) did not end in 300 s; what the integer encoding left open stays undecided
- the comparison of agent_a and agent_b
- the comparison of agent_a and variant: the translation of the monitors for the solver (yosys) did not end in 300 s; what the integer encoding left open stays undecided
- the comparison of agent_a and variant
- the comparison of agent_b and variant: the translation of the monitors for the solver (yosys) did not end in 300 s; what the integer encoding left open stays undecided
- the comparison of agent_b and variant
