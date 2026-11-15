I wrote `formal/agent_b.yaml` with 15 items: 2 assumptions, 10 properties and 3 scenarios. `fcp lint` reports no errors, and the `fcp explain` output matches what I intended for every item. I couldn't run the deeper checks for contradictions or reachability, because `fcp check` is not available to an agent.

**How it's modelled:** the function keeps no state between calls, so there's no ghost state to track. Instead, the reference model is a set of named expressions computed from the current arguments: the range `lo = min(a,b)` to `hi = max(a,b)`, which parities appear in the result, and whether every digit of each parity in the range is listed. Both `outcome` and `result` are checked against these. The list properties apply only when the arguments are positive and the call returned a list, so a call that raises fails only RB-OUT-1.

**Readings taken (recorded under `decisions`):**
- **Positive integers:** reading 1. "Given two positive integers" is an obligation on the caller, written as assumptions `a >= 1` and `b >= 1`.
- **Digits:** reading 1, the integers 0 to 9.
- **Between a and b:** inclusive (reading 1) and either argument order (reading 1).
- **Odd or even:** reading 5. Each call may choose its parity, and nothing links the parity of one call to another. "The selected parity" is taken as the parity of the returned elements; an empty list is allowed only when one parity has no digit in the range.
- **Descending or ascending order:** reading 6, either order on any call.
- **The three examples:** binding (reading 1). Each is a property, plus a scenario saying that answer must be possible. Under the per-call readings they pin even, ascending only on the three example calls, so they don't contradict anything.

**Left unformalized:**
- **R-IF-1:** it is non-functional. The function name and parameters are fixed by the adapter, not by anything in the trace.
- **R-FR-1:** marked `covered_by: [F-EMPTY]`. That frame rule is already added to every set, and frame.md says it need not be restated.

**Problems in the specification:**
1. **The answer for most calls isn't fixed.** "Odd or even" and "descending or ascending" offer choices, but the text never says how to choose, while all three examples show even and ascending. Taken literally, a call like `(3, 9)` has four valid answers: `[4,6,8]`, `[8,6,4]`, `[3,5,7,9]` and `[9,7,5,3]`. Only the example calls are pinned. This looks like an "even, ascending" spec that was loosened in the prose but not in the examples.
2. **"Digits" is misleading.** It means the integers 0 to 9 in the range, not the digits written in the numbers. Only `generate_integers(10, 14) => []` shows this.
3. **Some meanings come only from the examples:** that "between" includes the ends and ignores argument order, and that ascending order applies even when `a > b` (`(8, 2)`).
4. **No behaviour is given for `a = 0` or `b = 0`.** The adapter's inputs include 0, but the prompt only promises positive arguments.