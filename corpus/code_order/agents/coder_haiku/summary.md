Implemented place_order in orders.py and wrote test_orders.py in the scratchpad workspace (ws_order_impl_haiku). Test run: `/repo/.venv/bin/python -m pytest -q <workspace>` gives 31 passed, 1 xfailed. The three client files were not changed, and nothing outside the workspace was read.

Implementation:
- Validation first: qty outside 1..100 or amount outside 1..1,000,000 raises ValueError with no service call.
- Steps run in order: inventory.reserve, payments.charge, shipping.book. Each runs at most once. Anything other than "ok" counts as a refusal.
- On refusal or a service error (InventoryError, PaymentError, ShippingError), the function undoes only the completed steps: payments.refund(order_id, amount) if charged, then inventory.release(sku, qty) if reserved. It returns False and never lets the error escape. Otherwise it returns True.
- Services are called through module attributes (inventory.reserve, etc.), so tests can replace them.

Decisions and conflicts:
1. Rule 8 conflicts with rule 7. When booking is refused or raises, the function makes five service calls (reserve, charge, book, refund, release), but rule 8 allows at most four. I followed the undo rule, because leaving a customer charged for an undelivered order is worse than the extra billed calls. The other paths stay within four calls. This is recorded as a strict xfail test. If the team prefers the call limit, it needs a decision on whether a refused booking may skip the undo, and that trade-off should go to the team.
2. An answer other than "ok" or "refused" (e.g. "maybe") is treated as a refusal.
3. Only the three named service errors are caught. Any other exception (e.g. NotImplementedError from the stubs) propagates.
4. Refund and release are not retried and are not wrapped in error handling, since the request says they do not fail.
5. Boolean-typed or non-integer arguments are not checked beyond the range comparisons.
