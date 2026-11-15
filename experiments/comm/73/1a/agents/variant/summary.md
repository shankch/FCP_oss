I wrote `formal/variant.yaml`. `fcp lint` reports no errors, and the `fcp explain` English for every item matches what I intended.

**Items: 12 formal items, plus 4 requirements left unformalized and 9 decisions**
- **5 properties:**
  - RV-CH-1: for a non-empty `arr`, the call returns an integer equal to the number of elements that differ from their mirrored element.
  - RV-DEF-1: if the call returns an integer, it is 0 exactly when the written-out digits of `arr` read the same in reverse.
  - RV-EX-1, RV-EX-2, RV-EX-3: one for each example, stated as written.
- **3 scenarios** (RV-EX-1-S, RV-EX-2-S, RV-EX-3-S): each example's result must be possible.
- **4 don't-cares:** `changes` and `outcome` are free for the empty array (R-IN-1) and free in every call (R-CH-2).
- **Decisions:** all 9 flagged phrases are recorded with the readings you gave. Each affected item's note (or reason) says which reading it uses.

The digit-reversal check needed a large but closed expression (`textpal`), and there is no ghost state. I checked it by hand on `[12, 21]` (true), `[12]` (false), `[12, 12]` (false) and `[1, 2, 3, 2, 1]` (true). A script that compares it against plain string reversal on many arrays is in the scratchpad, but it didn't run because the command needed approval.

**Left unformalized**
- **R-FN-1, R-FN-2:** non-functional. The adapter fixes the function name and signature, and a broken function shows up as outcome 1, which RV-CH-1 rules out.
- **R-DEF-2:** marked as covered by RV-CH-1. Under the readings you gave, a change has no visible effect beyond the count.
- **R-FR-1:** marked as covered by F-ZERO, the frame rule that is already part of every set.

**Problems in the specification under these readings** (I recorded all of them in the notes and fixed none):
1. **The count contradicts two examples.** Counting both elements of each differing pair gives 8 for R-EX-1 (not 4) and 2 for R-EX-2 (not 1). As a result, RV-EX-1-S and RV-EX-2-S can never happen alongside RV-CH-1.
2. **R-CH-2 contradicts R-CH-1 and the examples.** "The return value is unspecified" conflicts with R-CH-1 ("returns how many elements it changed") and with all three examples. The R-CH-2 don't-cares are overridden wherever those items apply.
3. **The textual reading of "palindromic" contradicts the mirror count.** They disagree on multi-digit elements: `[12, 21]` gives 2 by the count but 0 by the definition, and `[12]` and `[12, 12]` give 0 by the count but must be non-zero by the definition. The decomposer's claim in R-DEF-1 that every one-element array is palindromic is false under this reading. The declared test scope uses only elements 1–9, so these conflicts will show up only through the constants (10, 100) that the formula adds to the scope.
4. **Two behaviours can't be observed.** The in-place change to `arr` (R-CH-1) and the printed output (R-CH-2) are not on the interface, so I didn't formalize either.