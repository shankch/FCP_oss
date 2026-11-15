I've written `formal/agent_b.yaml`. Lint reports no errors, and the English rendering from `fcp explain` matches what I intended for every item. I did not run the conflict search (`fcp check`).

**Items: 14** (7 properties, 7 scenarios). The design's frame rule F-ZERO is added automatically and is not counted.

**How it's built:** the function keeps no state between calls, so there is no ghost state. The model is a set of named expressions:
- `pal`: the text reads the same backwards, comparing characters exactly.
- `iso`: no letter appears twice, ignoring case.
- `expect = iso || pal`.

Both outputs are checked against `expect`:
- `outcome` must always be 0, meaning the call returned True or False.
- The function must return True exactly when `expect` holds, and False otherwise.

Each of the four docstring examples is both a property (that call always gives that answer) and a scenario (that answer must be possible). There are also scenarios for the three cases of the "or" reading: an isogram that isn't a palindrome, a palindrome that isn't an isogram, and neither.

**Readings I chose** (recorded under `decisions`):
- `text: str`: reading 1, a type hint that only constrains the caller.
- Palindrome: reading 1, exact comparison, so case and spaces count.
- Isogram: reading 2, no letter repeated ignoring case; spaces and other non-letters may repeat. "Letter" means an ASCII letter, following `frame.md`, so characters like 'é' count as non-letters.
- Isogram/Palindrome (R-CHK-1 and R-CHK-2): reading 1, the slash read literally as "or".
- The examples (R-EX-2, R-EX-3, R-EX-4): reading 1, each example is taken as written.

**Requirements left unformalized (6):**
- **R-IF-1:** only names the function and its parameter; `design.yaml` already binds the argument to the input.
- **R-IF-2:** a delivery requirement, not something a call can show.
- **R-ENV-1:** the inputs can only ever be strings, so the assumption holds automatically and nothing in the trace can state or break it.
- **R-DEF-1 and R-DEF-2:** definitions, realized by `pal` and `iso` and linked with `covered_by` to the properties that use them.
- **R-FR-1:** already the frame rule F-ZERO, which `frame.md` says need not be restated.

**Problems in the specification:**
1. **The rule and one example contradict each other.** Read literally as "isogram or palindrome", the docstring makes `candidate('zbcd')` return True, because no letter in 'zbcd' repeats. The example says False. As the rules require, I left this unrepaired: RB-CHK-1 and RB-EX-4 can't both hold for that call, and scenario RB-EX-4-S should come out unreachable.
2. **The "and" and "isogram only" readings would contradict two other examples instead.** 'aba' and 'aaaaa' repeat a letter but are expected to return True. Only "palindrome only" fits all four examples, which suggests "Isogram" is a mislabel. Picking it would repair the spec, so I didn't.
3. **The prompt doesn't define the details.** It doesn't say whether case, spaces or punctuation count for either test, and "Isogram" has several common meanings. My choices are in the item notes.