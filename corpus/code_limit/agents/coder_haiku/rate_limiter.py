"""Login attempt rate limiter for the Fernwood Outfitters store.

Each customer, identified by an int from 0 to 1000 inclusive, may make at most
3 allowed login attempts in any 60 seconds. A denied attempt locks that
customer out for the next 10 seconds. Times are whole seconds supplied by the
caller and must not go backwards from one call to the next.
"""

import numbers
import threading
from collections import deque

MIN_USER = 0
MAX_USER = 1000
MAX_ATTEMPTS = 3
WINDOW_SECONDS = 60
LOCKOUT_SECONDS = 10


def _as_int(name, value):
    if isinstance(value, bool) or not isinstance(value, numbers.Integral):
        raise TypeError(f"{name} must be an int, not {type(value).__name__}")
    return int(value)


class RateLimiter:
    """Decides whether each login attempt may go ahead.

    Each event at time e applies for times t with e <= t < e + duration:

    * An allowed attempt at time a counts toward the cap until time a + 60.
    * A denied attempt at time d locks the customer out until time d + 10.
      Every denied attempt restarts the lockout, including one that arrives
      during an existing lockout.
    * A lockout overrides the count: a locked-out customer is denied even
      when fewer than 3 allowed attempts are in the window.

    Denied attempts are never stored, so they do not use up the cap. A call
    that raises ValueError or TypeError changes no state.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._last_now = None
        self._allowed = {}       # user -> times of allowed attempts still in the window
        self._locked_until = {}  # user -> time the most recent lockout ends

    def allow(self, user: int, now: int) -> bool:
        user = _as_int("user", user)
        now = _as_int("now", now)
        if not MIN_USER <= user <= MAX_USER:
            raise ValueError(f"user must be from {MIN_USER} to {MAX_USER}, got {user}")

        with self._lock:
            if self._last_now is not None and now < self._last_now:
                raise ValueError(
                    f"now={now} is earlier than the previous call at {self._last_now}"
                )
            self._last_now = now

            times = self._allowed.setdefault(user, deque())
            while times and now - times[0] >= WINDOW_SECONDS:
                times.popleft()

            locked_until = self._locked_until.get(user)
            locked = locked_until is not None and now < locked_until
            if not locked and len(times) < MAX_ATTEMPTS:
                times.append(now)
                return True

            self._locked_until[user] = now + LOCKOUT_SECONDS
            return False
