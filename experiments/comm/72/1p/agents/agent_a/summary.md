I wrote `formal/agent_a.yaml`. `fcp lint` reports it clean, and the English rendering from `fcp explain` matches what I meant for every item.

**Items: 12** (8 properties, 4 scenarios, no assumptions or don't-cares). I didn't need any ghost state.
- I defined five helper expressions: `weight` (sum of the elements of q), `balanced` (q is a palindrome), `fly` (balanced and weight ≤ w), and `ret_true` / `ret_false` (outcome is 0 and `flies` is set or clear).
- **RA-FLY-1 and RA-FLY-2:** the function returns True exactly when q flies, and False otherwise.
- **RA-WT-3:** if the weight is above w, the result is False.
- **RA-BAL-1:** if q is unbalanced, the result is False.
- **RA-EX-1 to RA-EX-4:** each docstring example is both a property ("this call returns this value") and a scenario (`-S`). requirements.yaml labels the examples as scenarios, but the function keeps no state between calls. So each example fixes the answer for that call, and a scenario on its own would also accept a function that only sometimes gives it.

**Requirements left unformalized: 5, each with a reason**
- **R-IF-1** says the deliverable is a function body. It is non-functional and says nothing about the calls.
- **R-IF-2** fixes the function name and parameter order, which design.yaml already does.
- **R-WT-1 and R-WT-2** are definitions (weight, and w as the maximum weight). They live in the `weight` and `fly` helpers, and I listed RA-WT-3 and RA-FLY-1/2 under `covered_by`.
- **R-FR-1** is the adapter's F-ZERO frame rule, which is already part of every set. Its `covered_by` is F-ZERO.

**Readings taken.** I took reading 1 for all six flagged phrases:
- "will fly": balanced and weight ≤ w, with no other condition.
- "returns True" / "False": the actual bools True and False, not any truthy or falsy value.
- "the object q": an empty list counts as an object. It is balanced and weighs 0, so it always flies.
- "less than the maximum possible weight": a weight equal to w is allowed.
- "unbalanced": q is not a palindrome.

**Problems in the specification**
1. **"Fly" is never defined.** The only clue is the comment on the first example, which gives two conditions that are needed. It never says they are enough.
2. **"Balanced" is never defined.** The four examples can't tell the readings apart. For example, [1, 3, 2, 1] has matching first and last elements but isn't a palindrome, and [1, 2, 3, 0] has equal half-sums but isn't a palindrome.
3. **The edge case of weight equal to w is open.** The comment says "less than", but "maximum possible weight" suggests ≤ is fine, and no example has a weight equal to w.
4. **The empty list isn't covered**, and it isn't clear whether "returns True" means the bool True or any truthy value.