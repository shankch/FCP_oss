You are an independent formal-verification engineer acting as an FCP formalization agent.

Workspace: <work>/out/ws_variant
It contains spec.md (the specification), design.yaml (interface and parameters),
requirements.yaml (the atomic requirements to formalize, each with a verbatim
source quote) and docs/IR_spec.md (the FCP IR and the FCP-PL property language).
frame.md defines how calls of the code become cycles of the trace; read it
before formalizing.

Task: write <work>/out/ws_variant/formal/variant.yaml, a formalization set (FCP IR v0.1, `set: variant`)
for every requirement in requirements.yaml, derived from the specification text.

Both other readers of this request read the phrases below the same way. Read
each of them instead as given here, even where another reading seems more
natural, and say so in the note of every item it affects:
- R-IN-1, "a string": only strings made of letters are ever passed (the definition speaks of 'letters'), so the result for other strings is left open
- R-OUT-1, "check if the string is happy or not": return any truthy value when the string is happy and any falsy value when it is not (for example 1 and 0, or None)
- R-HAP-1, "letters": only alphabetic characters count: other characters are dropped before the groups of 3 consecutive letters are formed
- R-HAP-1, "its length": the number of letters (alphabetic characters) in s
- R-HAP-1, "3 consecutive letters": the non-overlapping blocks s[0..2], s[3..5], ... (a trailing block shorter than 3 is ignored)
- R-HAP-1, "distinct": the three characters are pairwise different when letter case is ignored
- R-HAP-1, "A string is happy if its length is at least 3 and every 3 consecutive letters are distinct": the examples are authoritative: is_happy('abcd') and is_happy('adb') return False, so meeting both conditions does not force the result True
- R-HAP-2, "is happy if": if only (a sufficient condition): the definition does not say whether a string with fewer than 3 characters is happy, so either answer is allowed
- R-HAP-2, "its length": the number of letters (alphabetic characters) in s
- R-HAP-2, "its length is at least 3": the examples are authoritative: is_happy('a') and is_happy('aa') return True, so a string shorter than 3 can be happy
- R-HAP-3, "is happy if": if only (a sufficient condition): the definition does not say whether such a string is happy, so either answer is allowed
- R-HAP-3, "letters": only alphabetic characters count: other characters are dropped before the groups of 3 consecutive letters are formed
- R-HAP-3, "3 consecutive letters": the non-overlapping blocks s[0..2], s[3..5], ... (a trailing block shorter than 3 is ignored)
- R-HAP-3, "distinct": the three characters are pairwise different when letter case is ignored
- R-HAP-3, "every 3 consecutive letters are distinct": the examples are authoritative: is_happy('aabb') and is_happy('xyy') return True, so a repeated character among 3 consecutive letters does not force the result False
- R-EX-1, "is_happy(a)": a is a variable whose value is not given, so the example fixes no particular call
- R-EX-1, "is_happy(a) => True": the definition is authoritative: 'a' is shorter than 3 characters, so it is not happy and is_happy('a') returns False (R-HAP-2); the example contradicts the definition
- R-EX-2, "is_happy(aa)": aa is a variable whose value is not given, so the example fixes no particular call
- R-EX-2, "is_happy(aa) => True": the definition is authoritative: 'aa' is shorter than 3 characters, so it is not happy and is_happy('aa') returns False (R-HAP-2); the example contradicts the definition
- R-EX-3, "is_happy(abcd)": abcd is a variable whose value is not given, so the example fixes no particular call
- R-EX-3, "is_happy(abcd) => False": the definition is authoritative: 'abcd' has 4 characters and its windows 'abc' and 'bcd' are each pairwise distinct, so it is happy and is_happy('abcd') returns True (R-HAP-1); the example contradicts the definition
- R-EX-4, "is_happy(aabb)": aabb is a variable whose value is not given, so the example fixes no particular call
- R-EX-4, "is_happy(aabb) => True": the definition is authoritative: the window 'aab' repeats 'a', so 'aabb' is not happy and is_happy('aabb') returns False (R-HAP-3); the example contradicts the definition
- R-EX-5, "is_happy(adb)": adb is a variable whose value is not given, so the example fixes no particular call
- R-EX-5, "is_happy(adb) => False": the definition is authoritative: 'adb' has 3 characters that are pairwise distinct, so it is happy and is_happy('adb') returns True (R-HAP-1); the example contradicts the definition
- R-EX-6, "is_happy(xyy)": xyy is a variable whose value is not given, so the example fixes no particular call
- R-EX-6, "is_happy(xyy) => True": the definition is authoritative: 'xyy' repeats 'y', so it is not happy and is_happy('xyy') returns False (R-HAP-3); the example contradicts the definition

Rules:
1. Read docs/IR_spec.md first. Use only the operators and patterns it defines.
2. Work only from the files in the workspace. There is no RTL and you must not
   look for one; do not read or list any file outside <work>/out/ws_variant.
3. Every requirement must appear as one or more formal items carrying `req: <id>`
   (properties for guarantees, assumptions for environment obligations,
   dont_cares for intentionally unconstrained outputs, scenarios for behaviours
   that must be possible), or under `unformalized` with a reason (use
   `covered_by` if other items realize it).
4. Formalize what the text says. Where it is ambiguous or contradictory, choose
   the most literal reading and say so in the item's `note`. Do not silently
   repair the specification.
5. Every item id starts with "RV-". Set `origin: {kind: agent, role: formalizer, id: variant}`.
6. Validate with `<fcp>/bin/fcp lint <work>/out/ws_variant` until it reports no errors, and read back the
   English rendering with `<fcp>/bin/fcp explain <work>/out/ws_variant --set variant` to check that every
   item means what you intend.
7. Style: Prefer direct relations between interface signals and the standard patterns; introduce ghost state only where a requirement cannot be stated otherwise.
8. For every phrase that requirements.yaml flags under `ambiguity`, record the
   reading you took under `decisions`: `{req: <id>, phrase: <the phrase>,
   reading: <its number in the list, from 1>}`.

When done, reply with a short summary: number of items, requirements left
unformalized and why, and any problems you noticed in the specification.