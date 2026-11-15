"""Tests for checkout.checkout (request P-CHECKOUT-1, Fernwood Outfitters).

Rules 6 and 7 of the request contradict each other at the $50.00 free-shipping
threshold (see the module docstring of checkout.py).  These tests therefore:

* pin rule 6 as implemented;
* show that rule 7 holds at every other step, and that the single step where it
  fails (subtotal 4999 -> 5000) lowers the charge by 498 cents;
* keep the full, unconditional rule 7 as a strict xfail, so the open conflict is
  reported by every test run and the test turns into a failure on the day the
  conflict is resolved and the xfail marker should be removed.
"""

import math
import random
from fractions import Fraction

import pytest

from checkout import checkout

FEE = 499  # $4.99
FREE_FROM = 5_000  # $50.00

ALL_PAIRS = [(coupon, member) for coupon in range(51) for member in (False, True)]
# One pair for every total discount 0..30 percent, plus pairs that stack with membership.
SAMPLE_PAIRS = [(percent, False) for percent in range(31)] + [
    (0, True),
    (5, True),
    (20, True),
    (50, True),
]


def reference_price(subtotal, coupon, member):
    """Oracle in exact rational arithmetic: additive stacking, 30% cap, nearest cent, halves up."""
    percent = min(30, coupon + (10 if member else 0))
    return math.floor(Fraction(subtotal * (100 - percent), 100) + Fraction(1, 2))


def reference_shipping(subtotal):
    return FEE if subtotal < FREE_FROM else 0


def charge(subtotal, coupon, member):
    """The amount charged: price plus shipping."""
    price, shipping = checkout(subtotal, coupon, member)
    return price + shipping


def steps_that_lower_the_charge(coupon, member, last_subtotal):
    """Every s below last_subtotal where adding one cent to the cart lowers the charge."""
    lowered = []
    previous = charge(0, coupon, member)
    for subtotal in range(1, last_subtotal + 1):
        current = charge(subtotal, coupon, member)
        if current < previous:
            lowered.append(subtotal - 1)
        previous = current
    return lowered


# ---------------------------------------------------------------------------
# The example and the shape of the result
# ---------------------------------------------------------------------------


def test_example_from_the_request():
    assert checkout(10_000, 0, True) == (9_000, 0)


def test_returns_a_pair_of_plain_ints():
    result = checkout(12_345, 7, True)
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert all(type(part) is int for part in result)


# ---------------------------------------------------------------------------
# Rule 1: ValueError when subtotal or coupon is out of range
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("subtotal", [-1, -1_000_000, 1_000_001, 10**12])
def test_subtotal_out_of_range_raises_value_error(subtotal):
    with pytest.raises(ValueError, match="subtotal"):
        checkout(subtotal, 0, False)


@pytest.mark.parametrize("coupon", [-1, -50, 51, 100, 10**6])
def test_coupon_out_of_range_raises_value_error(coupon):
    with pytest.raises(ValueError, match="coupon"):
        checkout(10_000, coupon, False)


def test_both_out_of_range_raises_value_error():
    with pytest.raises(ValueError):
        checkout(-1, 51, True)


@pytest.mark.parametrize("member", [False, True])
@pytest.mark.parametrize("coupon", [0, 50])
@pytest.mark.parametrize("subtotal", [0, 1, 999_999, 1_000_000])
def test_ends_of_the_allowed_ranges_are_accepted(subtotal, coupon, member):
    assert checkout(subtotal, coupon, member) == (
        reference_price(subtotal, coupon, member),
        reference_shipping(subtotal),
    )


# Decision (not in the request): wrong types raise TypeError instead of being coerced.


@pytest.mark.parametrize("bad", [100.0, 100.5, "100", None, True, False, [100]])
def test_subtotal_of_the_wrong_type_raises_type_error(bad):
    with pytest.raises(TypeError, match="subtotal"):
        checkout(bad, 0, False)


@pytest.mark.parametrize("bad", [10.0, 10.5, "10", None, True, False, [10]])
def test_coupon_of_the_wrong_type_raises_type_error(bad):
    with pytest.raises(TypeError, match="coupon"):
        checkout(10_000, bad, False)


@pytest.mark.parametrize("bad", [0, 1, None, "yes", "", 1.0])
def test_member_must_be_a_bool(bad):
    with pytest.raises(TypeError, match="member"):
        checkout(10_000, 0, bad)


