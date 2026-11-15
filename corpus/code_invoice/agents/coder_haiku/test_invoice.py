import random

import pytest

from invoice import invoice


def line(price, qty=1, sale=False):
    return {"price": price, "qty": qty, "sale": sale}


def test_example_from_request():
    result = invoice([{"price": 1999, "qty": 2, "sale": False}], True)
    assert result == {"lines": [3599], "discount": 399, "total": 3599}


def test_non_member_gets_no_discount():
    assert invoice([line(1999, 2)], False) == {"lines": [3998], "discount": 0, "total": 3998}


def test_member_with_only_sale_items_gets_no_discount():
    items = [line(500, 2, sale=True), line(100, sale=True)]
    assert invoice(items, True) == {"lines": [1000, 100], "discount": 0, "total": 1100}


def test_discount_only_on_non_sale_lines_and_order_is_kept():
    items = [line(1000), line(500, 3, sale=True), line(2500)]
    # gross 1000, 1500, 2500; discounts 100, 0, 250
    assert invoice(items, True) == {"lines": [900, 1500, 2250], "discount": 350, "total": 4650}


def test_line_discount_is_rounded_down_to_the_cent():
    # 10% of 15 cents is 1.5 cents, which rounds down to 1.
    assert invoice([line(15)], True) == {"lines": [14], "discount": 1, "total": 14}
    # 10% of 9 cents is 0.9 cents, which rounds down to 0.
    assert invoice([line(9)], True) == {"lines": [9], "discount": 0, "total": 9}


def test_invoice_discount_is_sum_of_rounded_line_discounts():
    # Each line discounts 1 cent (10% of 15 is 1.5). The invoice discount is
    # 2, not floor(10% of 30) = 3, so the lines and total still reconcile.
    result = invoice([line(15), line(15)], True)
    assert result == {"lines": [14, 14], "discount": 2, "total": 28}


def test_total_is_sum_of_lines_and_gross_minus_discount():
    items = [line(15), line(15), line(1999, 2), line(700, 3, sale=True)]
    result = invoice(items, True)
    gross = sum(i["price"] * i["qty"] for i in items)
    assert result["total"] == sum(result["lines"]) == gross - result["discount"]


def test_large_amounts_stay_exact():
    result = invoice([line(10**15 + 7, 3)], True)
    assert result == {
        "lines": [2700000000000019],
        "discount": 300000000000002,
        "total": 2700000000000019,
    }


def test_zero_price_item_is_allowed():
    assert invoice([line(0, 3)], True) == {"lines": [0], "discount": 0, "total": 0}


def test_random_orders_reconcile():
    rng = random.Random(20261108)
    for _ in range(500):
        items = [
            line(rng.randint(0, 5000), rng.randint(1, 9), sale=rng.random() < 0.3)
            for _ in range(rng.randint(1, 6))
        ]
        member = rng.random() < 0.5
        result = invoice(items, member)
        gross = [i["price"] * i["qty"] for i in items]
        discounted = [member and not i["sale"] for i in items]
        expected_lines = [g - (g // 10 if d else 0) for g, d in zip(gross, discounted)]
        expected_discount = sum(g // 10 for g, d in zip(gross, discounted) if d)
        assert result["lines"] == expected_lines
        assert result["discount"] == expected_discount
        assert result["total"] == sum(result["lines"]) == sum(gross) - result["discount"]


def test_empty_items_raises():
    with pytest.raises(ValueError):
        invoice([], True)
    with pytest.raises(ValueError):
        invoice([], False)


def test_zero_quantity_raises_even_with_other_valid_items():
    with pytest.raises(ValueError):
        invoice([line(100, 2), line(100, 0)], True)


@pytest.mark.parametrize("qty", [-1, -5])
def test_negative_quantity_raises(qty):
    with pytest.raises(ValueError):
        invoice([line(100, qty)], False)


def test_negative_price_raises():
    with pytest.raises(ValueError):
        invoice([line(-100)], True)


@pytest.mark.parametrize("price, qty", [(19.99, 1), (1999, 2.0), (True, 1), (1999, "2")])
def test_non_integer_price_or_quantity_raises(price, qty):
    with pytest.raises(TypeError):
        invoice([line(price, qty)], True)
