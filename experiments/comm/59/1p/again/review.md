# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 3.

## This review is partial
7 of the 10 steps of the check did not end. What the other steps found stands; no requirement is settled that rests on one of these:
- the scenarios of agent_a: passed the memory limit of 6.8 GB, also with one task at a time
- the scenarios of agent_b: passed the memory limit of 6.8 GB, also with one task at a time
- the open choices of agent_b: did not end in 900 s
- the comparison of agent_a and agent_b: was stopped: the check reached its time limit of 2340 s
- the comparison of agent_a and agent_b, in context: not run: the check reached its time limit of 2340 s
- the comparison of agent_a and variant: not run: the check reached its time limit of 2340 s
- the comparison of agent_b and variant: not run: the check reached its time limit of 2340 s

## Questions
1. **open** (factor): the request allows 2 or 3: which is meant?
   - `candidate(6)`
2. **ambiguity** (R-RET-1): "Return" can mean: the returned value must be a Python int / any number numerically equal to the required prime factor (for example the float 3.0) is acceptable. Which is meant?
3. **ambiguity** (R-RET-4): "the prime factor" can mean: any prime factor of n is acceptable (the definite article is loose) / the smallest prime factor of n / the largest prime factor of n / the unique prime factor of n: defined only when n has exactly one distinct prime factor (n is a prime power), with calls on n having several distinct prime factors outside the contract (contradicts 'is not a prime' in R-ENV-2, which admits such n). Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-ENV-2, "is not a prime": both took "n may be any composite number, including one with several distinct prime factors (such as 6 = 2 * 3), so 'the prime factor' (R-RET-4) has to pick one of them or accept any"
- R-ENV-3, "Assume": both took "a pure precondition: on n <= 1 or prime n any behaviour is acceptable, including raising an exception or not finishing"
- R-RET-1, "Return": both took "the returned value must be a Python int"
- R-RET-4, "the prime factor": both took "the unique prime factor of n: defined only when n has exactly one distinct prime factor (n is a prime power), with calls on n having several distinct prime factors outside the contract (contradicts 'is not a prime' in R-ENV-2, which admits such n)"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-ENV-1 (R-ENV-1): every call meets `n > 1`
- agent_a, RA-ENV-2 (R-ENV-2): every call meets `!n_prime`; `n_prime` is `n > 1 && all(i < 254: i + 2 < n -> n % (i + 2) != 0)`
- agent_b, RB-A-ENV1 (R-ENV-1): every call meets `n > 1`
- agent_b, RB-A-ENV2 (R-ENV-2): every call meets `!n_prime`; `n_prime` is `n >= 2 && all(i < 254: (i + 2) * (i + 2) <= n -> n % (i + 2) != 0)`
The readings leave these outputs free on purpose. Where a call shows two answers, a question above asks about it:
- agent_a, RA-ENV-3-OUTCOME (R-ENV-3): `outcome` is free when `n <= 1 || n_prime`; `n_prime` is `n > 1 && all(i < 254: i + 2 < n -> n % (i + 2) != 0)`
- agent_a, RA-ENV-3-FACTOR (R-ENV-3): `factor` is free when `n <= 1 || n_prime`; `n_prime` is `n > 1 && all(i < 254: i + 2 < n -> n % (i + 2) != 0)`
- agent_b, RB-D-ENV3-OUTCOME (R-ENV-3): `outcome` is free when `!in_contract`; `in_contract` is `n > 1 && !n_prime`
- agent_b, RB-D-ENV3-FACTOR (R-ENV-3): `factor` is free when `!in_contract`; `in_contract` is `n > 1 && !n_prime`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- conflict search of agent_a
