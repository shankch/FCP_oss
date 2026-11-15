"""Login rate limiter for Fernwood Outfitters (request P-LIMIT-1)."""

from __future__ import annotations

import threading
from collections import defaultdict, deque


class RateLimiter:
    """Limit how often each customer may try to log in.

    Call ``allow(user, now)`` once for every login attempt.  Each customer may
    have at most 3 allowed attempts in any 60 seconds.  Denied attempts do not
    count towards that limit, but every denied attempt starts a 10-second
    cooldown in which all of that customer's attempts are denied.

    Readings chosen where the request is open to more than one:

    * Valid customer ids are 0 to 1000 inclusive.  ``user`` and ``now`` must
      be ints (not bools); other types raise TypeError.
    * ``now`` is compared with the previous call for any customer, and may
      equal it.  A call that raises changes nothing: it is not an attempt,
      starts no cooldown and does not move the clock.
    * Durations are counted in whole seconds, starting with the event's own
      second.  An attempt allowed at ``t`` counts against attempts at ``t``
      to ``t + 59`` and has expired at ``t + 60``.  An attempt denied at
      ``d`` blocks attempts at ``d`` to ``d + 9``; the customer may try again
      at ``d + 10``.
    * The cooldown takes precedence over rule 4 ("allow whenever fewer than
      3 allowed attempts in the last 60 seconds"); otherwise the cooldown
      could never change an outcome.
    * An attempt denied during a cooldown is a denied attempt too, so it
      starts a new cooldown: retrying too soon extends the wait.

    One instance may be shared between threads.  State is kept in memory, in
    this object only.
    """

    MIN_USER = 0
    MAX_USER = 1000
    LIMIT = 3  # allowed attempts per customer ...
    WINDOW = 60  # ... in any this many seconds
    COOLDOWN = 10  # seconds of denials after a denied attempt

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_now: int | None = None
        # Per customer: times of allowed attempts still inside the window,
        # oldest first.  Never longer than LIMIT.
        self._allowed: defaultdict[int, deque[int]] = defaultdict(deque)
        # Per customer: the first time at which their cooldown is over.
        self._cooldown_ends: dict[int, int] = {}

    def allow(self, user: int, now: int) -> bool:
        """Return True if ``user``'s login attempt at time ``now`` may go ahead."""
        _require_int("user", user)
        _require_int("now", now)
        if not self.MIN_USER <= user <= self.MAX_USER:
            raise ValueError(
                f"user must be from {self.MIN_USER} to {self.MAX_USER}, got {user}"
            )

        with self._lock:
            if self._last_now is not None and now < self._last_now:
                raise ValueError(
                    f"now={now} is earlier than the previous call's now={self._last_now}"
                )
            self._last_now = now

            allowed = self._allowed[user]
            while allowed and now - allowed[0] >= self.WINDOW:
                allowed.popleft()

            cooldown_ends = self._cooldown_ends.get(user)
            in_cooldown = cooldown_ends is not None and now < cooldown_ends
            if in_cooldown or len(allowed) >= self.LIMIT:
                self._cooldown_ends[user] = now + self.COOLDOWN
                return False

            allowed.append(now)
            return True


def _require_int(name: str, value: object) -> None:
    # bool is a subclass of int, but True or False as an id or a time is a bug.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")
