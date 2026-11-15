# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 7.

## This review is partial
4 of the 10 steps of the check did not end. What the other steps found stands; no requirement is settled that rests on one of these:
- the conflicts of agent_a: the translation of the monitors for the solver (yosys) did not end in 300 s
- the open choices of agent_a: the translation of the monitors for the solver (yosys) did not end in 300 s
- the conflicts of agent_b: the translation of the monitors for the solver (yosys) did not end in 300 s
- the open choices of agent_b: the translation of the monitors for the solver (yosys) did not end in 300 s

What the checking process printed about it is in check_errors.txt.

## Questions
1. **depends** (R-RES-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
2. **readings** (R-RES-1): the two readings of this requirement were not shown to agree, and no call that separates them was found: do they mean the same?
3. **ambiguity** (R-RES-1): "2^n" can mean: 2 raised to the power n (2**n) / 2 XOR n, as the ^ operator means in Python. Which is meant?
4. **ambiguity** (R-RES-1): "modulo." can mean: modulo p: the sentence is cut off and p, the only other argument, is the modulus / the modulus is not stated, so the request does not constrain the returned value (contradicts the signature declaring p with no other role; see R-SIG-1). Which is meant?
5. **ambiguity** (R-RES-1): "2^n modulo" can mean: the least non-negative remainder, in 0 to p - 1 (Python's 2**n % p) / any integer congruent to 2^n modulo p. Which is meant?
6. **ambiguity** (R-RES-1): "Return" can mean: the returned value is a Python int / any number equal in value is acceptable, such as a float (which the trace records as outcome 2). Which is meant?
7. **ambiguity** (R-RES-2): "modulo" can mean: the call ends with an exception, as Python's 2**n % 0 raises ZeroDivisionError (outcome 1) / modulo 0 is the identity, so the call returns 2^n itself (outcome 2 once 2^n exceeds 1,023) / the behaviour for p = 0 is unconstrained (don't care), since p is meant to be a positive modulus (see R-SIG-2). Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-SIG-1, "p: int": both took "p is the modulus of the docstring's 'modulo' (the name modp suggests 'mod p')"
- R-SIG-2, "n: int": both took "n may be any int, negative included (2^n is then not an integer)"
- R-SIG-2, "p: int": both took "p may be any int, so p = 0 is a legal call that modp must handle, although 2^n modulo 0 is undefined (tension with R-RES-2)"
- R-RES-1, "2^n": both took "2 raised to the power n (2**n)"
- R-RES-1, "modulo.": both took "modulo p: the sentence is cut off and p, the only other argument, is the modulus"
- R-RES-1, "2^n modulo": both took "the least non-negative remainder, in 0 to p - 1 (Python's 2**n % p)"
- R-RES-1, "Return": both took "the returned value is a Python int"
- R-RES-2, "modulo": both took "the behaviour for p = 0 is unconstrained (don't care), since p is meant to be a positive modulus (see R-SIG-2)"

## Taken as given
The readings leave these outputs free on purpose. Where a call shows two answers, a question above asks about it:
- agent_a, RA-RES-2-OUTCOME (R-RES-2): `outcome` is free when `p == 0`
- agent_a, RA-RES-2-RESULT (R-RES-2): `result` is free when `p == 0`
- agent_b, RB-RES-2-outcome (R-RES-2): `outcome` is free when `p == 0`
- agent_b, RB-RES-2-result (R-RES-2): `result` is free when `p == 0`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the scenarios of agent_b: RB-SIG-2-p0
- the comparison of agent_a and agent_b: the translation of the monitors for the solver (yosys) did not end in 300 s; what the integer encoding left open stays undecided
- the comparison of agent_a and agent_b
- the comparison of agent_a and variant: the translation of the monitors for the solver (yosys) did not end in 300 s; what the integer encoding left open stays undecided
- the comparison of agent_a and variant
- the comparison of agent_b and variant: the translation of the monitors for the solver (yosys) did not end in 300 s; what the integer encoding left open stays undecided
- the comparison of agent_b and variant
