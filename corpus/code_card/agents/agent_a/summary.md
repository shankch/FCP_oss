I wrote `/work/ws_card_agent_a/formal/agent_a.yaml` (`set: agent_a`). `fcp lint` reports clean, and the `fcp explain` rendering of every item matches what I meant.

I also ran the spec-only `fcp check` (without mutation). The set is consistent, the scenario can be reached, no item is a tautology, `outcome`, `earned`, `ok` and `bal` are all fully determined, and none of the 237 call sequences it checked showed a conflict.

**12 items:**
- **1 assumption, GA-ENV-OP (R-SIG-1):** `op != 0`, since the adapter only defines calls for op 1 to 3. The type part of R-SIG-1 is already encoded by the `outcome` signal (0 means the call returned a value of its declared type).
- **10 properties:**
  - R-NEW-1: GA-NEW-1
  - R-RANGE-1: GA-RANGE-1
  - R-LOAD-1: GA-LOAD-1 and GA-LOAD-2
  - R-CAP-1: GA-CAP-1 and GA-CAP-2
  - R-BONUS-1: GA-BONUS-1
  - R-SPEND-1: GA-SPEND-1 and GA-SPEND-2
  - R-BAL-1: GA-BAL-1
- **1 scenario, GA-EX-1 (R-EX-1):** on a new card, `load(2000)`, then `spend(500)`, then `balance()` returning 1500.

The balance is hidden inside the object, so I used one ghost, `card`, for it: it starts at 0, an accepted load adds the amount plus its bonus, and a valid spend that the balance covers takes the amount off. GA-LOAD-2 and GA-SPEND-2 check the effect of a load or spend directly when the next call is `balance()`. GA-BAL-1 checks it at every later call.

**Left unformalized:** only R-FR-1. It is the adapter's frame rule F-ZERO, which is added to every set automatically.

**Problems in the specification** (each choice is explained in the item's `note`):
1. **"A load that would take it over" (R-CAP-1):** I read it as balance + amount + bonus > 50,000. The other reading counts the amount only. Then a load of $100.00 or more onto a balance within $5.00 of the cap would have to succeed and push the balance past $500.00. That contradicts "The balance is never more than $500.00", so the other reading makes rules 3 and 4 contradict each other.
2. **Rule 1 against rule 5 for spend:** rule 5 on its own makes `spend(0)` return True and `spend(50001)` return False, but rule 1 says both raise ValueError. I applied rule 1 to spend too, as R-RANGE-1 and R-SPEND-1 already do.
3. **"`load` adds `amount` to the balance" is unconditional**, yet rules 1 and 3 make some loads raise. I read a load that raises as adding nothing and earning no bonus.
4. **The prompt never says a call that raises leaves the balance unchanged.** I modelled it that way. For loads the cap forces it anyway; for spends nothing in the text says so.
5. **"The balance covers it"** is read as balance ≥ amount, so spending exactly the balance returns True.
6. **"On a new card" is only implied by the example's quote.** GA-EX-1 states it as: every call up to and including the load was `load(2000)`.

The check's output is in `/work/card_a_check/evidence.json`.
