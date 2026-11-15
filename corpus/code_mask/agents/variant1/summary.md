I wrote `formal/variant1.yaml`. `fcp lint` reports no errors, and I read the `fcp explain` output back: each item says what I meant it to say.

**Items: 13 in total.** All IDs start with `V1-`, origin is `{kind: agent, role: formalizer, id: variant1}`, and every requirement is covered.
- **10 properties:**
  - R-ERR-1 is split into its three ValueError conditions: bad characters, digit count, and Luhn failure.
  - R-RET-1: a valid number returns a string.
  - R-MASK-1, R-LAST4-1, and R-QUARTER-1 have one property each.
  - R-SEP-1 has two: one for where spaces and hyphens stay, one for the result's length.
  - R-EX-1: the worked example, stated as a property.
- **3 scenarios:**
  - R-EX-1: the worked example must be possible.
  - R-IN-2: a valid number containing spaces and hyphens returns.
  - R-IN-2: a number that starts with a separator and has two separators side by side still returns. This one shows the reading I was told to use.
- **No ghost state.** Each item relates `number`, `masked` and `outcome` directly; the Luhn sum is written as a nested sum-and-count expression in `defs`.
- **Decisions:** reading 1 for both flagged phrases, as you instructed: R-IN-2 "between groups of digits" means separators may appear anywhere, and R-ERR-1 "digits" means the characters 0 to 9. The note of every affected item says so.

**Left unformalized (3, each with `covered_by`):**
- **R-SIG-1** is the function signature. `design.yaml` already defines it, and V1-RET-1 covers "returns a string".
- **R-IN-1** defines a card number as 12–19 digits. It has no behaviour of its own; V1-ERR-COUNT and the `valid` definition realize it.
- **R-FR-1** is the adapter's frame rule F-EMPTY, which is already added to every set.

**Problems in the specification:**
1. **Rules 2 and 4 contradict each other for valid 12–15 digit numbers.** Such a number must be returned with its last four digits visible. But four digits is more than a quarter of 12–15 digits, where the limit is at most 3. No output satisfies every rule, so only valid numbers with 16–19 digits can meet the spec. I kept the conflict as written and explained it in the notes of V1-QUARTER-1, V1-LAST4-1 and V1-RET-1.
2. **The Luhn check is never defined.** I used the standard mod-10 algorithm on the digits 0–9, ignoring every other character. I worked through the example (its Luhn sum is 30, so it passes). I wrote a randomized comparison against a reference Luhn implementation, but it was not run because running Python needed approval.
3. **"Show a digit" is vague.** I took it to mean any digit character that appears in the result.
4. **"Spaces" is taken literally as the space character only.** A tab or a no-break space therefore raises ValueError.
5. **Rule 1 says "if", not "only if".** That a valid number does not raise comes only from "It returns the card number…" (R-RET-1).