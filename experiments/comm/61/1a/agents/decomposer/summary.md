I split `spec.md` into 9 requirements and anchored them. `fcp anchor` accepted every quote on the first run ("anchored 9 requirements"), and the output is in `requirements.yaml`.

**Requirements**
- **R-NF-1** (non_functional): the deliverable is the completed Python function `candidate(brackets: str)`.
- **R-IN-1** (assumption): the input contains only `(` and `)`.
- **R-RET-1** (guarantee): if every bracket has a partner, the function returns `True`.
- **R-RET-2** (guarantee): if some bracket has no partner, it returns `False`. Both RET items depend on R-IN-1.
- **R-SC-1..4** (scenario): the four doctest examples: `"("` gives False, `"()"` gives True, `"(()())"` gives True, `")(()"` gives False.
- **R-FR-1** (FRAME, guarantee): rule F-ZERO, which says `result` is false unless `outcome` is 0.

**Ambiguities flagged**
- **R-IN-1, other characters:** the frame includes strings with other characters, and the spec doesn't say what happens to them. Three readings: their result is unconstrained, they are ignored, or the string returns False.
- **R-IN-1, empty string:** it could be a valid input that returns True (no bracket is left unmatched), or outside the contract.
- **R-RET-2, "return True if":** it could mean "if and only if" (otherwise return False), or only a sufficient condition, leaving unmatched strings unconstrained.
- **R-RET-1/2, "has a corresponding … bracket":** four readings:
  1. Proper nesting.
  2. Equal numbers of `(` and `)`.
  3. Order matters but partners can be shared, so `"(()"` counts as matched.
  4. The literal word order, where a closing bracket's partner is another closing bracket.

**Contradictions** (each recorded as an ambiguity on both sides)
- The equal-count reading of R-RET-1 conflicts with **R-SC-4**: `")(()"` has two of each bracket but is expected to return False.
- The literal word-order reading of R-RET-1 conflicts with **R-SC-2** and **R-SC-3**, which are expected to return True.

One thing to watch: reading 3 (shared partners) fits all four examples, so the examples don't rule it out. It differs from proper nesting on inputs like `"(()"` or `"())"`.