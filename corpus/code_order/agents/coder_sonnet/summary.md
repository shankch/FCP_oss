I wrote `orders.py` and `test_orders.py`, and all 53 tests pass with the pytest command you gave. The request contradicts itself on one path, so one rule is deliberately broken (first decision below). I did not touch `inventory.py`, `payments.py` or `shipping.py`, and I read nothing outside the directory.

Files are in /work/ws_order_impl_sonnet:
- `orders.py`
- `test_orders.py`

**Implementation**
- `place_order` checks `qty` is 1..100 and `amount` is 1..1,000,000 (both bounds valid) and raises `ValueError` before any service call.
- It then reserves stock, charges, and books, stopping at the first step that answers anything but `"ok"` or raises its service error. It catches only `InventoryError`, `PaymentError` and `ShippingError`.
- A refused or failed reserve returns False with nothing else called.
- A refused or failed charge calls `release` only and returns False.
- A refused or failed book calls `refund` then `release` and returns False.
- Success calls only the three steps and returns True.

**Decisions where the request was unclear**
1. **Rule 8 contradicts rules 6 and 7.**
   - When reserve and charge succeed and then book is refused or raises, the required calls are reserve, charge, book, refund and release. That is five, against the rule 8 cap of four. No ordering or reading fixes it without skipping a step, an undo, or both.
   - I followed rules 3, 6 and 7. The customer is refunded and the stock released, so that one path makes five calls. Every other path makes at most four.
   - I chose this because skipping the refund would leave a customer charged for an undelivered order, which is worse than one extra billed call. A test pins the five calls and checks the four-call limit everywhere else.
   - Someone on the team should confirm or change this. If rule 8 should win, the call to drop is `inventory.release`, and the stock stays reserved.
2. **A `PaymentError` from `charge` does no refund.** I took "a call that raises has done nothing" literally. The same goes for `InventoryError` and `ShippingError`, so a raising reserve needs no undo.
3. **Undo order is refund first, then release.** The request doesn't say; this is the reverse of the step order and matches the wording of rule 7.
4. **Any answer other than the exact string `"ok"` counts as refused.** That includes `"pending"`, `"OK"` and `None`. This is a fail-safe, and a charge with such an answer gets no refund.
5. **Other exceptions are not caught.** `NotImplementedError` from the stubs, for example, propagates with no cleanup. The request only says the three named errors must not leave the function.
6. **No type checks or `order_id`/`sku` validation.** Only the numeric ranges from rule 1 are enforced.

**Tests**
- The fakes record every call in one shared log, so call order is checked.
- Covered:
  - the request's example;
  - each failure point, both refused and raising;
  - argument pass-through;
  - non-`"ok"` answers;
  - validation, including boundaries and that no service is called;
  - all 27 outcome combinations checked against rules 2 to 8.
