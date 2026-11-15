I broke spec.md into 18 requirements and wrote them to `requirements_draft.yaml`. `fcp anchor` accepted every quote on the first run ("anchored 18 requirements") and wrote `requirements.yaml` with the line numbers filled in.

**What's in it**
- **Interface and definition (2):** the task is to complete `pluck(arr)` (R-IF-1); each element of `arr` is a node, with its value and its index (R-DEF-1).
- **Input assumptions (4):** elements are non-negative integers (R-IN-1, restated by R-IN-4 from `0 <= node.value`); `arr` has at least 1 element (R-IN-2); `arr` has at most 10000 elements (R-IN-3).
- **Guarantees (7):**
  - Pick exactly one node (R-SEL-1), the node "with the value" (R-SEL-2), and on a tie the one with the smallest index (R-SEL-3).
  - Return it as `[value, index]` (R-OUT-1, R-OUT-2).
  - Return `[]` for an empty array (R-EMP-1) or when there are "no values" (R-EMP-2).
- **Scenarios (4):** Examples 1–4 (R-EX-1 to R-EX-4).
- **Frame rule (1):** F-EMPTY (R-FR-1, doc FRAME).

**Main ambiguity:** "The plucked node should be the node with the value" never says which value; a word seems to be missing. I gave four readings:
1. The smallest even value. This is the only rule-like reading that fits all four examples.
2. The smallest value. This fails Example 2: `[1,2,3]` would give `[1, 0]`, not `[2, 1]`.
3. Any node at all.
4. The node at index 1, since every example's output is `[arr[1], 1]`.

The same gap carries into "the value" in the tie-break rule and "no values" in the empty-result rule. "No values" could mean no node matches the rule, or simply an empty array.

**Contradictions, each recorded on both requirements:**
- **Empty input:** the constraint `1 <= nodes.length` (R-IN-2) says `arr` is never empty, but R-EMP-1 and Example 3 (R-EX-3) say an empty `arr` returns `[]`.
- **Smallest-value reading vs Example 2:** reading 2 of R-SEL-2 gives a different answer from R-EX-2.
- **Always pick a node vs return `[]`:** "pluck one of the nodes" (R-SEL-1) suggests every call returns a node, but R-EMP-1 and R-EMP-2 return `[]` for some inputs.
- **What gets returned:** "return it" (R-SEL-1) suggests returning just the node, but R-OUT-1 says to return the list `[value, index]`.

**Smaller ambiguities:**
- Whether the index starts at 0 or 1 (the examples show 0).
- Whether "pluck" means removing the node from `arr`, which would change the argument.
- Whether `nodes.length` means the length of `arr` or the size of the whole tree.
- Whether `node.value` means an integer or an attribute of a node object.
- Whether "branch of a tree" means the list's structure matters.

The examples' "Explanation" sections are empty. I mention it here but didn't flag it, because it doesn't change any requirement.