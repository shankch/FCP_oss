"""Charge a customer's card for an order, retrying when the payment service errors."""

MIN_AMOUNT_CENTS = 1
MAX_AMOUNT_CENTS = 1_000_000
MAX_ATTEMPTS = 3
# Seconds to wait before attempt 2 and before attempt 3.
WAIT_BEFORE_ATTEMPT = {2: 2, 3: 4}


def charge_order(api, order_id: int, amount: int) -> bool:
    """Charge `amount` cents for `order_id`; return True once the service answers "ok".

    Only an "error" answer is retried, and at most MAX_ATTEMPTS charges are made.
    "declined" and any answer other than "ok" or "error" return False at once.
    The function returns as soon as a charge is "ok", so it never charges again
    after that. Exceptions raised by api.charge or api.sleep are not caught.

    Raises ValueError, before any API call, if amount is not an int number of
    cents between MIN_AMOUNT_CENTS and MAX_AMOUNT_CENTS (inclusive). bool and
    non-int values such as floats are rejected too.
    """
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise ValueError(f"amount must be a whole number of cents, got {amount!r}")
    if not MIN_AMOUNT_CENTS <= amount <= MAX_AMOUNT_CENTS:
        raise ValueError(
            f"amount must be between {MIN_AMOUNT_CENTS} and {MAX_AMOUNT_CENTS:,} cents, got {amount}"
        )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        if attempt > 1:
            api.sleep(WAIT_BEFORE_ATTEMPT[attempt])
        result = api.charge(order_id, amount)
        if result == "ok":
            return True
        if result != "error":
            # "declined", or an answer the request does not define: never retry.
            return False
    # Every attempt returned "error".
    return False
