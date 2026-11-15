I wrote `formal/agent_b.yaml`. `fcp lint` reports it clean, and the `fcp explain` read-back matches what I meant for every item. I did not run `fcp check`, so the contradictions described below come from reading the text and have not been confirmed by the tool.

**Items: 13 in total**
- **1 assumption:** RB-IN-1, that every element of `array` is non-negative. The interface encoding already guarantees this; I stated it anyway to record what the caller must provide.
- **8 properties:**
  - RB-RET-1: every call returns normally (`outcome == 0`).
  - RB-RET-2: a returned list is a permutation of the argument.
  - RB-ORD-1 / RB-ORD-2: the sort order rules.
  - RB-EX-1 to RB-EX-4: each example as a guarantee, i.e. given that input, the call returns that list.
- **4 scenarios:** RB-EX-1-S to RB-EX-4-S, saying each example's behaviour must be possible.
- **No ghost state.** Each call is independent and the function keeps nothing between calls, so the model is a set of definitions computed from the current argument. Every output (`outcome`, and the length, contents and order of `result`) is checked against it.
- **12 decisions** are recorded, one for each phrase `requirements.yaml` flags as ambiguous.

**Requirements left unformalized: 4**
- **R-FR-1:** already covered by the adapter's frame rule F-EMPTY, which is added to every set automatically.
- **R-API-1:** the function name and its one parameter are fixed in `design.yaml`; they aren't something the trace can check.
- **R-DEF-1:** a definition. It becomes the `psum` def and is covered by RB-ORD-1 and RB-ORD-2.
- **R-MUT-1** ("don't change the given array"): the trace records only the argument as passed and the returned list, so whether the function changes its argument can't be seen.

**Problems in the specification**
1. **The two sort-order rules contradict each other.** The prompt says sort ascending "if the sum … is odd or even" and descending "if the sum … is even or odd". Read literally, both conditions are always true. Following the rule to take the most literal reading and not repair the text, I took that reading for both (reading 2 of each), and the note on each item explains why. As a result:
   - RB-ORD-1 and RB-ORD-2 together with RB-RET-1 and RB-RET-2 can't all hold for any input with two different values.
   - Example 3 conflicts with RB-ORD-2, and example 4 conflicts with RB-ORD-1.
   - So the scenarios RB-EX-3-S and RB-EX-4-S should be unreachable, and every implementation will fail at least one requirement.
2. **The requirement text has already been corrected.** R-ORD-1 and R-ORD-2 say "odd" and "even" alone, which is presumably what was meant (and what the examples show), but the verbatim quotes don't say that. I followed the quotes.
3. **Sorting a copy versus sorting the argument.** "You will sort the given array" and "sort it" conflict with "don't change the given array". I took the copy reading. The trace can't tell the two apart, so this choice has no formal effect.
4. **"First index value, last index value"** could mean the values at those positions or the positions themselves. Under the literal order rules the sum never affects the result, so this ambiguity doesn't matter in my set.