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
- R-IN-1, "positive integers": Only a description of typical inputs: the function must still follow the other requirements when a = 0 (for instance listing 0 as an even digit when it lies between a and b).
- R-IN-2, "positive integers": Only a description of typical inputs: the function must still follow the other requirements when b = 0 (for instance listing 0 as an even digit when it lies between a and b).
- R-SEL-1, "digits": The decimal digits that occur in the integers between a and b (for 10..14 this would include 0, 2 and 4, contradicting generate_integers(10, 14) => []).
- R-SEL-2, "between a and b": Exclusive: only values strictly greater than the smaller and strictly less than the larger argument (contradicts generate_integers(2, 8) => [2, 4, 6, 8], which contains 2 and 8).
- R-SEL-3, "odd or even": Even digits only (the parity every example shows).
- R-ORD-1, "in descending or ascending order": Always ascending (the order every example shows).
- R-EX-1, "generate_integers(2, 8) => [2, 4, 6, 8]": Illustrative: one admissible answer for an implementation that chose even digits in ascending order; an implementation that chose odd digits or descending order may return another list.
- R-EX-2, "generate_integers(8, 2) => [2, 4, 6, 8]": Illustrative: one admissible answer for an implementation that chose even digits in ascending order; an implementation that chose odd digits or descending order may return another list.
- R-EX-3, "generate_integers(10, 14) => []": Contradicts 'digits' read as the digits occurring in the numbers 10 to 14 (0, 2, 4 even; 1, 3 odd) or as the integers 10 to 14 themselves (R-SEL-1).

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