I split the request into 8 atomic requirements. `fcp anchor` accepted all 8 quotes on the first run and wrote `requirements.yaml`, with line numbers filled in by the tool.

| ID | Kind | Content |
|---|---|---|
| R-IF-1 | non_functional | A Python function `largest_prime_factor` that takes one integer parameter `n` |
| R-DEF-1 | definition | What a prime factor is, and what the largest one is |
| R-FN-1 | guarantee | When the assumptions hold, the call finishes and returns the largest prime factor of `n` |
| R-ENV-1 | assumption | `n > 1` |
| R-ENV-2 | assumption | `n` is not prime |
| R-EX-1 | scenario | `largest_prime_factor(13195)` returns 29 |
| R-EX-2 | scenario | `largest_prime_factor(2048)` returns 2 |
| R-FR-1 | guarantee (FRAME) | F-ZERO: `factor` is 0 unless `outcome` is 0 |

**Ambiguities flagged:**
- **R-FN-1, "Return":** it's unclear whether the result must be a Python `int`, or whether any numerically equal value is fine (e.g. `29.0`). The signature has no return annotation. Under the adapter, a non-int return counts as outcome 2.
- **R-ENV-1, "Assume n > 1":** three readings for `n` = 0 or 1:
  - anything goes;
  - it must raise an exception;
  - it must finish, but the result is otherwise free.
- **R-ENV-2, "is not a prime":** two readings for a prime `n`:
  - anything goes;
  - it must return `n` itself, because the largest prime factor of a prime is still well defined.

**No contradictions found.** Both examples satisfy the assumptions (`n` > 1 and not prime) and agree with the main rule: 13195 = 5·7·13·29 and 2048 = 2¹¹.

I added `depends` links (R-FN-1 depends on the definition and both assumptions; the two scenarios depend on R-FN-1). They aren't in your template, but the IR spec allows them and `fcp anchor` accepted them.