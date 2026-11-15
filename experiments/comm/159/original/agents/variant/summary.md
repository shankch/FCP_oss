I've written `formal/variant.yaml`. `fcp lint` reports it clean, and the `fcp explain` output matches what each item is meant to say.

**Items: 16 formal items.** Each of the 12 readings you specified is used and named in the note of every item it affects. All flagged phrases are recorded under `decisions`. The one phrase you didn't specify, "array" in R-RET-1, I read as a Python list (reading 1). The adapter treats a list and a tuple the same, so this choice can't be tested.
- **12 properties** (R-RET-1 ×2, R-RET-2, R-RET-3, R-EAT-1..5, R-IN-1..3). They share one helper, `want = max(need - number, 0)`, the carrots still needed in this call under your R-DEF-2 reading. Taken together they mean:
  - For an in-range call where the stock covers `want`, the only allowed answer is `[want, 0]`.
  - For an in-range call where the rabbit stays hungry (`remaining < want`), the call must return something other than a plain two-integer list (`outcome == 2`).
  - A call with any argument above 1000 must not answer with a two-integer list (`outcome != 0`).
- **4 scenarios** (R-EX-1..4). The examples are written exactly as the spec gives them.

**Left unformalized (6):**
- R-FN-1 and R-FN-2 are non-functional: delivering a complete function, and its name and argument order. The adapter fixes these, and they don't show up in the call trace.
- R-DEF-1, R-DEF-2 and R-DEF-3 are definitions. Each points to the items that realize it (`covered_by`): R-DEF-1 and R-DEF-2 through `want`, R-DEF-3 through the rule that a call never eats more than `remaining`.
- R-FR-1 is the adapter's own rule F-ZERO, which is already part of every set.

**Problems in the specification under these readings:**
1. **The set is inconsistent by design.** All four examples contradict the readings. My properties give eat(5,6,10) → [1,0], eat(4,8,9) → [4,0] and eat(1,10,10) → [9,0]. For eat(2,11,5) the rabbit stays hungry, so a plain pair isn't allowed at all. I left all of these conflicts visible rather than fixing them.
2. **The two-element result contradicts itself.** "Array of [two elements]" clashes with the requirement to report hunger (R-RET-1 and R-EAT-5, reading 2). The interface has no signal for a hunger report, so the only thing that can be checked is "not a plain two-integer list".
3. **R-EAT-3 and R-EAT-4 are nearly empty.** Because a hungry result isn't a pair, these two items only apply when `remaining == want`.
4. **"May eat more" can't happen.** R-EAT-1/2 allow the rabbit to eat more than it needs, but then "carrots left to eat" would be negative, which can't be returned. So in practice it must eat exactly `want`. I kept the subtraction as written and did not add `max(..., 0)`.
5. **Rejection of bad inputs is only partly checkable.** The trace only covers argument values 0 to 1023, so only 1001 to 1023 can be checked. Negative arguments never appear in the trace.