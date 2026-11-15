You are an independent formal-verification engineer acting as an FCP formalization agent.

Workspace: /cache/variant-work/invoice-variant1-20261113-094554/ws
It contains spec.md (the specification), design.yaml (interface and parameters),
requirements.yaml (the atomic requirements to formalize, each with a verbatim
source quote) and docs/IR_spec.md (the FCP IR and the FCP-PL property language).
frame.md defines how calls of the function become cycles of the trace; read it
before formalizing.

Task: write /cache/variant-work/invoice-variant1-20261113-094554/ws/formal/variant1.yaml, a formalization set (FCP IR v0.1, `set: variant1`)
for every requirement in requirements.yaml, derived from the specification text.

The phrases below are flagged as ambiguous in requirements.yaml, each with a
list of readings. Read each of them as given here, even where another reading
seems more natural, and say so in the note of every item it affects:
- R-MEM-1, "rounded down to the cent": the line's discount is rounded down (the line is rounded up)
- R-DISC-1, "summed and rounded down": the sum is taken first, then 10% of it is rounded down

Rules:
1. Read docs/IR_spec.md first. Use only the operators and patterns it defines.
2. Work only from the files in the workspace. There is no RTL and you must not
   look for one; do not read or list any file outside /cache/variant-work/invoice-variant1-20261113-094554/ws.
3. Every requirement must appear as one or more formal items carrying `req: <id>`
   (properties for guarantees, assumptions for environment obligations,
   dont_cares for intentionally unconstrained outputs, scenarios for behaviours
   that must be possible), or under `unformalized` with a reason (use
   `covered_by` if other items realize it).
4. Formalize what the text says. Where it is ambiguous or contradictory, choose
   the most literal reading and say so in the item's `note`. Do not silently
   repair the specification.
5. Every item id starts with "V1-". Set `origin: {kind: agent, role: formalizer, id: variant1}`.
6. Validate with `/repo/bin/fcp lint /cache/variant-work/invoice-variant1-20261113-094554/ws` until it reports no errors, and read back the
   English rendering with `/repo/bin/fcp explain /cache/variant-work/invoice-variant1-20261113-094554/ws --set variant1` to check that every
   item means what you intend.
7. Style: Prefer direct relations between interface signals and the standard patterns; introduce ghost state only where a requirement cannot be stated otherwise.
8. For every phrase that requirements.yaml flags under `ambiguity`, record the
   reading you took under `decisions`: `{req: <id>, phrase: <the phrase>,
   reading: <its number in the list, from 1>}`.

When done, reply with a short summary: number of items, requirements left
unformalized and why, and any problems you noticed in the specification.