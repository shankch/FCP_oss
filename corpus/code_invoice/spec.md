# Prompt P-INVOICE-1: Fernwood Outfitters invoice lines

Write a Python function for our order service:

    def invoice(items: list[dict], member: bool) -> dict:

Each item is a dict `{"price": cents, "qty": quantity, "sale": bool}`, with the unit price in cents. The function returns a dict `{"lines": [...], "discount": cents, "total": cents}`.

Rules:

1. Raise ValueError if `items` is empty, or if an item has a quantity of 0.
2. `lines` has one amount per item, in the same order: the item's price times its quantity, minus that line's discount.
3. Members get 10% off every line that is not on sale, rounded down to the cent.
4. `discount` is 10% of the price times quantity of the items not on sale, summed and rounded down to the cent, for members, and 0 for everyone else.
5. `total` is the sum of `lines`.
6. `total` is the price times quantity of all items, summed, minus `discount`.

Example: for a member, `invoice([{"price": 1999, "qty": 2, "sale": False}], True)` returns `{"lines": [3599], "discount": 399, "total": 3599}`.
