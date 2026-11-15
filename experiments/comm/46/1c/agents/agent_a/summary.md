I've written `formal/agent_a.yaml`. `fcp lint` reports clean, and the `fcp explain` output reads back as intended for every item.

**Items: 10 formal items.**
- **Properties (7):**
  - RA-BASE-1 to RA-BASE-4: each base call (n = 0 to 3) returns the stated integer, so `outcome == 0` as well as the right `result`.
  - RA-REC-1: for n ≥ 4, `result` is the sum of the four previous values.
  - RA-FN-1-INT: every call returns an int that fits (`outcome == 0`).
  - RA-FN-1-VAL: `result == FIB4[n]`.
- **Scenarios (3):** RA-EX-1 to RA-EX-3, one for each docstring example.
- **No assumptions and no don't-cares.** Every n from 0 to 63 has a fixed answer, and fib4(63) = 132,419,948,094,134,672 fits the 57-bit `result`.

`FIB4` is a table of the 64 values, computed from the base values and the recurrence. Python, `bc` and bash arithmetic were all blocked here, so I worked the values out by hand two independent ways, and every entry matched. RA-REC-1 is written as a sum of table entries and RA-FN-1-VAL reads the table directly, so a wrong entry would show up as a conflict between the two. I did not run `fcp check` to confirm this, because it may reach outside the workspace.

**Left unformalized (7):**
- **R-TASK-1, R-IF-1:** the deliverable, the function name and the signature are facts about the source code or the interface. No sequence of calls can show them.
- **R-ENV-1:** I took reading 1 (n may be any int). The encoding already makes n an integer from 0 to 63, so there is nothing left to assume.
- **R-DEF-1:** covered by RA-BASE-1 to RA-BASE-4, RA-REC-1 and `FIB4`.
- **R-NF-1 ("efficiently", reading 2: linear time, any memory) and R-NF-2 ("recursion", reading 2: no recursion of any kind):** running time and code structure don't show in a trace of calls. A call that never finishes shows as outcome 1, and RA-FN-1-INT already rules that out.
- **R-FR-1:** covered by the frame rule F-ZERO, which frame.md says need not be restated.

**Problems in the specification:**
1. **The examples contradict the definition.** The docstring shows fib4(5) → 0, fib4(6) → 0 and fib4(7) → 2. The base values and the recurrence give 4, 8 and 14. The examples can't be reconciled with the recurrence at n = 5 or n = 6. (2 is what the recurrence gives at n = 7 if the two earlier example values were true.)
   - I took reading 1 everywhere: the definition wins, since the prompt says the sequence is "defined as follows".
   - So the scenarios check fib4(5) = 4, fib4(6) = 8 and fib4(7) = 14, not the printed values. Each note says this and explains why the printed value would be unreachable.
   - Under the other reading, RA-REC-1 would fail at n = 5 and n = 6.
2. **Negative n is never addressed.** The trace can't carry it, so it makes no difference to the checks.
3. **"Efficiently" is vague.** The prompt gives no time or memory bound.
4. **Typos.** "Fibbonacci sequnece" is misspelled, which has no effect on meaning.

All 10 flagged ambiguous phrases are recorded under `decisions`.