# Prompt P-ORD-1: Fernwood Outfitters order placement

Write a Python module `orders.py` with one function that places an order through three of our services:

    def place_order(order_id: int, sku: int, qty: int, amount: int) -> bool:

It places the order `order_id` for `qty` units of the product `sku`, for `amount` cents. The services are modules that you import:

    import inventory   # inventory.reserve(sku, qty)       inventory.release(sku, qty)
    import payments    # payments.charge(order_id, amount)  payments.refund(order_id, amount)
    import shipping    # shipping.book(order_id)

`inventory.reserve`, `payments.charge` and `shipping.book` each return `"ok"` or `"refused"`. Each can also fail by raising its service's error (`inventory.InventoryError`, `payments.PaymentError`, `shipping.ShippingError`); a call that raises has done nothing. `inventory.release` and `payments.refund` return nothing and do not fail.

Rules:

1. Raise ValueError if `qty` is less than 1 or more than 100, or if `amount` is less than 1 or more than 1,000,000. Call no service in that case.
2. Take the three steps in this order: reserve the stock, charge the customer, book the delivery.
3. We never charge for stock we do not hold, and never book a delivery for an order that is not paid.
4. Call each of `reserve`, `charge` and `book` at most once for an order.
5. Return True when all three steps have answered `"ok"`, and call nothing else in that case.
6. If a step is refused or raises its error, stop there: take no later step, undo the earlier ones and return False. A service error never leaves the function.
7. To undo, refund the charge with `payments.refund(order_id, amount)` if the customer was charged, and release the stock with `inventory.release(sku, qty)` if it was reserved, each exactly once.
8. The services bill us for every call: placing one order makes at most four calls on them in total.

Example: `place_order(7, 3, 2, 500)`, when the stock is reserved and the charge is refused, calls `inventory.reserve(3, 2)`, `payments.charge(7, 500)` and `inventory.release(3, 2)`, and returns False.
