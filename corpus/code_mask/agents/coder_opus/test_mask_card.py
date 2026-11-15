"""Tests for mask_card (request P-MASK-1)."""

import doctest
import random

import pytest

import mask_card as mask_card_module
from mask_card import mask_card

DIGITS = "0123456789"
SEPARATORS = " -"

# Digits left visible, by digit count: the last four, but never more than a
# quarter of the digits (rule 4), so 12- to 15-digit cards show three.
SHOWN = {12: 3, 13: 3, 14: 3, 15: 3, 16: 4, 17: 4, 18: 4, 19: 4}


# --- helpers, written independently of the implementation ------------------


def luhn_ok(digits: str) -> bool:
    """Reference Luhn check: double every second digit from the right."""
    total = 0
    for offset, char in enumerate(reversed(digits)):
        product = int(char) * (2 if offset % 2 else 1)
        total += sum(int(p) for p in str(product))  # digit sum, e.g. 16 -> 7
    return total % 10 == 0


def make_valid(count: int, rng: random.Random) -> str:
    """Return a random Luhn-valid string of ``count`` digits."""
    payload = "".join(rng.choice(DIGITS) for _ in range(count - 1))
    return next(payload + d for d in DIGITS if luhn_ok(payload + d))


def make_invalid(count: int, rng: random.Random) -> str:
    """Return a random string of ``count`` digits that fails the Luhn check."""
    valid = make_valid(count, rng)
    return valid[:-1] + rng.choice([d for d in DIGITS if d != valid[-1]])


def with_random_separators(digits: str, rng: random.Random) -> str:
    """Put random runs of spaces and hyphens before, between and after digits."""

    def run() -> str:
        return "".join(rng.choice(SEPARATORS) for _ in range(rng.choice((0, 0, 0, 1, 2))))

    return run() + "".join(d + run() for d in digits)


def accepts(number: str) -> bool:
    try:
        mask_card(number)
    except ValueError:
        return False
    return True


def to_script(digits: str, zero: int) -> str:
    """Spell ASCII ``digits`` with the Unicode digits starting at code point ``zero``."""
    return "".join(chr(zero + int(d)) for d in digits)


# --- masking ---------------------------------------------------------------


def test_example_from_request():
    assert mask_card("4111 1111 1111 1111") == "**** **** **** 1111"


@pytest.mark.parametrize(
    "number, expected",
    [
        ("4111111111111111", "************1111"),
        ("4111-1111-1111-1111", "****-****-****-1111"),
        ("5555 5555 5555 4444", "**** **** **** 4444"),
        ("6011-0009-9013-9424", "****-****-****-9424"),
        ("12345678901234569", "*************4569"),  # 17 digits
        ("1234 5678 9012 3456 71", "**** **** **** **56 71"),  # 18 digits
        ("6205 5000 0000 0000 004", "**** **** **** ***0 004"),  # 19 digits
    ],
)
def test_long_cards_show_last_four_digits(number, expected):
    assert mask_card(number) == expected


@pytest.mark.parametrize(
    "number, expected",
    [
        ("1234 5678 9015", "**** **** *015"),  # 12 digits
        ("000000000000", "*********000"),  # 12 digits
        ("4222 2222 22222", "**** **** **222"),  # 13 digits
        ("3056 930902 5904", "**** ****** *904"),  # 14 digits
        ("3782 822463 10005", "**** ****** **005"),  # 15 digits
        ("3714-496353-98431", "****-******-**431"),  # 15 digits
    ],
)
def test_short_cards_show_only_a_quarter_of_their_digits(number, expected):
    assert mask_card(number) == expected


@pytest.mark.parametrize(
    "number, expected",
    [
        (" 4111 1111 1111 1111 ", " **** **** **** 1111 "),
        ("-4111111111111111-", "-************1111-"),
        ("4111111111111111     ", "************1111     "),
        ("4111  1111--1111 - 1111", "****  ****--**** - 1111"),
        ("4111 1111 1111 11-11", "**** **** **** 11-11"),
        ("41111111 11111111", "******** ****1111"),
        ("4 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1", "* * * * * * * * * * * * 1 1 1 1"),
    ],
)
def test_spaces_and_hyphens_stay_where_they_are(number, expected):
    assert mask_card(number) == expected


@pytest.mark.parametrize(
    "number",
    [
        "4111111111111111",
        "4012888888881881",
        "4222222222222",
        "5555555555554444",
        "5105105105105100",
        "378282246310005",
        "371449635398431",
        "6011111111111117",
        "6011000990139424",
        "30569309025904",
        "38520000023237",
        "3530111333300000",
        "3566002020360505",
        "6205500000000000004",
    ],
)
def test_accepts_published_test_card_numbers(number):
    shown = SHOWN[len(number)]
    assert mask_card(number) == "*" * (len(number) - shown) + number[-shown:]


@pytest.mark.parametrize("count, shown", sorted(SHOWN.items()))
def test_random_cards_keep_layout_and_show_only_the_last_digits(count, shown):
    rng = random.Random(count)
    for _ in range(200):
        digits = make_valid(count, rng)
        number = with_random_separators(digits, rng)
        result = mask_card(number)

        assert isinstance(result, str)
        assert len(result) == len(number)
        digit_positions = [i for i, c in enumerate(number) if c in DIGITS]
        visible_positions = [i for i, c in enumerate(result) if c in DIGITS]
        assert visible_positions == digit_positions[-shown:]
        for i, char in enumerate(number):
            if char in SEPARATORS or i in visible_positions:
                assert result[i] == char
            else:
                assert result[i] == "*"
        assert 4 * len(visible_positions) <= count  # never more than a quarter


# --- rejection -------------------------------------------------------------

