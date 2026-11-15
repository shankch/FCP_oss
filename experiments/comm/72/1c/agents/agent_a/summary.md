I wrote `formal/agent_a.yaml`. `fcp lint` reports it clean, and the `fcp explain` output matches what I intended for each item.

**Items: 11** (3 properties and 8 scenarios). The frame rule F-ZERO is added to the set automatically.
- **Definitions (macros, no ghost state):** `balanced` (q reads the same both ways; the empty list counts), `total` (the sum of q), `light` (`total <= w`) and `fly` (`balanced && light`).
- **Properties:** RA-RET-1 says that if q flies, the call returns True. RA-RET-2 says an unbalanced q returns False. RA-RET-3 says a q whose sum is over w returns False. Each one also requires `outcome == 0`, so every call must return a bool.
- **Scenarios:** RA-EX-1 to RA-EX-4 take each example's stated result as written. RA-WHY-1 to RA-WHY-4 take each comment as explaining the rule's result. Each also checks the comment's own facts, for example `total < w && !balanced` for `[1, 2], 5`.
- **Decisions:** all 13 flagged phrases are recorded, and I took reading 1 for each. That means: the empty list is balanced, "will fly if" means "if and only if", the rule is read as stated, the examples as written, and the comments as explaining the rule.

**Requirements left unformalized:**
- **R-API-1** (function name and parameter order): this is a fact about the code's signature, not about the calls in the trace.
- **R-IN-1 and R-IN-2** (q can be summed, w is a number): the input encoding already guarantees these. The trace only contains integers 0..255 in q and 0..2047 for w, so there is nothing left to assume.
- **R-DEF-1, R-DEF-2 and R-DEF-3** are definitions. They are `covered_by` the properties and scenarios that use the macros.
- **R-FR-1** is `covered_by` F-ZERO, which `frame.md` says need not be restated.

**Problems in the specification:**
1. **Every example contradicts the rule.** All four examples give the opposite of what the stated rule returns: `[1,2],5 ➞ True`, `[3,2,3],1 ➞ True`, `[3,2,3],9 ➞ False`, `[3],5 ➞ False`. In each case the example's own comment explains the rule's answer, not the one written. I didn't fix this. RA-EX-1 to RA-EX-4 contradict the RA-RET properties and the RA-WHY scenarios, so the consistency check should report all four example scenarios as unreachable.
2. **Empty list:** the spec doesn't say whether `[]` is balanced. Under my reading, `will_it_fly([], w)` returns True for every w.
3. **"will fly if"** reads as a one-way condition. The "False otherwise" requirements (R-RET-2 and R-RET-3) only make sense if it means "if and only if", so that is the reading I took.
4. **The comments say "less than" but the rule says "less than or equal".** These don't conflict, but no example tests the case where the sum exactly equals w.