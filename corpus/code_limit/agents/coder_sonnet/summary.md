I wrote `rate_limiter.py` and `test_rate_limiter.py`, and all 43 tests pass with the command you gave. I also ran the tests against 21 deliberately broken copies of the limiter, and every one was caught. That included each boundary decision below. Each decision is also written in the `RateLimiter` docstring.

`RateLimiter()` takes no arguments. It keeps, per customer, the allowed attempts that still count (at most 3) and the time of the last denial, so memory is bounded. A lock serialises calls.

**Where the request was unclear, and what I chose**

1. **Rules 4 and 5 contradict each other, and rule 5 wins.**
   - Take a customer allowed at 0, 1 and 2, then denied at 59. At 60 only the attempts at 1 and 2 are still inside the window. Rule 4 says allow, because that is fewer than 3; rule 5 says deny, because the denial was 1 second ago.
   - I chose deny. If rule 4 won, rule 5 could never change any answer, so it would do nothing.
   - To switch to the other reading, drop `blocked` from the `if window_full or blocked:` line in `allow`.
2. **A denial inside the 10-second block starts a fresh 10 seconds.** That is how I read rule 5 for every denied attempt, whatever caused it.
   - A customer who keeps retrying at least every 10 seconds therefore stays locked out indefinitely, even after the window has room. Retrying every second from 0 to 199 gives 3 allowed attempts and nothing after that.
   - I read rule 3 as "denied attempts don't count toward the 3-per-60 limit", not as "denied attempts have no effect". Otherwise rule 5 could never trigger.
3. **Where the time windows end:**
   - An allowed attempt at second `e` counts through `e+59` and no longer at `e+60`. After attempts at 0, 1 and 2, an attempt at 59 is denied and one at 60 is allowed.
   - A denial at second `d` blocks `d` through `d+9`, and `d+10` is free.
4. **User range:** "0 to 1,000" is inclusive, so 0 and 1000 are valid and -1 and 1001 raise `ValueError`.
5. **"Previous call":**
   - It means the previous call to `allow` for any customer, allowed or denied. An equal `now` is fine, and the first call accepts any int, including a negative one.
   - A call that raises changes nothing: it doesn't move the clock and doesn't use up quota.
6. **Wrong types** for `user` or `now` (floats, strings, `None`, `True`/`False`) also raise `ValueError`, not `TypeError`. The request names only `ValueError`, so callers need to handle only that one exception.
7. **Concurrent callers:** because the time check is global, if two threads read the clock and call `allow` out of order, the later one gets `ValueError`. Calls need to arrive in time order.
8. **Process scope:** state is in memory per instance, so it is not shared between processes.

Files are in the working directory:
- `rate_limiter.py`
- `test_rate_limiter.py`
