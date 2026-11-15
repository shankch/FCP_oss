I've written `formal/agent_a.yaml`. `fcp lint` reports it clean, and the `fcp explain` output matches what I intended for every item.

**Items: 8 formal items, plus the adapter's frame rule F-ZERO**
- **5 properties:** RA-RET-1 (if q flies, the call returns True), RA-RET-2 (if it doesn't, it returns False), and RA-EX-1, RA-EX-3 and RA-EX-4 (each example returns the value the prompt gives).
- **3 scenarios:** RA-EX-1-S, RA-EX-3-S and RA-EX-4-S, saying each of those example calls must be possible.
- No assumptions or don't-cares. Under my readings the return value is fully decided for every input.
- **Readings recorded under `decisions`:**
  - R-FLY-1 "will fly if": reading 1, "if and only if".
  - R-FLY-2 "palindromic list": reading 1, the empty list counts as balanced.
  - R-FLY-3 "more than or less than or equal": reading 3, the literal one.
  - R-FLY-3 "the sum of its elements is more than": reading 2, the rule governs.
  - R-EX-2: reading 2, the rule governs.

**Requirements left unformalized (6)**
- **R-IF-1:** it's non-functional. The function name and arguments are already fixed in `design.yaml`, so there's no behaviour to check.
- **R-FLY-1, R-FLY-2, R-FLY-3:** these are definitions. They're carried by named expressions (`flies`, `balanced`, `weight_ok`) used in RA-RET-1 and RA-RET-2, and are marked `covered_by` those two.
- **R-FR-1:** marked `covered_by: [F-ZERO]`. The adapter already adds that rule to every set, and lint accepts this.
- **R-EX-2:** it contradicts the rule read literally (details below). I let the rule govern, so its expected False isn't formalized. Adding it anyway would make the set impossible to satisfy for that call.

**Problems in the specification**
1. **The weight condition is a tautology.** "The sum … is more than or less than or equal the maximum possible weight w" is true for every sum, so taken literally, flying depends only on q being a palindrome. I wrote it literally as `total > w || total <= w` and didn't repair it. "Maximum possible weight" and the example comments strongly suggest `sum(q) <= w` was meant.
2. **The rule contradicts example R-EX-2.** Under the literal rule, `will_it_fly([3, 2, 3], 1)` returns True; the example says False. My set follows the rule. Any set that follows the example (`sum <= w`) will disagree with mine on balanced lists whose sum is above w, and that's where the comparison should show it.
3. **"will fly if" only states a sufficient condition.** I read it as "if and only if". Otherwise "will not fly" is never defined, "False otherwise" could never apply, and R-EX-1 (an unbalanced list returns False) wouldn't follow from the rule.
4. **The empty list isn't addressed.** The prompt doesn't say whether `[]` is balanced. I treated it as a palindrome, so `[]` flies.