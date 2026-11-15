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
- R-CARS-2, "simultaneously": both sets of cars start moving at the same instant
- R-CARS-3, "start out being very far from each other": the sets are only said to be far apart; their relative order is not stated, so they may be moving away from each other and never meet
- R-CARS-3, "very far": infinitely far apart, so that meetings may never actually happen
- R-CARS-4, "the same speed": all cars have equal speed at every instant, but that common speed may vary over time
- R-COL-1, "Two cars are said to collide when a car that's moving left to right hits a car that's moving right to left": seemingly contradicted by 'as if they did not collide' (R-COL-2): if the cars pass through each other unaffected, a meeting may not count as a collision at all
- R-COL-1, "collide": a collision is counted per meeting event, and the same pair could be counted more than once
- R-COL-2, "as if they did not collide": seemingly contradicts 'Two cars are said to collide' (R-COL-1): the cars behave as if no collision happened, which could be read as the meeting not being a collision
- R-OUT-1, "outputs": prints the number (to standard output)
- R-OUT-1, "the number of such collisions": the number of collisions under a different count of meetings (for example none, if the sets never approach each other, or one per car, n), depending on how R-CARS-3 and R-COL-1 are read

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