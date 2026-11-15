"""Client of the Fernwood payment service (a stub: the real client is not
installed in this workspace, so tests replace these functions)."""


class PaymentError(Exception):
    """The payment service could not be reached; the call did nothing."""


def charge(order_id: int, amount: int) -> str:
    """Charge amount cents for the order.  Returns "ok" or "refused"."""
    raise NotImplementedError('the payment service is not available here')


def refund(order_id: int, amount: int) -> None:
    """Refund amount cents of the order's charge."""
    raise NotImplementedError('the payment service is not available here')
