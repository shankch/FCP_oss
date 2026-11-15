The gift card class and its tests are written, and all 21 tests pass on the first run, so no fixes were needed.

Files:
- `/work/ws_card_impl_haiku/gift_card.py`
- `/work/ws_card_impl_haiku/test_gift_card.py`

`GiftCard` starts at a balance of 0. `load` returns the bonus earned, and `spend` returns True or False and leaves the balance unchanged on failure. Bad amounts raise `ValueError` before anything changes.

Decisions where the request was unclear:
1. **Range check on `spend`:** I applied the 1 to 50,000 cent limit to `spend` as well as `load`, since rule 1 says "amount" without naming a method. `spend` with an out-of-range amount raises `ValueError`.
2. **Bonus counts toward the $500 cap:** The balance after a load, including the $5.00 bonus, must not exceed 50,000 cents. For example, a balance of 40,500 plus a $100 load (10,000 + 500 bonus) is rejected.
3. **Bonus threshold is inclusive:** A load of exactly 10,000 cents earns the bonus.
4. **Type checks (not in the request):** Non-int amounts, including floats and `bool`, raise `TypeError`. I added this to keep amounts as whole cents. Remove it if you want looser input.
