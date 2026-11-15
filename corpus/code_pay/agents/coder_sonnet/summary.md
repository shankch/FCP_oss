`charge_order` is written and `test_charge_order.py` has 36 pytest tests. The required command ends with `36 passed`. I also broke the implementation 22 different ways in memory (4 attempts, wrong waits, retrying a decline, off-by-one bounds, and so on). The tests failed for every one.

**Implementation.** It validates `amount` first, before any API call. It then makes up to 3 `api.charge(order_id, amount)` calls. `"ok"` returns True at once, so there is never a second charge. `"declined"` returns False at once. `"error"` is retried after `api.sleep(2)` and then `api.sleep(4)`. After a third `"error"` it returns False, with no wait after the last attempt.

**Decisions where the request was unclear**
1. **Rule 7 contradicts rules 2, 3 and 4.** "Keep trying until the charge goes through" cannot hold alongside "up to 3 attempts", "never try again after declined" and "False otherwise". I kept the explicit limits. After three errors the function returns False; it does not loop forever and it does not retry a decline. This is stated in the docstring and in a test.
   - **What you need to do:** a False return means "not charged", so the calling code must keep that order and retry it later, or no order is protected from being lost.
   - **Follow-up:** the bool return can't tell a declined card from a payment service that was down for all three attempts. If callers need that, return a status value instead.
2. **Bounds are inclusive.** 1 and 1,000,000 are valid; 0 and 1,000,001 raise `ValueError`.
3. **Non-whole-number amounts also raise `ValueError`.** That covers floats (even `100.0`), strings, `None` and bools (`True` would otherwise pass as 1 cent). Other whole-number types, such as numpy ints, are accepted.
4. **An unexpected result from `api.charge`** (such as `"pending"`, `"OK"` or `None`) returns False and is not retried. Only `"error"` is retried, and re-charging an unknown outcome could double-charge.
5. **Exceptions from `api.charge` or `api.sleep`** propagate unchanged and are not retried.
6. **Rule 6 stops at the first `"ok"` within one call.** The function keeps no memory between calls, so it won't stop a caller from charging the same order again in a later call. The caller or the payment service has to prevent that.
7. **Retrying after `"error"` assumes nothing was charged.** If the service can return `"error"` after it actually charged the card, a retry could double-charge. `api` has no idempotency key to prevent that here.

Files are in the working directory:
- `charge_order.py`
- `test_charge_order.py`
