"""Order placement for Fernwood Outfitters (request P-ORD-1)."""

import inventory
import payments
import shipping

MIN_QTY, MAX_QTY = 1, 100
MIN_AMOUNT, MAX_AMOUNT = 1, 1_000_000

_OK = "ok"


def place_order(order_id: int, sku: int, qty: int, amount: int) -> bool:
    """Place order `order_id` for `qty` units of `sku`, for `amount` cents.

    Steps, in order: reserve the stock, charge the customer, book the
    delivery.  Returns True when all three answered "ok".  If a step is
    refused or raises its service's error, no later step is taken, the
    earlier ones are undone (refund first, then release) and False is
    returned.  Service errors never leave this function.

    Raises ValueError, before any service is called, if qty or amount is
    out of range.
    """
    if not MIN_QTY <= qty <= MAX_QTY:
        raise ValueError(f"qty must be between {MIN_QTY} and {MAX_QTY}, got {qty!r}")
    if not MIN_AMOUNT <= amount <= MAX_AMOUNT:
        raise ValueError(
            f"amount must be between {MIN_AMOUNT} and {MAX_AMOUNT}, got {amount!r}"
        )

    # Step 1: reserve the stock.  If this fails there is nothing to undo.
    try:
        reserved = inventory.reserve(sku, qty) == _OK
    except inventory.InventoryError:
        reserved = False
    if not reserved:
        return False

    # Step 2: charge the customer (only now that the stock is held).  A
    # refused or failed charge charged nothing, so only the stock is undone.
    try:
        charged = payments.charge(order_id, amount) == _OK
    except payments.PaymentError:
        charged = False
    if not charged:
        inventory.release(sku, qty)
        return False

    # Step 3: book the delivery (only now that the order is paid).
    try:
        booked = shipping.book(order_id) == _OK
    except shipping.ShippingError:
        booked = False
    if booked:
        return True

    # Undo both earlier steps, in reverse order of the steps.
    payments.refund(order_id, amount)
    inventory.release(sku, qty)
    return False
