"""Tests for parse_duration, organised by the numbered rules in request.md.

Where the request is silent, the tests pin down the choices documented in the
docstring of parse_duration: inclusive bounds, "24h" allowed, "05m" allowed,
"005m" rejected, lowercase units only, every kind of whitespace rejected, and
ValueError (not TypeError) for input that is not a str.
"""

import itertools

import pytest

from parse_duration import parse_duration

ONE_DAY = 24 * 60 * 60  # 86400 seconds


def parse_or_none(text):
    """Seconds for a valid duration, None where parse_duration raises ValueError."""
    try:
        return parse_duration(text)
    except ValueError:
        return None


def assert_rejected(text):
    with pytest.raises(ValueError):
        parse_duration(text)


# --- valid durations ---------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "seconds"),
    [
        # the examples in the request
        ("1h30m", 5400),
        ("45s", 45),
        # rule 1: one or more parts, each a number followed by a unit
        ("1h", 3600),
        ("1m", 60),
        ("1s", 1),
        ("2h", 7200),
        ("10m", 600),
        ("5m20s", 320),
        ("1h30m15s", 5415),
        ("10h20m30s", 37230),
        # rule 2: a unit may be left out, it just may not repeat
        ("2h5s", 7205),
        ("1h1m1s", 3661),
        # rule 3: both ends of 1..99 are valid, and minutes and seconds are not
        # capped at 59
        ("99s", 99),
        ("99m", 5940),
        ("90m", 5400),
        ("1h90m", 9000),
        ("99m99s", 6039),
        # rule 6: anything up to and including exactly one day
        ("23h59m59s", 86399),
        ("22h99m99s", 85239),
        ("24h", 86400),
        ("23h60m", 86400),
        ("23h59m60s", 86400),
        # a leading zero is only a one digit number written with two digits
        ("05m", 300),
        ("09s", 9),
        ("01h05m09s", 3909),
    ],
)
def test_valid_duration(text, seconds):
    assert parse_duration(text) == seconds


def test_result_is_a_plain_int():
    assert type(parse_duration("1h30m")) is int


def test_every_combination_of_boundary_numbers():
    # None means the unit is left out. Every number here is itself valid, so the
    # only reasons to reject are "no parts at all" and "longer than one day".
    numbers = (None, 1, 2, 9, 10, 23, 24, 25, 59, 60, 61, 98, 99)
    wrong = []
    for h, m, s in itertools.product(numbers, repeat=3):
        parts = [(h, "h"), (m, "m"), (s, "s")]
        text = "".join(f"{n}{unit}" for n, unit in parts if n is not None)
        total = 3600 * (h or 0) + 60 * (m or 0) + (s or 0)
        expected = total if text and total <= ONE_DAY else None
        if parse_or_none(text) != expected:
            wrong.append((text, expected))
    assert wrong == []


# --- rule 5: empty string ----------------------------------------------------


def test_empty_string_is_rejected():
    assert_rejected("")


# --- rule 3: every number is between 1 and 99 --------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "0s", "0m", "0h", "00s", "00m", "00h",
        "1h0m", "0h30m", "1h30m0s",
        "100s", "100m", "100h", "999s", "1h100m",
        "1440m", "86400s",  # a day's worth, but not as a number between 1 and 99
    ],
)  # fmt: skip
def test_number_outside_1_to_99_is_rejected(text):
    assert_rejected(text)


@pytest.mark.parametrize("text", ["005s", "001m", "0001h", "0099s"])
def test_zero_padding_beyond_two_digits_is_rejected(text):
    assert_rejected(text)


# --- rule 2: each unit at most once, in the order h, m, s --------------------


@pytest.mark.parametrize(
    "text",
    [
        # out of order
        "30m1h", "15s30m", "15s1h", "1s1m1h", "1m1h30s", "1h15s30m",
        # repeated
        "1h1h", "1m2m", "1s2s", "1h30m1h", "1h30m30m", "1h30m15s15s", "1h1m1s1s",
    ],
)  # fmt: skip
def test_repeated_or_misordered_units_are_rejected(text):
    assert_rejected(text)


