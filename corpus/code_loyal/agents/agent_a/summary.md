I wrote /work/ws_loyal_agent_a/formal/agent_a.yaml (`set: agent_a`). `fcp lint` reports clean, and the `fcp explain` rendering of every item says what I intended.

**Items: 15**
- **1 assumption.** LA-ENV-1 (R-SIG-1): `op` is between 1 and 4, so every call is one of the class's four methods.
- **13 properties:**
  - LA-NEW-1 (R-NEW-1): `after_reset`. In the first call on a new account, balance returns 0 and a redeem fails.
  - LA-TIER-1 (R-TIER-1).
  - LA-POINTS-1 (R-POINTS-1).
  - LA-CAP-1 and LA-CAP-2 (R-CAP-1).
  - LA-RANGE-1 and LA-RANGE-2 (R-RANGE-1): an invalid earn or redeem raises ValueError.
  - LA-EARN-1 (R-EARN-1).
  - LA-REDEEM-1 and LA-REDEEM-2 (R-REDEEM-1).
  - LA-GET-1 and LA-GET-2 (R-GET-1): tier and balance.
  - LA-KEEP-1 (R-KEEP-1): uses a rigid level `k` from 1 to 3 with `once`, so every tier value returned is at least every value returned before.
- **1 scenario.** LA-EX-1 (R-EX-1): earn(60000), redeem(50), balance() returns 550, then tier() returns 1, starting from 0 points.
- **Ghost state.** The account's points are internal, so I used one ghost, `pts100`, holding 100 times the points. Scaling by 100 avoids division: whole dollars × 100 is written as `amount - amount % 100`. Only inputs drive it, it starts at 0, and only a valid earn or a valid redeem the account can cover changes it. It saturates at 100 × 131,071, the largest balance the interface can carry.
- **Decisions:**
  - R-POINTS-1, "the account's tier": reading 1, the tier before the purchase. Reading 2 makes the earned points depend on themselves, and the example's balance of 550 holds only with reading 1.
  - R-CAP-1, "No purchase earns more than": reading 1, an over-cap purchase earns exactly 1,000. Nothing says such a purchase is refused, and rule 5 lists every case that raises.

**Left unformalized (3)**
- R-PKG-1: the split into modules is the structure of the code and does not show on the trace.
- R-RATE-1: a definition. It is the def `rate`, and items LA-POINTS-1 and LA-EARN-1 cover it.
- R-FR-1: it is already frame item F-ZERO in design.yaml, which is added to every set.

**Problems in the specification**
1. **Rule 1 contradicts rule 9.** Rule 1 sets the tier from the points the account has now; rule 9 says the tier `tier()` returns never goes down. I formalized both literally and did not repair the conflict. I ran one spec-only `fcp check`, which was more than the brief asked for, and its consistency analysis reported a conflict between R-GET-1 and R-KEEP-1: earn(50000), tier() returns 1, redeem(1), then tier() must be 0 by rule 1 and at least 1 by rule 9. The spec also doesn't say whether the earn rate follows the kept tier. The same run found the scenario reachable and no outputs left undetermined. It wrote a `.fcp/cache` directory into the workspace, which I deleted; the empty `.fcp` folder is still there.
2. **Rules 3 and 4 conflict as written** for any purchase whose rate × dollars exceeds 1,000, for example silver earn(50100) or gold earn(33400). The cap decision above resolves it, and LA-POINTS-1 applies only within the cap.
3. **Things the spec leaves open:**
   - Whether a call that raises ValueError changes the account. My model assumes it doesn't.
   - Rule 5 is read per method: the amount condition applies to earn and the points condition to redeem. Taken literally, it would also apply to the zero arguments that tier and balance carry on the trace.
   - There is no upper bound on points, but balance can only report up to 131,071, which an account passes after 132 maximal earns.
   - "Members keep what they have reached" could also mean tiers the points reached while `tier()` was never called. I formalized only the clause after the colon, which is about values `tier()` returned.
4. **The example presumes a new account but doesn't say so.** FCP-PL can't look back into the reset cycle, so the scenario requires 0 points before the earn instead. The example gives no results for earn or redeem, so the scenario requires none, and I checked balance before tier, in the order the example names them.
