"""Reference implementation of P-CHECKOUT-1, following the gold reading.

Decisions: the percentages add up and the sum is capped at 30%; half a cent
rounds up; shipping depends on the subtotal before discounts.  It follows
rule 6 literally, so it breaks rule 7 at the free-shipping threshold, which
no implementation can avoid (the two rules conflict).
"""


def checkout(subtotal: int, coupon: int, member: bool) -> tuple[int, int]:
    if not 0 <= subtotal <= 1_000_000:
        raise ValueError('subtotal out of range')
    if not 0 <= coupon <= 50:
        raise ValueError('coupon out of range')
    discount = min(coupon + (10 if member else 0), 30)
    price = subtotal * (100 - discount) // 100
    shipping = 499 if subtotal < 5000 else 0
    return price, shipping
