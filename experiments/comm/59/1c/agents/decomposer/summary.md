I split the request into 8 atomic requirements. The anchor command accepted all 8 quotes as verbatim on the first run, and the result is in `requirements.yaml`.

| ID | Kind | Content |
|---|---|---|
| R-IF-1 | non_functional | Fill in the given function stub ("Complete this function:") |
| R-IF-2 | definition | The function is `largest_prime_factor` and takes one integer argument `n` |
| R-FN-1 | guarantee | It returns the largest prime that divides `n` |
| R-ENV-1 | assumption | `n > 1` |
| R-ENV-2 | assumption | `n` is not a prime |
| R-EX-1 | scenario | `largest_prime_factor(13195)` returns `5` |
| R-EX-2 | scenario | `largest_prime_factor(2048)` returns `2` |
| R-FR-1 (FRAME) | guarantee | F-ZERO: `factor` is 0 unless `outcome` is 0 |

**Ambiguities and contradictions flagged:**
- **R-FN-1 contradicts R-EX-1.** 13195 = 5·7·13·29, so its largest prime factor is 29, but the example says 5. I recorded this as an ambiguity on both requirements. One reading treats the example as wrong. The other treats the examples as authoritative: 5 is the *smallest* prime factor of 13195, and the 2048 → 2 example fits either reading.
- **R-ENV-1 ("Assume n > 1").** One reading lets the function do anything when `n ≤ 1`. The other says it should raise an error. This matters because the checker also calls the function with 0 and 1.
- **R-ENV-2 ("is not a prime").** One reading lets the function do anything when `n` is prime. The other says it should still return `n` itself, since a prime's largest prime factor is the number itself.

R-EX-2 has no conflict with anything else.