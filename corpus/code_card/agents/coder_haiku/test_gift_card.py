import pytest

from gift_card import GiftCard


def test_new_card_has_zero_balance():
    assert GiftCard().balance() == 0


def test_load_and_spend_example():
    card = GiftCard()
    assert card.load(2000) == 0
    assert card.spend(500) is True
    assert card.balance() == 1500


def test_load_adds_to_balance():
    card = GiftCard()
    card.load(999)
    card.load(1)
    assert card.balance() == 1000


@pytest.mark.parametrize("amount", [0, -1, 50_001])
def test_load_rejects_out_of_range(amount):
    card = GiftCard()
    with pytest.raises(ValueError):
        card.load(amount)
    assert card.balance() == 0


@pytest.mark.parametrize("amount", [0, -5, 50_001])
def test_spend_rejects_out_of_range(amount):
    card = GiftCard()
    card.load(1000)
    with pytest.raises(ValueError):
        card.spend(amount)
    assert card.balance() == 1000


def test_load_limits_are_inclusive():
    card = GiftCard()
    assert card.load(1) == 0
    assert card.balance() == 1


def test_non_int_amount_rejected():
    card = GiftCard()
    with pytest.raises(TypeError):
        card.load(10.5)
    with pytest.raises(TypeError):
        card.spend(True)
    assert card.balance() == 0


def test_bonus_at_exactly_100_dollars():
    card = GiftCard()
    assert card.load(10_000) == 500
    assert card.balance() == 10_500


def test_no_bonus_just_under_100_dollars():
    card = GiftCard()
    assert card.load(9_999) == 0
    assert card.balance() == 9_999


def test_bonus_is_added_to_balance():
    card = GiftCard()
    card.load(20_000)
    assert card.balance() == 20_500


def test_balance_cap_is_inclusive():
    card = GiftCard()
    card.load(10_000)            # 10_500 with bonus
    card.load(10_000)            # 21_000
    card.load(10_000)            # 31_500
    card.load(10_000)            # 42_000
    assert card.load(7_500) == 0  # 49_500 exactly, no bonus, under cap
    assert card.balance() == 49_500
    card.load(500)               # 50_000 exactly
    assert card.balance() == 50_000


def test_load_over_cap_raises_and_keeps_balance():
    card = GiftCard()
    card.load(30_000)  # 30_500
    with pytest.raises(ValueError):
        card.load(20_000)  # would be 50_500 with bonus
    assert card.balance() == 30_500


def test_bonus_counts_toward_cap():
    card = GiftCard()
    card.load(40_000)  # 40_500
    with pytest.raises(ValueError):
        card.load(10_000)  # 10_000 + 500 bonus would push to 51_000
    assert card.balance() == 40_500


def test_spend_exact_balance_returns_true_and_zeroes():
    card = GiftCard()
    card.load(1234)
    assert card.spend(1234) is True
    assert card.balance() == 0


def test_spend_more_than_balance_fails_and_keeps_balance():
    card = GiftCard()
    card.load(500)
    assert card.spend(501) is False
    assert card.balance() == 500


def test_spend_on_empty_card_fails():
    card = GiftCard()
    assert card.spend(1) is False
    assert card.balance() == 0


def test_cards_are_independent():
    a, b = GiftCard(), GiftCard()
    a.load(100)
    assert b.balance() == 0