# ---------------------------------------------------------------------------
# Rules 2-4: member 10%, coupon N%, stacking, cap at 30%
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("member", [False, True])
@pytest.mark.parametrize("coupon", range(51))
def test_total_discount_is_member_plus_coupon_capped_at_30_percent(coupon, member):
    # On a $100.00 cart every percentage point is exactly 100 cents.
    expected_percent = min(30, coupon + (10 if member else 0))
    price, _ = checkout(10_000, coupon, member)
    assert price == 10_000 - 100 * expected_percent


@pytest.mark.parametrize(
    "coupon, member, price",
    [
        (0, False, 10_000),  # no discount
        (0, True, 9_000),  # member only: 10%
        (15, False, 8_500),  # coupon only: 15%
        (15, True, 7_500),  # stacked additively: 10 + 15 = 25% (multiplying would give 7_650)
        (20, True, 7_000),  # 10 + 20 = 30%, exactly the cap
        (21, True, 7_000),  # 31% would be over the cap
        (50, True, 7_000),  # 60% would be far over the cap
        (30, False, 7_000),  # a coupon alone at the cap
        (31, False, 7_000),  # the cap holds for a coupon alone, too
        (50, False, 7_000),
    ],
)
def test_named_discount_examples(coupon, member, price):
    assert checkout(10_000, coupon, member)[0] == price


# ---------------------------------------------------------------------------
# Rule 5: round the discounted price to the nearest cent
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "subtotal, coupon, member, price",
    [
        (1, 0, True, 1),  # 0.9
        (4, 0, True, 4),  # 3.6
        (14, 0, True, 13),  # 12.6
        (99, 0, True, 89),  # 89.1
        (333, 0, True, 300),  # 299.7
        (1, 30, False, 1),  # 0.7
        (2, 30, False, 1),  # 1.4
        (3, 30, False, 2),  # 2.1
        (999_999, 7, True, 829_999),  # 829_999.17
        (1_000_000, 50, True, 700_000),
        (0, 50, True, 0),
        (1_000_000, 0, False, 1_000_000),
    ],
)
def test_price_is_rounded_to_the_nearest_cent(subtotal, coupon, member, price):
    assert checkout(subtotal, coupon, member)[0] == price


@pytest.mark.parametrize(
    "subtotal, coupon, member, price",
    [
        (5, 0, True, 5),  # 4.5  (round half to even would give 4)
        (15, 0, True, 14),  # 13.5
        (10, 15, False, 9),  # 8.5  (round half to even would give 8)
        (30, 5, False, 29),  # 28.5 (round half to even would give 28)
        (10, 25, False, 8),  # 7.5
        (10, 5, False, 10),  # 9.5
    ],
)
def test_an_exact_half_cent_rounds_up(subtotal, coupon, member, price):
    assert checkout(subtotal, coupon, member)[0] == price


# ---------------------------------------------------------------------------
# Rule 6: shipping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "subtotal, shipping",
    [
        (1, 499),
        (2_500, 499),
        (4_998, 499),
        (4_999, 499),  # $49.99 pays
        (5_000, 0),  # $50.00 ships free
        (5_001, 0),
        (10_000, 0),
        (1_000_000, 0),
    ],
)
def test_orders_under_50_dollars_pay_shipping_and_50_or_more_ship_free(subtotal, shipping):
    assert checkout(subtotal, 0, False)[1] == shipping


def test_free_shipping_is_decided_on_the_subtotal_before_discounts():
    # Decision: a $50.00 cart discounted to $35.00 is still a $50.00 order.
    assert checkout(5_000, 50, True) == (3_500, 0)
    assert checkout(5_000, 1, False) == (4_950, 0)
    # ... and a cart under $50.00 pays shipping whatever its discount.
    assert checkout(4_999, 0, False) == (4_999, 499)
    assert checkout(4_999, 50, True) == (3_499, 499)


def test_an_empty_cart_is_under_50_dollars_so_it_pays_shipping():
    # Decision: rule 6 is applied literally to a subtotal of 0.
    assert checkout(0, 0, False) == (0, 499)
    assert checkout(0, 50, True) == (0, 499)


# ---------------------------------------------------------------------------
# Rule 7: adding items to the cart never lowers the amount charged (price + shipping)
# ---------------------------------------------------------------------------


