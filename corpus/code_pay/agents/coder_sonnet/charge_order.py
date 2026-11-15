"""Charge a customer's card for an order through the payment service, retrying on errors.

Implements request P-PAY-1 (Fernwood Outfitters payment retry).
"""

from numbers import Integral

MIN_AMOUNT_CENTS = 1
MAX_AMOUNT_CENTS = 1_000_000

MAX_ATTEMPTS = 3
# Seconds to wait before the 2nd and before the 3rd attempt (rule 5).
RETRY_DELAYS_SECONDS = (2, 4)


def charge_order(api, order_id: int, amount: int) -> bool:
    """Charge ``amount`` cents to the card on ``order_id``; True if a charge returned "ok".

    - ``amount`` must be a whole number of cents from 1 to 1,000,000 inclusive. Anything else
      (out of range, float, str, None, bool) raises ValueError before the api is touched.
    - "ok" -> return True at once; the order is never charged again (rule 6).
    - "declined" -> return False at once; a decline is never retried (rule 4).
    - "error" -> retry, at most 3 attempts in total: api.sleep(2) before the second attempt and
      api.sleep(4) before the third. There is no wait after the last attempt.
    - Any other result is not "ok", so it gives False (rule 2), and it is not retried: only
      "error" is retried (rule 3), and blindly re-charging an unknown outcome could double-charge.
    - Exceptions raised by api.charge or api.sleep propagate unchanged and are not retried.

    Rule 7 of the request ("keep trying until the charge goes through, so that no order is
    lost") contradicts rules 2, 3 and 4, which cap the attempts at 3, forbid retrying a decline
    and say to return False otherwise. The explicit limits win: after three "error" results the
    function gives up and returns False. False therefore means "not charged"; the caller must
    keep that order (for example queue it for a later retry) so that it is not lost.
    """
    if (
        isinstance(amount, bool)
        or not isinstance(amount, Integral)
        or not MIN_AMOUNT_CENTS <= amount <= MAX_AMOUNT_CENTS
    ):
        raise ValueError(
            f"amount must be a whole number of cents from {MIN_AMOUNT_CENTS} "
            f"to {MAX_AMOUNT_CENTS:,}, got {amount!r}"
        )

    for attempt in range(MAX_ATTEMPTS):
        if attempt > 0:
            api.sleep(RETRY_DELAYS_SECONDS[attempt - 1])
        result = api.charge(order_id, amount)
        if result == "ok":
            return True  # rule 6: stop at the first success, so the order is charged once
        if result != "error":
            return False  # rule 4: "declined" (or anything unrecognised) is final
    return False  # every attempt returned "error"
