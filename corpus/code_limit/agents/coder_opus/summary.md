I've written the `RateLimiter` class and its tests, and all 43 tests pass with the command you gave.

**How it works.** For each customer, the class keeps the times of their allowed attempts from the last 60 seconds (never more than 3) and the time their current cooldown ends. It also remembers the time of the last call. Each call takes the same small, fixed amount of work. Memory stays small, at most 1,001 customers with 3 timestamps each.

**Testing.** Besides tests for each rule and for every decision below, one test sends 12,000 random attempts and checks every answer against the rules worked out from the full history of calls. To make sure the tests can tell my readings apart from the alternatives, I tried 10 deliberately altered versions of the class, one per alternative reading plus a missing lock, and each one made at least one test fail. That check caught a bug in my own concurrency test: the first version could never fail. I fixed it, and it now fails 20 of 20 runs without the lock and passes 20 of 20 with it.

**Decisions where the request was unclear**, most important first:

1. **Rules 4 and 5 contradict each other, and I let rule 5 win.** Example: allowed at 0, 1 and 2, then denied at 59. At 60 only two allowed attempts fall in the last 60 seconds, so rule 4 says allow, but it is 1 second after a denial, so rule 5 says deny. If rule 4 won, the cooldown could never change any answer.
2. **Every denied attempt starts a new 10-second cooldown**, including attempts denied by a cooldown. This is the literal reading of rule 5. A customer who keeps retrying stays locked out until they pause for 10 seconds. I read rule 3 as "denied attempts don't count toward the 3", not "denied attempts have no effect", because the second reading would cancel rule 5.
3. **"Any 60 seconds" means 60 consecutive whole seconds.** An attempt allowed at second t counts until t+59 and has expired at t+60. So after 0, 1 and 2, the next attempt is allowed at 60, not 61. Earlier attempts in the same second count.
4. **Cooldown length:** a denial at second d blocks seconds d to d+9, and the customer can try again at d+10.
5. **"The previous call" means the previous call for any customer**, so there is one clock for the whole limiter. Equal times are fine, and a denied call still counts as a previous call.
6. **A call that raises an error changes nothing.** It doesn't count as an attempt, doesn't start a cooldown and doesn't move the clock. So a junk call with a bad id and a far-future time can't make later valid calls fail.
7. **Customer ids 0 to 1000 include both ends.**
8. **Wrong types raise TypeError, not ValueError.** This covers floats, strings, None and True/False, for both the id and the time. The request only names ValueError for out-of-range ids and earlier times.
9. **The first call accepts any whole-number time**, including negative ones, because the request sets no bounds.
10. **I added a lock, which wasn't requested,** so one limiter can be shared between threads. Without it, two simultaneous attempts could both take the third slot. Threads sharing one limiter must still pass times that never go backwards, or rule 1 raises. The state lives in memory in one object, so it isn't shared across server processes and is lost on restart.

Files are in the working directory:
- `rate_limiter.py`
- `test_rate_limiter.py`
