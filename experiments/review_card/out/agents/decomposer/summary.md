I wrote 24 requirements to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`, and all 24 entries now have line numbers.

**How the request breaks down**
- **Interface:** one non_functional requirement for the `GiftCard` class with its three methods (R-IF-1), and three guarantees on what each method returns (R-IF-2 to 4).
- **Units and start state:** "in cents" is a definition (R-UNIT-1), and "a new card has a balance of 0" is a guarantee (R-INIT-1).
- **Rule 1** became 4 requirements, one for each method and each bound (R-VAL-1 to 4).
- **Rules 2 to 6:** adding the amount on a load (R-LOAD-1), the $500.00 cap and the ValueError for a load over it (R-CAP-1, R-CAP-2), the bonus being added, returned, or 0 if none (R-BON-1 to 3), spend's deduction, True, False and balance-unchanged cases (R-SPD-1 to 4), and `balance()` (R-BAL-1).
- **The example** is a scenario (R-EX-1).
- **Frame rules:** F-ZERO and F-OTHER are R-FR-1 and R-FR-2, the IDs `design.yaml` already uses for them.

**Contradictions** (each one is recorded as an ambiguity on both requirements)
1. **The cap against the bonus** (R-CAP-1, R-CAP-2, R-BON-1): if "a load that would take it over" counts only the amount, then `load(50000)` on a new card passes and the $5.00 bonus brings the balance to 50,500, breaking "never more than $500.00". I listed four ways to resolve it: allow it over the cap, raise ValueError, cut the bonus, or drop the bonus.
2. **Rule 1 against rule 5 for `spend(0)`** (R-VAL-3 and R-SPD-2): rule 1 says ValueError, but any balance covers 0, so rule 5 says True.
3. **Rule 1 against rule 5 for `spend(50001)`** (R-VAL-4 and R-SPD-3): rule 1 says ValueError, but the balance can never cover it, so rule 5 says False.

**Other ambiguities flagged**
- Whether rule 1 applies to `spend` at all, or only to `load`.
- What happens to the balance when a call raises ValueError: unchanged, or not specified.
- "a $5.00 bonus": a flat 500 cents per qualifying load, or 500 cents for each full $100.00 loaded.
- "on the card": added to the balance, or kept separately.
- What "the bonus it earned" means when the cap cuts the bonus.
- "covers": the balance is at least the amount, or strictly more than it.

The task asked for `design: review`, so that is what the draft uses, but `design.yaml` names the design `code_card`. The anchor step didn't complain, but anything later that compares the two names may not match.