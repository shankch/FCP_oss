The rate limiter and its tests are written, and all 48 tests pass on the first run with the venv interpreter, so no fixes were needed.

Files:
- rate_limiter.py
- test_rate_limiter.py

**Implementation:** each customer keeps the times of at most 3 allowed attempts, pruned on every call, plus a lockout end time. One lock keeps the cap intact when calls arrive concurrently. The tests cover the request's example, each rule and its boundaries, and 20 seeded random call sequences checked against a rule-by-rule restatement. As a check on the tests, I planted 10 bugs in memory (for example, lockouts not restarting, denied attempts taking a slot, a 9-second lockout, no time-order check). Each one made at least one test fail.

**Decisions where the request was unclear:**
1. Valid user ids are 0 to 1000 inclusive. Non-int arguments, including bool, raise TypeError, which the request did not specify.
2. "Last 60 seconds": an allowed attempt at time a counts up to a+59. An attempt exactly 60 seconds later no longer sees it.
3. Lockout: a denial at d blocks attempts until d+10. An attempt at exactly d+10 is allowed if the count permits.
4. Every denied attempt restarts the 10-second lockout, including one that arrives during a lockout. This is the literal reading of rule 5. If the team wants a fixed 10 seconds from the first denial, make the lockout assignment at the end of `allow` conditional on the customer not already being locked. Two tests will then need updating.
5. The lockout overrides rule 4. Read literally, rule 4 would let a locked-out customer through whenever they had fewer than 3 attempts in the window, and rule 5 would then never change an outcome.
6. Denied attempts are not stored, so they never use up the cap, but they do start lockouts.
7. There is one clock for all customers, and "previous call" means the previous accepted call on the limiter. Equal times are allowed and earlier times raise ValueError. Calls that raise ValueError or TypeError change no state, so they do not move the clock.
8. Negative times are accepted because the request gives no lower bound.
9. Calls are serialized with a lock. This was not requested, but it keeps the cap intact when request threads call at the same time.
10. State lives in process memory. It is lost on restart, and each server process keeps its own counts, so with several processes the limit applies per process rather than per customer overall.
