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
- R-CTX-1, "you need to eat more carrots": The rabbit eats at least `need` further carrots and may eat more when stock allows.
- R-DEF-2, "the number of carrots that you need to eat": need is the day's total requirement including the carrots already eaten, so only max(0, need - number) more carrots are needed.
- R-RET-1, "an array": Any two-element sequence, such as a tuple, would do.
- R-TOT-1, "total number of eaten carrots": Only the carrots eaten in these meals: need.
- R-TOT-1, "the number of carrots that you need to eat": need is the day's total, so the first element is max(number, need).
- R-TOT-2, "total number of eaten carrots": Only the carrots eaten in these meals: remaining.
- R-LEFT-1, "the number of carrots left after your meals": The remaining argument unchanged, as all three of those examples show, so the second element is remaining (contradicting the literal prose 'left after your meals').
- R-LEFT-2, "you will eat all remaining carrots": The second element is the remaining argument unchanged, as eat(2, 11, 5) -> [7, 5] shows, even though all of it is eaten.
- R-HUN-1, "will still be hungry": The returned value must somehow report the unmet need (e.g. an extra element or flag), which would conflict with the two-element list of R-RET-1.
- R-EX-1, "eat(5, 6, 10) -> [11, 10]": The second element is an error; following R-LEFT-1 the intended result is [11, 4].
- R-EX-2, "eat(4, 8, 9) -> [12, 9]": The second element is an error; following R-LEFT-1 the intended result is [12, 1].
- R-EX-3, "eat(1, 10, 10) -> [11, 10]": The second element is an error; following R-LEFT-1 the intended result is [11, 0].
- R-EX-4, "eat(2, 11, 5) -> [7, 5]": The second element is an error; following R-LEFT-2 the intended result is [7, 0].
- R-ENV-1, "0 <= number <= 1000": A rule the function enforces: it must reject (e.g. raise on) number outside 0..1000.
- R-ENV-2, "0 <= need <= 1000": A rule the function enforces: it must reject (e.g. raise on) need outside 0..1000.
- R-ENV-3, "0 <= remaining <= 1000": A rule the function enforces: it must reject (e.g. raise on) remaining outside 0..1000.

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