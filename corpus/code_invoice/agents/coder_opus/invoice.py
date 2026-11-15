"""Invoice lines for the Fernwood Outfitters order service.

All amounts are integer cents. Member discounts are computed with integer
arithmetic so there is no floating-point rounding.

Note on rounding: the request rounds the member discount down per line
(rule 3) but also defines ``discount`` as 10% of the summed non-sale amounts,
rounded down once (rule 4). With several discounted lines those differ: two
non-sale lines of 15 cents give per-line discounts 1 + 1 = 2, while
floor(10% of 30) = 3. Rules 5 and 6 then cannot both hold. This
implementation rounds per line, as rule 3 says, and reports ``discount`` as
the sum of the per-line discounts, so that
``total == sum(lines) == gross - discount`` always holds. It agrees with
rule 4 whenever at most one line is discounted (as in the request's example).
"""


def _check_item(index: int, item) -> tuple[int, int, bool]:
    if not isinstance(item, dict):
        raise ValueError(f"item {index} must be a dict, got {type(item).__name__}")
    for key in ("price", "qty", "sale"):
        if key not in item:
            raise ValueError(f"item {index} is missing {key!r}")
    price, qty, sale = item["price"], item["qty"], item["sale"]
    if not isinstance(price, int) or isinstance(price, bool):
        raise ValueError(f"item {index}: price must be an integer number of cents")
    if not isinstance(qty, int) or isinstance(qty, bool):
        raise ValueError(f"item {index}: qty must be an integer")
    if not isinstance(sale, bool):
        raise ValueError(f"item {index}: sale must be a bool")
    if qty == 0:
        raise ValueError(f"item {index} has a quantity of 0")
    if qty < 0:
        raise ValueError(f"item {index} has a negative quantity")
    if price < 0:
        raise ValueError(f"item {index} has a negative price")
    return price, qty, sale


def invoice(items: list[dict], member: bool) -> dict:
    """Return ``{"lines": [...], "discount": cents, "total": cents}``.

    Each line is ``price * qty`` minus that line's discount. Members get
    10% off every line not on sale, rounded down to the cent; non-members
    get no discount. ``discount`` is the sum of the line discounts and
    ``total`` is the sum of the lines.

    Raises ValueError if ``items`` is empty or an item is malformed
    (missing key, wrong type, quantity of 0 or below, negative price).
    """
    if not isinstance(member, bool):
        raise ValueError("member must be a bool")
    if not items:
        raise ValueError("items is empty")

    lines = []
    discount = 0
    for index, item in enumerate(items):
        price, qty, sale = _check_item(index, item)
        amount = price * qty
        line_discount = amount // 10 if member and not sale else 0
        lines.append(amount - line_discount)
        discount += line_discount

    return {"lines": lines, "discount": discount, "total": sum(lines)}
