import os

BALANCE_FILE = "balance.txt"
TMP_FILE = "balance.txt.tmp"
MAX_CENTS = 100_000_000


def _remove_quietly(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


def save_balance(cents: int) -> bool:
    """Atomically store `cents` as decimal digits in balance.txt.

    Returns True once the balance is in balance.txt. Returns False if the
    write or the replace fails; the previous balance.txt is never modified
    by a failed write. If only the replace fails, balance.txt.tmp is kept so
    the balance can be recovered from it.
    """
    if isinstance(cents, bool) or not isinstance(cents, int):
        raise TypeError("cents must be an int")
    if cents < 0 or cents > MAX_CENTS:
        raise ValueError(f"cents must be between 0 and {MAX_CENTS}, got {cents}")

    try:
        f = open(TMP_FILE, "w", encoding="ascii")
        try:
            f.write(str(cents))
            f.flush()
            os.fsync(f.fileno())
        finally:
            f.close()
    except OSError:
        _remove_quietly(TMP_FILE)
        return False

    try:
        os.replace(TMP_FILE, BALANCE_FILE)
    except OSError:
        return False
    return True
