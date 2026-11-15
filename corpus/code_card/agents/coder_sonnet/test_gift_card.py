import pytest

from gift_card import GiftCard


def card_with(balance):
    """A card holding `balance` cents, built from loads below the bonus threshold."""
    c = GiftCard()
    while balance > 0:
        step = min(balance, 9_999)
        c.load(step)
        balance -= step
    return c


# --- new card / example ---------------------------------------------------

def test_new_card_is_empty():
    assert GiftCard().balance() == 0


def test_example_from_request():
    c = GiftCard()
    c.load(2000)
    assert c.spend(500) is True
    assert c.balance() == 1500


# --- rule 1: amount range -------------------------------------------------

@pytest.mark.parametrize("amount", [0, -1, -500, 50_001, 100_000])
def test_load_rejects_out_of_range(amount):
    c = GiftCard()
    with pytest.raises(ValueError):
        c.load(amount)
    assert c.balance() == 0


@pytest.mark.parametrize("amount", [0, -1, 50_001])
def test_spend_rejects_out_of_range(amount):
    c = card_with(1000)
    with pytest.raises(ValueError):
        c.spend(amount)
    assert c.balance() == 1000


def test_load_accepts_smallest_amount():
    c = GiftCard()
    assert c.load(1) == 0
    assert c.balance() == 1


def test_spend_accepts_smallest_amount():
    c = card_with(1)
    assert c.spend(1) is True
    assert c.balance() == 0


@pytest.mark.parametrize("bad", [10.5, "100", None, True, False])
def test_non_int_amounts_are_rejected(bad):
    c = card_with(1000)
    with pytest.raises(TypeError):
        c.load(bad)
    with pytest.raises(TypeError):
        c.spend(bad)
    assert c.balance() == 1000


# --- rule 2: load adds ----------------------------------------------------

def test_loads_accumulate():
    c = GiftCard()
    c.load(300)
    c.load(450)
    assert c.balance() == 750


# --- rule 3: balance cap --------------------------------------------------

def test_balance_can_reach_exactly_the_cap():
    c = card_with(40_000)
    assert c.load(9_999) == 0
    assert c.balance() == 49_999
    c.load(1)
    assert c.balance() == 50_000


def test_load_over_cap_is_rejected_and_card_unchanged():
    c = card_with(49_990)
    with pytest.raises(ValueError):
        c.load(11)
    assert c.balance() == 49_990


def test_full_card_rejects_any_load():
    c = card_with(50_000)
    with pytest.raises(ValueError):
        c.load(1)
    assert c.balance() == 50_000


def test_bonus_counts_towards_cap():
    # 40,000 + 9,500 = 49,500 fits; the 10,000 load plus bonus would reach 50,500.
    c = card_with(40_000)
    with pytest.raises(ValueError):
        c.load(10_000)
    assert c.balance() == 40_000


def test_load_whose_bonus_lands_exactly_on_cap_is_accepted():
    c = card_with(39_500)
    assert c.load(10_000) == 500
    assert c.balance() == 50_000


def test_maximum_single_load_never_fits_because_of_bonus():
    c = GiftCard()
    with pytest.raises(ValueError):
        c.load(50_000)
    assert c.balance() == 0


def test_cap_still_applies_after_spending():
    c = card_with(50_000)
    c.spend(100)
    assert c.load(100) == 0
    assert c.balance() == 50_000


# --- rule 4: bonus --------------------------------------------------------

def test_no_bonus_below_100_dollars():
    c = GiftCard()
    assert c.load(9_999) == 0
    assert c.balance() == 9_999


def test_bonus_at_exactly_100_dollars():
    c = GiftCard()
    assert c.load(10_000) == 500
    assert c.balance() == 10_500


def test_bonus_is_flat_not_per_hundred():
    c = GiftCard()
    assert c.load(30_000) == 500
    assert c.balance() == 30_500


def test_each_qualifying_load_earns_its_own_bonus():
    c = GiftCard()
    assert c.load(10_000) == 500
    assert c.load(10_000) == 500
    assert c.balance() == 21_000


def test_small_loads_do_not_add_up_to_a_bonus():
    c = GiftCard()
    for _ in range(3):
        assert c.load(5_000) == 0
    assert c.balance() == 15_000


def test_bonus_is_spendable():
    c = GiftCard()
    c.load(10_000)
    assert c.spend(10_500) is True
    assert c.balance() == 0


# --- rule 5: spend --------------------------------------------------------

def test_spend_exact_balance():
    c = card_with(700)
    assert c.spend(700) is True
    assert c.balance() == 0


def test_spend_more_than_balance_fails_and_keeps_balance():
    c = card_with(700)
    assert c.spend(701) is False
    assert c.balance() == 700


def test_spend_on_empty_card_fails():
    c = GiftCard()
    assert c.spend(1) is False
    assert c.balance() == 0


def test_spend_returns_real_bools():
    c = card_with(100)
    assert c.spend(50) is True
    assert c.spend(51) is False


def test_repeated_spends_until_exhausted():
    c = card_with(1000)
    assert c.spend(400) is True
    assert c.spend(400) is True
    assert c.spend(400) is False
    assert c.balance() == 200


# --- rule 6: balance ------------------------------------------------------

def test_balance_does_not_change_state():
    c = card_with(123)
    assert c.balance() == c.balance() == 123


def test_cards_are_independent():
    a, b = GiftCard(), GiftCard()
    a.load(500)
    assert b.balance() == 0
