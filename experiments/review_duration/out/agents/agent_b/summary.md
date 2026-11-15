I wrote `formal/agent_b.yaml`. `fcp lint` reports it clean, and I read through the `fcp explain` output: each item says what I meant it to say. I tried to cross-check the parsing model against a separate Python parser on many test strings, but that command needed approval this session couldn't give. The model has been checked by hand only (by tracing strings like `"24h"`, `"0100s"`, `"1h0m"`), not by running it.

**Items: 19 formal items, plus 3 entries under `unformalized`.**
- **14 properties.** The core is a model of the parse built from `defs`: whether the text follows rules 1–4, the number before each unit, and the total in seconds. If the text is a duration, the call must return the total (RB-CONV-1); otherwise it must raise ValueError (RB-ERR-1). Each format rule (R-FMT-1 to 6, R-NUM-1, R-ERR-2, R-MAX-1) also gets its own "this input raises ValueError" property, plus `outcome != 3` for R-IF-2 and "never returns more than 86400" for R-MAX-1.
- **5 scenarios:** `"1h30m"` → 5400, `"45s"` → 45, `"24h"` → 86400, `"99m99s"` → 6039, and a duration using all three units.
- **No ghost state**, even though the style rule asks for it. `frame.md` says calls are independent and `prev(x)` can be any earlier call, so state carried across calls would mean nothing. The model is a parse of the current text instead, and both outputs are checked against it.

**Left unformalized (3):**
- **R-NF-1** ("a Python function for our scheduling app"): not something you can see in the calls.
- **R-IF-1** (the name and signature): the adapter fixes these. A function that can't be called this way fails every call. But "exactly one parameter" can't be seen in the trace.
- **R-FR-1:** `covered_by: [F-ZERO]`. This frame rule is added to every set automatically, and `frame.md` says it need not be restated.

**Problems in the specification:**
1. **Rule 3 and rule 6 conflict.** Rule 3 allows up to 99 of every unit, so `"99h"` is 356,400 seconds, but rule 6 says a duration is never longer than one day. I took the literal reading: rule 6 is a further rule about what a duration is, like rules 1–4. So `"25h"` and `"24h1s"` raise ValueError, and exactly 86,400 seconds is allowed. That makes rule 3 a necessary condition, not a promise that every number works with every unit. R-NUM-1's text adds "every number from 1 to 99 is allowed for every unit", which goes beyond its quote and contradicts R-MAX-1 for 25 to 99 hours. I flagged this in the notes rather than settle it.
2. **Rule 6 comes after rule 5's "anything else"**, so it's unclear whether rule 5 covers texts longer than a day. Rule 6 could also be read as a promise about callers, or as a cap on the result. The notes say which reading I didn't take.
3. **Other gaps the spec leaves open, and what I chose:**
   - Leading zeros: allowed, so `"01h"` is one hour.
   - A sign such as `"+1h"`: not allowed, so it raises.
   - Upper-case units such as `"1H"`: not allowed, so it raises.
   - A unit may be skipped: `"1h5s"` is valid.
   - "Between 1 and 99" includes both ends.
   - The same 1–99 range applies to every unit, so `"90m"` is valid.
   - Only the space character is meant, with no trimming. Other whitespace raises anyway because it isn't a digit or a unit.
4. **The output encoding blurs R-IF-2.** Outcome 3 covers both "returned a non-int" and "returned an int that is negative or too large". So `outcome != 3` is slightly stronger than the text, but the other properties rule out those returns anyway.