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
- R-TASK-1, "Complete this function": Any implementation of a function eat with this signature is acceptable, and the docstring may be changed or dropped.
- R-API-1, "eat(number, need, remaining)": The arguments may be any numbers, including non-integers.
- R-CTX-1, "hungry rabbit": The rabbit eats as many carrots as it can, up to what it needs (it never declines carrots it needs while some are available).
- R-DEF-1, "a certain number of carrots": This count is narrative only and is not tied to any argument.
- R-DEF-1, "already have eaten": Carrots eaten in total, not only toward today's meals.
- R-DEF-2, "need to eat more carrots": need is the total number of carrots for the day's meals, of which number are already eaten, so need - number are still to be eaten.
- R-DEF-3, "remaining": The carrots left in stock that the rabbit can still eat.
- R-DEF-3, "need, remaining": Contradiction with R-EAT-2: if remaining is the stock available, the rabbit cannot complete the day's meals when remaining is less than need, yet the prompt says it eats to complete them.
- R-ENV-1, "a certain number": Any integer; no bound is placed on number at all.
- R-ENV-2, "need to eat more carrots": need is at least 0; a need of 0 is a valid call.
- R-EAT-2, "complete the day's meals": Contradiction with R-DEF-3: if remaining is the stock available, the meals cannot be completed when remaining is less than need, yet this says the rabbit eats to complete them.
- R-OUT-1, "complete the day's meals.": eat returns a list [total carrots eaten after the meal, carrots left after the meal], that is [number + min(need, remaining), max(remaining - need, 0)].

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