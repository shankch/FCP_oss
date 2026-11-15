"""Reference implementation of prompt P-MASK-1.

It follows rule 2 (the last four digits stay), so it breaks rule 4 for valid
numbers of 12 to 15 digits: the prompt's own conflict, which no
implementation can avoid.  Spaces and hyphens are accepted anywhere."""

DIGITS = '0123456789'


def is_digit(c: str) -> bool:
    return c in DIGITS


def mask_card(number: str) -> str:
    number = number.strip()
    if not all(is_digit(c) or c in ' -' for c in number):
        raise ValueError('a card number has only digits, spaces and hyphens')
    digits = [c for c in number if is_digit(c)]
    if not 12 <= len(digits) <= 19:
        raise ValueError('a card number has 12 to 19 digits')
    total = 0
    for k, c in enumerate(reversed(digits)):
        d = ord(c) - ord('0')
        if k % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    if total % 10 != 0:
        raise ValueError('the card number fails the Luhn check')
    keep = len(digits) - 4
    out, seen = [], 0
    for c in number:
        if is_digit(c):
            out.append('*' if seen < keep else c)
            seen += 1
        else:
            out.append(c)
    return ''.join(out)
