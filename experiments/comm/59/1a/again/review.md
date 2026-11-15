# FCP review

Before any code: the request alone.

Settled: 0 requirements. Questions: 5.

## This review is partial
8 of the 10 steps of the check did not end. What the other steps found stands; no requirement is settled that rests on one of these:
- the scenarios of agent_a: passed the memory limit of 6.8 GB, also with one task at a time
- the conflicts of agent_a: passed the memory limit of 6.8 GB, also with one task at a time
- the open choices of agent_a: passed the memory limit of 6.8 GB, also with one task at a time
- the scenarios of agent_b: passed the memory limit of 6.8 GB, also with one task at a time
- the open choices of agent_b: did not end in 900 s
- the comparison of agent_a and agent_b: passed the memory limit of 6.8 GB, also with one task at a time
- the comparison of agent_a and agent_b, in context: passed the memory limit of 6.8 GB, also with one task at a time
- the comparison of agent_a and variant: passed the memory limit of 6.8 GB, also with one task at a time

## Questions
1. **depends** (R-FAC-1, R-FAC-2, R-FAC-3, R-RET-1): both readers gave the same answer to every ambiguity listed under "Shared answers"; read the other way, these requirements mean something else: are those answers meant?
2. **ambiguity** (R-FAC-3): "the smallest or largest prime factor" can mean: Either answer is acceptable on every call independently: each call may return the smallest or the largest prime factor of its n. / The implementation picks one convention and keeps it: either every call returns the smallest prime factor, or every call returns the largest. / Only the largest prime factor is correct, as the example candidate(13195) == 29 shows; 'smallest or' is not a real option. / Only the smallest prime factor is correct; this contradicts the example candidate(13195) == 29, whose smallest prime factor is 5.. Which is meant?
3. **ambiguity** (R-FAC-3): "smallest or largest (contradiction with the example candidate(13195) -> 29)" can mean: No contradiction: the example shows one allowed answer (the largest, 29); returning 5 (the smallest) for 13195 is also correct. / Contradiction: if the example is a required output, returning the smallest prime factor 5 for 13195 is wrong although 'smallest or largest' allows it, so the example overrides the 'smallest' option.. Which is meant?
4. **ambiguity** (R-EX-1): ">>> candidate(13195) 29" can mean: An illustration of one acceptable behaviour: a call candidate(13195) returning 29 must be possible, but returning 5 (the smallest prime factor) is also acceptable. / A required output: candidate(13195) must return 29, which rules out the 'smallest' option of 'smallest or largest' at least for this n (and, read as a convention, for every n).. Which is meant?
5. **ambiguity** (R-EX-1): "candidate(13195) returns 29 (contradiction with 'the smallest or largest prime factor')" can mean: Consistent: 29 is the largest prime factor, one of the two answers 'smallest or largest' allows. / Contradiction: under the reading that the smallest prime factor is required (or allowed and chosen), the answer for 13195 is 5, not 29.. Which is meant?

## Shared answers
Both readers took the same reading of these flagged phrases. A third reader took the other reading of all of them; the requirements on which its reading differs depend on these answers:
- R-ENV-1, "Assume n > 1": both took "For n <= 1 (0 and 1 in the trace) the outcome and the returned value are completely unconstrained (any value, any exception, or no answer is acceptable)."
- R-ENV-2, "is not a prime": both took "For a prime n the outcome and the returned value are completely unconstrained."
- R-FAC-3, "the smallest or largest prime factor": both took "Either answer is acceptable on every call independently: each call may return the smallest or the largest prime factor of its n."
- R-EX-1, "candidate(13195) returns 29 (contradiction with 'the smallest or largest prime factor')": both took "Consistent: 29 is the largest prime factor, one of the two answers 'smallest or largest' allows."

## Taken as given
The readings take these conditions on the caller from the request. A reading says nothing about a call outside its conditions, and no open choice is reported there:
- agent_a, RA-ENV-1-OUT (R-ENV-1): `outcome` is free when `n <= 1`
- agent_a, RA-ENV-1-FAC (R-ENV-1): `factor` is free when `n <= 1`
- agent_a, RA-ENV-2-OUT (R-ENV-2): `outcome` is free when `n_prime`; `n_prime` is `n > 1 && !any(d < 256: d >= 2 && d < n && n_divs[d])`
- agent_a, RA-ENV-2-FAC (R-ENV-2): `factor` is free when `n_prime`; `n_prime` is `n > 1 && !any(d < 256: d >= 2 && d < n && n_divs[d])`
- agent_b, RB-A-ENV-1 (R-ENV-1): every call meets `n > 1`
- agent_b, RB-A-ENV-2 (R-ENV-2): every call meets `!n_prime`; `n_prime` is `n >= 2 && all(i < 254: i + 2 < n -> n % (i + 2) != 0)`
- agent_b, RB-D-ENV-1-OUTCOME (R-ENV-1): `outcome` is free when `n <= 1`
- agent_b, RB-D-ENV-1-FACTOR (R-ENV-1): `factor` is free when `n <= 1`
- agent_b, RB-D-ENV-2-OUTCOME (R-ENV-2): `outcome` is free when `n_prime`; `n_prime` is `n >= 2 && all(i < 254: i + 2 < n -> n % (i + 2) != 0)`
- agent_b, RB-D-ENV-2-FACTOR (R-ENV-2): `factor` is free when `n_prime`; `n_prime` is `n >= 2 && all(i < 254: i + 2 < n -> n % (i + 2) != 0)`

## Limits of this review
These searches were cut short, by their time budget or by a rule they cannot use. What they found stands; what lies beyond was not searched:
- conflict search of agent_b
- the comparison of agent_b and variant
- the comparison of agent_b and variant: it cannot assume RV-FAC-3 (rules stated for every value of a variable), and requirements they bear on stay undecided
