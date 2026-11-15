I've written `formal/agent_b.yaml`. `fcp lint` reports it clean, and the `fcp explain` read-back says what I meant for every item.

**Items: 13 formal items.**
- 10 properties:
  - RB-BASE-1..4: the four base values.
  - RB-REC-1: the recurrence, checked against a ghost model (below).
  - RB-REC-5/6/7: the values every sign choice can reach for n = 5..7, so a single call there is checked.
  - RB-FUN-1: every call returns, i.e. `outcome != 1`.
  - RB-NF-1: the same check, for "efficiently"; the only part of it the trace shows.
- 3 scenarios: RB-EX-1..3 for the docstring examples.
- 9 decisions, one for each flagged phrase.

**The model.** I read '+/-' literally (reading 4): each sign may be + or − separately for every n. The recurrence then ties fib4(n) to the function's own answers for n−1..n−4. Calls are independent, so the model remembers the last value returned for each index 4..126 (ghosts `f4`..`f126`) and uses 0, 0, 2, 0 for indices 0..3. When all four predecessors are known, the result must equal one of the 8 sign combinations. Outcome 2 is allowed only for a value that `result` can't carry (negative, or 2^118 or more).

The relational check has two limits. It only fires when the predecessors were called earlier in the same trace. It also stops after a negative element, because the adapter records that as outcome 2 with no value.

I couldn't use a fixed-table model: precomputing exact 118-bit tables would need Python, which needs approval here. Writing the recurrence as chained `defs` also blows up exponentially (index 30 alone took 97 s to lint). I chose reading 4 because it adds nothing the text doesn't say.

**Left unformalized (5):**
- **R-TASK-1:** it's about the form of the deliverable, not about calls.
- **R-IF-1:** the interface already gives one int argument, 0..127. Under reading 1 nothing is said about negative n, and negative n never appears in the trace.
- **R-NF-2 (no recursion):** this is a property of the source code; a trace can't show it.
- **R-DEF-1:** covered by the base and recurrence items.
- **R-FR-1:** covered by the existing frame rule F-ZERO.

**Problems in the specification:**
1. **The examples contradict the definition.** From the base values, fib4(5) can only be −4, 0 or 4 under any choice of signs, so the example fib4(5) = 2 is impossible. With all '+' the sequence gives 4, 8, 14 for n = 5, 6, 7.
2. **The other two examples depend on the reading.** fib4(6) = 4 and fib4(7) = 6 are reachable only if the signs vary per n (0, 0, 2, 0, 2, 4, 4, 6). No fixed choice of signs gives both. I kept all three examples literal, so FCP will report RB-EX-1 as unreachable against RB-REC-5 instead of the conflict being smoothed over.
3. **'+/-' leaves the value undetermined**, so the determinacy check will flag outputs as free.
4. **Negative values can't be told apart from bad returns.** Most sign choices produce negative elements, which the adapter records as outcome 2. That's the same code as returning a non-integer.

The scratch copy of the bundle I tested with is in the session scratchpad and isn't part of the workspace.