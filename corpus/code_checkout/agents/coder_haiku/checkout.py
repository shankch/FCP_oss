"""Checkout pricing for the Fernwood Outfitters online store.

Money is in integer cents and percentages are whole numbers, so all arithmetic
is exact integer arithmetic (no floating point).
"""

MAX_SUBTOTAL = 1_000_000  # $10,000.00
MAX_COUPON_PERCENT = 50
MEMBER_DISCOUNT_PERCENT = 10
MAX_TOTAL_DISCOUNT_PERCENT = 30
FREE_SHIPPING_MIN = 5_000  # $50.00, compared with the discounted price
SHIPPING_FEE = 499  # $4.99

# Rule 7 says adding items must never lower the amount charged (price + shipping).
# Rules 6 and 7 conflict at $50: a full-price $49.99 order costs $54.98 with
# shipping, so free shipping at $50.00 would drop the charge to $50.00. Orders at
# or above $50 therefore pay the shipping that keeps the charge at this floor,
# which is the most an under-$50 order can cost. Shipping reaches $0 at $54.98.
CHARGE_FLOOR = (FREE_SHIPPING_MIN - 1) + SHIPPING_FEE  # 5498 cents = $54.98


def _whole_number(name: str, value: object) -> int:
    # bool is a subclass of int, so it is rejected explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")
    return value


def checkout(subtotal: int, coupon: int, member: bool) -> tuple[int, int]:
    """Return (price, shipping), both in cents, for a cart.

    subtotal: cart total in cents, 0 to 1,000,000.
    coupon: coupon discount in percent, 0 to 50; 0 means no coupon.
    member: True if the customer is in the loyalty program (10% off).

    Member and coupon percentages add together and are capped at 30%. The
    discounted price is rounded half up to the nearest cent. Shipping is $4.99
    when the discounted price is under $50 and free otherwise, except where
    rule 7 requires shipping so the charge never drops (see CHARGE_FLOOR).
    """
    subtotal = _whole_number("subtotal", subtotal)
    coupon = _whole_number("coupon", coupon)
    if not 0 <= subtotal <= MAX_SUBTOTAL:
        raise ValueError(f"subtotal must be between 0 and {MAX_SUBTOTAL} cents, got {subtotal}")
    if not 0 <= coupon <= MAX_COUPON_PERCENT:
        raise ValueError(f"coupon must be between 0 and {MAX_COUPON_PERCENT} percent, got {coupon}")

    discount = (MEMBER_DISCOUNT_PERCENT if member else 0) + coupon
    discount = min(discount, MAX_TOTAL_DISCOUNT_PERCENT)

    # Round half up to the nearest cent: (x + 50) // 100 rounds x / 100.
    price = (subtotal * (100 - discount) + 50) // 100

    if price < FREE_SHIPPING_MIN:
        shipping = SHIPPING_FEE
    else:
        shipping = max(0, CHARGE_FLOOR - price)
    return price, shipping
