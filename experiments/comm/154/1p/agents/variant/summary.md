I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and I read back the `fcp explain` output to check that each item says what I meant. I couldn't run it against real code: `fcp code` is not available to agents. Instead I checked the matching rule by hand on all six examples and on a reversed case ("cba" against "abc").

**Items (11 in total, plus the two built-in frame rules):**
- **RV-RET-1:** on the six example calls, the call must return something (`outcome != 1`).
- **RV-RET-1-DC:** on every other call, how the call ends (`outcome`) is left free.
- **RV-RULE-1 and RV-RULE-2:** when the call returns a bool (`outcome == 0`), it returns True exactly when b matches a. The match test is shared and works like this:
  - b must not be empty.
  - Some rotation of b, or some rotation of the reverse of b, must appear as a contiguous substring of a.
  - Letters are compared ignoring case.
- **RV-EX-1 to RV-EX-6:** one scenario per example.
- **Decisions:** all 8 flagged phrases are recorded with reading 2, as you instructed. Every affected item's note says so.

**Left unformalized:** only R-SIG-1, the function's name and argument order. That is set by the `function` section of `design.yaml`, not by anything in the trace. R-FR-1 and R-FR-2 are already covered by the frame rules F-ZERO and F-CODE.

**Choices worth checking:**
- **Ignoring case:** I used Python's `str.lower` over all of Latin-1, not just A–Z. So À matches à, while ß, µ and ÿ match only themselves. Code that compares with `upper()` or `casefold()` turns "ß" into "SS" or "ss", so it can give a different answer on such calls.
- **Rules apply only to bool returns:** under your readings, a call outside the examples may raise. A non-bool return also counts as long as it is truthy or falsy as expected. So I didn't read "returns True" as forbidding either case.
- **Defs used inside quantifiers:** I wrote the character comparisons as small defs that use the quantifier variables. I confirmed with lint that it resolves those names where the def is used: an unbound name is rejected, while the quantifier variables are accepted.

**Problems in the specification:**
1. **No rule is stated.** The six examples fit "some rotation of b" and "some rotation of b or of its reverse" equally well. They also say nothing about an empty b, upper case, or calls outside the examples.
2. **Truthy returns can't be checked.** Under the "any truthy/falsy value" reading, a non-bool return is recorded only as `outcome 2`, with no value. So whether it was truthy or falsy can't be observed. RV-RET-1 and the True scenarios accept any non-bool return, including a wrong falsy one like `0`.
3. **R-RULE-1 and R-RULE-2 become the same rule.** The readings say "True exactly when" and "False exactly when", which I took to mean both directions. That makes RV-RULE-1 and RV-RULE-2 the same relation stated twice.
4. **`explain` drops the parentheses in RV-RULE-2.** It shows the item as `outcome == 0 -> !result <-> !match`, which can be misread. The trigger and the condition are separate arguments, so what the item means is correct.