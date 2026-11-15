"""Card-number masking for Fernwood Outfitters order confirmations and emails."""

from __future__ import annotations

__all__ = ["mask_card"]

_DIGITS = frozenset("0123456789")  # ASCII digits only
_SEPARATORS = frozenset(" -")  # ASCII space and ASCII hyphen-minus only

_MIN_DIGITS = 12
_MAX_DIGITS = 19
_LAST_DIGITS_SHOWN = 4
_MASK = "*"


def mask_card(number: str) -> str:
    """Return ``number`` with all but its last few digits replaced by ``*``.

    ``number`` may contain ASCII digits, spaces and hyphens in any
    arrangement. Every space and hyphen stays where it is and each hidden
    digit becomes exactly one ``*``, so the result has the same length as
    ``number``.

    The last four digits stay visible, but never more than a quarter of the
    digits: cards with 16 to 19 digits show their last four digits, cards
    with 12 to 15 digits show only their last three.

    >>> mask_card("4111 1111 1111 1111")
    '**** **** **** 1111'
    >>> mask_card("3782-822463-10005")
    '****-******-**005'

    Raises:
        TypeError: if ``number`` is not a ``str``.
        ValueError: if ``number`` contains a character other than an ASCII
            digit, space or hyphen; has fewer than 12 or more than 19 digits;
            or fails the Luhn check. The message never repeats card digits.
    """
    if not isinstance(number, str):
        raise TypeError(f"card number must be a str, not {type(number).__name__}")

    digits = []
    for position, char in enumerate(number):
        if char in _DIGITS:
            digits.append(int(char))
        elif char not in _SEPARATORS:
            # Name the position only: error messages end up in logs, so they
            # must not repeat any part of the card number.
            raise ValueError(
                "card number may contain only digits, spaces and hyphens "
                f"(invalid character at position {position})"
            )

    if not _MIN_DIGITS <= len(digits) <= _MAX_DIGITS:
        raise ValueError(
            f"card number must have {_MIN_DIGITS} to {_MAX_DIGITS} digits, "
            f"got {len(digits)}"
        )

    if not _passes_luhn(digits):
        raise ValueError("card number fails the Luhn check")

    # Showing the last four digits would reveal more than a quarter of a
    # 12- to 15-digit card; the quarter limit is a security rule, so it wins.
    shown = min(_LAST_DIGITS_SHOWN, len(digits) // 4)
    first_shown = len(digits) - shown  # counted in digits, not characters

    masked = []
    digit_index = 0
    for char in number:
        if char in _SEPARATORS:
            masked.append(char)
        else:
            masked.append(char if digit_index >= first_shown else _MASK)
            digit_index += 1
    return "".join(masked)


def _passes_luhn(digits: list[int]) -> bool:
    """Return True if ``digits`` (most significant first) pass the Luhn check."""
    total = 0
    for offset, digit in enumerate(reversed(digits)):
        if offset % 2 == 1:  # every second digit, counting left from the check digit
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0