def test_price_never_decreases_as_the_cart_grows():
    subtotals = sorted(
        set(range(0, 301)) | set(range(4_900, 5_101)) | set(range(0, 1_000_001, 997)) | {1_000_000}
    )
    for coupon, member in ALL_PAIRS:
        prices = [checkout(subtotal, coupon, member)[0] for subtotal in subtotals]
        assert prices == sorted(prices), (coupon, member)


def test_charge_never_decreases_above_the_free_shipping_threshold():
    rng = random.Random(7)
    subtotals = sorted(rng.randint(FREE_FROM, 1_000_000) for _ in range(20_000))
    for coupon, member in SAMPLE_PAIRS:
        charges = [charge(subtotal, coupon, member) for subtotal in subtotals]
        assert charges == sorted(charges), (coupon, member)


def test_charge_never_decreases_below_the_free_shipping_threshold():
    for coupon, member in SAMPLE_PAIRS:
        charges = [charge(subtotal, coupon, member) for subtotal in range(FREE_FROM)]
        assert charges == sorted(charges), (coupon, member)


def test_rule_7_fails_only_at_the_free_shipping_threshold():
    # Every one-cent step from 0 to $60.00, for a pair of every discount level:
    # the charge only ever falls on the step from $49.99 to $50.00.
    for coupon, member in SAMPLE_PAIRS:
        assert steps_that_lower_the_charge(coupon, member, 6_000) == [4_999], (coupon, member)


def test_rules_6_and_7_conflict_at_the_free_shipping_threshold():
    # Concrete case from the module docstring of checkout.py.
    assert checkout(4_999, 0, False) == (4_999, 499)
    assert checkout(5_000, 0, False) == (5_000, 0)
    assert charge(4_999, 0, False) == 5_498
    assert charge(5_000, 0, False) == 5_000
    # The same $4.98 drop for every coupon/member combination.
    for coupon, member in ALL_PAIRS:
        assert charge(4_999, coupon, member) - charge(5_000, coupon, member) == FEE - 1


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "Request rules 6 and 7 contradict each other: rule 6 drops shipping from "
        "$4.99 to $0 at $50.00, so a $50.00 cart is charged 498 cents less than a "
        "$49.99 cart.  Rule 6 is implemented as written; see checkout.py."
    ),
)
def test_rule_7_adding_items_never_lowers_the_charge():
    for coupon, member in SAMPLE_PAIRS:
        assert steps_that_lower_the_charge(coupon, member, 6_000) == [], (coupon, member)


def test_a_discount_never_raises_the_charge():
    # Why free shipping is judged on the subtotal: a coupon or membership must never make
    # the customer pay more (it would if a discount could drop a cart under $50.00).
    subtotals = sorted(set(range(0, 61)) | set(range(4_900, 5_101)) | {5_555, 7_143, 10_000, 1_000_000})
    for subtotal in subtotals:
        for member in (False, True):
            charges = [charge(subtotal, coupon, member) for coupon in range(51)]
            assert charges == sorted(charges, reverse=True), (subtotal, member)
        for coupon in range(51):
            assert charge(subtotal, coupon, True) <= charge(subtotal, coupon, False), (subtotal, coupon)


# ---------------------------------------------------------------------------
# Cross-checks against an independent exact-arithmetic oracle
# ---------------------------------------------------------------------------


def test_matches_the_oracle_for_every_small_cart():
    for subtotal in range(301):
        for coupon, member in ALL_PAIRS:
            assert checkout(subtotal, coupon, member) == (
                reference_price(subtotal, coupon, member),
                reference_shipping(subtotal),
            ), (subtotal, coupon, member)


def test_matches_the_oracle_for_random_carts():
    rng = random.Random(20261108)
    for _ in range(20_000):
        subtotal = rng.randint(0, 1_000_000)
        coupon = rng.randint(0, 50)
        member = rng.random() < 0.5
        price, shipping = checkout(subtotal, coupon, member)
        assert (price, shipping) == (
            reference_price(subtotal, coupon, member),
            reference_shipping(subtotal),
        ), (subtotal, coupon, member)
        # Never more than 30% off (to within the half-cent of rounding), never a surcharge.
        assert 100 * price >= 70 * subtotal - 50
        assert price <= subtotal
