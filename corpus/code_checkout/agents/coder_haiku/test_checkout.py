import pytest

from checkout import checkout


def charge(subtotal, coupon, member):
    """Amount charged: price plus shipping."""
    price, shipping = checkout(subtotal, coupon, member)
    return price + shipping


# Rules 2-5: member discount, coupon, stacking with a 30% cap, rounding.


def test_request_example_member_with_100_dollar_cart():
    assert checkout(10_000, 0, True) == (9_000, 0)


def test_no_member_and_no_coupon_pays_full_price():
    assert checkout(10_000, 0, False) == (10_000, 0)


def test_coupon_alone_takes_its_percent_off():
    assert checkout(10_000, 20, False) == (8_000, 0)


def test_member_discount_and_coupon_add_together():
    # 10% member + 15% coupon = 25% off
    assert checkout(10_000, 15, True) == (7_500, 0)


@pytest.mark.parametrize(
    "coupon, price",
    [
        (19, 7_100),  # 29% total, under the cap
        (20, 7_000),  # 30% total, exactly the cap
        (21, 7_000),  # 31% total, capped at 30%
    ],
)
def test_total_discount_is_capped_at_30_percent_for_members(coupon, price):
    assert checkout(10_000, coupon, True) == (price, 0)


def test_coupon_alone_is_capped_at_30_percent():
    assert checkout(10_000, 50, False) == (7_000, 0)


@pytest.mark.parametrize(
    "subtotal, coupon, member, expected",
    [
        (1_005, 0, True, (905, 499)),  # 904.5 rounds half up, not to even
        (15, 20, True, (11, 499)),  # 10.5 at 30% off rounds up
        (3, 20, True, (2, 499)),  # 2.1 at 30% off rounds down
        (1, 0, True, (1, 499)),  # 0.9 rounds up
        (1_001, 15, False, (851, 499)),  # 850.85 rounds up
    ],
)
def test_discounted_price_rounds_to_nearest_cent(subtotal, coupon, member, expected):
    assert checkout(subtotal, coupon, member) == expected


# Rule 6: shipping is judged on the discounted price, with the rule 7 floor.


def test_under_50_dollars_pays_4_99_shipping():
    assert checkout(4_999, 0, False) == (4_999, 499)


def test_empty_cart_is_accepted_and_pays_under_50_shipping():
    assert checkout(0, 0, False) == (0, 499)


def test_shipping_threshold_uses_the_discounted_price():
    # A $50.00 cart is $45.00 after the member discount, so shipping applies.
    assert checkout(5_000, 0, True) == (4_500, 499)


@pytest.mark.parametrize(
    "subtotal, shipping",
    [(5_000, 498), (5_001, 497), (5_497, 1), (5_498, 0), (6_000, 0)],
)
def test_shipping_tapers_to_free_once_charge_reaches_54_98(subtotal, shipping):
    assert checkout(subtotal, 0, False) == (subtotal, shipping)


# Rule 7: adding items never lowers the amount charged (price + shipping).


def test_charge_does_not_drop_at_the_50_dollar_line():
    assert charge(4_999, 0, False) == 5_498  # $49.99 + $4.99
    assert charge(5_000, 0, False) == 5_498  # $50.00 + $4.98
    assert charge(5_498, 0, False) == 5_498  # $54.98, free shipping
    assert charge(5_499, 0, False) == 5_499


@pytest.mark.parametrize("member", [False, True])
@pytest.mark.parametrize("coupon", range(0, 51))
def test_adding_items_never_lowers_the_charge(member, coupon):
    # Every subtotal from $0.00 to $80.00 (covers the shipping boundary at every
    # discount level, the highest being near $78.54), plus a sample of the rest.
    subtotals = sorted(set(range(0, 8_001)) | set(range(0, 1_000_001, 997)))
    charges = [charge(s, coupon, member) for s in subtotals]
    assert all(a <= b for a, b in zip(charges, charges[1:]))


# Rule 1: out-of-range values raise ValueError; non-integers raise TypeError.


@pytest.mark.parametrize("subtotal", [-1, 1_000_001])
def test_subtotal_out_of_range_raises_value_error(subtotal):
    with pytest.raises(ValueError):
        checkout(subtotal, 0, False)


@pytest.mark.parametrize("coupon", [-1, 51])
def test_coupon_out_of_range_raises_value_error(coupon):
    with pytest.raises(ValueError):
        checkout(10_000, coupon, False)


def test_range_endpoints_are_accepted():
    assert checkout(0, 0, False) == (0, 499)
    assert checkout(1_000_000, 50, True) == (700_000, 0)


@pytest.mark.parametrize(
    "subtotal, coupon",
    [(10_000.0, 0), (True, 0), (10_000, 10.0), (10_000, False)],
)
def test_non_integer_inputs_raise_type_error(subtotal, coupon):
    with pytest.raises(TypeError):
        checkout(subtotal, coupon, False)


def test_returns_integer_cents():
    price, shipping = checkout(10_000, 5, True)
    assert isinstance(price, int)
    assert isinstance(shipping, int)
