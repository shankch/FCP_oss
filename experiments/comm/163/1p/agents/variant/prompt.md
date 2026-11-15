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
- R-IF-2, "generate_integers": The name is meant: the function generates integers of any size (even integers between a and b), which contradicts the docstring's 'even digits' (contradiction with R-RET-2).
- R-IN-1, "positive": Used loosely for non-negative: a >= 0 and b >= 0; calls with 0 must also satisfy every other requirement.
- R-IN-1, "a and b": a <= b is implicitly assumed: a call with a > b is outside the precondition and its behaviour is unconstrained.
- R-RET-1, "return": Any collection of the values is acceptable (a list, tuple, set, generator, ...).
- R-RET-2, "even digits": 'Digits' is used loosely for numbers: every element is an even integer of any size, as the function name generate_integers suggests (contradiction with R-IF-2).
- R-RET-3, "between": Exclusive: only values strictly greater than the lower bound and strictly less than the upper bound lie between a and b.
- R-RET-3, "a and b": Ordered: the range runs from a up to b, so nothing lies between them when a > b and the list is empty.
- R-RET-3, "even digits": Even integers of any size, as the function name generate_integers suggests: each element itself lies between a and b.
- R-RET-4, "between": Exclusive: a and b themselves never appear; only values strictly between them are required.
- R-RET-4, "a and b": Ordered: the even digits from a up to b must appear; nothing is required when a > b.
- R-RET-4, "even digits": Every even integer of any size between a and b must appear, as the function name generate_integers suggests (contradiction with R-IF-2).
- R-RET-5, "the even digits": One entry per occurrence (for instance per occurrence of a digit in the decimal writing of the numbers between a and b): duplicates are allowed or required.
- R-RET-6, "return the even digits": Ascending order is implied, as is conventional for a list of numbers in a range.

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