"""Invoice lines for Fernwood Outfitters (request P-INVOICE-1).

All money is integer cents. Nothing here uses floating point, so "10% rounded
down to the cent" is exact integer floor division by 10.
"""

from __future__ import annotations

MEMBER_DISCOUNT_DIVISOR = 10  # 10% == 1/10


def _read_item(item: dict, index: int) -> tuple[int, int, bool]:
    """Validate one item and return (price, qty, sale)."""
    try:
        price = item["price"]
        qty = item["qty"]
        sale = item["sale"]
    except KeyError as missing:
        raise ValueError(f"item {index} is missing key {missing}") from None
    except TypeError:
        raise ValueError(f"item {index} is not a dict") from None

    # bool is a subclass of int; True as a price or quantity is a bug, not a number.
    for name, value in (("price", price), ("qty", qty)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"item {index}: {name} must be an integer, got {value!r}")

    if qty == 0:
        raise ValueError(f"item {index}: quantity must not be 0")
    if qty < 0:
        raise ValueError(f"item {index}: quantity must not be negative, got {qty}")
    if price < 0:
        raise ValueError(f"item {index}: price must not be negative, got {price}")

    return price, qty, bool(sale)


def invoice(items: list[dict], member: bool) -> dict:
    """Price an order.

    Each item is ``{"price": cents, "qty": quantity, "sale": bool}``. Returns
    ``{"lines": [...], "discount": cents, "total": cents}``.

    Members get 10% off every line that is not on sale. The discount is worked
    out per line (price * qty, then 10% rounded down to the cent), and
    ``discount`` is the sum of those line discounts. That keeps the invoice
    consistent: ``total == sum(lines) == sum(price * qty) - discount``.

    Raises ValueError if ``items`` is empty, if any item has a quantity of 0,
    or if an item is malformed (missing key, non-integer or negative price or
    quantity).
    """
    items = list(items)
    if not items:
        raise ValueError("items must not be empty")

    lines: list[int] = []
    discount = 0
    for index, item in enumerate(items):
        price, qty, sale = _read_item(item, index)
        gross = price * qty
        line_discount = gross // MEMBER_DISCOUNT_DIVISOR if member and not sale else 0
        discount += line_discount
        lines.append(gross - line_discount)

    return {"lines": lines, "discount": discount, "total": sum(lines)}
