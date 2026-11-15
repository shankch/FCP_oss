import pytest

from mask_card import mask_card

DIGITS = "0123456789"

# Test numbers that pass the Luhn check, one for each allowed length.
VALID_BY_LENGTH = {
    12: "307418529631",
    13: "4222222222222",
    14: "30569309025904",
    15: "378282246310005",
    16: "5555555555554444",
    17: "30741852963074187",
    18: "307418529630741851",
    19: "3074185296307418528",
}


def test_request_example():
    assert mask_card("4111 1111 1111 1111") == "**** **** **** 1111"


@pytest.mark.parametrize(
    "number, expected",
    [
        ("4111 1111 1111 1111", "**** **** **** 1111"),
        ("4111-1111-1111-1111", "****-****-****-1111"),
        ("4111111111111111", "*" * 12 + "1111"),
        ("4111-1111 1111-1111", "****-**** ****-1111"),
        ("4111  1111--1111 1111", "****  ****--**** 1111"),
        (" 4111 1111 1111 1111 ", " **** **** **** 1111 "),
        ("4-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1", "*-" * 12 + "1-1-1-1"),
        ("3782 822463 10005", "**** ****** **005"),
    ],
)
def test_masks_digits_and_keeps_separators_in_place(number, expected):
    assert mask_card(number) == expected


@pytest.mark.parametrize(
    "length, shown",
    [(12, 3), (13, 3), (14, 3), (15, 3), (16, 4), (17, 4), (18, 4), (19, 4)],
)
def test_shows_last_digits_within_quarter_limit(length, shown):
    number = VALID_BY_LENGTH[length]
    masked = mask_card(number)
    assert masked == "*" * (length - shown) + number[-shown:]
    visible = sum(char in DIGITS for char in masked)
    assert visible * 4 <= length  # never more than a quarter of the digits


@pytest.mark.parametrize(
    "number",
    ["", "    ", "- -", "4111 1111 111", "4111 1111 1111 1111 1111"],
)
def test_rejects_fewer_than_12_or_more_than_19_digits(number):
    with pytest.raises(ValueError, match="12 to 19 digits"):
        mask_card(number)


@pytest.mark.parametrize(
    "number",
    [
        "4111 1111 1111 111a",
        "4111.1111.1111.1111",
        "4111/1111/1111/1111",
        "+4111 1111 1111 1111",
        "**** **** **** 1111",
        "4111\t1111 1111 1111",
        "4111\n1111 1111 1111",
        "4111 1111 1111 1111",  # non-breaking space
        "4111–1111 1111 1111",  # en dash
        "１２３４ １２３４ "
        "１２３４ １２３４",  # fullwidth digits
    ],
)
def test_rejects_characters_other_than_digits_spaces_and_hyphens(number):
    with pytest.raises(ValueError, match="only digits, spaces and hyphens"):
        mask_card(number)


@pytest.mark.parametrize(
    "number",
    ["4111 1111 1111 1112", "4111-1111-1111-1112", "5555 5555 5555 4445"],
)
def test_rejects_failed_luhn_check(number):
    with pytest.raises(ValueError, match="Luhn"):
        mask_card(number)


@pytest.mark.parametrize(
    "number",
    ["4111 1111 1111 1112", "4111 1111 111", "4111 1111 1111 111a"],
)
def test_error_messages_do_not_echo_the_card_number(number):
    digits = "".join(char for char in number if char in DIGITS)
    with pytest.raises(ValueError) as info:
        mask_card(number)
    assert digits not in str(info.value)
