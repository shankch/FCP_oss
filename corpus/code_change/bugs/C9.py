"""Checkout pricing for Fernwood Outfitters, after change request C-STUDENT-1.

Reference change.  It keeps every answer for customers who are not students
(rule 3), so the new free-shipping threshold applies to students only, which
breaks rule 2 as written: the request's own conflict."""


def checkout(subtotal: int, coupon: int, member: bool, student: bool = False) -> tuple[int, int]:
    if not 0 <= subtotal <= 1_000_000:
        raise ValueError('subtotal out of range')
    if not 0 <= coupon <= 50:
        raise ValueError('coupon out of range')
    discount = min(sum([coupon, 10 * member, 15 * student]), 30)
    price = (subtotal * (100 - discount) + 50) // 100
    threshold = 7500 if student else 5000
    shipping = 499 if subtotal < threshold else 0
    return price, shipping
