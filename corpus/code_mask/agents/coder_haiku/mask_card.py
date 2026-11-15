"""Mask payment card numbers for order confirmation pages and emails."""

_DIGITS = frozenset("0123456789")
_SEPARATORS = frozenset(" -")
_MIN_DIGITS = 12
_MAX_DIGITS = 19
_MAX_SHOWN = 4


def _passes_luhn(digits: str) -> bool:
    total = 0
    for position, char in enumerate(reversed(digits)):
        value = int(char)
        if position % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def mask_card(number: str) -> str:
    """Return the card number with every digit hidden except the last few.

    The last four digits stay visible, but never more than a quarter of the
    digits, so a 12- to 15-digit number shows only its last three. Spaces and
    hyphens keep their positions, so the result is as long as the input.

    Raises ValueError if the input contains anything other than ASCII digits,
    spaces and hyphens, has fewer than 12 or more than 19 digits, or fails the
    Luhn check. Error messages never include the card number.
    """
    for char in number:
        if char not in _DIGITS and char not in _SEPARATORS:
            raise ValueError("card number may contain only digits, spaces and hyphens")

    digits = "".join(char for char in number if char in _DIGITS)
    if not _MIN_DIGITS <= len(digits) <= _MAX_DIGITS:
        raise ValueError("card number must have 12 to 19 digits")
    if not _passes_luhn(digits):
        raise ValueError("card number fails the Luhn check")

    shown = min(_MAX_SHOWN, len(digits) // 4)  # never more than a quarter
    first_shown = len(digits) - shown

    masked = []
    index = 0  # position of the current digit within `digits`
    for char in number:
        if char in _SEPARATORS:
            masked.append(char)
        else:
            masked.append(char if index >= first_shown else "*")
            index += 1
    return "".join(masked)
