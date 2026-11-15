I wrote `formal/variant.yaml`. It lints clean, and the `fcp explain` output says what I intended for every item. However, **the set contradicts itself on the four example calls**, because of the readings you assigned.

**What's in it:** 12 formal items: 6 properties, 1 scenario, 4 don't-cares, plus the frame rule F-ZERO that `fcp explain` adds to every set. There are 11 `decisions` entries, all reading 2, as you specified, and every affected item says in its note that the reading was imposed.
- **R-RET-1** has two properties, one for each half of "True exactly when". Both use simple definitions over the input string, with no extra internal state. The R-RET-1 readings count only "(" and ")" (other characters are skipped), require at least as many ")" as "(", and require every ")" to have an earlier unmatched "(". Together those mean the string is correctly balanced. Because of the inversion reading, the function returns True when the string is *not* balanced and False when it is. Non-empty strings only.
- **R-EX-1 to R-EX-4** are properties, not scenarios, because each reading fixes what the call returns: "(" → False, "()" → True, "(()())" → True, ")(()" → False.
- **R-IN-1** has no input assumption, because other characters may occur. Instead there is a scenario showing that a call containing another character can still return True or False. Two don't-cares leave the empty string's return value and outcome unconstrained.
- **R-FN-2** has two don't-cares for the empty string, which is the only input the docstring says nothing about under these readings. It adds no obligation of its own: everywhere else the R-RET-1 and example properties already require a True/False return.

**Left unformalized (2):**
- **R-FN-1**: just the function's name and signature. `design.yaml` already defines that, and it isn't something a trace can check.
- **R-FR-1**: covered by the built-in frame rule F-ZERO (`covered_by: [F-ZERO]`).

**Problems:**
1. **The assigned readings contradict each other.** R-RET-1 reading 2 (the sentence is inverted) gives "(" → True, "()" → False, "(()())" → False, ")(()" → True. Reading 2 of R-EX-1 to R-EX-4 says the opposite for each call. So each example property directly conflicts with one of the R-RET-1 properties. No implementation can satisfy the set, and any consistency check will flag those four calls. I kept the conflict visible and recorded it in each note rather than fixing it, as the rules require.
2. **The prompt itself contradicts itself.** All four docstring examples are the exact negation of normal bracket matching, while the sentence and the function name describe normal matching.
3. **Strings with no brackets:** "the empty string is unconstrained" is applied literally, to the length-0 string only. A non-empty string with no brackets, such as "a", still falls under R-RET-1. After skipping it counts as balanced, so it must return False.
4. **Counting plus whole-string correctness is just normal balanced brackets**, so the counting reading changes nothing once the whole-string reading is taken.