"""Crash-safe storage of the Fernwood ledger balance.

The balance lives in ``balance.txt`` in the current directory, as its
decimal digits (no sign, no newline).  It is never written in place: the
digits go to ``balance.txt.tmp``, which is flushed, fsynced and closed, and
only then moved over ``balance.txt`` with ``os.replace``.  Because the move
is atomic, a crash leaves ``balance.txt`` holding either the old balance or
the new one, never a damaged mix.
"""

import os

BALANCE_FILE = "balance.txt"
TEMP_FILE = BALANCE_FILE + ".tmp"
MAX_CENTS = 100_000_000


def save_balance(cents: int) -> bool:
    """Save ``cents`` to ``balance.txt``; return True once it is there.

    Raises TypeError if ``cents`` is not an int (bool is rejected too) and
    ValueError if it is negative or more than 100,000,000; in both cases no
    file is touched.

    Returns False, without raising, when the filesystem fails:

    * before the move (removing a stale temp file, creating, writing,
      fsyncing or closing the temp file): the temp file is removed and
      ``balance.txt`` is left as it was;
    * at the move (``os.replace`` fails): ``balance.txt.tmp`` is kept,
      complete and fsynced, so the balance can be recovered from it.
    """
    if isinstance(cents, bool) or not isinstance(cents, int):
        raise TypeError(f"cents must be an int, not {type(cents).__name__}")
    if cents < 0 or cents > MAX_CENTS:
        raise ValueError(f"cents must be between 0 and {MAX_CENTS}, got {cents}")
    digits = str(int(cents))

    # A balance.txt.tmp that is already here is stale: either the leftover of
    # an earlier save whose os.replace failed (its balance is superseded by
    # this newer one) or a partial file from a crash.  Remove it, then create
    # the temp file exclusively, so that we always write to a fresh file and
    # never through a symlink or hard link that leads to balance.txt itself.
    try:
        os.unlink(TEMP_FILE)
    except FileNotFoundError:
        pass
    except OSError:
        return False

    try:
        tmp = open(TEMP_FILE, "x", encoding="ascii")
    except OSError:
        return False

    try:
        try:
            tmp.write(digits)
            tmp.flush()
            os.fsync(tmp.fileno())
        finally:
            tmp.close()
    except OSError:
        _discard_temp()
        return False
    except BaseException:
        # e.g. KeyboardInterrupt: never leave a partial temp file behind.
        _discard_temp()
        raise

    try:
        os.replace(TEMP_FILE, BALANCE_FILE)
    except OSError:
        # Keep the temp file: it holds the complete, fsynced balance.
        return False
    return True


def _discard_temp() -> None:
    """Remove the temp file, ignoring failures (the caller returns False)."""
    try:
        os.unlink(TEMP_FILE)
    except OSError:
        pass
