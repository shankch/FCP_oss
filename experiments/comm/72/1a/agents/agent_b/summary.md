I wrote `formal/agent_b.yaml`. `fcp lint` reports no errors, and I read back the `fcp explain` output: every item means what I intended. I didn't run any deeper checks such as `fcp check`.

**Items: 9** (6 properties and 3 scenarios). The design is a function with no memory between calls, so instead of ghost state the model is a set of definitions computed from each call's inputs: `balanced` (q reads the same reversed), `total` (sum of q), `weight_ok` and `flies`. Both outputs are checked against `flies`.
- **RB-RET-1 / RB-RET-2:** if q flies, the call returns the bool True; if it doesn't, it returns the bool False. "Returns a bool" means `outcome == 0`.
- **RB-FLY-1:** whenever a bool is returned, `fly` equals "balanced and meets the weight condition".
- **RB-EX-1, -3, -4:** each example is a property (that exact call gives that result) and also a scenario (that result must be possible).

**Not formalized: 5 requirements**
- **R-IF-1:** this is the function's name and arguments, which the adapter binding in `design.yaml` already fixes. It isn't something a trace can check.
- **R-FLY-2, R-FLY-3:** these are definitions. They live in `balanced`, `total` and `weight_ok` and are marked as covered by RB-FLY-1, RB-RET-1 and RB-RET-2.
- **R-FR-1:** the frame rule F-ZERO already covers it, and it's added to every set automatically.
- **R-EX-2:** it contradicts the rule as I read it (below). Adding it would make the set inconsistent.

**Readings taken** (recorded under `decisions`):
- "will fly if" → 1: "if and only if". The examples explain False by naming the condition that fails.
- "palindromic list" → 1: the empty list counts as palindromic.
- "more than or less than or equal" → 3: taken literally, this is true for every sum.
- "the sum of its elements is more than" → 2, and R-EX-2's phrase → 2: in both, the rule wins over the example.

**Problems in the specification**
1. **The weight condition is meaningless as written.** "More than or less than or equal the maximum possible weight w" holds for any sum. So, literally, `w` never matters and q flies exactly when it's balanced. That's the reading I used, because the rules said to take the most literal one. It clashes with the term "maximum possible weight", which only makes sense as sum ≤ w.
2. **Example 2 contradicts the rule.** `will_it_fly([3, 2, 3], 1) ➞ False` with "3+2+3 is more than the maximum possible weight" only works if the condition is sum ≤ w. Examples 1, 3 and 4 fit either reading. Under my reading, RB-RET-1 requires True for this call, so code that implements sum ≤ w fails it. This is the most likely place for my set to disagree with another formalizer's.
3. **The probable intent is "sum ≤ w"** (reading 1 everywhere), which fits every example and the word "maximum". If the spec owner confirms it, `weight_ok` becomes `total <= w` and R-EX-2 becomes the property `q == [3, 2, 3] && w == 1 -> outcome == 0 && !fly`. I wrote that alternative into R-EX-2's `reason`.