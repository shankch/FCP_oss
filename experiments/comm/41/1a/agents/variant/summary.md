I've written `formal/variant.yaml`. Lint reports clean, and the English rendering from `fcp explain` says what I intended.

**Items: 2 formal items, plus 12 decisions.**
- **RV-OUT-1-RET** (R-OUT-1) leaves `collisions` deliberately unconstrained for every call.
- **RV-OUT-1-END** (R-OUT-1) leaves `outcome` deliberately unconstrained for every call.

Both follow from the instructed reading that "outputs" means "prints; the return value is unspecified". Printed text isn't recorded in the trace, so nothing observable is left to pin down. A call that prints and returns `None` (outcome 2) conforms. I also left outcome 1 (raised or didn't finish) open: from the trace alone, a call that printed and then raised looks the same as one that never printed.

The interface's built-in rule F-ZERO (`collisions` is 0 unless `outcome` is 0) is added to the set automatically, and R-FR-1 points to it.

**Unformalized: 11 requirements.**
- **R-IF-1** is about the form of the deliverable (function name and parameter), not behaviour, and `design.yaml` already fixes it.
- **R-ENV-1** gets no assumption: under the instructed reading, n can be any int, so there's no limit to place on the input. The trace can't carry negative n either, since `n` is a 10-bit unsigned input.
- **R-RD-1, R-CAR-1, R-CAR-2, R-POS-1, R-SPD-1, R-COL-1, R-COL-2 and R-OUT-2** only shape the number of collisions. Under the print reading that number is printed, not returned, so it never appears in the trace. Writing `collisions == n*n` would contradict "the return value is unspecified".
- **R-FR-1** is covered by F-ZERO, as above.

Each forced reading is stated in the `note` or `reason` of every entry it affects.

**Problems in the specification.** Under the instructed readings it contradicts itself, so the n*n value can't be checked anywhere:
- **Car counts (R-CAR-2):** "exactly n cars" contradicts "a different set" meaning a set of a different size (n vs 2*n). This holds for every n > 0.
- **Counting collisions (R-COL-1, R-COL-2):** reading meetings as not counted makes the count 0. That contradicts the definition of a collision, and n*n.
- **Starting side (R-POS-1):** the text gives only the distance between the sets, not which side each starts on. So the count is either n*n or 0, which contradicts "a single number determined by n".
- **Separately ambiguous:** the count "2*n or n", "outputs" (print vs return), and the result for negative n.

The result is that this set constrains nothing on the trace. Any implementation passes it, including one that just prints and returns `None`.