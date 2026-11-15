import random

import pytest

from gift_card import GiftCard


def card_with(balance: int) -> GiftCard:
    """A card holding `balance` cents, built from loads under $100 (no bonus)."""
    card = GiftCard()
    while balance > 0:
        step = min(balance, 9_999)
        card.load(step)
        balance -= step
    return card


# --- new card and the request's example ---------------------------------

def test_new_card_balance_is_zero():
    assert GiftCard().balance() == 0


def test_example_from_request():
    card = GiftCard()
    card.load(2000)
    card.spend(500)
    assert card.balance() == 1500


def test_cards_are_independent():
    a, b = GiftCard(), GiftCard()
    a.load(100)
    assert a.balance() == 100
    assert b.balance() == 0


# --- rule 1: amount range -----------------------------------------------

@pytest.mark.parametrize("amount", [0, -1, -50_000, 50_001, 10**9])
def test_load_rejects_out_of_range(amount):
    card = card_with(1000)
    with pytest.raises(ValueError):
        card.load(amount)
    assert card.balance() == 1000


@pytest.mark.parametrize("amount", [0, -1, -50_000, 50_001, 10**9])
def test_spend_rejects_out_of_range(amount):
    card = card_with(1000)
    with pytest.raises(ValueError):
        card.spend(amount)
    assert card.balance() == 1000


def test_spend_over_range_raises_even_when_it_could_not_be_covered():
    # An out-of-range spend is an error, not a "not covered" False.
    with pytest.raises(ValueError):
        GiftCard().spend(50_001)


@pytest.mark.parametrize("amount", [1.0, 100.5, "100", None, True, False])
def test_non_int_amounts_rejected(amount):
    card = card_with(1000)
    with pytest.raises(TypeError):
        card.load(amount)
    with pytest.raises(TypeError):
        card.spend(amount)
    assert card.balance() == 1000


def test_smallest_amount_accepted():
    card = GiftCard()
    assert card.load(1) == 0
    assert card.balance() == 1
    assert card.spend(1) is True
    assert card.balance() == 0


def test_largest_spend_accepted():
    card = card_with(50_000)
    assert card.spend(50_000) is True
    assert card.balance() == 0


# --- rule 2: load adds the amount ---------------------------------------

def test_load_adds_amount():
    card = GiftCard()
    card.load(1234)
    card.load(766)
    assert card.balance() == 2000


# --- rule 4: bonus -------------------------------------------------------

def test_load_just_under_100_dollars_earns_no_bonus():
    card = GiftCard()
    assert card.load(9_999) == 0
    assert card.balance() == 9_999


def test_load_of_exactly_100_dollars_earns_bonus():
    card = GiftCard()
    assert card.load(10_000) == 500
    assert card.balance() == 10_500


def test_every_qualifying_load_earns_its_own_bonus():
    card = GiftCard()
    assert card.load(10_000) == 500
    assert card.load(20_000) == 500
    assert card.balance() == 31_000


def test_small_loads_do_not_add_up_to_a_bonus():
    card = GiftCard()
    for _ in range(3):
        assert card.load(5_000) == 0
    assert card.balance() == 15_000


def test_spend_does_not_earn_bonus():
    card = card_with(20_000)
    assert card.spend(15_000) is True
    assert card.balance() == 5_000


# --- rule 3: $500.00 balance limit --------------------------------------

def test_load_up_to_exactly_the_limit_without_bonus():
    card = card_with(40_001)
    assert card.load(9_999) == 0
    assert card.balance() == 50_000


def test_load_up_to_exactly_the_limit_with_bonus():
    card = GiftCard()
    assert card.load(49_500) == 500
    assert card.balance() == 50_000


def test_load_over_the_limit_raises_and_keeps_balance():
    card = card_with(45_000)
    with pytest.raises(ValueError):
        card.load(5_001)
    assert card.balance() == 45_000


def test_load_on_a_full_card_raises():
    card = card_with(50_000)
    with pytest.raises(ValueError):
        card.load(1)
    assert card.balance() == 50_000


def test_bonus_counts_toward_the_limit():
    # 40_000 + 10_000 is exactly 50_000, but the 500 bonus would take it over.
    card = card_with(40_000)
    with pytest.raises(ValueError):
        card.load(10_000)
    assert card.balance() == 40_000


@pytest.mark.parametrize("amount", [49_501, 49_999, 50_000])
def test_largest_loads_never_fit_because_of_the_bonus(amount):
    card = GiftCard()
    with pytest.raises(ValueError):
        card.load(amount)
    assert card.balance() == 0


# --- rule 5: spend -------------------------------------------------------

def test_spend_covered_returns_true_and_deducts():
    card = card_with(2_000)
    assert card.spend(500) is True
    assert card.balance() == 1_500


def test_spend_of_whole_balance_is_covered():
    card = card_with(2_000)
    assert card.spend(2_000) is True
    assert card.balance() == 0


def test_spend_one_cent_over_balance_returns_false_and_keeps_balance():
    card = card_with(2_000)
    assert card.spend(2_001) is False
    assert card.balance() == 2_000


def test_spend_on_empty_card_returns_false():
    card = GiftCard()
    assert card.spend(1) is False
    assert card.balance() == 0


def test_room_freed_by_spend_can_be_reloaded():
    card = card_with(50_000)
    assert card.spend(10_000) is True
    assert card.load(9_500) == 0
    assert card.balance() == 49_500


# --- invariants under random operations ----------------------------------

def test_random_operations_match_a_model_and_keep_the_invariant():
    rng = random.Random(1234)
    card = GiftCard()
    model = 0
    for _ in range(5_000):
        amount = rng.choice([
            rng.randint(-10, 0),
            rng.randint(1, 9_999),
            rng.randint(10_000, 50_000),
            rng.randint(50_001, 60_000),
            rng.choice([1, 9_999, 10_000, 49_500, 50_000]),
        ])
        if rng.random() < 0.5:
            bonus = 500 if amount >= 10_000 else 0
            if not 1 <= amount <= 50_000 or model + amount + bonus > 50_000:
                with pytest.raises(ValueError):
                    card.load(amount)
            else:
                assert card.load(amount) == bonus
                model += amount + bonus
        else:
            if not 1 <= amount <= 50_000:
                with pytest.raises(ValueError):
                    card.spend(amount)
            elif amount <= model:
                assert card.spend(amount) is True
                model -= amount
            else:
                assert card.spend(amount) is False
        assert card.balance() == model
        assert 0 <= card.balance() <= 50_000
