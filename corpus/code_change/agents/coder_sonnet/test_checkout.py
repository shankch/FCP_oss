"""Tests of checkout.py, including the student pricing of change request C-STUDENT-1."""
import pytest

from checkout import checkout


# Customers who are not students: nothing may change for them.

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


def test_non_student_free_shipping_limit_stays_fifty_dollars():
    # The $75 limit is for students only, so a $74.99 order still ships free.
    assert checkout(7499, 0, False) == (7499, 0)


def test_shipping_is_judged_before_discounts():
    # 30% off takes $50.00 down to $35.00, but the subtotal is what counts.
    assert checkout(5000, 30, False) == (3500, 0)


# Students.

def test_student_discount():
    # The example of the change request.
    assert checkout(10000, 0, False, True) == (8500, 0)


def test_student_discount_adds_to_member_discount():
    assert checkout(10000, 0, True, student=True) == (7500, 0)


def test_student_discount_adds_to_coupon():
    assert checkout(10000, 10, False, student=True) == (7500, 0)


@pytest.mark.parametrize('coupon, member, price', [
    (4, True, 7100),    # 4 + 10 + 15 = 29%: just under the cap
    (5, True, 7000),    # 5 + 10 + 15 = 30%: exactly the cap
    (10, True, 7000),   # 35%: capped
    (50, False, 7000),  # 65%: capped
])
def test_student_cap(coupon, member, price):
    assert checkout(10000, coupon, member, student=True) == (price, 0)


def test_student_rounding_half_up():
    # 15% off 10 cents leaves 8.5 cents, which rounds up to 9.
    assert checkout(10, 0, False, student=True) == (9, 499)


@pytest.mark.parametrize('subtotal, expected', [
    (4999, (4249, 499)),
    (5000, (4250, 499)),  # a student does not ship free at $50
    (7499, (6374, 499)),
    (7500, (6375, 0)),    # a student ships free from $75
])
def test_student_free_shipping_starts_at_seventy_five_dollars(subtotal, expected):
    assert checkout(subtotal, 0, False, student=True) == expected


def test_student_shipping_is_judged_before_discounts():
    # 30% off takes $75.00 down to $52.50, but the subtotal is what counts.
    assert checkout(7500, 50, False, student=True) == (5250, 0)


@pytest.mark.parametrize('student', [False, True])
@pytest.mark.parametrize('subtotal, coupon', [(-1, 0), (1_000_001, 0), (100, 51), (100, -1)])
def test_out_of_range(subtotal, coupon, student):
    with pytest.raises(ValueError):
        checkout(subtotal, coupon, False, student)
