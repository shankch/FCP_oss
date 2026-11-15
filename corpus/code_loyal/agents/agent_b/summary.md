I wrote the agent_b formalization set at /work/ws_loyal_agent_b/formal/agent_b.yaml. `fcp lint` reports clean, and I read every item back with `fcp explain`; each one means what I intended. I also ran the spec-only part of `fcp check` (under a 6 GB memory cap): it found exactly one conflict, and it is the contradiction in the spec described below.

**Items: 19 in total** (17 properties, 1 assumption, 2 scenarios), plus 3 requirements listed under `unformalized` and 2 recorded decisions. Every item id starts with LB-.
- **Specification model:** three ghosts.
  - `pts` is the account's points. It is driven only by the inputs: a valid earn adds the purchase's points (rate × whole dollars, capped at 1,000), and a successful redeem takes the points off.
  - `top` is the highest tier `tier()` has returned. It has to follow the output `t`, because R-KEEP-1 is a statement about returned values.
  - `calls` counts calls since the reset. It is only there so the example can say "a new account".
  - The rate, the tier and floor(amount / 100) are defs. The IR has no division, so whole dollars are computed with two nested `count` quantifiers.
- **Checks:**
  - Every output is checked against the model: `earned`, `ok`, `t` and `bal`, and `outcome` on every call.
  - "Adds the points to the account" (LB-EARN-2) and "takes them off / stays as it was" (LB-REDEEM-3) are checked by a balance call made right after the earn or redeem.
  - The assumption LB-SIG-1 is `op` in 1..4, because the frame encodes only the four methods.
  - The scenarios LB-EX-1 and LB-EX-2 cover the example with balance and tier queried in either order.
- **Decisions:**
  - R-POINTS-1, reading 1 (the tier before the purchase). The example needs it: earn(60000) must earn 600 for balance to be 550 after redeem(50).
  - R-CAP-1, reading 1 (a purchase that would earn more earns exactly 1,000).
- **Check results:** the set is consistent in every single trigger situation, both scenarios are reachable, no output is left undetermined, and there are no tautologies.

**Unformalized (3):**
- **R-PKG-1:** the package layout can't be seen in a trace of calls.
- **R-RATE-1:** a definition, realised by the `rate` def and covered by LB-POINTS-1, LB-CAP-2 and LB-EARN-1.
- **R-FR-1:** realised by the frame rule F-ZERO, which is added to every set.

**Problems in the specification:**
1. **Rules 1/8 and rule 9 contradict each other (R-TIER-1 and R-GET-1 vs R-KEEP-1).**
   - Rule 1 makes the tier a function of the points held now, so a redeem can lower it. Rule 9 says the tier `tier()` returns never goes down.
   - The checker's conflict search found the shortest case: earn(50000) gives 500 points; tier() returns 1; redeem(1) leaves 499; the next tier() must return 0 by rule 1 and at least 1 by rule 9. The minimal conflicting set is R-GET-1 + R-KEEP-1.
   - I formalized both rules literally and did not repair this.
   - The other reading, "the tier is the highest one ever reached", would also change the earning rate after a drop. I describe it in the notes but did not take it.
2. **Rule 3 alone contradicts rule 4.** Rule 3 by itself would require more than 1,000 points for large silver or gold purchases. I state LB-POINTS-1 only where the cap doesn't apply, and say so in its note.
3. **Rule 5 is written as if it applied to every call.** Taken literally, it would make `tier()` and `balance()` raise, since the encoding sets amount and points to 0 in those calls. I limited the amount check to earn calls and the points check to redeem calls.
4. **The text never says what a call that raises ValueError does to the account.** The model leaves the account unchanged, and the notes say so.
5. **R-EX-1 doesn't fix the order of `balance()` and `tier()`.** I covered both orders.
6. **Minor limits of the encoding:**
   - The frame counts a balance above 131,071 as outcome 3, and the `pts` ghost saturates at that value. Reaching it takes more than 131 purchases, far beyond any analysis depth.
   - The `note` fields don't appear in the `evidence.json` that `fcp check` writes; it records every note as empty. They are in the YAML, and lint accepts them.
