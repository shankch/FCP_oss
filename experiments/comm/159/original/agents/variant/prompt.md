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
- R-DEF-2, "the number of carrots that you need to eat": need is the day's total requirement including the carrots already eaten, so only max(need - number, 0) more are needed (this contradicts eat(5, 6, 10) -> [11, 4], which would become [6, 9])
- R-RET-1, "return an array of [ total number of eaten carrots after your meals, the number of carrots left after your meals ]": the result must also report that the rabbit is still hungry (R-EAT-5), which contradicts returning exactly two elements
- R-RET-2, "total number of eaten carrots": only the carrots eaten in this call, without number
- R-RET-3, "the number of carrots left": the carrots the rabbit still has left to eat: need minus the carrots eaten in this call
- R-EAT-1, "you need to eat more carrots": the rabbit eats at least need carrots and may eat more, e.g. all remaining carrots
- R-EAT-2, "you need to eat more carrots": the rabbit eats at least need carrots and may eat more, e.g. all remaining carrots
- R-EAT-3, "not enough remaining carrots": remaining <= need (gives the same result when remaining == need)
- R-EAT-4, "not enough remaining carrots": remaining <= need (gives the same result when remaining == need)
- R-EAT-5, "but will still be hungry": the result must report that the rabbit is still hungry (a flag or the shortfall), which contradicts returning exactly two elements (R-RET-1)
- R-IN-1, "Constrain": the function must reject number outside 0..1000 (for example by raising an exception)
- R-IN-2, "Constrain": the function must reject need outside 0..1000 (for example by raising an exception)
- R-IN-3, "Constrain": the function must reject remaining outside 0..1000 (for example by raising an exception)

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