I wrote the `GiftCard` class and 42 pytest tests for it, and all 42 pass with the command you gave. Nothing needed fixing.

**How it works:** the card keeps its balance as an integer number of cents and starts at 0. `load` and `spend` both check `amount` first. `load` works out the bonus ($5.00 when the load is $100.00 or more), refuses the load if the amount plus the bonus would take the balance over $500.00, and returns the bonus. `spend` takes the amount off only if the balance covers it. When anything raises or returns False, the balance is unchanged.

**The tests** cover the example from the request, the edges of every rule (1, 50,000, 50,001, 9,999 vs 10,000, landing exactly on the $500.00 limit, one cent over the balance), and 5,000 random loads and spends checked against a simple running total.

**Decisions where the request was unclear:**
1. **The bonus counts toward the $500.00 limit.** If the amount plus the $5.00 bonus would go over, the whole load raises `ValueError`. This is the only reading that keeps both "never more than $500.00" and "every load … earns a $5.00 bonus". The catch is that loads from 49,501 to 50,000 cents can never succeed, even on an empty card, though rule 1 allows them. The other choices would be to shrink the bonus to fit, which breaks "every load earns $5.00", or to let the balance go over, which breaks rule 3. **The store team should confirm which one they want.**
2. **The range check in rule 1 applies to `spend` as well as `load`.** So `spend(50001)` raises `ValueError` rather than returning False.
3. **"The balance covers it" means the balance is at least the amount,** so spending the exact balance succeeds and leaves 0.
4. **The bonus is per load and depends only on that load's amount.** Several smaller loads that add up to $100.00 earn nothing, and `spend` never earns a bonus.
5. **Amounts that aren't whole numbers raise `TypeError`,** which the request didn't cover. That includes floats, strings, `None`, and `True`/`False` (Python treats True and False as integers, but they aren't amounts).
6. **The limits are named constants** at the top of the file. `GiftCard()` takes no arguments.

Files are in /work/ws_card_impl_opus:
- gift_card.py
- test_gift_card.py