# --- rule 4: spaces are not allowed ------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        " ", "\n", "\t",
        " 1h", "1h ", " 1h ", "1h 30m", "1 h", "1h30m ", "1h  30m",
        "\t1h", "1h\t", "\n1h", "1h\n", "1h30m\n", "1h\r\n", "1h\n30m",
        "\x0b1h", "1h\x0c", " 1h", "1h 30m",
    ],
)  # fmt: skip
def test_whitespace_is_rejected(text):
    assert_rejected(text)


# --- rule 1: whole number + unit, nothing else -------------------------------


@pytest.mark.parametrize(
    "text",
    [
        # no number, no unit, or neither
        "1", "45", "h", "m", "s", "hms", "hm", "1hm", "h1", "1h30", "1h30m15",
        "1hh", "1h1", "x", "abc",
        # other units and spellings
        "1d", "1w", "1ms", "1hr", "1min", "1sec", "PT1H30M", "P1D",
        # separators and punctuation
        "1h30m!", "1h,30m", "1h:30m", "1:30", "1h-30m", "1h+30m", "1h/30m",
        "1h30m15s.",
        # not whole numbers, or not written as plain digits
        "-1h", "+1h", "-1s", "1.5h", "0.5s", ".5s", "1,5h",
        "1e1s", "1_0s", "0x1s",
    ],
)  # fmt: skip
def test_malformed_duration_is_rejected(text):
    assert_rejected(text)


@pytest.mark.parametrize("text", ["1H", "1M", "1S", "1H30M", "1h30M", "1H30m"])
def test_units_must_be_lowercase(text):
    assert_rejected(text)


@pytest.mark.parametrize(
    "text",
    [
        "１h",  # fullwidth digit one
        "٣s",  # Arabic-Indic digit three
        "²s",  # superscript two
        "१s",  # Devanagari digit one
        "1ｈ",  # fullwidth h
        "1ſ",  # long s
    ],
)
def test_only_ascii_digits_and_letters_are_accepted(text):
    assert_rejected(text)


@pytest.mark.parametrize("text", ["\x00", "1h\x0030m", "1h30m\x00"])
def test_nul_character_is_rejected(text):
    assert_rejected(text)


# --- rule 6: a duration is never longer than one day -------------------------


@pytest.mark.parametrize(
    "text",
    [
        "24h1s", "24h1m", "24h1m1s", "24h99s",
        "25h", "30h", "99h", "99h99m99s",
        "23h60m1s", "23h61m", "23h99m", "23h59m61s",
    ],
)  # fmt: skip
def test_longer_than_one_day_is_rejected(text):
    assert_rejected(text)


# --- rule 5: anything else is a ValueError, even if it is not a string -------


@pytest.mark.parametrize(
    "value",
    [None, 0, 90, 5400, 1.5, True, b"1h", bytearray(b"1h"), ["1h"], ("1h",), object()],
)
def test_input_that_is_not_a_str_raises_value_error(value):
    assert_rejected(value)


# --- cross-check against an independently written parser ---------------------


def reference_parse(text):
    """Naive left-to-right parser (no regex) used as an oracle.

    Returns the number of seconds, or None if the text is not a valid duration.
    """
    digits_chars = "0123456789"
    pos = 0
    total = 0
    last_rank = -1  # rank in "hms" of the previous part
    while pos < len(text):
        end = pos
        while end < len(text) and text[end] in digits_chars:
            end += 1
        digits = text[pos:end]
        if not 1 <= len(digits) <= 2 or end == len(text):
            return None
        unit = text[end]
        if unit not in "hms":
            return None
        rank = "hms".index(unit)
        if rank <= last_rank:
            return None
        number = int(digits)
        if not 1 <= number <= 99:
            return None
        total += number * (3600, 60, 1)[rank]
        last_rank = rank
        pos = end + 1
    if last_rank == -1 or total > ONE_DAY:
        return None
    return total


def test_agrees_with_reference_parser_on_every_short_string():
    mismatches = []
    for length in range(7):
        for chars in itertools.product("0124hms", repeat=length):
            text = "".join(chars)
            if parse_or_none(text) != reference_parse(text):
                mismatches.append(text)
    assert mismatches[:10] == []
