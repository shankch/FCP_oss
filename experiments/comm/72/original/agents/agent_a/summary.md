I wrote `formal/agent_a.yaml`. It has 12 formal items, 8 properties and 4 scenarios, and covers all 12 requirements. `fcp lint` reports it clean, and I read back the `fcp explain` output: every item says what I meant it to.

**Items**
- **Shared definitions:** `bal` (q reads the same both ways, so the empty list counts as balanced), `wsum` (the sum of q) and `light` (`wsum <= w`).
- **RA-OUT-1:** every call returns a real Python `bool`, so `outcome == 0` at every call.
- **RA-FLY-1:** if `bal && light`, the call returns True.
- **RA-FLY-2:** if q is not balanced, the call returns False.
- **RA-FLY-3:** if the sum is greater than w, the call returns False.
- **RA-EX-1…4:** each example is written twice. One copy is a property ("this exact call returns this value") and one is a scenario (this call with this result must be possible). The examples state the result outright, so I treated them as guarantees too, not only as things that must be possible.

**Not formalized as items** (5 requirements, each with a reason)
- **R-IF-1** (the function name and its two parameters): this is a fact about the interface, which `design.yaml` already fixes. It isn't something the trace can show.
- **R-DEF-1, R-DEF-2, R-DEF-3:** these are definitions. The shared definitions above carry them, and they are marked `covered_by` the RA-FLY properties.
- **R-FR-1:** this is the adapter's frame rule F-ZERO, which is added to every set automatically. It is marked `covered_by: [F-ZERO]`.

**Readings taken:** I recorded all 12 flagged phrases under `decisions`, and every one takes reading 1:
- the answer must be the bool True or False, not just any truthy or falsy value;
- "will fly if" means "if and only if", so "False otherwise" applies to every other case;
- the empty list is a palindrome, so `will_it_fly([], w)` returns True for any w;
- the weight test is `<=`, as the rule says;
- the example comments that say "is less than" describe only their own calls.

**Problems in the specification**
1. **Boundary contradiction.** The rule says the sum must be "less than or equal" to w, but the comments on the True examples say "is less than". No example has a sum equal to w, so the examples never settle whether that case flies. I followed the rule (`<=`).
2. **"If" is not "if and only if".** "The object q will fly if …" literally gives only a condition that is enough to fly. The False cases (RA-FLY-2 and RA-FLY-3) depend entirely on reading it as "if and only if". With the other reading, an unbalanced or overweight q would have no required answer.
3. **Empty list.** The prompt never says what `will_it_fly([], w)` should return. My reading returns True for every w ≥ 0.
4. **Return type.** The prompt doesn't say whether truthy values like 1 or 0 are acceptable answers. I took the strict reading that only the bool True or False counts.
5. **Input ranges.** The prompt doesn't define negative numbers, list lengths or value sizes at all. Only the adapter's limits (at most 8 elements, values 0–255, w up to 4,095) bound them.