I wrote `requirements_draft.yaml` with 10 requirements. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml` ("anchored 10 requirements").

**Requirements**
- **R-IF-1** (non_functional): the code is a Python function `candidate` that takes one integer `n`.
- **R-DEF-1** (definition): a prime is an integer greater than 1 whose only divisors are 1 and itself.
- **R-ENV-1, R-ENV-2** (assumptions): `n > 1`, and `n` is not prime.
- **R-ENV-3** (dont_care): when `n ≤ 1` or `n` is prime, the request sets no obligation.
- **R-RET-1..4** (guarantees, all conditional on the assumptions): the call returns an integer normally; the result divides `n`; the result is prime; the result is "the" prime factor, i.e. one specific factor.
- **R-FR-1** (FRAME, F-ZERO): `factor` is 0 unless `outcome` is 0.

The request has no examples, so there are no scenarios.

**Ambiguities flagged**
- **"the prime factor" (R-RET-4):** this is the main open question. The readings are any prime factor, the smallest, the largest, or the unique one (only defined when `n` is a power of a single prime).
- **Contradiction, recorded on both R-RET-4 and R-ENV-2:** "the" implies there is only one prime factor. But "not a prime" allows numbers like 6 = 2·3, which have two. R-ENV-2 has two readings: `n` is any composite number, or `n` is meant to be a power of one prime.
- **"Assume" (R-ENV-3):** what happens when the assumption fails. The readings are any behaviour (including raising an exception or never finishing), a normal integer return whose value is free, or returning `n` itself when `n` is prime.
- **"Return" (R-RET-1):** whether the result must be a Python `int`, or a number of equal value such as `3.0` is also acceptable. This matters because the adapter records a float as outcome 2, not outcome 0.