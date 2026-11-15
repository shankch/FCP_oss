I wrote `formal/agent_b.yaml`. `fcp lint` reports clean, and the `fcp explain` output matches what I meant for every item.

**Items: 14** (8 properties and 6 scenarios). There are no assumptions and no don't-cares. The function has no memory, so the reference model is a set of defs over each call's arguments:
- `weight` is the sum of the elements of q.
- `balanced` means q is a palindrome.
- `fly` is `balanced && weight <= w`.
- `ret_true` / `ret_false` mean outcome 0 with `flies` set to 1 / 0.

What the properties check:
- **RB-FLY-1 / RB-FLY-2:** if `fly` holds the call returns True; otherwise it returns False.
- **RB-WT-3:** a weight above w gives False.
- **RB-BAL-1:** an unbalanced q gives False.
- **RB-EX-1..4:** each of the four examples, checked as a guarantee for that exact call. Each also has a cover scenario showing it can happen.
- **Two extra scenarios** record readings I chose: the empty list flies, and a balanced q whose weight equals w flies.

All four examples agree with the model.

**Requirements not formalized: 5, each with a reason.**
- **R-IF-1** ("Complete this function"): this describes the submitted code, so no trace of calls can check it.
- **R-IF-2** (the name and order of the arguments): the adapter fixes these. A misnamed function would end every call with outcome 1, so RB-FLY-1/2 catch it. Covered by those two.
- **R-WT-1, R-WT-2** (definitions): carried by the `weight` and `light` defs. Covered by RB-FLY-1/2 and RB-WT-3.
- **R-FR-1:** this is the frame rule F-ZERO, which is already added to every set. Covered by F-ZERO.

**Readings I chose (all reading 1):**
- "will fly" means balanced and not too heavy, with no other condition.
- True and False are the actual Python bools.
- An empty q is valid and always flies.
- A weight equal to w is allowed.
- "Unbalanced" means not a palindrome.

**Problems in the specification:**
1. **Flying is never defined.** Balance and the weight limit are only implied by the comment on one example. The word "but" suggests they are the only conditions, but nothing says so.
2. **"Balanced" is never defined.** All the examples fit each of the three readings (palindrome, first and last elements equal, equal half sums), so they don't settle it.
3. **The limit is unclear at equality.** "less than" in the comment conflicts with "maximum possible weight" when the sum equals w, and no example tests that case.
4. **The empty list isn't mentioned.**
5. **The return type is only implied.** The examples show `True`/`False`, but the prompt never rules out other truthy or falsy values.

Of these, the definition of balance and the equality case are the most likely places for another reader of the prompt to choose differently.