I wrote `formal/variant2.yaml`. `fcp lint` reports no errors, and the `fcp explain` output matches what I meant for every item.

**Items: 10.** There is 1 assumption, 8 properties and 1 scenario, plus the frame rule F-ZERO, which is added to every set automatically.
- **Hidden state:** the card's balance can only be seen through `balance()`, so it needed one ghost, `b`. It starts at 0. An accepted load adds the amount plus its bonus, a spend the balance covers takes the amount off, and every other call leaves it unchanged. `V2-BAL-1` (`balance()` returns `b`) is what checks those changes. Everything else relates the interface signals directly using `implies`.
- **One item per requirement:**
  - R-NEW-1: while only `balance()` has been called on a card, it returns 0.
  - R-RANGE-1: load or spend with an amount outside 1..50,000 raises ValueError.
  - R-LOAD-1: a valid load that stays within the cap returns.
  - R-CAP-1 (two items): a load over the cap raises ValueError, and `balance()` never returns more than 50,000.
  - R-BONUS-1: a load that returns gives 500 if the amount is 10,000 or more, otherwise 0.
  - R-SPEND-1: a valid spend returns, with `ok == (b >= amount)`.
  - R-BAL-1: `balance()` returns `b`.
  - R-EX-1: a scenario (cover).
- **Assumption `V2-A-OP` (R-SIG-1):** `op != 0`, because every call is one of the three methods.
- **Ambiguity decision:** R-CAP-1 uses reading 2 as you instructed: a load is over the cap when balance + amount + bonus is more than $500.00. It is recorded under `decisions`, and the note of every item it affects says so.

**Unformalized:** only R-FR-1. It is the adapter's frame rule, which holds by construction, so I didn't restate it. It is marked `covered_by: [F-ZERO]`.

**Problems in the specification:**
1. **Rules 1 and 5 contradict each other for spends.** Read literally, rule 5 makes `spend(0)` return True (the balance "covers" 0) and makes a spend over 50,000 return False, while rule 1 says both raise. I let rule 1 take precedence, as the requirement texts do, and said so in the notes.
2. **Rule 2 has no conditions.** "load adds amount to the balance" ignores rules 1 and 3. I limited it to loads those rules accept.
3. **What a failed call does to the balance is never stated.** I assumed a call that raises ValueError leaves the balance unchanged. That is the usual meaning of rejecting a call, but it is my reading, not the text's.
4. **The cap and the bonus interact (the flagged phrase).** Under reading 2, a load whose amount fits but whose bonus doesn't is rejected: for example, `load(10000)` on a 40,000 balance raises. Under reading 1 the bonus could push the balance over $500.00, which breaks "never more than $500.00".
5. **The example never says "new card".** That condition comes only from the R-EX-1 text. Since the card's only state is its balance, I wrote it as "balance 0 before the load" instead of adding a ghost that counts calls.
6. **Minor points.** Rule 1 says "amount" without naming the methods; I applied it to load and spend, since `balance()` takes no amount. "Every load of $100.00 or more earns a $5.00 bonus" gives one bonus per load, however large the load.