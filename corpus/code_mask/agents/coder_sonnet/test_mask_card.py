"""Tests for mask_card (Fernwood Outfitters request P-MASK-1).

Decision pinned by these tests: rule 2 (keep the last four digits) and rule 4
(never show more than a quarter of the digits) conflict for 12 to 15 digit
numbers, where a quarter is only 3 digits.  mask_card lets the security rule win:
12-15 digit cards show their last 3 digits, 16-19 digit cards show their last 4.
If the store decides otherwise, update EXPECTED_SHOWN, LENGTH_CASES, the 12-15
digit entries of LITERAL_CASES and SEPARATOR_CASES, and the two rule 4 tests.
"""

import random

import pytest

from mask_card import mask_card

DIGITS = "0123456789"

# digit count -> number of trailing digits that may stay visible (rule 2 vs rule 4)
EXPECTED_SHOWN = {12: 3, 13: 3, 14: 3, 15: 3, 16: 4, 17: 4, 18: 4, 19: 4}


# ---------------------------------------------------------------------------
# Helpers.  The Luhn helper is written differently from the implementation
# (lookup table instead of arithmetic) so the tests do not merely mirror it.
# ---------------------------------------------------------------------------

_DOUBLED = (0, 2, 4, 6, 8, 1, 3, 5, 7, 9)  # digit d -> digit sum of 2*d


def luhn_valid(digits: str) -> bool:
    total = 0
    for position, char in enumerate(reversed(digits)):
        digit = int(char)
        total += _DOUBLED[digit] if position % 2 else digit
    return total % 10 == 0


def with_check_digit(payload: str) -> str:
    """Append the single check digit that makes `payload` Luhn-valid."""
    candidates = [payload + c for c in DIGITS if luhn_valid(payload + c)]
    assert len(candidates) == 1
    return candidates[0]


def luhn_number(length: int, rng: random.Random | None = None) -> str:
    """A Luhn-valid number of `length` digits (length >= 1).

    Without `rng` the leading digits are 1234567890123... so that the visible tail
    is easy to tell from the hidden head; with `rng` they are random.
    """
    assert length >= 1
    if rng is None:
        payload = ("1234567890" * 5)[: length - 1]
    else:
        payload = "".join(rng.choice(DIGITS) for _ in range(length - 1))
    return with_check_digit(payload)


def digits_of(text: str) -> str:
    return "".join(c for c in text if c in DIGITS)


_SEPARATOR_CHOICES = ["", "", "", " ", "-", "  ", " - ", "--"]


def with_random_separators(digits: str, rng: random.Random) -> str:
    """Interleave `digits` with random runs of spaces/hyphens, also at both ends."""
    pieces = [rng.choice(_SEPARATOR_CHOICES)]
    for digit in digits:
        pieces.append(digit)
        pieces.append(rng.choice(_SEPARATOR_CHOICES))
    return "".join(pieces)


# ---------------------------------------------------------------------------
# The example from the request
# ---------------------------------------------------------------------------


def test_example_from_the_request():
    assert mask_card("4111 1111 1111 1111") == "**** **** **** 1111"


# ---------------------------------------------------------------------------
# Literal expectations
# ---------------------------------------------------------------------------

# (input, expected).  Every input is a published-style test number that passes Luhn.
LITERAL_CASES = [
    # 16 digits: a quarter is exactly 4, so the last four digits stay visible
    ("4111111111111111", "************1111"),
    ("4111-1111-1111-1111", "****-****-****-1111"),
    ("5555 5555 5555 4444", "**** **** **** 4444"),
    ("5105-1051-0510-5100", "****-****-****-5100"),
    ("6011 1111 1111 1117", "**** **** **** 1117"),
    ("3530 1113 3330 0000", "**** **** **** 0000"),
    ("4012 8888 8888 1881", "**** **** **** 1881"),
    # 15 digits (Amex style): a quarter is 3.75, so at most 3 digits stay visible
    ("3782 822463 10005", "**** ****** **005"),
    ("371449635398431", "************431"),
    # 14 digits (Diners Club style): a quarter is 3.5 -> 3
    ("3056 930902 5904", "**** ****** *904"),
    ("3852-000002-3237", "****-******-*237"),
    # 13 digits: a quarter is 3.25 -> 3
    ("4222 2222 22222", "**** **** **222"),
    # 12 digits: a quarter is exactly 3
    ("1234 5678 9015", "**** **** *015"),
]


