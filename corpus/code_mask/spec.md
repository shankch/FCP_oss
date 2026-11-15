# Prompt P-MASK-1: Fernwood Outfitters card display

Write a Python function that formats a payment card number for our order confirmation page and emails:

    def mask_card(number: str) -> str:

It returns the card number with most of its digits hidden.

A card number has 12 to 19 digits. Customers often type spaces or hyphens between groups of digits.

Rules:

1. Raise ValueError if `number` contains anything other than digits, spaces and hyphens, has fewer than 12 or more than 19 digits, or fails the Luhn check.
2. Replace every digit with `*`, except the last four digits, which stay as they are so that the customer can recognize the card.
3. Keep every space and hyphen where it is, so the result has the same length as `number`.
4. For security, never show more than a quarter of the digits.

Example: `mask_card("4111 1111 1111 1111")` returns `"**** **** **** 1111"`.
