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
- R-FN-1, "Evaluate whether": the function returns any value that compares equal to True or False (e.g. 1 or 0), not necessarily of type bool
- R-FN-2, "4 numbers": non-negative integers (zero allowed): every n >= 0 qualifies, so the result is always True
- R-FN-2, "the sum of 4": four or more summands
- R-FN-2, "can be written as": the statement is abbreviated and the examples fix the kind of number (e.g. four positive even numbers), so the examples take precedence
- R-EX-1, "candidate(4)": the example holds, so the main statement must be read narrowly (e.g. four positive even numbers, or four integers of at least 2), under which 4 does not qualify
- R-EX-1, "== False": the call returns any value equal to False (e.g. 0)
- R-EX-2, "candidate(6)": the example holds, so the main statement must be read narrowly (e.g. four positive even numbers, or four integers of at least 2), under which 6 does not qualify
- R-EX-2, "== False": the call returns any value equal to False (e.g. 0)
- R-EX-3, "candidate(8)": contradiction: if the four numbers must be distinct positive integers, the smallest such sum is 10, so 8 would not qualify and candidate(8) would be False
- R-EX-3, "== True": the call returns any value equal to True (e.g. 1)

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