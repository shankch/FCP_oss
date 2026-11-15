I wrote `formal/agent_b.yaml`. `fcp lint` reports it clean, and the `fcp explain` output reads as I intended for every item. I also wrote a small Python brute-force check of the formulas, but running it needed approval and wasn't run. I checked the cases by hand instead (below).

**Items: 8 in total (7 properties, 1 scenario)**
- **RB-IF-3:** every call returns a list (`outcome == 0`).
- **RB-RM-1:** a value that occurs two or more times in `numbers` does not appear in `result`.
- **RB-RM-2:** a value that occurs exactly once appears exactly once in `result`.
- **RB-RM-3-MEMBER / RB-RM-3-LEN:** every element of `result` comes from `numbers`, and `result` is no longer than `numbers`.
- **RB-ORD-1:** the elements of `result` are in the order of their first occurrence in `numbers`.
- **RB-EX-1 (scenario):** the docstring example, `[1,2,3,2,4]` → `[1,2,3,4]`.

**Approach:** The function keeps no state between calls, so ghost state wouldn't add anything. Instead, the model is computed from `numbers` in the same call: how many times each value occurs. Each output is checked against that model. Items RB-RM-1 to RB-ORD-1 only apply when the call returns normally, so the duty to return at all stays with R-IF-3 alone.

By hand: the RM and ORD items together allow exactly one result, `[x for x in numbers if numbers.count(x) == 1]`. RB-ORD-1 on its own rejects `[1,3,2,4]` for `[1,2,3,2,4]`.

**Left unformalized (5, each with a reason):**
- **R-FR-1:** marked `covered_by: [F-EMPTY]`, because the frame rule is added to every set automatically.
- **R-IF-1:** an instruction about the deliverable, not about how a call behaves.
- **R-IF-2:** the function's name and argument are fixed by the adapter's `function` section; there's nothing to check in the trace.
- **R-IN-1:** true by how the interface encodes inputs, so an assumption would say nothing.
- **R-DEF-1:** a definition, built into the occurrence counts of RB-RM-1 and RB-RM-2 (`covered_by` those).

**Readings recorded under `decisions`:** R-IF-3 1, R-DEF-1 1, R-RM-1 1, R-RM-3 1, R-ORD-1 1, R-EX-1 2.

**Problems in the specification**
1. **The prose contradicts the example.** Read literally, "remove all elements that occur more than once" turns `[1,2,3,2,4]` into `[1,3,4]`, but the doctest shows `[1,2,3,4]`. The function's name points the same way as the example. Following the "most literal reading, don't repair" rule, I formalized the prose literally (RB-RM-1). I kept the example as scenario RB-EX-1, which therefore can never happen alongside RB-RM-1 and RB-IF-3. FCP's consistency check should flag this conflict, and both item notes explain it. The spec author needs to say whether the prose or the example is right.
2. **Two ambiguities make no difference to my items:**
   - Under my reading of RM-1 no repeated value is kept, so the three readings of R-ORD-1 give the same result for any behaviour that meets RB-RM-1.
   - Whether the list is changed in place or a new one is returned (R-RM-3) can't be seen: the trace doesn't record the argument after the call.
3. **The adapter covers less than the prompt.** The prompt allows any integers. The adapter only covers lists of up to 8 numbers from 0 to 255, so negative numbers, large values and longer lists are never checked.