I wrote `formal/variant1.yaml`. `fcp lint` reports no errors, and I read the `fcp explain` output item by item: each one says what I meant. I couldn't run any deeper check because `fcp check` is blocked for agents. So I haven't confirmed that the example scenario can be reached; I checked it by hand only.

**Items: 14.** One assumption, 12 properties and one scenario. The frame rule F-ZERO is added to every set automatically.
- **Assumption (R-SIG-1):** every call is one of the four methods, so `op` is 1 to 4.
- **Properties:**
  - R-NEW-1: a new account has 0 points.
  - R-TIER-1: tier is set by the 500 and 2,000 point thresholds.
  - R-POINTS-1: points earned when the amount is at or under the cap.
  - R-CAP-1: two items. Earnings are never over 1,000, and a purchase that would earn more earns exactly 1,000.
  - R-RANGE-1: two items, one for `earn` and one for `redeem`.
  - R-EARN-1 and R-REDEEM-1: one item each.
  - R-GET-1: two items, one for `tier()` and one for `balance()`.
  - R-KEEP-1: the returned tier never goes down.
- **Scenario (R-EX-1):** on a new account, `earn(60000)`, `redeem(50)`, then `balance()` returns 550 and `tier()` returns 1.
- **Hidden state:** one value holds the account's points times 100, because FCP-PL has no division and "whole dollars" needs one. A small call counter exists only to pin "new account" in the example. Everything else is stated directly on the interface signals.
- **Decisions:** reading 1 for both flagged phrases. The rate uses the tier before the purchase, and a purchase that would earn more than 1,000 earns exactly 1,000. Every item these readings touch says so in its note. That includes the balance, tier and redeem items, because the stored points follow those readings. The example itself only works under reading 1 of R-POINTS-1.

**Left unformalized: 3**
- **R-PKG-1:** the split into three modules can't be seen in the trace.
- **R-RATE-1:** a definition; it's covered by the `rate` formula used in V1-POINTS-1, V1-CAP-2 and V1-EARN-1.
- **R-FR-1:** this is the frame rule F-ZERO itself, so it's covered by that.

**Problems in the specification**
1. **Contradiction between R-TIER-1/R-GET-1 and R-KEEP-1.** Rule 1 makes the tier depend on the current points, and `redeem` can lower the points. Example: `earn(60000)` gives 600 points, so `tier()` returns 1. After `redeem(200)` there are 400 points, so `tier()` must return 0, but R-KEEP-1 forbids that. No implementation can meet both. I formalized both as written and flagged the conflict in the notes of V1-TIER-1, V1-GET-1 and V1-KEEP-1.
2. **R-RANGE-1 doesn't say which method each limit applies to.** I applied it to each method's own argument: `amount` for `earn`, `points` for `redeem`. Taken literally, the `amount` of 0 that the trace records in other calls would make every `tier()` and `balance()` call raise ValueError.
3. **The spec doesn't say what a call that raises ValueError does to the account.** My model leaves the account unchanged, and the notes say so.
4. **The spec puts no upper limit on the balance, but `bal` is only 17 bits.** My model is exact up to 131,071 points and stops growing there. Reaching that takes more than 131 maximum purchases, far beyond the checked sequences of up to 10 calls.