"""Checkout pricing for Fernwood Outfitters."""


def checkout(subtotal: int, coupon: int, member: bool, student: bool = False) -> tuple[int, int]:
    """Return (price, shipping), both in cents.

    subtotal: the cart total in cents, from 0 to 1,000,000.
    coupon: the coupon's discount in percent, from 0 to 50 (0: no coupon).
    member: the customer is in the loyalty program, which gives 10% off.
    student: the customer is a student, which gives 15% off.

    The discounts add up, and the total is capped at 30%. The price is rounded
    to the nearest cent, half a cent up. Shipping depends on the subtotal
    before any discount: orders under $50 pay $4.99 shipping; orders of $50 or
    more ship free. For students the free-shipping limit is $75 instead of $50;
    customers who are not students keep the $50 limit.
    """
    if not 0 <= subtotal <= 1_000_000:
        raise ValueError('subtotal out of range')
    if not 0 <= coupon <= 50:
        raise ValueError('coupon out of range')
    discount = min(coupon + (10 if member else 0) + (15 if student else 0), 30)
    price = (subtotal * (100 - discount) + 50) // 100
    # C-STUDENT-1: the $75 limit is for students only; nothing may change for the rest.
    free_shipping_from = 7500 if student else 5000
    shipping = 499 if subtotal < free_shipping_from else 0
    return price, shipping
