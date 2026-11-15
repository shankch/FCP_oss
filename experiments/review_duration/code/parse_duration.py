"""Parse short duration strings such as "1h30m" or "45s" into seconds."""

import re

__all__ = ["parse_duration"]

# Limits from the request: every number is 1..99, a duration is at most a day.
_MIN_NUMBER = 1
_MAX_NUMBER = 99
_MAX_SECONDS = 24 * 60 * 60

# Each part is its own optional group, written in the only order allowed, so a
# unit can be left out but can neither repeat nor come out of order. Notes:
#   * It is used with fullmatch(). A "$" anchor would let a trailing "\n"
#     through, and match() would let any trailing text through.
#   * [0-9] rather than \d, because \d also matches digits of other scripts.
#   * No re.IGNORECASE: the units are the lowercase letters h, m and s.
#   * A number is at most two digits, which also keeps int() on bounded input.
_PARTS = re.compile(r"(?:([0-9]{1,2})h)?(?:([0-9]{1,2})m)?(?:([0-9]{1,2})s)?")

# Name and size in seconds of the unit behind each group of _PARTS.
_UNITS = (("hours", 3600), ("minutes", 60), ("seconds", 1))


def _invalid(text: str, reason: str) -> ValueError:
    return ValueError(f"invalid duration {text!r}: {reason}")


def parse_duration(text: str) -> int:
    """Convert a duration such as "1h30m" or "45s" into a number of seconds.

    A duration is one to three parts written in the order hours, minutes,
    seconds. Each part is a number followed by its unit letter (h, m or s),
    each unit appears at most once, and there are no spaces: "1h", "5m20s",
    "1h30m15s". Every number is between 1 and 99 and the whole duration is at
    most one day (86400 seconds). Anything else, including the empty string,
    raises ValueError.

    Where the request leaves room, these are the choices made:

    * Bounds are inclusive. "1s" and "99s" are valid, "0s" and "100s" are not.
      "24h" is exactly one day and valid, "24h1s" is longer and is not.
    * The one-day limit is on the total. It overrides the 1..99 range, which on
      its own would allow "25h" or "99h"; those raise ValueError (they are not
      clamped to a day).
    * Minutes and seconds are not capped at 59: "90m" is 5400 seconds.
    * A number is one or two ASCII digits. "05m" is 5 minutes, but "00m" is 0
      (out of range) and "005m" has too many digits. Signs, decimal points,
      underscores and digits of other scripts are rejected.
    * Units are lowercase only ("1H" is rejected).
    * Whitespace of any kind, anywhere, is rejected, not only the space
      character. That includes a trailing newline.
    * An argument that is not a str also raises ValueError (not TypeError), so
      callers have a single exception to handle.

    >>> parse_duration("1h30m")
    5400
    >>> parse_duration("45s")
    45
    """
    if not isinstance(text, str):
        raise ValueError(f"duration must be a str, not {type(text).__name__}")

    match = _PARTS.fullmatch(text)
    if match is None:
        raise _invalid(
            text,
            "expected parts like '1h', '30m', '45s' with numbers from 1 to 99, "
            "each unit at most once, in the order h, m, s, with no spaces",
        )
    numbers = match.groups()
    if all(digits is None for digits in numbers):
        raise _invalid(text, "at least one part is required")  # only "" gets here

    total = 0
    for digits, (name, unit_seconds) in zip(numbers, _UNITS):
        if digits is None:
            continue
        number = int(digits)
        if not _MIN_NUMBER <= number <= _MAX_NUMBER:
            raise _invalid(
                text,
                f"{name} must be between {_MIN_NUMBER} and {_MAX_NUMBER}, "
                f"got {number}",
            )
        total += number * unit_seconds

    if total > _MAX_SECONDS:
        raise _invalid(
            text,
            f"{total} seconds is longer than one day ({_MAX_SECONDS} seconds)",
        )
    return total
