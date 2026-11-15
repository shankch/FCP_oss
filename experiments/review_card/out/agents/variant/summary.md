I wrote `formal/variant.yaml`. It lints clean, and I read back the `fcp explain` rendering: each item means what I intended. I also ran the spec-only `fcp check` on the set. It is consistent, the R-EX-1 scenario can be reached, there are no tautologies, and none of the 133 call sequences it checked showed a conflict.

**Items:** 25 in total, 24 properties and 1 scenario (RV-EX-1), plus 20 `decisions`. Every phrase from your list is applied as given, and the note of each affected item says so. The card's balance is internal, so I used four ghosts: `bal` (the modelled balance), `known` (whether the model knows it), `earned` (bonuses kept on the card outside the balance) and `fresh` (no call made yet, for "on a new card").

**Unformalized (4):**
- **R-IF-1:** class and method names are structural; the adapter handles them, so they aren't a property of the trace.
- **R-UNIT-1:** a definition of units, covered by the items that use 50000, 10000 and 500.
- **R-FR-1 and R-FR-2:** frame rules that every set gets automatically, covered by F-ZERO and F-OTHER.

**Readings I chose myself (not in your list):**
- **"Raise ValueError":** I took reading 2, the literal one. The balance after a ValueError is unspecified, bounded only by R-CAP-1, and the model takes it back from the next `balance()` call. Because of this, `outcome`, `spent` and `balance` are not fully determined. Every witness the check found starts with a call that raised ValueError; `bonus` is fully determined.
- **R-CAP-2 "raise ValueError for a load":** also reading 2, for the same reason.
- **R-SPD-2 and R-SPD-3:** reading 1 ("for every amount"), which fits your load-only readings of R-VAL-3 and R-VAL-4.
- **Valid loads succeed:** the decomposed R-LOAD-1 doesn't say this. I read rule 2 ("`load` adds `amount`") as unconditional, so a load that rules 1 and 3 don't reject must not raise (RV-LOAD-1b).

**Problems in the specification and the required readings:**
1. **The readings contradict each other.** The readings for R-CAP-1, R-CAP-2 and R-BON-1 all use the example "load(50000) on a new card leaves 50,500", which assumes the bonus goes into the balance. The readings for R-LOAD-1 and R-BON-1 "on the card" say it doesn't. In this set the balance is 50,000 after that load.
2. **The bonus is never visible.** R-BON-2 read as "the bonus actually added to the balance", together with the R-LOAD-1 and "on the card" readings, makes `load` always return 0. That contradicts R-BON-2's own "(500 for a $5.00 bonus)", and the bonus R-BON-1 grants is never reported. Its size (500 per full $100) only shows up as extra allowance in the R-CAP-1 bound. The "cap cuts it" clause never applies, because R-BON-1 is read as granting the full bonus.
3. **spend(0) doesn't always return True.** The R-VAL-3 reading says spend(0) returns True by R-SPD-2. With "covers" read as strictly more than the amount, that only holds when the balance is above 0; on a new card spend(0) returns False. The same reading means the whole balance can never be spent.
4. **Rule 1 doesn't name a method.** It says `amount` without saying load or spend, so in the specification text itself the clash between R-VAL-3/4 and R-SPD-2/3 is real.

The check run left temporary files in the workspace; I deleted them, so only `formal/variant.yaml` was added.