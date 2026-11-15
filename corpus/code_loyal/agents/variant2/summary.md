I wrote `formal/variant2.yaml`. `fcp lint` reports it clean, and I read every item back with `fcp explain`; each one says what I meant.

**Items: 16 in total.** There are 15 properties and 1 scenario, with no assumptions or don't-cares.
- Every flagged phrase is read as you specified and recorded under `decisions`: reading 2 for R-POINTS-1 and reading 2 for R-CAP-1.
- The notes on V2-POINTS-1, V2-CAP-1, V2-CAP-2, V2-EARN-1 and V2-EX-1 say which reading they use.
- I needed two pieces of ghost state:
  - **`pts`:** the account's points, which are never output except by `balance()`. It starts at 0, adds whatever `earn` returns, and subtracts a successful `redeem`.
  - **`calls`:** a call counter, used only so the example scenario starts on a new account.
- R-KEEP-1 is a direct statement with one fixed level `k`: once `tier()` has returned at least `k`, it never returns less.

**Left unformalized (4):**
- **R-PKG-1:** the package and module layout can't be seen in a trace of calls.
- **R-SIG-1:** this is a definition. The interface carries it, and it is covered by the earn, redeem, range and getter properties, which force every call to raise ValueError or return a value of the right type.
- **R-RATE-1:** this is a definition, built into the earning-rate expressions. It is covered by V2-POINTS-1 and V2-CAP-2.
- **R-FR-1:** this is the adapter's frame rule, F-ZERO in `design.yaml`, which is already part of every set.

**Problems in the specification.** I found these by working through the arithmetic by hand. I only ran lint and explain, not FCP's consistency check.
1. **The tier contradicts itself.** R-TIER-1 and R-GET-1 make the tier depend on the current points, but R-KEEP-1 says it never goes down. Example: `earn(50000)` earns 1,000 points and `tier()` returns 1. After `redeem(600)` the account has 400 points, so `tier()` must return 0 by R-TIER-1 and at least 1 by R-KEEP-1. I formalized all three literally and noted the clash rather than fixing it.
2. **The example can't happen under the readings given.** With reading 2 for "the account's tier", `earn(60000)` on 0 points can only earn 1,200 points at the silver rate. That is over the cap, so with reading 2 for the cap the purchase is refused. The balance stays 0 and `redeem(50)` fails, so V2-EX-1 is unreachable. Under the other cap reading the balance would be 950. The example only works with reading 1 of the tier phrase.
3. **Reading 2 of "the account's tier" is circular and can allow two answers.** The points earned set the tier, which sets the rate, which sets the points earned. On 0 points, a $300 purchase can earn 300 (still basic) or 600 (then silver). Both are allowed, so the result isn't fixed.
4. **Things the text doesn't say:**
   - How a refused purchase is reported. Because R-EARN-1 says `earn` returns what the purchase earns, I read it as returning 0 and adding nothing.
   - What a call that raises ValueError does to the account. I assumed it leaves the account unchanged.
5. **Representation limit.** The points model stops growing at 131,071, the largest value `bal` can carry. Real balances can't get near that within the checked call sequences.