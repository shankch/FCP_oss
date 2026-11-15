# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 3.

## This review is partial
5 of the 10 steps of the check did not end. What the other steps found stands; no requirement is settled that rests on one of these:
- the scenarios of agent_a: passed the memory limit of 6.8 GB, also with one task at a time
- the open choices of agent_a: did not end in 900 s
- the comparison of agent_a and agent_b, in context: was stopped: the check reached its time limit of 2340 s
- the comparison of agent_a and variant: not run: the check reached its time limit of 2340 s
- the comparison of agent_b and variant: not run: the check reached its time limit of 2340 s

## Questions
1. **scenario** (R-EX-1): the behaviour RB-EX-1 describes can never happen under agent_b: the reading's own rules forbid it. Is the example, or the rule, what is meant?
2. **ambiguity** (R-FN-1): "the largest prime factor of n" can mean: the greatest prime p that divides n, as the words say (for 13195 = 5 * 7 * 13 * 29 this is 29), which contradicts the example largest_prime_factor(13195) -> 5 (R-EX-1) / the value the examples show: for 13195 the example gives 5, which is the smallest prime factor of 13195 (and 2 for 2048 fits both), so the intended result follows the examples (smallest prime factor) rather than the words. Which is meant?
3. **ambiguity** (R-EX-1): "largest_prime_factor(13195) 5" can mean: the example is wrong: 13195 = 5 * 7 * 13 * 29, so by R-FN-1 the largest prime factor is 29 and the call must return 29, not 5 / the example is authoritative: the call must return 5 (the smallest prime factor of 13195), and R-FN-1's 'largest' is to be read through the examples. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-FN-1, "the largest prime factor of n": both took "the greatest prime p that divides n, as the words say (for 13195 = 5 * 7 * 13 * 29 this is 29), which contradicts the example largest_prime_factor(13195) -> 5 (R-EX-1)"
- R-ENV-1, "Assume n > 1": both took "a precondition on the caller: for n <= 1 any outcome (any returned value, an exception, no answer) is acceptable"
- R-ENV-2, "and is not a prime": both took "a precondition on the caller: for a prime n any outcome is acceptable"
- R-EX-1, "largest_prime_factor(13195) 5": both took "the example is authoritative: the call must return 5 (the smallest prime factor of 13195), and R-FN-1's 'largest' is to be read through the examples"

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-ENV-1 (R-ENV-1): every call meets `n > 1`
- agent_a, RA-ENV-2 (R-ENV-2): every call meets `!n_prime`; `n_prime` is `n >= 2 && all(i < 254: (i + 2) * (i + 2) <= n -> n % (i + 2) != 0)`
- agent_b, RB-ENV-1 (R-ENV-1): every call meets `n > 1`
- agent_b, RB-ENV-2 (R-ENV-2): every call meets `!n_is_prime`; `n_is_prime` is `n >= 2 && all(j < 54: primes[j] * primes[j] <= n -> n % primes[j] != 0)`
- agent_b, RB-ENV-1-D-OUT (R-ENV-1): `outcome` is free when `n <= 1`
- agent_b, RB-ENV-1-D-FAC (R-ENV-1): `factor` is free when `n <= 1`
- agent_b, RB-ENV-2-D-OUT (R-ENV-2): `outcome` is free when `n_is_prime`; `n_is_prime` is `n >= 2 && all(j < 54: primes[j] * primes[j] <= n -> n % primes[j] != 0)`
- agent_b, RB-ENV-2-D-FAC (R-ENV-2): `factor` is free when `n_is_prime`; `n_is_prime` is `n >= 2 && all(j < 54: primes[j] * primes[j] <= n -> n % primes[j] != 0)`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- the comparison of agent_a and agent_b
- the comparison of agent_a and agent_b: it cannot assume RA-FN-1-MAX (rules stated for every value of a variable), and requirements they bear on stay undecided
