# Prompt P-LIMIT-1: Fernwood Outfitters login rate limiter

Write a Python class that limits how often each customer can try to log in:

    class RateLimiter:
        def allow(self, user: int, now: int) -> bool:

`allow` is called once for every login attempt, with the customer's id `user`, from 0 to 1,000, and the time `now` in whole seconds. It returns True if the attempt may go ahead.

Rules:

1. Raise ValueError if `user` is out of range, or if `now` is earlier than in the previous call.
2. Allow at most 3 attempts per customer in any 60 seconds.
3. Attempts that are not allowed do not count.
4. Allow an attempt whenever the customer had fewer than 3 allowed attempts in the last 60 seconds.
5. After a denied attempt, deny that customer's attempts for the next 10 seconds.

Example: attempts by one customer at 0, 1 and 2 seconds are allowed, and a fourth at 3 seconds is denied.
