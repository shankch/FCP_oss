I've written `formal/variant.yaml` (set `variant`). `fcp lint` reports it clean, and the `fcp explain` output matches what I intended for each item. Every flagged phrase uses the reading you gave, and each affected item says so in its note.

**Items: 17**
- **1 assumption, RV-IN-1:** only strings made entirely of letters are passed, so the result for any other string is left open. The empty string still counts.
- **1 property, RV-OUT-1 (`outcome != 1`):** the call must finish without raising. A non-bool return is allowed under the truthy/falsy reading.
- **6 example properties (RV-HAP-1A/B, 2A/B, 3A/B):** because the examples are authoritative in R-HAP-1/2/3, 'abcd' and 'adb' must give a falsy result, and 'a', 'aa', 'aabb' and 'xyy' a truthy one.
- **3 don't-cares on `happy` (RV-HAP-1C/2C/3C):** "is happy if" is only a sufficient condition and meeting it doesn't force True, so the answer is open in all three cases: fewer than 3 letters, every block distinct, or some block repeated. The six example strings are excluded. The blocks use your readings: letters only, non-overlapping blocks of three, case ignored. They are built from the helper definitions `nl` and `rep`.
- **6 scenarios (RV-EX-1…6):** the argument is a variable with no given value, so each example only says that *some* call returns a truthy (or falsy) value.
- **27 decisions,** all reading 2.

I checked `rep` by hand against the example strings. I wrote a Python cross-check in the scratchpad but didn't run it, because the command needed approval.

**Left unformalized (2)**
- **R-API-1:** the function name and signature are a property of the source code, not of a trace of calls. A missing function would show up as outcome 1, which RV-OUT-1 rejects.
- **R-FR-1:** covered by the design's frame rule F-ZERO, which frame.md says not to restate.

**Problems I noticed**
1. **The spec contradicts itself.** Read literally, every one of the six examples gives the opposite of what the definition says.
2. **The readings you set contradict each other.** R-HAP-1/2/3 treat the examples as authoritative ('a' gives True). R-EX-1…6 treat the definition as authoritative ('a' gives False). They only avoid a direct clash because the "variable argument" reading means R-EX names no particular string. The notes on both sides point this out.
3. **The definition ends up fixing nothing.** Under these readings, `happy` is free for every string except the six examples. The three don't-cares together cover every string.
4. **The interface can't check truthy/falsy.** The trace only records whether a bool was True or False. Any other return (outcome 2) is accepted as either, so a function that returns None for a happy string would pass.
5. **Two things are weak by construction.**
   - The letter-filtering in `nl`/`rep` makes no difference once RV-IN-1 is assumed, since only letters are passed.
   - The R-EX scenarios are very weak: any truthy or falsy result anywhere satisfies them.