"""Invoice lines and totals for Fernwood Outfitters orders.

All money is in integer cents. The 10% member discount is rounded down to the
cent with integer floor division, so no floating-point arithmetic is involved.
"""


def _require_int(value, field: str, index: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"item {index}: {field} must be an integer, got {value!r}")


def invoice(items: list[dict], member: bool) -> dict:
    """Return {"lines": [...], "discount": cents, "total": cents} for an order.

    Each item is {"price": unit price in cents, "qty": quantity, "sale": bool}.
    Members get 10% off each line that is not on sale, rounded down to the cent.
    The invoice discount is the sum of those line discounts, so the lines,
    discount and total always reconcile. Non-members and sale lines get no
    discount.

    Raises ValueError if items is empty, if an item has a quantity below 1, or
    if an item has a negative price. Raises TypeError if a price or quantity is
    not an integer.
    """
    items = list(items)
    if not items:
        raise ValueError("items must not be empty")

    lines = []
    discount = 0
    for index, item in enumerate(items):
        price = item["price"]
        qty = item["qty"]
        sale = item["sale"]
        _require_int(price, "price", index)
        _require_int(qty, "qty", index)
        if qty < 1:
            raise ValueError(f"item {index}: quantity must be at least 1, got {qty}")
        if price < 0:
            raise ValueError(f"item {index}: price must not be negative, got {price}")

        gross = price * qty
        line_discount = gross // 10 if member and not sale else 0
        discount += line_discount
        lines.append(gross - line_discount)

    return {"lines": lines, "discount": discount, "total": sum(lines)}
