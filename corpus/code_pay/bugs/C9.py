"""Reference implementation of prompt P-PAY-1.

It follows rule 3 (at most 3 attempts) over rule 7, so after three errors it
returns False, which breaks rule 7: the prompt's own conflict.  It waits
2 seconds before the second attempt and 4 before the third."""


def charge_order(api, order_id: int, amount: int) -> bool:
    if not 1 <= amount <= 1_000_000:
        raise ValueError('amount out of range')
    attempt = -1
    while attempt < 2:
        attempt += 1
        if attempt > 0:
            api.sleep(2 ** attempt)
        answer = api.charge(order_id, amount)
        if answer == 'ok':
            return True
        if answer == 'declined':
            return False
    return False
