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
- R-ENV-1, "n: int": n may be any Python int, so negative n must also be handled (with some unstated result)
- R-CAR-1, "2*n or n cars": exactly n cars drive left to right
- R-CAR-1, "2*n or n": one fixed count is meant, consistent with the function outputting a single number of collisions (R-OUT-2)
- R-CAR-2, "2*n or n cars": exactly n cars drive right to left
- R-CAR-2, "a different set": a set of a different size: if one set has n cars the other has 2*n cars
- R-CAR-2, "2*n or n": one fixed count is meant, consistent with the function outputting a single number of collisions (R-OUT-2)
- R-POS-1, "start out being very far from each other": only the distance is stated, not the side: if the left-to-right set starts on the right, the sets move apart and no collision ever happens
- R-COL-1, "said to collide": since the cars continue as if they did not collide (R-COL-2), the meeting is not a collision and is not counted, contradicting this definition
- R-COL-2, "as if they did not collide": the collision is treated as not having happened, so it is not counted, contradicting the definition of a collision (R-COL-1)
- R-OUT-1, "outputs": prints the number of collisions; the return value is unspecified
- R-OUT-2, "the number of such collisions": n*n (n cars in each direction)
- R-OUT-2, "the number": a single number determined by n, so one fixed car count must be meant (R-CAR-1, R-CAR-2)

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