VALID = "4111 1111 1111 1111"


@pytest.mark.parametrize(
    "number",
    [
        pytest.param(VALID.replace(" ", "\t"), id="tab"),
        pytest.param(VALID.replace(" ", "\n"), id="newline"),
        pytest.param(VALID + "\n", id="trailing-newline"),
        pytest.param(VALID + "\r", id="carriage-return"),
        pytest.param(VALID.replace(" ", " "), id="no-break-space"),
        pytest.param(VALID.replace(" ", " "), id="narrow-no-break-space"),
        pytest.param(VALID.replace(" ", " "), id="thin-space"),
        pytest.param(VALID.replace(" ", "　"), id="ideographic-space"),
        pytest.param(VALID.replace(" ", "​"), id="zero-width-space"),
        pytest.param("﻿" + VALID, id="byte-order-mark"),
        pytest.param(VALID.replace(" ", "‐"), id="unicode-hyphen"),
        pytest.param(VALID.replace(" ", "‑"), id="non-breaking-hyphen"),
        pytest.param(VALID.replace(" ", "–"), id="en-dash"),
        pytest.param(VALID.replace(" ", "—"), id="em-dash"),
        pytest.param(VALID.replace(" ", "−"), id="minus-sign"),
        pytest.param(VALID.replace(" ", "­"), id="soft-hyphen"),
        pytest.param(VALID.replace(" ", "."), id="dot"),
        pytest.param(VALID.replace(" ", "/"), id="slash"),
        pytest.param(VALID.replace(" ", "_"), id="underscore"),
        pytest.param(VALID.replace(" ", ","), id="comma"),
        pytest.param("+" + VALID, id="plus-sign"),
        pytest.param("(4111) 1111 1111 1111", id="parentheses"),
        pytest.param(VALID + "x", id="trailing-letter"),
        pytest.param("4111 1111 1111 111l", id="letter-l-for-one"),
        pytest.param(VALID + "\x00", id="nul"),
        pytest.param(to_script("4111111111111111", 0xFF10), id="fullwidth-digits"),
        pytest.param(to_script("4111111111111111", 0x0660), id="arabic-indic-digits"),
        pytest.param(to_script("4111111111111111", 0x0966), id="devanagari-digits"),
        pytest.param(to_script("4111111111111111", 0x1D7CE), id="math-bold-digits"),
        pytest.param("4111 1111 1111 111¹", id="superscript-one"),
    ],
)
def test_rejects_characters_other_than_ascii_digits_spaces_and_hyphens(number):
    with pytest.raises(ValueError, match="only digits, spaces and hyphens"):
        mask_card(number)


@pytest.mark.parametrize("count", [1, 2, 4, 8, 10, 11, 20, 21, 25, 32])
def test_rejects_fewer_than_12_or_more_than_19_digits(count):
    rng = random.Random(count)
    digits = make_valid(count, rng)  # passes Luhn, so only the count is wrong
    for number in (digits, " ".join(digits), with_random_separators(digits, rng)):
        with pytest.raises(ValueError, match="12 to 19 digits"):
            mask_card(number)


@pytest.mark.parametrize("number", ["", " ", "-", " - - ", "    ----    "])
def test_rejects_input_without_digits(number):
    with pytest.raises(ValueError, match="12 to 19 digits"):
        mask_card(number)


@pytest.mark.parametrize("number", ["4111 1111 1111 1112", "4111111111111110", "3782-822463-10006"])
def test_rejects_numbers_that_fail_luhn(number):
    with pytest.raises(ValueError, match="Luhn"):
        mask_card(number)


@pytest.mark.parametrize("count", range(12, 20))
def test_rejects_random_numbers_that_fail_luhn(count):
    rng = random.Random(100 + count)
    for _ in range(100):
        number = with_random_separators(make_invalid(count, rng), rng)
        with pytest.raises(ValueError, match="Luhn"):
            mask_card(number)


@pytest.mark.parametrize(
    "number", ["4111111111111111", "4222222222222", "378282246310005", "6205500000000000004"]
)
def test_rejects_every_single_digit_typo(number):
    typos = [
        number[:i] + d + number[i + 1 :]
        for i in range(len(number))
        for d in DIGITS
        if d != number[i]
    ]
    assert [t for t in typos if accepts(t)] == []


@pytest.mark.parametrize("count", range(12, 20))
def test_accepts_exactly_the_numbers_that_pass_luhn(count):
    rng = random.Random(200 + count)
    candidates = [make_valid(count, rng) for _ in range(100)]
    candidates += ["".join(rng.choice(DIGITS) for _ in range(count)) for _ in range(300)]
    assert [c for c in candidates if accepts(c) != luhn_ok(c)] == []


@pytest.mark.parametrize(
    "number",
    [
        "5555 5555 5555 4445",  # fails Luhn
        "8765 4321 8765 4321 8765",  # 20 digits
        "4111 1111 1111 1111 x",  # invalid character
    ],
)
def test_error_messages_do_not_reveal_the_card_number(number):
    digits = "".join(c for c in number if c in DIGITS)
    with pytest.raises(ValueError) as excinfo:
        mask_card(number)
    message = str(excinfo.value)
    for i in range(len(digits) - 3):
        assert digits[i : i + 4] not in message


@pytest.mark.parametrize(
    "value",
    [4111111111111111, None, b"4111 1111 1111 1111", list("4111111111111111")],
    ids=["int", "none", "bytes", "list"],
)
def test_rejects_non_string_input(value):
    with pytest.raises(TypeError):
        mask_card(value)


def test_docstring_examples_are_correct():
    results = doctest.testmod(mask_card_module)
    assert results.attempted > 0
    assert results.failed == 0
