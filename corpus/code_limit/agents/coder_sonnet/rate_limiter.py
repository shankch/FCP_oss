"""Login rate limiter for Fernwood Outfitters (request P-LIMIT-1)."""

from __future__ import annotations

import threading


def _require_int(value: object, name: str) -> None:
    # bool is a subclass of int, but True/False is never a customer id or a time.
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an int, got {value!r}")


class _Customer:
    """What is remembered about one customer: at most three times plus one."""

    __slots__ = ("allowed_at", "last_denied_at")

    def __init__(self) -> None:
        # Allowed attempts that still count towards the limit, oldest first.
        self.allowed_at: list[int] = []
        # Second of the customer's most recent denied attempt, if any.
        self.last_denied_at: int | None = None


class RateLimiter:
    """Limits how often each customer may try to log in.

    ``allow(user, now)`` is called once for every login attempt and returns
    True if the attempt may go ahead.  ``user`` is a customer id from 0 to 1000
    (both included); ``now`` is the time in whole seconds.

    How the rules are applied, including the points the request leaves open:

    * Rules 2-4.  An attempt is denied if the customer already has 3 allowed
      attempts in the last 60 seconds.  Only allowed attempts are counted;
      denied ones never are.
    * Rule 5.  A denied attempt blocks the customer's attempts for the next
      10 seconds.  Every denied attempt starts a fresh 10 seconds, also one
      that was itself denied by an earlier block, so a customer who keeps
      retrying at least every 10 seconds stays blocked.
    * Rule 4 against rule 5.  They disagree when a customer is denied and,
      within 10 seconds, the oldest of their 3 attempts leaves the window
      (allowed at 0, 1, 2; denied at 59; at 60 only two attempts remain):
      rule 4 says allow, rule 5 says deny.  Rule 5 wins.  If rule 4 won, the
      10-second block could never change an answer and rule 5 would do nothing.
    * Edges.  An effect that starts at second x and lasts N seconds covers
      x .. x+N-1 and is over at x+N: an allowed attempt at second e counts
      until e+59 and not at e+60; a denial at second d blocks d .. d+9 and not
      d+10.
    * Rule 1.  ``ValueError`` if ``user`` is not an int from 0 to 1000, if
      ``now`` is not an int, or if ``now`` is earlier than in the previous
      call to ``allow`` (for any customer, allowed or denied; equal is fine,
      and the first call may use any time).  A call that raises changes
      nothing: it does not move the clock and does not use up any quota.

    State is kept in memory, per instance: at most 1001 customers with four
    numbers each.  Calls are serialised with a lock.
    """

    MAX_USER_ID = 1000
    MAX_ATTEMPTS = 3
    WINDOW_SECONDS = 60
    COOLDOWN_SECONDS = 10

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_now: int | None = None  # `now` of the previous successful call
        self._customers: dict[int, _Customer] = {}

    def allow(self, user: int, now: int) -> bool:
        """Record one login attempt by ``user`` at second ``now``.

        Returns True if the attempt may go ahead, False if it is denied.
        """
        _require_int(user, "user")
        _require_int(now, "now")
        if not 0 <= user <= self.MAX_USER_ID:
            raise ValueError(f"user must be from 0 to {self.MAX_USER_ID}, got {user}")

        with self._lock:
            if self._last_now is not None and now < self._last_now:
                raise ValueError(
                    f"now={now} is earlier than in the previous call ({self._last_now})"
                )
            # Nothing below can fail, so a call that raised never got this far.
            self._last_now = now

            customer = self._customers.get(user)
            if customer is None:
                customer = self._customers[user] = _Customer()

            # An allowed attempt at second e stops counting at second e + 60.
            customer.allowed_at = [
                e for e in customer.allowed_at if now - e < self.WINDOW_SECONDS
            ]
            window_full = len(customer.allowed_at) >= self.MAX_ATTEMPTS

            # Blocked from a denial at second d until second d + 10.
            blocked = (
                customer.last_denied_at is not None
                and now - customer.last_denied_at < self.COOLDOWN_SECONDS
            )

            # Rule 5 beats rule 4: a block denies even when the window has room.
            if window_full or blocked:
                customer.last_denied_at = now
                return False

            customer.allowed_at.append(now)
            return True
