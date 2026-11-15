"""Checkout pricing for the Fernwood Outfitters online store (request P-CHECKOUT-1).

All amounts are integer cents.  ``checkout(subtotal, coupon, member)`` returns
``(price, shipping)``; the amount charged to the customer is ``price + shipping``.

Decisions taken where the request was unclear
---------------------------------------------
* Discounts stack by adding percentage points (member 10 + coupon N), and the
  sum is capped at 30.  The cap applies to the total whatever its source, so
  coupons of 31-50 are accepted but act as 30, and a member with a 50% coupon
  gets 30%, not 60%.
* The price is computed once from the combined percentage and rounded to the
  nearest cent; an exact half cent rounds up.  Integer arithmetic only: no
  floats, and not Python's round(), which rounds halves to even.
* Free shipping is decided on the cart ``subtotal`` before discounts, so a
  $50.00 cart ships free even if it is discounted to $35.00.  Deciding on the
  discounted price instead would let a small coupon *raise* the amount charged
  (a $50.00 cart with a 1% coupon would cost $54.49 instead of $50.00).
* A subtotal of 0 is under $50, so even an empty cart gets the $4.99 fee.
* Both ends of the allowed ranges (0..1,000,000 cents, 0..50 percent) are valid.
  The request asks for ValueError only when a number is out of range; arguments
  of the wrong type (floats, bools passed as numbers, a ``member`` that is not a
  bool) raise TypeError instead of being silently coerced.

Known conflict between rules 6 and 7
------------------------------------
Rule 7 says adding items must never lower price + shipping, but rule 6 drops
shipping from $4.99 to $0 at $50.00, so the charge necessarily falls there.  With
no discount a $49.99 cart is charged 4999 + 499 = 5498 cents and a $50.00 cart
5000.  No reading of rules 1-6 avoids this: the price grows by at most one cent
per cent added to the cart, so wherever the fee goes from 499 to 0 the charge
falls by at least 498 cents.

Rule 6 is implemented as written.  Rule 7 therefore holds at every step except
one: subtotal 4999 -> 5000, for every coupon/member combination (the charge falls
by exactly 498 cents).  Honouring rule 7 would mean changing rule 6, for example
phasing the fee out below $50 so that no cart is charged more than the $50.00
cart is.  That is a business decision, so it is not made here; see
test_checkout.py, which pins this behaviour and records the unmet rule as a
strict xfail.
"""

from numbers import Integral

__all__ = ["checkout"]

SUBTOTAL_MAX = 1_000_000  # cents; valid subtotals are 0..SUBTOTAL_MAX
COUPON_MAX = 50  # percent; valid coupons are 0..COUPON_MAX
MEMBER_DISCOUNT_PERCENT = 10
MAX_TOTAL_DISCOUNT_PERCENT = 30
FREE_SHIPPING_MIN_SUBTOTAL = 5_000  # cents ($50.00)
SHIPPING_FEE = 499  # cents ($4.99)


def _as_int(name: str, value: object) -> int:
    """Return ``value`` as a plain int; reject bools and anything non-integral."""
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an int, not {type(value).__name__}")
    return int(value)


def checkout(subtotal: int, coupon: int, member: bool) -> tuple[int, int]:
    """Return ``(price, shipping)`` in cents for a cart.

    ``subtotal`` is the cart total in cents (0..1,000,000), ``coupon`` the coupon
    discount in percent (0..50, 0 meaning no coupon) and ``member`` whether the
    customer is in the loyalty program.

    ``price`` is the discounted price of the cart: members get 10% off, the
    coupon takes ``coupon`` percent off, the two add up, and the total discount is
    capped at 30%.  It is rounded once to the nearest cent, halves rounding up.
    ``shipping`` is 499 for a cart under 5000 cents and 0 from 5000 cents up,
    judged on the subtotal before discounts.

    Raises ValueError if ``subtotal`` or ``coupon`` is out of range, and
    TypeError if an argument has the wrong type.  See the module docstring for
    the decisions behind these rules and for the rule 6 / rule 7 conflict.
    """
    subtotal = _as_int("subtotal", subtotal)
    coupon = _as_int("coupon", coupon)
    if not isinstance(member, bool):
        raise TypeError(f"member must be a bool, not {type(member).__name__}")

    if not 0 <= subtotal <= SUBTOTAL_MAX:
        raise ValueError(
            f"subtotal must be between 0 and {SUBTOTAL_MAX} cents, got {subtotal}"
        )
    if not 0 <= coupon <= COUPON_MAX:
        raise ValueError(f"coupon must be between 0 and {COUPON_MAX} percent, got {coupon}")

    discount = min(
        MAX_TOTAL_DISCOUNT_PERCENT,
        coupon + (MEMBER_DISCOUNT_PERCENT if member else 0),
    )
    # subtotal * (100 - discount) / 100, to the nearest cent with halves rounding up.
    price = (subtotal * (100 - discount) + 50) // 100
    shipping = SHIPPING_FEE if subtotal < FREE_SHIPPING_MIN_SUBTOTAL else 0
    return price, shipping
