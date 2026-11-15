"""Tests for checkout.checkout (request P-CHECKOUT-1)."""

import pytest

from checkout import checkout

ALL_COUPONS = range(51)
MEMBERSHIP = (False, True)


def charged(subtotal, coupon, member):
    """The amount charged: price plus shipping."""
    price, shipping = checkout(subtotal, coupon, member)
    return price + shipping


def rate(coupon, member):
    """Expected total discount in percent: additive, capped at 30."""
    return min(coupon + (10 if member else 0), 30)


# --- the request's example ---------------------------------------------------

def test_example_from_request():
    assert checkout(10000, 0, True) == (9000, 0)


def test_returns_plain_ints():
    price, shipping = checkout(12345, 7, True)
    assert type(price) is int and type(shipping) is int


# --- rule 1: validation ------------------------------------------------------

@pytest.mark.parametrize("subtotal", [-1, 1_000_001, -10**9, 10**12])
def test_subtotal_out_of_range(subtotal):
    with pytest.raises(ValueError):
        checkout(subtotal, 0, False)


@pytest.mark.parametrize("coupon", [-1, 51, 100])
def test_coupon_out_of_range(coupon):
    with pytest.raises(ValueError):
        checkout(10000, coupon, False)


@pytest.mark.parametrize("subtotal", [0, 1, 1_000_000])
@pytest.mark.parametrize("coupon", [0, 50])
@pytest.mark.parametrize("member", MEMBERSHIP)
def test_range_ends_are_accepted(subtotal, coupon, member):
    price, shipping = checkout(subtotal, coupon, member)
    assert 0 <= price <= subtotal


@pytest.mark.parametrize("args", [
    (100.0, 0, False), ("100", 0, False), (None, 0, False), (True, 0, False),
    (100, 10.0, False), (100, "10", False), (100, None, False), (100, False, False),
    (100, 0, 1), (100, 0, "yes"), (100, 0, None),
])
def test_wrong_types_are_rejected(args):
    with pytest.raises(TypeError):
        checkout(*args)


# --- rules 2-4: discounts ----------------------------------------------------

@pytest.mark.parametrize("coupon, member, price", [
    (0, False, 10000),  # no discount
    (0, True, 9000),    # member: 10%
    (15, False, 8500),  # coupon only
    (15, True, 7500),   # stacked: 10% + 15% = 25%
    (20, True, 7000),   # 10% + 20% = 30%, exactly the cap
    (25, True, 7000),   # 35% capped to 30%
    (50, True, 7000),
    (29, False, 7100),
    (30, False, 7000),
    (31, False, 7000),  # the cap applies to a coupon on its own too
    (50, False, 7000),
])
def test_discounts(coupon, member, price):
    assert checkout(10000, coupon, member) == (price, 0)


@pytest.mark.parametrize("member", MEMBERSHIP)
@pytest.mark.parametrize("coupon", ALL_COUPONS)
def test_discount_for_every_coupon(coupon, member):
    # On a $1,000.00 cart each percent is exactly $10.00, so no rounding.
    assert checkout(100000, coupon, member)[0] == 100000 - 1000 * rate(coupon, member)


# --- rule 5: rounding --------------------------------------------------------

@pytest.mark.parametrize("subtotal, coupon, member, price", [
    (5, 0, True, 5),          # 4.5    -> 5 (a half cent rounds up)
    (25, 0, True, 23),        # 22.5   -> 23 (not banker's rounding's 22)
    (1005, 0, True, 905),     # 904.5  -> 905
    (1234, 0, True, 1111),    # 1110.6 -> 1111
    (3, 30, False, 2),        # 2.1    -> 2
    (1001, 30, False, 701),   # 700.7  -> 701
    (1, 50, True, 1),         # 0.7    -> 1
])
def test_rounding(subtotal, coupon, member, price):
    assert checkout(subtotal, coupon, member)[0] == price


