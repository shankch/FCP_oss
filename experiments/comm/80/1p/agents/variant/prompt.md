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
- R-IN-1, "a string": only strings of lowercase letters (the only characters any example uses) are valid arguments; the answer on other strings is a don't care
- R-IN-1, "a string s": only non-empty strings are given; the answer on the empty string is a don't care
- R-DEF-1, "happy": s has at least 3 characters and no two adjacent characters are equal; e.g. 'aba' is happy, 'abca' is happy, 'ab' is not happy
- R-DEF-1, "the string": letters are compared ignoring case, so 'aA' contains a repeated letter
- R-FN-2, "check": any truthy or falsy return value (e.g. 1/0, a non-empty or empty value, None for not happy) counts as the answer
- R-EX-1, "is_happy(a)": literal Python: a call with the value of a variable named a, which the request does not give (so not a string, at odds with R-IN-1)
- R-EX-2, "is_happy(aa)": literal Python: a call with the value of a variable named aa, which the request does not give (so not a string, at odds with R-IN-1)
- R-EX-3, "is_happy(abcd)": literal Python: a call with the value of a variable named abcd, which the request does not give (so not a string, at odds with R-IN-1)
- R-EX-4, "is_happy(aabb)": literal Python: a call with the value of a variable named aabb, which the request does not give (so not a string, at odds with R-IN-1)
- R-EX-5, "is_happy(adb)": literal Python: a call with the value of a variable named adb, which the request does not give (so not a string, at odds with R-IN-1)
- R-EX-6, "is_happy(xyy)": literal Python: a call with the value of a variable named xyy, which the request does not give (so not a string, at odds with R-IN-1)

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