@pytest.mark.parametrize(("number", "expected"), LITERAL_CASES)
def test_literal_cases(number, expected):
    assert mask_card(number) == expected
    assert len(expected) == len(number)  # sanity check of the table itself


def test_literal_inputs_are_luhn_valid_per_the_independent_helper():
    # Guards against a typo in the table above being mistaken for an implementation bug.
    for number, _ in LITERAL_CASES:
        assert luhn_valid(digits_of(number)), number


# digits -> expected output, one entry per allowed length (rule 2 vs rule 4)
LENGTH_CASES = [
    ("123456789015", "*********015"),  # 12 digits -> last 3
    ("1234567890128", "**********128"),  # 13 -> last 3
    ("12345678901237", "***********237"),  # 14 -> last 3
    ("123456789012347", "************347"),  # 15 -> last 3
    ("1234567890123452", "************3452"),  # 16 -> last 4
    ("12345678901234569", "*************4569"),  # 17 -> last 4
    ("123456789012345671", "**************5671"),  # 18 -> last 4
    ("1234567890123456785", "***************6785"),  # 19 -> last 4
]


@pytest.mark.parametrize(("number", "expected"), LENGTH_CASES, ids=lambda v: str(len(v)))
def test_every_allowed_length_rule_2_vs_rule_4(number, expected):
    assert luhn_valid(number)
    assert mask_card(number) == expected


@pytest.mark.parametrize("digit_count", range(12, 20))
def test_shown_digits_per_length_matches_the_table(digit_count):
    number = luhn_number(digit_count)
    shown = EXPECTED_SHOWN[digit_count]
    assert mask_card(number) == "*" * (digit_count - shown) + number[-shown:]


# ---------------------------------------------------------------------------
# Rule 4: never more than a quarter of the digits
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("digit_count", range(12, 20))
def test_never_shows_more_than_a_quarter_of_the_digits(digit_count):
    rng = random.Random(digit_count)
    for _ in range(100):
        number = luhn_number(digit_count, rng)
        visible = len(digits_of(mask_card(number)))
        assert 4 * visible <= digit_count
        assert visible <= 4


@pytest.mark.parametrize("digit_count", range(12, 20))
def test_shows_as_many_digits_as_both_rules_allow(digit_count):
    # Not over-masked either: the visible count is the largest one that is
    # at most 4 (rule 2) and at most a quarter of the digits (rule 4).
    number = luhn_number(digit_count)
    visible = len(digits_of(mask_card(number)))
    assert visible == max(v for v in range(0, 5) if 4 * v <= digit_count)


# ---------------------------------------------------------------------------
# Rule 3: spaces and hyphens stay where they are
# ---------------------------------------------------------------------------

SEPARATOR_CASES = [
    ("4111-1111 1111-1111", "****-**** ****-1111"),  # mixed hyphens and spaces
    (" 4111 1111 1111 1111", " **** **** **** 1111"),  # leading space kept
    # trailing separators kept; "last four digits" means digits, not characters
    ("4111 1111 1111 1111 ", "**** **** **** 1111 "),
    ("4111 1111 1111 1111-", "**** **** **** 1111-"),
    ("-4111--1111  1111 - 1111 ", "-****--****  **** - 1111 "),  # repeated separators
    ("4 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1", "* * * * * * * * * * * * 1 1 1 1"),  # grouping is free
    ("41111111 11111111", "******** ****1111"),  # uneven groups
    ("3782-822463-10005", "****-******-**005"),  # 15 digits, 4-6-5 grouping
]


@pytest.mark.parametrize(("number", "expected"), SEPARATOR_CASES)
def test_separators_are_kept_in_place(number, expected):
    result = mask_card(number)
    assert result == expected
    assert len(result) == len(number)


def test_separator_runs_do_not_count_as_digits_in_either_direction():
    twelve = luhn_number(12)
    nineteen = luhn_number(19)
    eleven = luhn_number(11)
    twenty = luhn_number(20)
    # lots of separators around a valid digit count: accepted, same length as the input
    for number in (" - ".join(twelve), " - ".join(nineteen)):
        assert len(mask_card(number)) == len(number)
    # plenty of characters but too few / too many digits: rejected
    for number in (" - ".join(eleven), "-".join(twenty)):
        with pytest.raises(ValueError):
            mask_card(number)


