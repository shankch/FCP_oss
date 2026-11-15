I wrote `requirements_draft.yaml` with 11 atomic requirements. `fcp anchor` accepted every quote on the first run ("anchored 11 requirements") and wrote `requirements.yaml` with the line numbers filled in.

**Requirements**
- **R-IF-1** (non_functional): the deliverable is a Python function `will_it_fly(q, w)`.
- **R-RET-1 / R-RET-2** (guarantee): it returns `True` when q will fly and `False` otherwise. I split these because each can be checked on its own.
- **R-FLY-1 / 2 / 3** (definition): the rule for flying is "balanced and passes the weight test". Balanced means q is a palindromic list. The weight test compares the sum of q's elements with the maximum weight w.
- **R-EX-1 … R-EX-4** (scenario): the four examples, each with its explanatory comment.
- **R-FR-1** (FRAME, guarantee): F-ZERO, which `design.yaml` refers to.

**Ambiguities flagged**
- **R-FLY-3, "more than or less than or equal"** has three readings:
  1. sum ≤ w: "more than or" is a slip. This is the only reading that fits all four examples.
  2. sum ≥ w.
  3. Taken literally, every sum passes, so only balance matters.
- **R-FLY-1, "will fly if"**: either the two conditions together are exactly what makes q fly, or they are only enough to make it fly, which leaves unbalanced lists undecided.
- **R-FLY-2, "palindromic list"**: it's unclear whether the empty list `[]` counts as balanced.

**Contradiction flagged** (recorded on both requirements)
- **R-FLY-3 vs R-EX-2**: the rule says a sum "more than" w can still fly. The example `will_it_fly([3, 2, 3], 1) ➞ False` says the opposite, because "3+2+3 is more than the maximum possible weight". Both requirements list the two ways to resolve it: either the example wins or the rule wins.