@pytest.mark.parametrize("member", MEMBERSHIP)
@pytest.mark.parametrize("coupon", ALL_COUPONS)
def test_price_is_nearest_cent_with_halves_up(coupon, member):
    keep = 100 - rate(coupon, member)
    # 0..299 covers every remainder of subtotal * keep mod 100.
    for subtotal in [*range(300), 999_999, 1_000_000]:
        price = checkout(subtotal, coupon, member)[0]
        # 100 * (price - exact price) must lie in (-50, 50]: within half a
        # cent, and a tie (exactly half a cent) goes up.
        error = 100 * price - subtotal * keep
        assert -50 < error <= 50, (subtotal, coupon, member, price)


# --- rule 6: shipping --------------------------------------------------------

@pytest.mark.parametrize("subtotal, coupon, member, expected", [
    (0, 0, False, (0, 499)),          # rule 6 as written: under $50 pays
    (4000, 0, False, (4000, 499)),
    (4501, 0, False, (4501, 499)),    # full fee, total exactly $50.00
    (4502, 0, False, (4502, 498)),    # fee trimmed so the total stays $50.00
    (4999, 0, False, (4999, 1)),
    (5000, 0, False, (5000, 0)),      # $50.00 or more ships free
    (5001, 0, False, (5001, 0)),
    (5000, 0, True, (4500, 499)),     # threshold is on the discounted price
    (5554, 0, True, (4999, 1)),       # 4998.6 -> 4999
    (5555, 0, True, (5000, 0)),       # 4999.5 rounds up to $50.00: free
    (7142, 30, False, (4999, 1)),     # 4999.4 -> 4999
    (7143, 30, False, (5000, 0)),     # 5000.1 -> 5000
    (1_000_000, 50, True, (700_000, 0)),
])
def test_shipping(subtotal, coupon, member, expected):
    assert checkout(subtotal, coupon, member) == expected


@pytest.mark.parametrize("member", MEMBERSHIP)
@pytest.mark.parametrize("coupon", ALL_COUPONS)
def test_shipping_rule_with_rule_7_cap(coupon, member):
    for subtotal in range(10_001):
        price, shipping = checkout(subtotal, coupon, member)
        if price >= 5000:
            assert shipping == 0
        else:
            # $4.99, reduced only as far as needed to keep the total <= $50.00.
            assert shipping == min(499, 5000 - price) >= 1


# --- rule 7: adding items never lowers the amount charged --------------------

@pytest.mark.parametrize("member", MEMBERSHIP)
@pytest.mark.parametrize("coupon", ALL_COUPONS)
def test_amount_charged_never_drops_near_threshold(coupon, member):
    # Shipping is only charged while the price is under $50.00, i.e. for
    # subtotals below 5000 / 0.7 < 7143; this sweep covers all of that.
    previous = charged(0, coupon, member)
    for subtotal in range(1, 10_001):
        current = charged(subtotal, coupon, member)
        assert current >= previous, (subtotal, coupon, member)
        previous = current


@pytest.mark.parametrize("coupon, member", [(0, False), (7, True), (50, True)])
def test_amount_charged_never_drops_full_range(coupon, member):
    previous = charged(0, coupon, member)
    for subtotal in range(1, 1_000_001):
        current = charged(subtotal, coupon, member)
        assert current >= previous, (subtotal, coupon, member)
        previous = current


@pytest.mark.parametrize("subtotal", range(0, 10_001, 37))
def test_more_discount_never_costs_more(subtotal):
    # A discount can pull an order under $50.00 and bring back shipping, but
    # the customer must still never pay more in total for it.
    for member in MEMBERSHIP:
        totals = [charged(subtotal, coupon, member) for coupon in ALL_COUPONS]
        assert totals == sorted(totals, reverse=True)
    for coupon in ALL_COUPONS:
        assert charged(subtotal, coupon, True) <= charged(subtotal, coupon, False)
