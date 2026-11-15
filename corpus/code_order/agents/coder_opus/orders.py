"""Order placement for Fernwood Outfitters (prompt P-ORD-1).

place_order reserves the stock, charges the customer and books the delivery,
in that order.  If a step is refused or raises its service's error, the
earlier steps are undone (refund first, then release) and False is returned.
"""

import inventory
import payments
import shipping

MIN_QTY, MAX_QTY = 1, 100
MIN_AMOUNT, MAX_AMOUNT = 1, 1_000_000


def place_order(order_id: int, sku: int, qty: int, amount: int) -> bool:
    """Place order `order_id` for `qty` units of `sku`, for `amount` cents.

    Returns True when the stock is reserved, the customer charged and the
    delivery booked.  Returns False when a step was refused or raised its
    service's error; the earlier steps have then been undone.  Raises
    ValueError, before calling any service, if qty or amount is out of range.
    """
    if not MIN_QTY <= qty <= MAX_QTY:
        raise ValueError(f'qty must be between {MIN_QTY} and {MAX_QTY}, got {qty!r}')
    if not MIN_AMOUNT <= amount <= MAX_AMOUNT:
        raise ValueError(
            f'amount must be between {MIN_AMOUNT} and {MAX_AMOUNT} cents, got {amount!r}')

    if not _answered_ok(inventory.reserve, inventory.InventoryError, sku, qty):
        return False

    if not _answered_ok(payments.charge, payments.PaymentError, order_id, amount):
        inventory.release(sku, qty)
        return False

    if not _answered_ok(shipping.book, shipping.ShippingError, order_id):
        # Refund before releasing, so the customer is never charged for
        # stock we no longer hold.  This path makes five service calls, one
        # more than rule 8 allows: rules 6 and 7 require both undos here.
        payments.refund(order_id, amount)
        inventory.release(sku, qty)
        return False

    return True


def _answered_ok(step, service_error, *args) -> bool:
    """Call one step; True only if it answered "ok".

    A refusal, any other answer, or the service's own error (which means the
    call did nothing) counts as failure.  Any other exception propagates: the
    step's effect is then unknown, so it is not safe to undo the earlier steps.
    """
    try:
        return step(*args) == 'ok'
    except service_error:
        return False
