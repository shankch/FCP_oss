"""Client of the Fernwood inventory service (a stub: the real client is not
installed in this workspace, so tests replace these functions)."""


class InventoryError(Exception):
    """The inventory service could not be reached; the call did nothing."""


def reserve(sku: int, qty: int) -> str:
    """Reserve qty units of sku.  Returns "ok" or "refused"."""
    raise NotImplementedError('the inventory service is not available here')


def release(sku: int, qty: int) -> None:
    """Release qty reserved units of sku."""
    raise NotImplementedError('the inventory service is not available here')
