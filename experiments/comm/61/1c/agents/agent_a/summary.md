I wrote `formal/agent_a.yaml` with 11 items. Lint is clean, and the English rendering from `fcp explain` matches what I intended. The spec contradicts itself, and that conflict is left in the file on purpose, so no implementation can satisfy the whole set.

**Items**
- **1 assumption:** RA-IN-1 says the argument contains only `(` and `)`. The empty string counts as valid.
- **6 properties:**
  - RA-FN-2: every valid argument gets a True or False back.
  - RA-RET-1: the docstring sentence.
  - RA-EX-1 to RA-EX-4: each example, written as "this call returns this value".
- **4 scenarios:** RA-EX-1-S to RA-EX-4-S say each example call must be possible.
- **11 decisions:** reading 1 for every flagged phrase.
- RA-FN-2 and RA-RET-1 also check validity in their own conditions, so they still hold call by call if an earlier call broke the precondition.

**Readings taken (the most literal one each time)**
- "return True if" only says when True is required; when the condition fails, the result is left open.
- "a corresponding closing bracket" means each `(` is paired with its own later `)`, with pairs nested properly.
- "every opening bracket" puts no constraint on extra `)`.
- The docstring sentence and the four examples are each taken exactly as written.

**Not formalized**
- **R-FN-1:** it only defines the name and the one string argument, which the interface in `design.yaml` already covers. Nothing behavioural to state.
- **R-FR-1:** this is frame rule F-ZERO, which is added to every set automatically. I marked it `covered_by: [F-ZERO]`.

**Problems in the specification**
1. **The sentence and the examples contradict each other.** All four examples return the opposite of normal bracket matching, while the sentence asks for normal matching:
   - `"()"` and `"(()())"` are correctly matched, so RA-RET-1 requires True, but RA-EX-2 and RA-EX-3 require False. This clash holds under every reading of the sentence.
   - Under the usual "True if and only if" reading, `"("` and `")(()"` would clash too. Under the readings I took, the sentence says nothing about those two strings, so they don't.
   - I kept both sides instead of choosing one, and explained this in the notes on each item.
2. **The function name** (correct_bracketing) agrees with the sentence and disagrees with the examples.
3. **The docstring never says when False is returned** or what happens to other characters, so a lot of behaviour is left open.

`fcp check` is refused for agents, so I couldn't run the consistency analysis to confirm the conflicts. Instead I worked out the bracket-matching definition by hand on all four examples and the empty string. It gives true for `"()"` and `"(()())"`, false for `"("` and `")(()"`, and true for `""`. That means the conflicts should be exactly RA-RET-1 against RA-EX-2 and RA-EX-3.