@pytest.mark.parametrize("digit_count", range(12, 20))
def test_random_numbers_with_random_separators(digit_count):
    rng = random.Random(1000 + digit_count)
    shown = EXPECTED_SHOWN[digit_count]
    for _ in range(200):
        digits = luhn_number(digit_count, rng)
        number = with_random_separators(digits, rng)
        result = mask_card(number)

        assert isinstance(result, str)
        assert len(result) == len(number)  # rule 3
        for original, masked in zip(number, result):
            if original in " -":
                assert masked == original  # rule 3: separators untouched
            else:
                assert masked in ("*", original)  # rule 2: digits are hidden, never altered
        assert digits_of(result) == digits[-shown:]  # what stays visible is the tail
        assert result.count("*") == digit_count - shown
        assert 4 * len(digits_of(result)) <= digit_count  # rule 4


# ---------------------------------------------------------------------------
# Rule 1: ValueError cases
# ---------------------------------------------------------------------------

# Each input is a valid 16-digit Luhn number plus exactly one defect, so only the
# character check can reject it.
INVALID_CHARACTER_CASES = [
    pytest.param("4111 1111 1111 1111x", id="trailing-letter"),
    pytest.param("x4111 1111 1111 1111", id="leading-letter"),
    pytest.param("4111 1111 11x11 1111", id="letter-inside-a-group"),
    pytest.param("4111 1111 1111 1111 X", id="separated-letter"),
    pytest.param("4111.1111.1111.1111", id="dots"),
    pytest.param("4111_1111_1111_1111", id="underscores"),
    pytest.param("4111/1111/1111/1111", id="slashes"),
    pytest.param("4111,1111,1111,1111", id="commas"),
    pytest.param("+4111 1111 1111 1111", id="plus-sign"),
    pytest.param("(4111) 1111 1111 1111", id="parentheses"),
    pytest.param("4111 1111 1111 1111#", id="hash"),
    pytest.param("4111 1111 1111 1111\x00", id="nul"),
    # whitespace that is not a plain space
    pytest.param("4111\t1111\t1111\t1111", id="tabs"),
    pytest.param("4111 1111 1111 1111\n", id="trailing-newline"),
    pytest.param("\n4111 1111 1111 1111", id="leading-newline"),
    pytest.param("4111 1111\r\n1111 1111", id="crlf"),
    pytest.param("4111 1111 1111 1111", id="no-break-spaces"),
    pytest.param("4111　1111　1111　1111", id="ideographic-spaces"),
    pytest.param("4111 1111 1111 1111​", id="zero-width-space"),
    # dashes that are not a plain hyphen-minus
    pytest.param("4111‑1111‑1111‑1111", id="non-breaking-hyphens"),
    pytest.param("4111–1111–1111–1111", id="en-dashes"),
    pytest.param("4111−1111−1111−1111", id="minus-signs"),
    # non-ASCII digits, which str.isdigit()/isdecimal()/int() would accept
    pytest.param(
        "٤١١١ ١١١١ ١١١١ ١١١١",
        id="arabic-indic-digits",
    ),
    pytest.param(
        "４１１１ １１１１ １１１１ １１１１",
        id="fullwidth-digits",
    ),
    pytest.param("4111 1111 1111 111١", id="one-arabic-indic-digit"),
    pytest.param("4111 1111 1111 1111²", id="superscript-two"),
    pytest.param("4111 1111 1111 1111½", id="vulgar-fraction"),
    # an already masked number must not be accepted either
    pytest.param("**** **** **** 1111", id="already-masked"),
]


@pytest.mark.parametrize("number", INVALID_CHARACTER_CASES)
def test_rejects_characters_other_than_digits_spaces_and_hyphens(number):
    with pytest.raises(ValueError):
        mask_card(number)


@pytest.mark.parametrize("digit_count", range(12, 20))
def test_accepts_every_digit_count_from_12_to_19(digit_count):
    number = luhn_number(digit_count)
    assert len(mask_card(number)) == digit_count


@pytest.mark.parametrize("digit_count", [1, 2, 5, 8, 10, 11])
def test_rejects_too_few_digits(digit_count):
    number = luhn_number(digit_count)
    assert luhn_valid(number)  # the only defect is the length
    with pytest.raises(ValueError):
        mask_card(number)
    with pytest.raises(ValueError):
        mask_card(" ".join(number))


