"""Tests of checkout.py, including student pricing (change request C-STUDENT-1)."""
import pytest

from checkout import checkout


# Customers who are not students: nothing changes for them.

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


def test_non_student_free_shipping_still_starts_at_fifty_dollars():
    assert checkout(7499, 0, False) == (7499, 0)
    assert checkout(7499, 0, False, False) == (7499, 0)


def _checkout_before_change(subtotal, coupon, member):
    """checkout() as it was before C-STUDENT-1, frozen for the test below."""
    discount = min(coupon + (10 if member else 0), 30)
    price = (subtotal * (100 - discount) + 50) // 100
    shipping = 499 if subtotal < 5000 else 0
    return price, shipping


@pytest.mark.parametrize('subtotal', [
    0, 1, 5, 49, 50, 51, 4999, 5000, 5001, 7499, 7500, 7501,
    10000, 123_457, 999_999, 1_000_000,
])
def test_nothing_changes_for_non_students(subtotal):
    for coupon in range(51):
        for member in (False, True):
            expected = _checkout_before_change(subtotal, coupon, member)
            assert checkout(subtotal, coupon, member) == expected
            assert checkout(subtotal, coupon, member, False) == expected
            assert checkout(subtotal, coupon, member, student=False) == expected


# Students: 15% off, added to the other discounts with the total still capped
# at 30%, and free shipping from $75.

def test_student_discount():
    # The example from the change request.
    assert checkout(10000, 0, False, True) == (8500, 0)
    assert checkout(10000, 0, False, student=True) == (8500, 0)


def test_student_discount_adds_to_coupon():
    assert checkout(10000, 10, False, True) == (7500, 0)


def test_student_discount_adds_to_membership():
    assert checkout(10000, 0, True, True) == (7500, 0)


def test_student_discount_adds_to_coupon_and_membership():
    assert checkout(10000, 4, True, True) == (7100, 0)


@pytest.mark.parametrize('coupon, member', [(5, True), (6, True), (15, False), (20, False), (50, True)])
def test_student_cap(coupon, member):
    assert checkout(10000, coupon, member, True) == (7000, 0)


def test_student_rounding_half_up():
    assert checkout(10, 0, False, True) == (9, 499)


def test_student_order_under_75_dollars_pays_shipping():
    assert checkout(5000, 0, False, True) == (4250, 499)
    assert checkout(7499, 0, False, True) == (6374, 499)


def test_student_75_dollars_ships_free():
    assert checkout(7500, 0, False, True) == (6375, 0)


def test_student_shipping_uses_subtotal_before_discounts():
    # The discounted price is $68.00, but the $80.00 subtotal ships free.
    assert checkout(8000, 0, False, True) == (6800, 0)


def test_student_range_ends():
    assert checkout(0, 0, False, True) == (0, 499)
    assert checkout(1_000_000, 50, True, True) == (700_000, 0)


@pytest.mark.parametrize('student', [False, True])
@pytest.mark.parametrize('subtotal, coupon', [(-1, 0), (1_000_001, 0), (100, 51), (100, -1)])
def test_out_of_range(subtotal, coupon, student):
    with pytest.raises(ValueError):
        checkout(subtotal, coupon, False, student)
