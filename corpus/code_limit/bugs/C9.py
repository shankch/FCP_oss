"""Reference implementation of prompt P-LIMIT-1.

It follows rule 5 (the penalty) over rule 4, so it breaks rule 4 on the
prompt's own conflict, which no implementation can avoid.  Decisions: an
attempt exactly 60 seconds earlier is outside the window; the penalty ends 10
seconds after the denial, and every denial starts it again; "the previous
call" is the previous call that did not raise."""


class RateLimiter:
    def __init__(self):
        self.last = None             # now of the previous call that did not raise
        self.allowed = {}            # user -> times of allowed attempts
        self.blocked_until = {}      # user -> first time the penalty no longer applies

    def allow(self, user: int, now: int) -> bool:
        if not 0 <= user <= 1000:
            raise ValueError('user is out of range')
        if self.last is not None and now < self.last:
            raise ValueError('now is earlier than in the previous call')
        self.last = now
        from collections import deque
        recent = self.allowed.setdefault(user, deque())
        while recent and now - recent[0] >= 60:
            recent.popleft()
        if now < self.blocked_until.get(user, 0) or len(recent) >= 3:
            self.blocked_until[user] = now + 10
            return False
        recent.append(now)
        return True
