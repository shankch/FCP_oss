I wrote 17 atomic requirements to `requirements_draft.yaml`, and `fcp anchor` accepted every quote on the first run, writing the anchored file to `requirements.yaml`.

**What's in it**
- **Frame (1):** R-FR-1, the F-EMPTY rule.
- **Definition and input assumptions (5):** R-DEF-1 says the nodes are the elements of `arr`, with value and index. R-IN-1 and R-IN-4 say elements are non-negative integers. R-IN-2 says the length is at least 1 and R-IN-3 says it is at most 10000; I split the length bounds so each can be checked on its own.
- **Guarantees (7):**
  - R-PL-1: if `arr` has an even value, a node is returned.
  - R-PL-2: the returned value is the smallest even value.
  - R-PL-3: ties go to the smallest index.
  - R-OUT-1: the result is a two-element list `[value, index]`.
  - R-OUT-2: `arr[index] == value`.
  - R-EMP-1: no even values returns `[]`.
  - R-EMP-2: an empty array returns `[]`.
- **Scenarios (4):** R-EX-1 to R-EX-4, the four examples.

**Contradictions (each recorded as an ambiguity on both sides)**
1. **Examples 1, 2 and 4 contradict the rule.** They give `[4,2,3]→[4,0]`, `[1,2,3]→[3,2]` and `[5,0,3,0,4,2]→[5,0]`. All three match "largest value and its index", not "smallest even value". The rule would give `[2,1]`, `[2,1]` and `[0,1]`, and Example 2 even returns an odd value. This is recorded on R-PL-2, R-PL-3, R-OUT-1 and R-EX-1/2/4.
2. **The length constraint contradicts the empty-array cases.** `1 <= nodes.length` conflicts with "the given array is empty, return []" and with Example 3. This is recorded on R-IN-2, R-EMP-2 and R-EX-3.

**Other ambiguities flagged**
- Whether 0 counts as even (R-PL-2, R-EMP-1).
- Whether "pluck" means just selecting the node or also removing it from `arr`, and whether "return it" means `[value, index]` or the value alone (R-PL-1).
- What the misspelled `smalest_value` means: smallest even, smallest overall, or largest as the examples show (R-OUT-1).
- Whether the index is 0-based or 1-based (R-OUT-2). Every example is consistent with 0-based.
- Whether "a branch of a tree" is just a flat list (R-DEF-1).

The examples also have empty "Explanation" headings. I didn't record that as a requirement because there was nothing to quote.