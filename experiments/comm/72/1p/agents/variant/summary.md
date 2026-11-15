I've written `formal/variant.yaml`. `fcp lint` reports it clean, and the `fcp explain` output matches what I intended for every item.

**Items: 14.** That is 9 properties, 4 scenarios and 1 don't-care, plus the frame rule F-ZERO, which the tool adds to every set automatically.
- **Shared definitions:**
  - The weight is the sum of q's elements.
  - q is balanced when its first element equals its last.
  - `may_fly` means q is non-empty, balanced and lighter than w (strictly).
  - `ret_true` and `ret_false` mean the call returned the bool True or False, or returned a value of another type (outcome 2).
- **R-FLY-1:** there are three items.
  - For a q that may fly, the call must return some value: no exception and no hang.
  - An empty q returns a falsy value.
  - A don't-care leaves the answer open wherever q may fly, except for the two True examples.
- **R-FLY-2, R-WT-3, R-BAL-1:** each is a direct rule that the call returns a falsy value when q can't fly, when sum(q) ≥ w, and when the first and last elements differ.
- **R-EX-1 to R-EX-4:** each example has a property that fixes the answer to that call, plus a scenario. The function keeps no state, so an example states what that call must return, not just what it may return.
- **Decisions:** all six flagged phrases are recorded with the readings you gave (reading 2 each time), and every item those readings affect says so in its note.

**Left unformalized (5):**
- **R-IF-1:** it is about the program text you hand in (a body for the stub), not about the calls.
- **R-IF-2:** the adapter in `design.yaml` already fixes the function name and argument order. A wrongly named or ordered function would raise an error on every call, which my rules forbid.
- **R-WT-1 and R-WT-2:** these are definitions. They are realized by the shared definitions above and covered by RV-WT-3, RV-FLY-2 and RV-FLY-1-RET.
- **R-FR-1:** this is the frame rule, covered by F-ZERO.

**Problems in the specification:**
1. **The weight readings contradict each other.** R-WT-2 calls w "the maximum possible weight that q may have and still fly", so a weight equal to w should be allowed. The reading you set for R-WT-3 makes sum(q) == w not fly. I noted the conflict and didn't fix it.
2. **Truthy and falsy can't really be checked.** The adapter records any non-bool return as outcome 2 without saying whether it is truthy or falsy. So `ret_true` and `ret_false` both accept every non-bool return, and those checks pass whatever such a value is. For the same reason, any non-bool return also satisfies the True-example scenarios.
3. **"Fly" is never defined.** The prompt gives no condition that makes q fly, so the answer for a balanced, light enough list is open everywhere except at the two True examples.
4. **"Balanced" is never defined.** Under the first/last-element reading, a list like [1, 2, 3, 1] counts as balanced.
5. **My own choice:** I also read the examples' "➞ True / ➞ False" as truthy/falsy, the same way as the "returns True" and "False" readings. This is noted in each example item.