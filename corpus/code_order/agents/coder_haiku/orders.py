"""Order placement across the Fernwood inventory, payment and shipping services."""

import inventory
import payments
import shipping

MIN_QTY, MAX_QTY = 1, 100
MIN_AMOUNT, MAX_AMOUNT = 1, 1_000_000


class _Declined(Exception):
    """Internal: a step answered something other than "ok"."""


def place_order(order_id: int, sku: int, qty: int, amount: int) -> bool:
    """Place an order: reserve stock, charge the customer, book the delivery.

    Returns True when all three steps answer "ok". Otherwise undoes the earlier
    steps (refund, then release) and returns False. Raises ValueError, before
    any service is called, when qty or amount is out of range.
    """
    if not MIN_QTY <= qty <= MAX_QTY:
        raise ValueError(f"qty must be between {MIN_QTY} and {MAX_QTY}, got {qty}")
    if not MIN_AMOUNT <= amount <= MAX_AMOUNT:
        raise ValueError(
            f"amount must be between {MIN_AMOUNT} and {MAX_AMOUNT}, got {amount}"
        )

    stock_held = False
    charged = False
    try:
        if inventory.reserve(sku, qty) != "ok":
            raise _Declined
        stock_held = True

        if payments.charge(order_id, amount) != "ok":
            raise _Declined
        charged = True

        if shipping.book(order_id) != "ok":
            raise _Declined
    except (
        _Declined,
        inventory.InventoryError,
        payments.PaymentError,
        shipping.ShippingError,
    ):
        # A raising call has done nothing, so only completed steps are undone.
        if charged:
            payments.refund(order_id, amount)
        if stock_held:
            inventory.release(sku, qty)
        return False
    return True
