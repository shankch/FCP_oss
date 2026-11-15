I wrote `formal/agent_a.yaml`. `fcp lint` reports clean, and the `fcp explain` read-back says what I intended for every item.

**Items:** 14 formal items, all prefixed `PA-`: 11 properties and 3 scenarios. There are no assumptions, don't-cares, ghosts or rigids; every item relates the argument and result of the same call, using five defs (`nd`, `bad_char`, `luhn_sum`, `valid`, `shown`).
- **R-ERR-1** (PA-ERR-1/2/3): ValueError (`outcome == 1`) on a bad character, a digit count outside 12–19, or a failed Luhn check. My Luhn def matched a standard Luhn implementation on 200,000 random strings.
- **R-RET-1** (PA-RET-1/2, scenarios PA-RET-S12/S19): a valid number returns a string, with more than half its digits hidden.
- **R-MASK-1, R-LAST4-1, R-SEP-1, R-QUARTER-1** (PA-MASK-1, PA-LAST4-1, PA-SEP-1/2, PA-QUARTER-1): the masking rules. PA-QUARTER-1 is the check 4 × digits shown ≤ digits in the number.
- **R-EX-1**: a scenario (PA-EX-1) and also a property (PA-EX-2), because the result depends only on the argument.

**Left unformalized:** four requirements, each with `covered_by`.
- **R-SIG-1:** the signature is the interface already defined in `design.yaml`; the return type is checked by PA-RET-1.
- **R-IN-1, R-IN-2:** definitions realized through the defs and the ERR/RET/SEP items.
- **R-FR-1:** the frame rule F-EMPTY is in every set by construction.

**Problems in the specification:**
1. **Contradiction (critical):** for a valid number with 12–15 digits, the function must return (R-RET-1) and show the last four digits (R-LAST4-1), but may show at most a quarter of them, i.e. 3 to 3.75 (R-QUARTER-1). An example is `"411111111117"`. I formalized it literally and did not repair it. A spec-only `fcp check` on my set confirms it: the minimal conflicting set is {PA-LAST4-1, PA-QUARTER-1, PA-RET-1}, with solver input `'5-    40  8  344 -- 05-0-  --0-8'` (12 digits, passes Luhn). Without scenario PA-RET-S12, the consistency check had called the spec consistent, which is why I added it.
2. **Ambiguities, with the reading I chose:**
   - "digits": the ten characters 0–9, so ², ³ and ¹ must raise.
   - "between groups of digits": separators may appear anywhere, any number of times.
   - Not flagged by the decomposer: "spaces" and "hyphens" mean only the characters 32 and 45, so tab, no-break space and soft hyphen must raise.
   - Not flagged: the Luhn check is named but not defined; I used the standard one.
   - Not flagged: "most" means more than half.
   - Not flagged: "show" means digits in the returned string. A digit leaked in an exception message can't be seen in the trace.

**Tool issues (not spec problems):**
- `fcp check` ran its spec-only analyses (tautology, consistency, determinacy), then crashed with `KeyError: 'ref'` at the verify step, because this function design has no RTL variant.
- Determinacy reports `masked` and `masked__len` as undetermined. Both witnesses differ only in raw port values the monitors ignore: bits beyond the string length, and lengths above 32 (e.g. `number__len` = 57) that the monitors clamp. The frame says such calls are not part of the trace.

I removed the check outputs afterwards. The only extra item left in the workspace is an empty `.fcp/cache` directory, which `lint` and `explain` recreate on every run.
