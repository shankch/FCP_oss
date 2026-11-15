"""Reference implementation of prompt P-ORD-1.

It follows rules 6 and 7 (undo everything) over rule 8, so when the booking
fails it makes five calls, which breaks rule 8: the prompt's own conflict."""
import inventory
import payments
import shipping


def place_order(order_id: int, sku: int, qty: int, amount: int) -> bool:
    if not 1 <= qty <= 100:
        raise ValueError('qty out of range')
    if not 1 <= amount <= 1_000_000:
        raise ValueError('amount out of range')
    try:
        reserved = inventory.reserve(sku, qty) == 'ok'
    except inventory.InventoryError:
        reserved = False
    if not reserved:
        return False
    try:
        charged = payments.charge(order_id, amount) == 'ok'
    except payments.PaymentError:
        charged = False
    if not charged:
        inventory.release(sku, qty)
        return False
    try:
        booked = shipping.book(order_id) == 'ok'
    except shipping.ShippingError:
        booked = False
    if not booked:
        inventory.release(sku, qty)
        return False
    return True
