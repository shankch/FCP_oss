I've written `formal/agent_a.yaml`. `fcp lint` reports no errors, and the `fcp explain` output matches what I intended for every item. Because I read each requirement literally, **the set contradicts itself on purpose**: the rule and the four examples say opposite things, and I didn't repair that.

**Items: 12 in total**, all carrying `req:`.
- **8 properties:**
  - `RA-RES-1`: the function returns True when the last character is a letter standing alone.
  - `RA-RES-2`: it returns False in every other case.
  - `RA-RES-3`: every call returns a bool (`outcome == 0`).
  - `RA-EX-1`…`RA-EX-4`: each example's input gives its stated result.
- **4 scenarios** (`RA-EX-1-S`…`RA-EX-4-S`): each example's behaviour must be possible. The function is deterministic, so I treated each example as a fixed result for that input, not just a possible one.
- **3 defs, no ghost state:** `last_alpha`, `last_alone`, `lone_letter`.
- **12 decisions**, one for each flagged phrase.

**Left unformalized:**
- **R-IF-1:** the function's name and argument are fixed by the `function` section of design.yaml. There's no behaviour to state.
- **R-IN-1:** the interface already guarantees that `txt` is a string; frame.md leaves non-string arguments out of the trace.
- **R-DEF-1:** a definition, not a behaviour. It's realized by the defs, and `covered_by` points to `RA-RES-1` and `RA-RES-2`.
- **R-FR-1:** already stated by frame rule `F-ZERO`, which is added to every set. `covered_by` points to `F-ZERO`.

**Readings I took:**
- Each rule and example as written.
- The last character is `txt[-1]`, even when it's a space.
- An alphabetical character is an ASCII letter (a–z, A–Z).
- Only the space character separates words.
- A word is a run of any non-space characters.
- **"A group of characters" means two or more characters.** This is the one non-default choice. If a single character counted as a word, every letter would belong to one and the main rule could never return True.

**Problems in the specification:**
1. **The four examples are exactly the opposite of the rule.** Under the rule, "apple pie" gives False, "apple pi e" gives True, and both "apple pi e " and "" give False. The examples say True, False, True, True. Either True and False are swapped in the rule, or the examples were flipped. As a result, the properties can't all hold together on those four inputs, and none of the scenarios can be reached alongside the rule. FCP's consistency check should report the conflicting pairs (`RA-RES-2` with EX-1, EX-3 and EX-4; `RA-RES-1` with EX-2).
2. **"A group of characters" makes the main rule meaningless if read as one or more characters.** Every letter would then be part of a word, so the function would never return True.
3. **"Alphabetical character" doesn't say whether letters above code 127 count.** Python's `str.isalpha()` accepts Latin-1 letters such as é, but FCP's `isalpha` covers ASCII only.