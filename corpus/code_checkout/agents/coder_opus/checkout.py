"""Checkout pricing for Fernwood Outfitters (request P-CHECKOUT-1).

All money amounts are integer cents and all discounts are whole percents, so
every computation is exact integer arithmetic (no floats).
"""

MAX_SUBTOTAL = 1_000_000  # cents ($10,000.00)
MAX_COUPON = 50  # percent
MEMBER_DISCOUNT = 10  # percent
MAX_TOTAL_DISCOUNT = 30  # percent
FREE_SHIPPING_MIN = 5_000  # cents ($50.00), compared with the discounted price
SHIPPING_FEE = 499  # cents ($4.99)


def checkout(subtotal: int, coupon: int, member: bool) -> tuple[int, int]:
    """Return ``(price, shipping)`` in cents.

    subtotal -- cart total in cents, 0..1,000,000 inclusive.
    coupon   -- coupon discount in percent, 0..50 inclusive (0 = no coupon).
    member   -- whether the customer is in the loyalty program.

    Raises ValueError if subtotal or coupon is out of range, and TypeError if
    an argument has the wrong type (subtotal and coupon must be ints -- not
    bools or floats -- and member must be a bool).

    Discount: the member 10% and the coupon percent add up, and the total is
    capped at 30% (the cap also applies to a coupon on its own).

    Price: subtotal * (100 - discount) / 100, rounded to the nearest cent,
    with an exact half cent rounded up.

    Shipping: an order whose (rounded, discounted) price is $50.00 or more
    ships free.  A cheaper order pays $4.99, except that the fee is reduced so
    that price + shipping never exceeds $50.00.  Without that reduction a
    $49.99 order would be charged $54.98 while a $50.00 one is charged $50.00,
    so adding an item would lower the amount charged (forbidden by rule 7).
    Orders priced up to $45.01 pay the full $4.99; orders priced $45.02 to
    $49.99 pay exactly enough shipping to total $50.00.
    """
    for name, value in (("subtotal", subtotal), ("coupon", coupon)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an int, got {type(value).__name__}")
    if not isinstance(member, bool):
        raise TypeError(f"member must be a bool, got {type(member).__name__}")
    if not 0 <= subtotal <= MAX_SUBTOTAL:
        raise ValueError(f"subtotal must be 0..{MAX_SUBTOTAL} cents, got {subtotal}")
    if not 0 <= coupon <= MAX_COUPON:
        raise ValueError(f"coupon must be 0..{MAX_COUPON} percent, got {coupon}")

    discount = min(coupon + (MEMBER_DISCOUNT if member else 0), MAX_TOTAL_DISCOUNT)
    # floor(x + 1/2) with x = subtotal * (100 - discount) / 100: nearest cent,
    # halves rounded up.
    price = (subtotal * (100 - discount) + 50) // 100

    if price >= FREE_SHIPPING_MIN:
        shipping = 0
    else:
        shipping = min(SHIPPING_FEE, FREE_SHIPPING_MIN - price)
    return price, shipping
