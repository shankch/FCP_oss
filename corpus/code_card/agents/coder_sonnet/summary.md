I wrote `GiftCard` and its tests, and all 38 tests pass.

`GiftCard` keeps its balance in integer cents. `load`, `spend` and `balance` follow the six rules in the request. Invalid and rejected calls change nothing.

Where the request was unclear, I decided as follows:

1. **Bonus and the $500 cap:** a load is rejected if the balance plus the amount plus the bonus would be over 50,000 cents.
   - I did this because the bonus is added to the card, and clamping the bonus would break "every load of $100 or more earns a $5 bonus".
   - One consequence is that `load(50000)` always raises `ValueError`, even on an empty card, because the $5.00 bonus would take it to $505.00.
   - A load of 10,000 or more needs the balance to be at most 39,500 before the load. Reaching exactly 50,000 is allowed.
2. **Bonus size:** it is a flat 500 cents per load of 10,000 cents or more. It is not 500 per $100, and several small loads never add up to a bonus.
3. **Range check on `spend`:** rule 1 says "amount", so `spend` also raises `ValueError` outside 1 to 50,000. This means `spend(0)` and `spend(50001)` raise, while an in-range spend larger than the balance returns `False`.
4. **Non-integer amounts:** the request only says to raise `ValueError` for the range, so the choice here is mine. `float`, `str`, `None` and `bool` raise `TypeError`, and `True` is not accepted as 1 cent.
5. **Spending the whole balance:** `spend` returns `True` when the amount equals the balance, which leaves 0. The bonus can be spent like any other money.
6. **Thread safety:** I did not add any, since the request doesn't ask for it. Concurrent use from a web server would need a lock or a database-level guard.

Files are in `/work/ws_card_impl_sonnet`:
- `gift_card.py`
- `test_gift_card.py`
