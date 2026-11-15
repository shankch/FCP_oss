I wrote 17 atomic requirements to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run and wrote `requirements.yaml`.

**What's in it**
- **Function and definitions (2):** one non-functional requirement to complete `pluck(arr)`, and one definition: elements of `arr` are the nodes, a node's value is the element and its index is its position.
- **Assumptions (4):** elements are non-negative integers, at least 1 element, at most 10000 elements, and every element is ≥ 0.
- **Guarantees (6):**
  - Exactly one node is plucked when there is an even value.
  - Its value is the smallest even value.
  - Ties go to the smallest index.
  - The result has the shape `[value, index]`.
  - A non-empty list with no even values returns `[]`.
  - An empty list returns `[]`.
- **Scenarios (4):** Examples 1–4.
- **Frame rule (1):** `R-FR-1` for F-EMPTY, which matches the `req:` already in `design.yaml`.

**Contradiction (recorded as an ambiguity on all three requirements involved)**
- The constraint `1 <= nodes.length` (`R-IN-2`) conflicts with "the given array is empty, return []" (`R-EMP-2`) and with Example 3, `Input: []` (`R-EX-3`). The two readings are:
  1. An empty list is a valid call and must return `[]`.
  2. An empty list is outside the precondition, so its result is unconstrained.

**Other ambiguities flagged**
- **"branch of a tree":** `arr` is either a flat list of values, or it encodes a tree structure that matters.
- **"nodes.length":** the length of `arr`, or the number of nodes in the tree.
- **"return it":** return `[value, index]`, or the bare value.
- **"pluck":** only report the node, or remove it from `arr`.
- **"smallest even value":** the smallest among the even values, or the overall minimum and only if it is even. Example 2 favours the first reading.
- **"smalest_value":** a typo for the smallest even value, or the overall minimum.
- **"its index":** counted from 0 or from 1. The examples show counting from 0.
- **Explanations in Examples 1 and 2:** "2 has the smallest index" is literally false in both. In `[4,2,3]` the even 4 is at index 0, and in `[1,2,3]` the 1 is at index 0.
- **Example 4:** it says "0 is the smallest value" rather than "smallest even value".