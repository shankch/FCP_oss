"""Payment retry for Fernwood Outfitters orders (request P-PAY-1)."""

MIN_AMOUNT = 1          # cents
MAX_AMOUNT = 1_000_000  # cents
# Seconds to wait before each retry: 2 before the 2nd attempt, 4 before the 3rd.
# The first attempt plus one retry per entry gives 3 attempts in total.
RETRY_WAITS = (2, 4)


def charge_order(api, order_id: int, amount: int) -> bool:
    """Charge ``amount`` cents for order ``order_id``; return True if it went through.

    ``api.charge(order_id, amount)`` returns "ok", "declined" or "error";
    ``api.sleep(seconds)`` waits that many seconds.

    * "ok" is final: True is returned and the order is never charged again.
    * "declined" is final: False is returned and the card is never retried.
    * "error" is retried, waiting 2 s before the 2nd attempt and 4 s before the
      3rd, for at most 3 attempts in total. If the 3rd attempt also returns
      "error", False is returned with no further wait.
    * Any other status is not one the service is documented to return; it is
      treated as final (not retried, since the order might already have been
      charged) and False is returned.

    "Keep trying until the charge goes through" is honoured within the
    3-attempt limit: an "error" is never given up on before the 3rd attempt,
    but the limit and the no-retry-after-decline rule still apply. A False
    result means the order is not known to be paid; the caller must keep the
    order (e.g. queue it for a later retry or manual follow-up) so it is not lost.

    Raises ValueError, before contacting the payment service, if ``amount`` is
    not a whole number of cents from 1 to 1,000,000 inclusive. Exceptions
    raised by ``api.charge`` or ``api.sleep`` propagate unchanged and are not
    retried.
    """
    if (
        not isinstance(amount, int)
        or isinstance(amount, bool)
        or not (MIN_AMOUNT <= amount <= MAX_AMOUNT)
    ):
        raise ValueError(
            f"amount must be a whole number of cents from {MIN_AMOUNT:,} "
            f"to {MAX_AMOUNT:,}, got {amount!r}"
        )

    status = api.charge(order_id, amount)
    for wait in RETRY_WAITS:
        # Only "error" is retried: after "ok" the order must never be charged
        # again, and a "declined" card (or an unrecognised status) is final.
        if status != "error":
            break
        api.sleep(wait)
        status = api.charge(order_id, amount)
    return status == "ok"
