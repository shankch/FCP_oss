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
- R-SIG-1, "x, y, z": the parameters map to number, need and remaining in some other order: the signature and the docstring use different names and nothing states the mapping (seeming contradiction between the signature and the Variables section)
- R-MEAL-1, "no or more carrots": 'need or more': need is only a minimum and the rabbit may eat more than need carrots when the stock allows
- R-RET-1, "an array": any array-like sequence of two integers (list, tuple, array.array, ...)
- R-RET-2, "needed or eaten": needed: number + need, regardless of the stock (fits eat(5, 6, 10), eat(4, 8, 9) and eat(1, 10, 10), but contradicts eat(2, 11, 5) -> [7, 0], which would give 13)
- R-RET-2, "before or after your meals": before the meal: the first element is number alone (contradicts every example, e.g. eat(5, 6, 10) would give 5, not 11)
- R-RET-2, "total number": only the carrots eaten in this meal, min(need, remaining) (contradicts every example, e.g. eat(5, 6, 10) would give 6, not 11)
- R-RET-3, "needed or eaten left": carrots still needed after the meal: max(need - remaining, 0) (contradicts eat(5, 6, 10) -> [11, 4], eat(4, 8, 9) -> [12, 1] and eat(2, 11, 5) -> [7, 0], which would give 0, 0 and 6)
- R-HUN-1, "not enough remaining carrots": remaining <= need (at remaining == need both readings give the same returned list)
- R-HUN-3, "will still be hungry": the returned list reports the unmet need need - remaining, e.g. as the second element (contradicts eat(2, 11, 5) -> [7, 0], which would then be [7, 6])
- R-EX-1, "[11, 4]": the second element is the carrots still needed (reading 2 of R-RET-3), which would give [11, 0]: the example contradicts that reading
- R-EX-2, "[12, 1]": the second element is the carrots still needed (reading 2 of R-RET-3), which would give [12, 0]: the example contradicts that reading
- R-EX-4, "[7, 0]": the first element is the total needed (reading 2 of R-RET-2 'needed or eaten'), which would give 13: the example contradicts that reading
- R-VAR-1, "@number": number is y, the second parameter
- R-VAR-2, "@need": need is x, the first parameter
- R-VAR-3, "@remaining": remaining is x, the first parameter
- R-CON-1, "0 <= number <= 1000": a check the function must make: it must reject number outside 0..1000, e.g. by raising an exception
- R-CON-2, "0 <= need <= 1000": a check the function must make: it must reject need outside 0..1000, e.g. by raising an exception
- R-CON-3, "0 <= remaining <= 1000": a check the function must make: it must reject remaining outside 0..1000, e.g. by raising an exception

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