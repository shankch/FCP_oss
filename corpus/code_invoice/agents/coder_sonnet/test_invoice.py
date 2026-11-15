import copy
import random

import pytest

from invoice import invoice


def item(price, qty=1, sale=False):
    return {"price": price, "qty": qty, "sale": sale}


# --- the example from the request ------------------------------------------

def test_request_example():
    assert invoice([item(1999, 2)], True) == {"lines": [3599], "discount": 399, "total": 3599}


# --- members vs non-members ---------------------------------------------------

def test_non_member_pays_full_price_and_no_discount():
    result = invoice([item(1999, 2), item(500, 3)], False)
    assert result == {"lines": [3998, 1500], "discount": 0, "total": 5498}


def test_non_member_gets_nothing_even_on_sale_items():
    result = invoice([item(1000, 1, sale=True)], False)
    assert result == {"lines": [1000], "discount": 0, "total": 1000}


def test_member_gets_no_discount_on_sale_items():
    result = invoice([item(1000, 3, sale=True)], True)
    assert result == {"lines": [3000], "discount": 0, "total": 3000}


def test_member_mixed_sale_and_regular_lines_keep_order():
    items = [item(1000, 1), item(2000, 1, sale=True), item(3000, 2)]
    result = invoice(items, True)
    assert result["lines"] == [900, 2000, 5400]
    assert result["discount"] == 100 + 600
    assert result["total"] == 900 + 2000 + 5400


def test_member_exact_ten_percent_has_no_rounding():
    assert invoice([item(1000, 1)], True) == {"lines": [900], "discount": 100, "total": 900}


# --- rounding ----------------------------------------------------------------

def test_discount_rounds_down_not_to_nearest():
    # 10% of 19 is 1.9 -> 1; 10% of 16 is 1.6 -> 1
    assert invoice([item(19)], True)["discount"] == 1
    assert invoice([item(16)], True)["discount"] == 1


def test_discount_below_one_cent_is_zero():
    assert invoice([item(9)], True) == {"lines": [9], "discount": 0, "total": 9}


def test_rounding_is_on_price_times_quantity_not_unit_price():
    # unit discount would be floor(0.5) = 0; the line is 10 cents, so 1 cent off
    assert invoice([item(5, 2)], True) == {"lines": [9], "discount": 1, "total": 9}


def test_rounding_is_per_line_and_discount_is_sum_of_line_discounts():
    # Two lines of 1999: each loses floor(199.9) = 199, so 398 in total.
    # (Rounding the combined 3998 once would give 399 and the lines would not
    # add up to the total.)
    result = invoice([item(1999), item(1999)], True)
    assert result == {"lines": [1800, 1800], "discount": 398, "total": 3600}


# --- the invariants stated in the rules ---------------------------------------

def check_rules(items, member, result):
    gross = [i["price"] * i["qty"] for i in items]
    assert len(result["lines"]) == len(items)
    expected_line_discounts = [
        (g // 10) if (member and not i["sale"]) else 0 for g, i in zip(gross, items)
    ]
    # rule 2 and 3
    assert result["lines"] == [g - d for g, d in zip(gross, expected_line_discounts)]
    # rule 4
    assert result["discount"] == (sum(expected_line_discounts) if member else 0)
    # rule 5
    assert result["total"] == sum(result["lines"])
    # rule 6
    assert result["total"] == sum(gross) - result["discount"]


def test_rules_hold_for_random_orders():
    rng = random.Random(20240607)
    for _ in range(2000):
        items = [
            item(rng.randint(0, 100_000), rng.randint(1, 9), rng.random() < 0.4)
            for _ in range(rng.randint(1, 8))
        ]
        for member in (True, False):
            check_rules(items, member, invoice(items, member))


# --- errors ------------------------------------------------------------------

@pytest.mark.parametrize("member", [True, False])
def test_empty_items_raises(member):
    with pytest.raises(ValueError):
        invoice([], member)


@pytest.mark.parametrize("member", [True, False])
def test_zero_quantity_raises(member):
    with pytest.raises(ValueError):
        invoice([item(1000, 0)], member)


def test_zero_quantity_raises_even_when_other_items_are_fine():
    with pytest.raises(ValueError):
        invoice([item(1000, 2), item(500, 0, sale=True), item(300, 1)], True)


def test_zero_quantity_on_a_sale_item_raises():
    with pytest.raises(ValueError):
        invoice([item(1000, 0, sale=True)], False)


def test_negative_quantity_raises():
    with pytest.raises(ValueError):
        invoice([item(1000, -1)], True)


def test_negative_price_raises():
    with pytest.raises(ValueError):
        invoice([item(-1000, 1)], True)


@pytest.mark.parametrize("bad", [19.99, "1999", None, True])
def test_non_integer_price_raises(bad):
    with pytest.raises(ValueError):
        invoice([item(bad, 1)], True)


@pytest.mark.parametrize("bad", [1.5, "2", None, True])
def test_non_integer_quantity_raises(bad):
    with pytest.raises(ValueError):
        invoice([item(1000, bad)], True)


@pytest.mark.parametrize("missing", ["price", "qty", "sale"])
def test_missing_key_raises(missing):
    bad = item(1000, 1)
    del bad[missing]
    with pytest.raises(ValueError):
        invoice([bad], True)


# --- edge cases ----------------------------------------------------------------

def test_free_item_is_allowed():
    assert invoice([item(0, 3)], True) == {"lines": [0], "discount": 0, "total": 0}


def test_single_item_single_quantity_non_member():
    assert invoice([item(1)], False) == {"lines": [1], "discount": 0, "total": 1}


def test_large_amounts_are_exact():
    # would lose precision (and round wrongly) with floats
    price = 10**15 + 9
    result = invoice([item(price, 3)], True)
    gross = price * 3
    assert result["discount"] == gross // 10
    assert result["total"] == gross - gross // 10


def test_input_is_not_modified():
    items = [item(1999, 2), item(500, 1, sale=True)]
    snapshot = copy.deepcopy(items)
    invoice(items, True)
    assert items == snapshot


def test_result_values_are_ints_and_lines_is_a_list():
    result = invoice([item(1999, 2)], True)
    assert isinstance(result["lines"], list)
    assert all(type(x) is int for x in result["lines"])
    assert type(result["discount"]) is int
    assert type(result["total"]) is int
    assert set(result) == {"lines", "discount", "total"}