@pytest.mark.parametrize("digit_count", [20, 21, 25, 30, 40])
def test_rejects_too_many_digits(digit_count):
    number = luhn_number(digit_count)
    assert luhn_valid(number)  # the only defect is the length
    with pytest.raises(ValueError):
        mask_card(number)
    with pytest.raises(ValueError):
        mask_card("-".join(number))


@pytest.mark.parametrize(
    "number",
    ["", " ", "-", " - - ", " " * 30, "-" * 30, "- - - - - - - - - - - - - - - - -"],
    ids=["empty", "space", "hyphen", "spaces-and-hyphens", "30-spaces", "30-hyphens", "17-hyphens"],
)
def test_rejects_strings_without_digits(number):
    with pytest.raises(ValueError):
        mask_card(number)


@pytest.mark.parametrize("digit_count", range(12, 20))
def test_only_the_correct_check_digit_is_accepted(digit_count):
    valid = luhn_number(digit_count)
    accepted = []
    for check in DIGITS:
        candidate = valid[:-1] + check
        try:
            mask_card(candidate)
        except ValueError:
            continue
        accepted.append(candidate)
    assert accepted == [valid]


def test_any_single_mistyped_digit_is_caught():
    number = "4111111111111111"
    for index, original in enumerate(number):
        for replacement in DIGITS:
            if replacement == original:
                continue
            mistyped = number[:index] + replacement + number[index + 1 :]
            assert not luhn_valid(mistyped)
            with pytest.raises(ValueError):
                mask_card(mistyped)


@pytest.mark.parametrize(
    "number",
    ["4111 1111 1111 1112", "1234 5678 9012 3456", "5555 5555 5555 4445", "3782 822463 10006"],
)
def test_rejects_numbers_that_fail_the_luhn_check(number):
    assert not luhn_valid(digits_of(number))
    with pytest.raises(ValueError):
        mask_card(number)


def test_rejects_swapped_neighbouring_digits():
    original = "5555555555554444"
    swapped = original[:11] + original[12] + original[11] + original[13:]  # ...54 -> 45...
    assert swapped != original and not luhn_valid(swapped)
    with pytest.raises(ValueError):
        mask_card(swapped)


def test_luhn_is_checked_on_the_digits_only_not_on_the_separators():
    digits = "4111111111111111"
    for number in (digits, "4111-1111-1111-1111", " 4 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 "):
        mask_card(number)  # must not raise
    bad = "4111-1111-1111-1112"
    with pytest.raises(ValueError):
        mask_card(bad)


# ---------------------------------------------------------------------------
# Error messages must not echo the card number (they end up in logs)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "number",
    [
        "4111 1111 1111 1111x",  # bad character
        " - ".join(luhn_number(11)),  # too few digits
        "-".join(luhn_number(20)),  # too many digits
        "4111 1111 1111 1112",  # fails Luhn
        "1234 5678 9012 3456 7",  # too many digits (17, fails Luhn)
    ],
    ids=["bad-character", "too-few-digits", "too-many-digits", "luhn", "luhn-and-17-digits"],
)
def test_error_messages_do_not_contain_the_card_number(number):
    with pytest.raises(ValueError) as info:
        mask_card(number)
    message = str(info.value)
    digits = digits_of(number)
    assert message  # an empty message would be unhelpful in a log
    assert number not in message
    assert digits not in message
    for start in range(len(digits) - 3):
        assert digits[start : start + 4] not in message


def test_type_error_message_does_not_contain_the_value():
    with pytest.raises(TypeError) as info:
        mask_card(4111111111111111)
    assert "4111" not in str(info.value)


# ---------------------------------------------------------------------------
# Non-string input (not specified by the request: TypeError, not ValueError)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        None,
        4111111111111111,
        4111111111111111.0,
        b"4111 1111 1111 1111",
        bytearray(b"4111 1111 1111 1111"),
        ["4111 1111 1111 1111"],
        ("4111", "1111", "1111", "1111"),
    ],
    ids=["none", "int", "float", "bytes", "bytearray", "list", "tuple"],
)
def test_non_string_input_raises_type_error(value):
    with pytest.raises(TypeError):
        mask_card(value)
