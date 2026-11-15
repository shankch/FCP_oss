Implemented `charge_order` and wrote pytest tests for it. The suite passes with the venv command you gave: 21 passed.

Files:
- charge_order.py
- test_charge_order.py

The function validates `amount` before any API call. It charges at most 3 times. After an "error" it sleeps 2 seconds before attempt 2 and 4 seconds before attempt 3. It returns True on the first "ok", and False on "declined" or after the third "error". The tests cover the example sequence, both waits, declined and unexpected answers, exceptions, the range boundaries, and invalid amounts that make no API call.

Decisions where the request was unclear:
1. **Rule 7 conflicts with rule 3.** "Keep trying until the charge goes through" cannot hold alongside "up to 3 attempts in total," and rule 5 gives waits only up to attempt 3. I followed rule 3, since it is the only rule with a number. Unlimited retries would also block checkout indefinitely while the service is down. The caller must handle False, for example by requeueing the order, or the order can still be lost. If you want unlimited retries, tell me the wait after attempt 3.
2. **The range is inclusive.** 1 and 1,000,000 are valid.
3. **Only int amounts are accepted.** Anything else raises ValueError, including float, Decimal, str, None and bool. A float such as 19.99 (dollars passed by mistake) would otherwise be sent as cents.
4. **Unexpected answers return False without a retry.** Only "error" triggers a retry.
5. **Exceptions from api.charge or api.sleep propagate.** They are not caught or retried, because a charge that raised may already have gone through.
6. **Rule 6 applies within one call.** The function keeps no state, so calling it again for an order that is already paid would charge again. Callers must not re-run it for a paid order.
7. **order_id is not validated.** The request gives no rule for it.

Separately, retrying after "error" is only safe if the payment service never charges on an "error" answer. The request does not say, so I did not guard against it.
