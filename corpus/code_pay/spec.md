# Prompt P-PAY-1: Fernwood Outfitters payment retry

Write a Python function that charges a customer's card for an order through our payment service, retrying when the service fails:

    def charge_order(api, order_id: int, amount: int) -> bool:

`api.charge(order_id, amount)` asks the payment service to charge `amount` cents for the order and returns `"ok"`, `"declined"` or `"error"`. `api.sleep(seconds)` waits that many seconds.

Rules:

1. Raise ValueError if `amount` is not between 1 and 1,000,000 cents.
2. Return True once a charge returns `"ok"`, and False otherwise.
3. If a charge returns `"error"`, try again, up to 3 attempts in total.
4. Never try again after `"declined"`.
5. Before each new attempt, wait: 2 seconds before the second attempt and 4 seconds before the third.
6. Never charge an order again once a charge has returned `"ok"`.
7. Keep trying until the charge goes through, so that no order is lost.

Example: if the first charge returns `"error"` and the second `"ok"`, the function calls `api.charge`, `api.sleep(2)` and `api.charge`, and returns True.
