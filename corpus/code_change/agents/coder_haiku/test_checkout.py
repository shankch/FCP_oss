"""Tests of checkout.py."""
import pytest

from checkout import checkout


def test_member_discount():
    assert checkout(10000, 0, True) == (9000, 0)


def test_coupon():
    assert checkout(10000, 20, False) == (8000, 0)


def test_cap():
    assert checkout(10000, 25, True) == (7000, 0)


def test_rounding_half_up():
    assert checkout(5, 0, True) == (5, 499)


def test_small_order_pays_shipping():
    assert checkout(4999, 0, False) == (4999, 499)


def test_fifty_dollars_ships_free():
    assert checkout(5000, 0, False) == (5000, 0)


@pytest.mark.parametrize('subtotal', [6000, 7499])
def test_non_student_free_shipping_still_starts_at_50(subtotal):
    assert checkout(subtotal, 0, False) == (subtotal, 0)


def test_non_student_gets_no_student_discount():
    assert checkout(10000, 0, False, False) == (10000, 0)


@pytest.mark.parametrize('coupon, member, expected', [
    (0, False, (8500, 0)),   # 15% student discount alone
    (5, False, (8000, 0)),   # 15% + 5% coupon
    (0, True, (7500, 0)),    # 15% + 10% member
    (15, False, (7000, 0)),  # 15% + 15% is exactly the 30% cap
    (25, True, (7000, 0)),   # 15% + 10% + 25% would be 50%, capped at 30%
])
def test_student_discount(coupon, member, expected):
    assert checkout(10000, coupon, member, True) == expected


def test_student_rounding_half_up():
    # 10 cents at 85% is 8.5 cents, which rounds up to 9
    assert checkout(10, 0, False, True) == (9, 499)


@pytest.mark.parametrize('subtotal, expected', [
    (5000, (4250, 499)),  # $50 is not free shipping for students
    (7499, (6374, 499)),
    (7500, (6375, 0)),    # $75 ships free for students
])
def test_student_free_shipping_starts_at_75(subtotal, expected):
    assert checkout(subtotal, 0, False, True) == expected


@pytest.mark.parametrize('subtotal, coupon', [(-1, 0), (1_000_001, 0), (100, 51), (100, -1)])
def test_out_of_range(subtotal, coupon):
    with pytest.raises(ValueError):
        checkout(subtotal, coupon, False)
