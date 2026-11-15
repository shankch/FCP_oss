import random

import pytest

from invoice import invoice


def item(price, qty=1, sale=False):
    return {"price": price, "qty": qty, "sale": sale}


# --- the request's example -------------------------------------------------

def test_request_example():
    assert invoice([item(1999, 2)], True) == {
        "lines": [3599],
        "discount": 399,
        "total": 3599,
    }


# --- rule 1: validation ----------------------------------------------------

def test_empty_items_raises():
    with pytest.raises(ValueError):
        invoice([], True)
    with pytest.raises(ValueError):
        invoice([], False)


def test_zero_quantity_raises():
    with pytest.raises(ValueError):
        invoice([item(500, 1), item(500, 0)], False)


def test_zero_quantity_raises_for_sale_item_too():
    with pytest.raises(ValueError):
        invoice([item(500, 0, sale=True)], True)


@pytest.mark.parametrize(
    "bad",
    [
        {"price": 100, "qty": -1, "sale": False},   # negative quantity
        {"price": -100, "qty": 1, "sale": False},   # negative price
        {"price": 1.5, "qty": 1, "sale": False},    # non-integer cents
        {"price": 100, "qty": 1.0, "sale": False},  # non-integer quantity
        {"price": True, "qty": 1, "sale": False},   # bool is not a price
        {"price": 100, "qty": True, "sale": False},  # bool is not a quantity
        {"price": 100, "qty": 1, "sale": "no"},     # sale must be bool
        {"price": 100, "qty": 1},                   # missing key
        "not a dict",
    ],
)
def test_malformed_item_raises(bad):
    with pytest.raises(ValueError):
        invoice([bad], True)


def test_member_must_be_bool():
    with pytest.raises(ValueError):
        invoice([item(100)], "yes")


def test_input_not_mutated():
    items = [item(1999, 2), item(500, 3, sale=True)]
    snapshot = [dict(i) for i in items]
    invoice(items, True)
    assert items == snapshot


# --- rules 2 and 3: lines ---------------------------------------------------

def test_lines_keep_item_order():
    result = invoice([item(300), item(100), item(200)], False)
    assert result["lines"] == [300, 100, 200]


def test_non_member_pays_full_price():
    result = invoice([item(1999, 2), item(500, 3, sale=True)], False)
    assert result == {"lines": [3998, 1500], "discount": 0, "total": 5498}


def test_member_sale_item_not_discounted():
    result = invoice([item(1000, 1, sale=True)], True)
    assert result == {"lines": [1000], "discount": 0, "total": 1000}


def test_member_discount_rounds_down_per_line():
    # 10% of 999 = 99.9 -> 99 off
    assert invoice([item(999)], True)["lines"] == [900]
    # 10% of 9 = 0.9 -> 0 off
    assert invoice([item(9)], True)["lines"] == [9]


def test_member_mixed_sale_and_regular():
    result = invoice([item(1999, 2), item(500, 3, sale=True), item(250, 4)], True)
    # 3998 - 399, 1500 untouched, 1000 - 100
    assert result == {"lines": [3599, 1500, 900], "discount": 499, "total": 5999}


def test_free_item():
    assert invoice([item(0, 5)], True) == {"lines": [0], "discount": 0, "total": 0}


# --- rules 4, 5, 6: discount and total --------------------------------------

def test_discount_is_sum_of_rounded_line_discounts():
    # Where rules 3 and 4 disagree: each 15-cent line rounds 1.5 -> 1 cent off,
    # so the discount is 2, not floor(10% of 30) = 3. This keeps
    # total == sum(lines) == gross - discount.
    result = invoice([item(15), item(15)], True)
    assert result == {"lines": [14, 14], "discount": 2, "total": 28}


def test_invariants_hold_on_random_orders():
    rng = random.Random(20261109)
    for _ in range(2000):
        items = [
            item(rng.randint(0, 50_000), rng.randint(1, 20), rng.random() < 0.3)
            for _ in range(rng.randint(1, 8))
        ]
        member = rng.random() < 0.5
        result = invoice(items, member)
        gross = sum(i["price"] * i["qty"] for i in items)

        assert len(result["lines"]) == len(items)
        assert result["total"] == sum(result["lines"])        # rule 5
        assert result["total"] == gross - result["discount"]  # rule 6

        for line, i in zip(result["lines"], items):
            amount = i["price"] * i["qty"]
            if member and not i["sale"]:
                assert line == amount - amount // 10           # rule 3
            else:
                assert line == amount

        if not member:
            assert result["discount"] == 0                      # rule 4
        else:
            eligible = sum(i["price"] * i["qty"] for i in items if not i["sale"])
            # Per-line rounding can fall short of rounding the summed
            # discount once by at most (discounted lines - 1) cents.
            discounted = sum(1 for i in items if not i["sale"])
            shortfall = eligible // 10 - result["discount"]
            assert 0 <= shortfall <= max(discounted - 1, 0)
