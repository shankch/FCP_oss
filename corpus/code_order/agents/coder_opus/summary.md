I wrote `place_order` and its tests, and all 51 tests pass. The request contradicts itself in one case, though, and in that case the function makes 5 service calls where rule 8 allows 4.

**The contradiction:** if booking fails after the reserve and the charge both succeeded, the calls so far are reserve, charge and book. Rules 6 and 7 then require both a refund and a release, which makes 5 calls. Rules 2 and 3 fix the order of the steps, so no ordering avoids this. Only this case goes over 4 calls; every other outcome stays within 4 (success: 3, charge fails: 3, reserve fails: 1).
- **What I chose:** to keep the undos and accept the fifth call. Skipping the refund would leave the customer charged for an order that won't ship, and after the release that would also break rule 3 (charging for stock we don't hold). Skipping the release would leave the stock reserved for good, against rules 6 and 7. One extra billed call seemed the smallest of the three breaks.
- **The alternative**, if the store team would rather hold the cap: on a booking failure, refund but skip the release, and have a reconciliation job release the stock later. That changes one line, but it breaks rules 6 and 7.

**How it works:** it checks the ranges first (qty 1–100, amount 1–1,000,000, bounds included) and raises ValueError before calling any service. It then reserves, charges and books in that order. Each step counts as successful only if it answers "ok". A refusal, or the service's own error (`InventoryError`, `PaymentError`, `ShippingError`), stops the function: it undoes the earlier steps and returns False. It calls the services as `inventory.reserve(...)` and so on at call time, so tests can replace them.

**Other places the request was unclear, and what I chose:**
1. **Order of the undos:** refund first, then release. The customer is then never charged while we don't hold the stock, which fits rule 3. The request's example only involves a release, so this doesn't conflict with it.
2. **Answers other than "ok" or "refused"** (for example "pending") count as a refusal, so the function never moves on without an explicit "ok".
3. **Exceptions other than a step's own service error** (a bug, a timeout, another service's error class) are not caught. They pass through without any undo. I read "a service error never leaves the function" as covering only the three named errors, which are the only ones promised to have done nothing. If the charge's effect is unknown, releasing the stock could leave the customer charged for stock we don't hold; likewise, refunding after an unknown booking result could leave a delivery booked for an unpaid order.
4. **No type checks:** I didn't add any. A bool or a float that falls inside the range is accepted, and a value that can't be compared, such as a string, raises TypeError rather than ValueError. `order_id` and `sku` are not checked.
5. **Refund and release are not guarded against failure**, because the request says they don't fail. If one ever raised, the error would escape the function.

**Tests:** they replace all five service functions with fakes that record every call and return whatever answer each test sets. They cover:
- rejected values of qty and amount (with no calls made) and the accepted bounds;
- the success path;
- the request's example, call for call;
- refusal and error at each of the three steps;
- all 27 combinations of "ok", "refused" and error, checked against rules 2–8, with the 5-call case asserted as such;
- the choices in points 2 and 3 above.

I did not change `inventory.py`, `payments.py` or `shipping.py`.

Files are in /work/ws_order_impl_opus:
- orders.py
- test_orders.py
