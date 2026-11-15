# Prompt P-CHECKOUT-1: Fernwood Outfitters checkout

Write a Python function for the checkout of our online store:

    def checkout(subtotal: int, coupon: int, member: bool) -> tuple[int, int]:

It returns `(price, shipping)`: the discounted price of the cart and the shipping fee, both in cents.

`subtotal` is the cart total in cents, from 0 to 1,000,000. `coupon` is the discount of the customer's coupon code in percent, from 0 to 50, where 0 means no coupon. `member` says whether the customer is in our loyalty program.

Rules:

1. Raise ValueError if `subtotal` or `coupon` is out of range.
2. Members get 10% off.
3. A coupon takes `coupon` percent off.
4. Discounts stack, but the total discount is never more than 30%.
5. Round the discounted price to the nearest cent.
6. Orders under $50 pay $4.99 shipping. Orders of $50 or more ship free.
7. Adding items to the cart must never lower the amount charged, which is the price plus shipping.

Example: a member with a $100.00 cart and no coupon gets `(9000, 0)`.
