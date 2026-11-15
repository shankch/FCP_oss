"""Mask payment card numbers for the order confirmation page and e-mails.

Request P-MASK-1 (Fernwood Outfitters).  The only public name is `mask_card`.
"""

from __future__ import annotations

from collections.abc import Sequence

__all__ = ["mask_card"]

# Only these characters are accepted.  This is deliberately narrower than
# str.isdigit() / str.isspace(): Arabic-Indic or full-width digits, tabs,
# newlines, no-break spaces and Unicode dashes are all rejected.
_DIGITS = frozenset("0123456789")
_SEPARATORS = frozenset(" -")  # U+0020 SPACE and U+002D HYPHEN-MINUS

_MIN_DIGITS = 12
_MAX_DIGITS = 19

_SHOWN_DIGITS = 4  # rule 2: the last four digits stay visible ...
_SHOWN_FRACTION = 4  # rule 4: ... but never more than 1/4 of all the digits


def _shown_digit_count(digit_count: int) -> int:
    """How many trailing digits may stay visible for a card with `digit_count` digits.

    Rule 2 asks for four.  Rule 4 forbids showing more than a quarter of the digits,
    i.e. at most digit_count // 4 of them (digit counts are whole numbers).  The two
    rules agree for 16 to 19 digits (4 shown) but conflict for 12 to 15 digits, where
    a quarter is only 3.  Rule 4 is the security rule ("never") so it wins there:
    12-15 digits show 3, 16-19 digits show 4.
    """
    return min(_SHOWN_DIGITS, digit_count // _SHOWN_FRACTION)


def _passes_luhn(digits: Sequence[int]) -> bool:
    """Standard Luhn (mod 10) check over a sequence of decimal digits."""
    total = 0
    for position, digit in enumerate(reversed(digits)):
        if position % 2 == 1:  # every second digit, starting next to the check digit
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def mask_card(number: str) -> str:
    """Return `number` with every digit but the last few replaced by ``*``.

    Spaces and hyphens are kept exactly where they are (leading, trailing and
    repeated ones included), so the result has the same length as `number`.

    The last four digits stay visible, except that no more than a quarter of the
    digits may ever be visible: cards with 12 to 15 digits therefore show only
    their last three digits, cards with 16 to 19 digits show their last four.
    "Last digits" means the last digit characters; trailing spaces or hyphens do
    not count.

    Raises:
        ValueError: if `number` contains anything other than the ASCII digits
            0-9, spaces and hyphens, has fewer than 12 or more than 19 digits,
            or fails the Luhn check.  The message never contains the number.
        TypeError: if `number` is not a `str` (a caller bug, not bad input).
    """
    if not isinstance(number, str):
        raise TypeError(f"card number must be a str, not {type(number).__name__}")

    if any(char not in _DIGITS and char not in _SEPARATORS for char in number):
        raise ValueError("card number may contain only digits, spaces and hyphens")

    digits = [int(char) for char in number if char in _DIGITS]
    digit_count = len(digits)
    if not _MIN_DIGITS <= digit_count <= _MAX_DIGITS:
        raise ValueError(
            f"card number must have {_MIN_DIGITS} to {_MAX_DIGITS} digits, "
            f"got {digit_count}"
        )

    if not _passes_luhn(digits):
        raise ValueError("card number fails the Luhn check")

    first_shown = digit_count - _shown_digit_count(digit_count)  # index among the digits
    masked = []
    digit_index = 0
    for char in number:
        if char in _DIGITS:
            masked.append(char if digit_index >= first_shown else "*")
            digit_index += 1
        else:
            masked.append(char)
    return "".join(masked)
