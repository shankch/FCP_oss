I've finished `formal/variant.yaml`. Lint reports no errors, and the `fcp explain` output matches what I meant each item to say. Under your readings the specification contradicts itself, so the set does too: no implementation can pass it.

**Items (3, plus the frame rule F-ZERO, which is added to every set automatically):**
- **RV-CAR-1** (assumption, R-CAR-1): `n >= 1`. Calls with n = 0 are outside the request.
- **RV-FN-1** (property, R-FN-1): `outcome == 0 && result == n * n`. With n cars each way, every left-to-right car starting to the left of every right-to-left car, and cars passing through each other, every pair meets exactly once. The largest value, 1,046,529, fits in `result`.
- **RV-CAR-4** (property, R-CAR-4): `result == 0`. If every car has the same constant velocity, the gaps between cars never change. The sets start far apart, so no car ever meets another and there are no collisions.

**Not formalized (6), each with a reason:**
- **R-FN-2**: the function's name and signature are already set by the `function` section of `design.yaml`.
- **R-RD-1, R-CAR-2, R-CAR-3, R-COL-1**: these describe the car model, which can't be observed in the trace. They feed into RV-FN-1 and RV-CAR-4, which they list under `covered_by`. R-CAR-3 is labelled an assumption, but it is about where the cars start, not about the argument n.
- **R-FR-1**: covered by F-ZERO, which `frame.md` says need not be restated.

The notes on all these entries name the readings you gave and say they were used as instructed. All 9 flagged phrases are recorded under `decisions`.

**Problems in the specification:**
1. **The readings contradict each other.** Reading "the same speed" as the same velocity contradicts the two sets driving in opposite directions. I kept both sides rather than fix that: RV-FN-1 requires n·n and RV-CAR-4 requires 0. For every n ≥ 1 these can't both hold, so any implementation fails one of them, and FCP's consistency check should report the pair as conflicting. This is deliberate; leaving R-CAR-4 out would have quietly repaired the text.
2. **The docstring stops mid-sentence.** It never says what the function returns or when two cars collide. Returning the collision count, and defining a collision as a left-to-right car meeting a right-to-left car, come only from your instructions, not from the text.
3. **n = 0 is excluded only by your reading of R-CAR-1.** The text itself allows it.