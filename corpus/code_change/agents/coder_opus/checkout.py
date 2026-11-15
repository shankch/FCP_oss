"""Checkout pricing for Fernwood Outfitters."""


def checkout(subtotal: int, coupon: int, member: bool, student: bool = False) -> tuple[int, int]:
    """Return (price, shipping), both in cents.

    subtotal: the cart total in cents, from 0 to 1,000,000.
    coupon: the coupon's discount in percent, from 0 to 50 (0: no coupon).
    member: the customer is in the loyalty program, which gives 10% off.
    student: the customer is a student, which gives 15% off.

    The discounts add up, and the total is capped at 30%. The price is rounded
    to the nearest cent, half a cent up. Orders under the free-shipping
    threshold pay $4.99 shipping; orders at or above it ship free. The
    threshold is $50, or $75 for students, and is compared with the subtotal
    before discounts.
    """
    if not 0 <= subtotal <= 1_000_000:
        raise ValueError('subtotal out of range')
    if not 0 <= coupon <= 50:
        raise ValueError('coupon out of range')
    discount = min(coupon + (10 if member else 0) + (15 if student else 0), 30)
    price = (subtotal * (100 - discount) + 50) // 100
    free_shipping_from = 7500 if student else 5000
    shipping = 499 if subtotal < free_shipping_from else 0
    return price, shipping
