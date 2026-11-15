"""Crash-safe saving of the Fernwood ledger balance."""

import os

BALANCE_FILE = "balance.txt"
TEMP_FILE = "balance.txt.tmp"
MAX_CENTS = 100_000_000


def _discard_temp() -> None:
    """Remove the temporary file; a failure to remove it is not reported."""
    try:
        os.remove(TEMP_FILE)
    except OSError:
        pass


def save_balance(cents: int) -> bool:
    """Save ``cents`` to ``balance.txt`` in the current directory, atomically.

    The decimal digits are written to ``balance.txt.tmp``, flushed, fsynced and
    closed, and only then moved over ``balance.txt`` with ``os.replace``.
    ``balance.txt`` itself is never opened.

    Returns True once the balance is in ``balance.txt``, False otherwise.
    If the temporary file could not be written completely it is removed.  If
    only ``os.replace`` failed, the complete temporary file is kept so the
    balance can be recovered from it.

    Raises ValueError, before any file is touched, if ``cents`` is negative or
    more than 100,000,000.  Raises TypeError if ``cents`` is not an int.
    """
    if isinstance(cents, bool) or not isinstance(cents, int):
        raise TypeError(f"cents must be an int, not {type(cents).__name__}")
    if cents < 0 or cents > MAX_CENTS:
        raise ValueError(f"cents must be between 0 and {MAX_CENTS}, got {cents}")

    digits = str(int(cents))

    try:
        tmp = open(TEMP_FILE, "w", encoding="ascii")
    except OSError:
        # Nothing of ours was created; a leftover temporary file from an
        # earlier failed replace is not ours to delete (it may hold a balance).
        return False

    try:
        with tmp:  # closes the file, even on error
            tmp.write(digits)
            tmp.flush()
            os.fsync(tmp.fileno())
    except BaseException as exc:
        # The temporary file is incomplete: it is no use for recovery.
        _discard_temp()
        if isinstance(exc, OSError):
            return False
        raise

    try:
        os.replace(TEMP_FILE, BALANCE_FILE)
    except Exception:
        # Keep the complete temporary file so the balance can be recovered.
        return False
    return True
