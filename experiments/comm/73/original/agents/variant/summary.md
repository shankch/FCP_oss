I wrote `formal/variant.yaml`. `fcp lint` reports no errors, and the `fcp explain` output matches what I intended for each item. I did not run `fcp check`; you asked only for lint and explain.

**Items (10):**
- **3 properties (RV-EX-1..3):** each example call must return a value equal to the stated answer. Either the call returns that integer (outcome 0), or it returns a non-integer value (outcome 2). Raising an exception fails.
- **3 scenarios (RV-EX-1-S..3-S):** each example call must be possible and able to end as the example states.
- **4 don't-cares:**
  - R-IN-1: how a call on `[]` ends, and what it returns, are left free.
  - R-RES-1: how the call ends and what it returns are left free on every other non-empty array, except the three examples.

The note of every affected item says that the reading was the one you gave, not the more natural one. `decisions` records reading 2 for all five phrases you set. For R-DEF-2 "any other element", which you didn't set, I took reading 1: any integer value.

**Left unformalized (4):**
- **R-IF-1:** the function's name and parameter are not something a call trace can show. The function binding in design.yaml covers them.
- **R-DEF-1, R-DEF-2:** these definitions only feed R-RES-1. Under your reading of "find", R-RES-1's result is only printed, and printed output is not in the trace.
- **R-FR-1:** covered by the frame rule F-ZERO, which is added to every set automatically.

**Problems in the specification under these readings:**
1. **"Find" means print, but the examples test the return value.** A function that only prints returns `None`, so `smallest_change(...) == 4` would fail. I formalized the examples on the return value, as their text says.
2. **Textual palindromes conflict with example 1.** If an element can be changed to any integer, `[1,2,3,5,4,7,9,6]` needs only 1 change, not 4. Changing the first element to 697453 gives 6974532354796, which reads the same reversed. This is not a formal conflict, because R-RES-1 constrains nothing in the trace. I reported it rather than fixing it.
3. **The example properties are looser than intended.** The trace records any non-integer return, such as 4.0, as outcome 2 without its value. Allowing 4.0 therefore also lets through a string or `None` on the example calls.
4. **"Any sequence type" cannot be checked.** The trace only ever passes lists, so it can't show whether tuples or `array.array` are accepted.
5. **Overall, this set is very weak.** The three example calls are the only outputs it constrains; everything else is left free.