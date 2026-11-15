"""Client of the Fernwood shipping service (a stub: the real client is not
installed in this workspace, so tests replace this function)."""


class ShippingError(Exception):
    """The shipping service could not be reached; the call did nothing."""


def book(order_id: int) -> str:
    """Book the delivery of the order.  Returns "ok" or "refused"."""
    raise NotImplementedError('the shipping service is not available here')
