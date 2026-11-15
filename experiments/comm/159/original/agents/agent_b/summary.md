I've written `formal/agent_b.yaml`, and `fcp lint` reports no errors. I read the `fcp explain` output back and every item says what I intended. I also checked all four prompt examples against the model by hand, and each one gives the stated result.

**Items: 19 in total**
- **Model:** because `eat` keeps no state between calls (frame.md), the model is a set of named expressions recomputed from each call's arguments, not ghost state:
  - `ate` (carrots eaten in this call) is `remaining < need ? remaining : need`.
  - The expected first element is `number + ate`; the expected second is `remaining - ate`.
- **3 assumptions** (R-IN-1..3): each argument is at most 1000. The lower bound of 0 already holds because frame.md leaves negative arguments out of the trace.
- **12 properties:**
  - R-RET-1: every in-range call returns (`outcome == 0`).
  - R-RET-2 and R-RET-3: when a list is returned, `eaten` and `left` match the model.
  - R-EAT-1..5: the two cases, need ≤ remaining and remaining < need, each checked literally.
  - R-EX-1..4: each prompt example as a guarantee for that exact call.
- **4 scenarios** (R-EX-1..4): each example must also be possible.
- **13 decisions** recorded. Every flagged phrase took reading 1 except "array", which took reading 2. That's deliberate: frame.md gives a returned list and a returned tuple the same outcome code (0), so the check can't require a list only. A numpy-style array gets outcome 2 and is rejected.

**Not formalized (6), each with a reason**
- **R-FN-1** (write a complete function): this is about the deliverable, not about what a call returns. The part you can observe, that every call returns, is covered by RB-RET-1.
- **R-FN-2** (the name `eat` and the argument order): these are fixed by how design.yaml binds the function, not by anything in a call's inputs and outputs.
- **R-DEF-1/2/3:** these define the arguments. They're covered by the properties that use them.
- **R-FR-1:** this is the frame rule F-ZERO, which design.yaml adds to every set automatically; I marked it covered by F-ZERO, and lint accepted that.

**Problems in the specification**
- **"need":** the docstring says "the number of carrots that you need to eat" but also "eat more carrots to complete the day's meals". That could mean need is the whole day's total, but only the "extra carrots" reading matches the examples.
- **"will still be hungry":** a two-element return has no way to report this, so it's narrative only. R-EAT-5 also follows directly from R-EAT-3, so it adds nothing.
- **"array":** the prompt says "array", but the brackets and examples show a Python list. The trace encoding can't tell a list from a tuple anyway.
- **"Constrain":** it doesn't say what should happen outside 0..1000. I read it as a rule the caller must follow, so no behaviour is required there. The checker's test values include 1001, which only matters under the other two readings (reject the input, or apply the same rule anyway).
- **Boundary case:** the only example at the "not enough" boundary, eat(1, 10, 10), has remaining == need. Both readings of "not enough" give the same answer there, so the examples don't settle it.
- **Typos:** "thet" and "Constrain".