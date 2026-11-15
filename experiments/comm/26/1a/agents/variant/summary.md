I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and the `fcp explain` rendering of every item says what I intended. I couldn't test it against sample code because `fcp code` isn't available to agents, so I checked the subsequence and removal formulas by hand on the example and on a reordered result instead.

**Items: 6** (5 properties, 1 scenario), plus the frame rule F-EMPTY, which is added to every set automatically.
- **RV-IO-2:** every call returns a list without an error (`outcome == 0`).
- **RV-FN-1:** every value that occurs 2 or more times in `numbers` is absent from `result`.
- **RV-FN-2:** every value left in `result` occurs fewer than 2 times in `numbers`.
- **RV-FN-3:** `result` keeps the input's order, i.e. it is the input with some elements removed. I check this with eight named helper expressions (`m1`..`m8`) that match `result` against `numbers` in order. They are not extra state.
- **RV-EX-1-CALL** (property) and **RV-EX-1-COVER** (scenario): `candidate([1, 2, 3, 2, 4])` returns `[1, 3, 4]`. I added the property as well as the scenario because the example states what the call returns.

I recorded all 8 decisions with the readings you gave, and each affected item's note says it uses an imposed reading:
- **R-FN-1:** "K" means "more than once", "occur K time(s)" means "at least K", "time(s)" contradicts the example, and "remove" means in place.
- **R-FN-2:** the same readings of "K" and "at least K", and the rule only requires removal; it says nothing about keeping the others.
- **R-EX-1:** the example contradicts R-FN-1.

**Left unformalized (3):**
- **R-NF-1:** it is about the deliverable, not how a call behaves. RV-IO-2 checks the part you can observe.
- **R-IO-1:** the input format already guarantees it, since `numbers` can only carry a list of up to 8 integers from 0 to 255. There is nothing left to assume.
- **R-FR-1:** this is the frame rule F-EMPTY, which `frame.md` says need not be restated. I marked it as covered by F-EMPTY.

**Problems in the specification:**
1. **K is never defined.** It looks like a template value that was never filled in, and `candidate` has no parameter for it. The singular "time" allows K = 1, which turns the example into `[2, 2]`, and any K of 3 or more removes nothing. Only K = 2 matches the example, and the example doesn't say whether that means exactly 2 or at least 2.
2. **The in-place reading of "remove" can't be checked.** The trace records the argument as passed and the returned list, not the argument after the call. So only the returned list is constrained.
3. **Under your readings, R-FN-2 adds nothing beyond R-FN-1.** RV-FN-2 is logically the same as RV-FN-1. Nothing requires values that occur once to be kept, so returning `[]` satisfies every rule except on the example input. The example property is the only thing that forces 1, 3 and 4 to be kept there.
4. **Outcome 2 covers two different things.** It means both "returned another type" and "returned a list longer than 8 or with an element outside 0 to 255". So `outcome == 0` is slightly stronger than "returns a list of integers". This makes no difference here, because a correct result never has more elements than the input.
5. **The signature allows inputs the trace excludes.** `List[int]` permits negative integers and lists longer than 8, which `frame.md` leaves out of the trace.