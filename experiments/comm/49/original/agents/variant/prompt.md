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
- R-RES-1, "2^n": 2 XOR n, which is what 2 ^ n means in Python code; this reading contradicts the examples modp(3, 5) = 3, modp(1101, 101) = 2, modp(0, 101) = 1 and modp(3, 11) = 8
- R-RES-1, "modulo p": for n = 0 the value 2^0 = 1 is returned as is, as the example modp(0, 101) = 1 may be generalized to modp(0, p) = 1 for every p, so modp(0, 1) is 1; this contradicts the first reading at p = 1
- R-RES-1, "Return": any number equal to the residue is acceptable, such as the float 3.0 (the doctest output 3 and the frame's outcome 2 for other types argue against this)
- R-RES-2, "modulo p": the call must raise an exception for p = 0, as Python's 2**n % 0 raises ZeroDivisionError and pow(2, n, 0) raises ValueError
- R-EX-3, "modp(0, 101)": an illustration that modp(0, p) is 1 for every p, which contradicts R-RES-1's reduced result 2^0 mod 1 = 0 at p = 1

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