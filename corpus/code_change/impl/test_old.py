"""Tests of checkout.py as it was before the change."""
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


@pytest.mark.parametrize('subtotal, coupon', [(-1, 0), (1_000_001, 0), (100, 51), (100, -1)])
def test_out_of_range(subtotal, coupon):
    with pytest.raises(ValueError):
        checkout(subtotal, coupon, False)
