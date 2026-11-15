I've written `formal/variant.yaml`. `fcp lint` reports clean, and the `fcp explain --set variant` output matches what I meant for each item.

**Items: 9 formal items**
- **`RV-FN-1`:** every call ends with outcome 0 or 2, so it returns a value rather than raising.
- **`RV-FN-2`:** when the call returns a bool, `result == (n != 4 && n != 6)`.
- **`RV-EX-1`, `RV-EX-2`, `RV-EX-3`:** each example is stated as a guarantee. For n = 4 or 6 the call returns False or any non-bool value; for n = 8 it returns True or any non-bool value.
- **`RV-EX-1-S`, `RV-EX-2-S`, `RV-EX-3-S`:** each example call can return the plain bool value it names.
- **Decisions:** all 11 flagged phrases are recorded. Every reading you assigned is used and stated in the notes. For R-IN-1, which you didn't assign, I took reading 1 (n is a non-negative integer).

**Requirements not formalized (4)**
- **R-IF-1** (a complete implementation, not a stub): this isn't a property of a single call. It's covered by `RV-FN-1`, `RV-FN-2` and the three example properties.
- **R-IF-2** (named `candidate`, takes one parameter `n`): the adapter's function section in `design.yaml` fixes this, so it isn't something the trace can show.
- **R-IN-1** (n is the given number): the 16-bit signal already limits n to 0–65,535, and `frame.md` leaves negative and non-integer arguments out of the trace. An assumption would constrain nothing.
- **R-FR-1:** this is the adapter's rule F-ZERO, which is part of every set automatically. It's covered by F-ZERO.

**Problems in the specification and in the assigned readings**
1. **The prompt contradicts its own examples.** Under any plain reading of "4 numbers", 4 and 6 can be written as such a sum, yet the examples say False. If the numbers must be distinct, 8 can't be (the smallest such sum is 10), yet the example says True.
2. **Your readings for R-FN-2 conflict with each other.** Reading "4 numbers" as non-negative integers makes every n qualify, including 4 and 6. "The examples take precedence" says they don't. To use both, I let the examples override only at the arguments they name: False at 4 and 6, True everywhere else. The note on `RV-FN-2` says this is my choice and not a fix to the spec. Without that override, the set would conflict with R-EX-1 and R-EX-2. The "four or more summands" reading has no effect once every n already qualifies.
3. **The R-EX-3 reading ("candidate(8)" is a contradiction) changes nothing in this set.** That contradiction only arises if the numbers must be distinct, and this set doesn't require that. Even if it did, the examples take precedence. So the example is formalized as written (True), and the formula comes out the same as under the other reading.
4. **The trace can't fully express "any value equal to True or False"** (R-FN-1 and the three "== True/False" readings). A return of the number 1 or 0 is recorded only as "returned something else" (outcome 2), with no value. The properties therefore accept any such return, including None, which is weaker than the readings. `RV-FN-2` can only check calls that return a real bool. The scenarios require the real bool so that an unreadable return can't satisfy them.