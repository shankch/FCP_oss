I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and the `fcp explain` output matches what I intended for every item. Because I took the readings you assigned, the set contradicts itself in several places. That is intended, but it means no implementation can satisfy the whole set.

**Items: 10 formal items, plus 18 decisions (one for every flagged phrase)**
- **1 assumption:** RV-IN-2 says `arr` is never empty.
- **7 properties:**
  - RV-SEL-1: `outcome == 2` on every call. Returning "the value alone" means returning an integer, and the adapter records any non-list return as outcome 2 without its value.
  - RV-OUT-1: if `arr` has an even value, `outcome == 2`.
  - RV-SEL-3: if the smallest even value appears more than once, `outcome == 2`.
  - RV-SEL-2: if a non-empty list is returned, its first element is the smallest even value in `arr`.
  - RV-OUT-2: if a two-element list is returned, its index is 1-based.
  - RV-EMP-1: if `arr` is empty, the result is `[]`.
  - RV-EMP-2: if `arr` has no even value, the result is `[]`.
- **2 scenarios:** Examples 1 and 4, exactly as written.
- Each note names the readings that affect the item, including where R-DEF-1 (tree structure) and R-IN-4 (node objects) apply.

**Left unformalized (8)**
- **R-IF-1:** a non-functional requirement (it only says to deliver the function).
- **R-DEF-1:** under your reading the tree structure decides which node can be plucked, but the spec never says how.
- **R-IN-1:** always true by construction, since the list slots hold unsigned numbers.
- **R-IN-3:** under your reading it limits the size of the whole tree, which isn't an argument. All it implies for `arr` is at most 10,000 elements, and the interface already allows at most 8.
- **R-IN-4:** under your reading `arr` holds node objects, which the list adapter can't represent.
- **R-EX-2:** under your reading the example is wrong, so it isn't a required behaviour. I didn't add the "corrected" answer `[1, 0]` because the spec never states it, and it would contradict the smallest-even rule I took for R-SEL-2.
- **R-EX-3:** under your reading the empty input is outside the allowed inputs.
- **R-FR-1:** already covered by the frame rule F-EMPTY.

**Contradictions in the set**
I worked these out from the formulas. I only ran `lint` and `explain`, not `fcp check`, so the tool hasn't confirmed them yet.
- **RV-SEL-1 vs RV-EMP-2:** they clash on any `arr` with no even value, e.g. `[1]`. Your readings already say R-SEL-1 contradicts R-EMP-2.
- **The examples vs the outcome-2 items:** RV-EX-1 and RV-EX-4 can't be reached with RV-SEL-1 and RV-OUT-1 (RV-SEL-3 too, for Example 4). The examples return lists; those items require a bare value.
- **The examples vs RV-OUT-2:** with 1-based indexing, Example 1's `[2, 1]` points to `arr[0] = 4`, and Example 4's `[0, 1]` points to `arr[0] = 5`.
- **Items that can never fire:**
  - RV-EMP-1 never applies, because RV-IN-2 rules out empty input. That matches your "vacuous" reading.
  - RV-SEL-2 and RV-OUT-2 never apply here, because RV-SEL-1 forbids returning a list.
- **Not formalized:** removing the node from `arr` (the "pluck" reading), because the interface doesn't record `arr` after the call. The smallest-index tie-break also can't be seen when only the value is returned, since all tied nodes have the same value.

**Problems in the spec**
- "The node with the value" seems to be missing a qualifier. Only "smallest even value" fits all four examples.
- If the qualifier is "smallest value", Example 2 is wrong.
- The constraint `1 <= nodes.length` contradicts both the empty-array clause and Example 3.
- "Return it" conflicts with the `[value, index]` list form.
- `nodes.length` and `node.value` don't match the input, which is a plain list of integers.
- The tree in "a branch of a tree" is never defined.
- Every "Explanation" line in the examples is empty.