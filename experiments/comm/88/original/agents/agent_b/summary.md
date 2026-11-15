I wrote `formal/agent_b.yaml` with 14 items. `fcp lint` reports clean, and the `fcp explain` rendering of every item matches what I intended. I did not run `fcp check`, so I haven't confirmed that the properties are consistent with each other or that the scenarios can be reached.

**Items (8 properties, 6 scenarios, no assumptions or don't-cares)**
- **How it's modelled:** `sort_array` keeps nothing between calls, so there is no ghost state. The reference model is a set of named expressions (defs) worked out from `array` on each call: the first value plus the last value, which order rule that sum selects, whether `result` has the same values with the same counts (a rearrangement), and whether it is non-decreasing or non-increasing. Both outputs are checked against these.
- **RB-RET-1:** every call returns a list (`outcome == 0`).
- **RB-RET-2:** if the call returns, `result` has the same length as `array` and every value appears the same number of times.
- **RB-ORD-1 / RB-ORD-2:** a returned list is non-decreasing when `array` is non-empty and `array[0] + array[last]` is odd, and non-increasing when it is even.
- **The four examples (R-EX-1 to R-EX-4):** each has a scenario showing the call can happen, plus a property requiring that exact output. The function always gives the same answer for the same input, so "f(x) => y" is a promise, not just something possible. All four examples agree with the order rules.
- **Two extra scenarios:** these require that a sorted result with equal neighbours is possible, which pins down "ascending" as non-decreasing (equal values allowed).
- **`decisions`:** recorded for all 11 flagged phrases, all taking reading 1.

**Requirements left unformalized (6)**
- **R-IF-1 and R-IF-2:** non-functional; they're about the deliverable and the function's name and parameter. RB-RET-1 checks the part that shows up in a call: a stub that returns None or raises fails it.
- **R-IN-1:** the trace can only hold lists of up to 8 values from 0 to 255, so this assumption is always true and stating it would add nothing.
- **R-RET-3 and R-NC-1:** `frame.md` says the trace doesn't record whether the result is the same object as `array`, or what `array` holds after the call. So neither "returns a copy" nor "don't change the given array" can be checked.
- **R-FR-1:** already in every set as frame item F-EMPTY, which `frame.md` says need not be restated.

**Problems in the specification**
- **It contradicts itself on changing the input.** "You will sort the given array" and "sort it" read as sorting the input in place, but the note says "don't change the given array". I took the reading where a copy is sorted. Since the trace can't see either way, this choice doesn't affect any check.
- **"Sum(first index value, last index value)" is unclear.** It could mean the values at those positions or the index numbers 0 and len−1. All four examples fit both readings, so they don't settle it. I took the values, as the requirement text says.
- **The empty array isn't covered by either rule.** `[]` has no first or last value. The example `[] => []` handles it, and in practice the result is empty either way.
- **Minor:** a one-element array always counts as "even" (the element is added to itself), so the descending rule applies to it. "Ascending" and "descending" have to mean equal values are allowed, because otherwise an array with repeated values would have no valid answer.