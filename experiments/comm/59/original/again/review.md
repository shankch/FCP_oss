# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 1.

## This review is partial
6 of the 10 steps of the check did not end. What the other steps found stands; no requirement is settled that rests on one of these:
- the scenarios of agent_a: passed the memory limit of 6.8 GB, also with one task at a time
- the open choices of agent_a: did not end in 900 s
- the scenarios of agent_b: passed the memory limit of 6.8 GB, also with one task at a time
- the comparison of agent_a and agent_b, in context: was stopped: the check reached its time limit of 2340 s
- the comparison of agent_a and variant: not run: the check reached its time limit of 2340 s
- the comparison of agent_b and variant: not run: the check reached its time limit of 2340 s

## Questions
1. **ambiguity** (R-FN-1): "Return" can mean: The returned value must be a Python int equal to the largest prime factor. / Any returned value numerically equal to the largest prime factor is acceptable, e.g. the float 29.0 or a numpy integer (no return type is annotated in the signature).. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-FN-1, "Return": both took "The returned value must be a Python int equal to the largest prime factor."
- R-ENV-1, "Assume n > 1": both took "Precondition only: for n <= 1 (0 and 1 here) any behaviour is acceptable: any returned value, any exception, or not finishing."
- R-ENV-2, "is not a prime": both took "Precondition only: for prime n any behaviour is acceptable: any returned value, any exception, or not finishing."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-ENV-1 (R-ENV-1): every call meets `n > 1`
- agent_a, RA-ENV-2 (R-ENV-2): every call meets `!n_prime`; `n_prime` is `n >= 2 && all(i < 254: n == i + 2 || n % (i + 2) != 0)`
- agent_b, RB-ENV-1 (R-ENV-1): every call meets `n > 1`
- agent_b, RB-ENV-2 (R-ENV-2): every call meets `!n_prime`; `n_prime` is `n >= 2 && all(j < 54: primes[j] < n -> n % primes[j] != 0)`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- conflict search of agent_a
- the comparison of agent_a and agent_b
