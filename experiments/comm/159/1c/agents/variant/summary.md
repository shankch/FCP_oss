I wrote `formal/variant.yaml`. `fcp lint` reports it clean, and the `fcp explain` output matches what I meant for every item.

**Items: 15** (11 properties, 4 scenarios; no assumptions, no don't-cares), plus 16 entries under `decisions`, all reading 2 as you specified.
- **Valid inputs only:** I read R-ENV-1..3 as rules the function enforces, so they are properties: an argument over 1000 means the call must not return a list (`outcome != 0`). All the other properties apply only to calls with arguments in 0..1000.
- **Return shape (R-RET-1):** I read "an array" as allowing a tuple. The adapter records a tuple as outcome 2 and can't see its contents. So a valid call must return a two-element list or end with outcome 2, and the rules about element values only apply when a list came back.
- **Element rules under your readings:** R-CTX-1 says the first element is at least `number + need` and at most `number + remaining`. R-TOT-1 has two items, one per flagged phrase: `result[0] == need` and `result[0] == max(number, need)`. R-TOT-2 gives `result[0] == remaining`. R-LEFT-1 and R-LEFT-2 both give `result[1] == remaining`.
- **Hungry (R-HUN-1):** when `remaining < need`, the call must return a third element or end with outcome 2.
- **Examples (R-EX-1..4):** scenarios with the corrected results [11,4], [12,1], [11,0] and [7,0].

Each affected note states the reading it follows.

**Left unformalized (5):**
- **R-API-1:** it's about the deliverable, not behaviour. A wrong signature would show up as outcome 1, which RV-RET-1 already forbids.
- **R-DEF-1 and R-DEF-3:** these only define what the arguments mean; they're covered by the items that use them.
- **R-DEF-2:** a definition, covered by RV-TOT-1-DAY. Per the reason recorded with it, I didn't apply its "need is the day's total" reading to the conditions `remaining >= need` / `remaining < need`, which the requirements state literally.
- **R-FR-1:** already covered by the adapter's built-in rule F-EMPTY (`result` is empty unless `outcome` is 0).

**Problems in the specification:**
- **Examples contradict the prose:** in all four, the second element is the starting `remaining`, not what's "left after your meals". And eat(2, 11, 5) → [7, 5] contradicts "you will eat all remaining carrots".
- **"Still hungry" doesn't fit the return value:** a two-element list has nowhere to report it.
- **Constraints are unclear:** the spec doesn't say whether the 0..1000 limits are a promise by the caller or a check the function must do.
- **Typos:** "thet" and "Constrain".

**Conflicts the readings create inside this set** (noted on the items, and expected for a variant set):
- The two R-TOT-1 readings disagree whenever `number > need`.
- All four example scenarios conflict with the TOT and LEFT items under these readings.
- RV-HUN-1 combined with RV-RET-1 leaves outcome 2 as the only allowed answer when stock is short, so RV-EX-4 can't be met.
- RV-CTX-1 treats `need` as the further carrots to eat, while R-DEF-2's reading treats it as the day's total.

Because the element rules apply only when a list is returned, the properties alone can be satisfied by returning a non-list for every valid call. The contradictions only show up through the example scenarios.