I've written `requirements_draft.yaml` and anchored it. `fcp anchor` accepted all 11 quotes on the first run (no quotes were rejected), and the result is in `requirements.yaml`.

**The requirements:**
- **R-GEN-1** (non_functional): fill in the body of the given function and keep its signature.
- **R-ARG-1** (definition): there is one integer argument, `n`.
- **R-ENV-1 and R-ENV-2** (assumption): `n > 1`, and `n` is not prime. These are two separate requirements.
- **R-RET-1**: for allowed `n`, the call finishes and returns an integer (outcome 0).
- **R-FAC-1**: the result divides `n`.
- **R-FAC-2**: the result is prime.
- **R-FAC-3**: the result is the smallest or the largest prime factor, and never one in between.
- **R-EX-1 and R-EX-2** (scenario): `candidate(13195)` returns 29, and `candidate(2048)` returns 2.
- **R-FR-1** (FRAME, for rule F-ZERO): `factor` is 0 unless `outcome` is 0.

**Ambiguities flagged:**
- **"smallest or largest"** (R-FAC-3) has four readings:
  - each call may return either one;
  - the code picks one and always returns that one;
  - only the largest counts, as the example suggests;
  - only the smallest counts.
- **Contradiction between R-FAC-3 and the 13195 example.** 29 is the largest prime factor of 13195; the smallest is 5. If the example is a required output, it rules out the "smallest" option. If it just illustrates one allowed answer, there is no conflict. I recorded this as an ambiguity on both R-FAC-3 and R-EX-1.
- **Inputs outside the assumptions** (R-ENV-1, R-ENV-2): either the behaviour is completely free, or it still has to be defined. For a prime `n`, one reading says the function should return `n` itself, since `n` is then its own smallest and largest prime factor.