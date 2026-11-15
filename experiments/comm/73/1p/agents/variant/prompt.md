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
- R-IN-1, "an array arr of integers": Only non-empty lists are valid inputs; behaviour on the empty list is unspecified.
- R-IN-1, "integers": Non-negative integers only.
- R-CNT-1, "the number of elements that need to be changed": The number of positions whose element differs from its mirror element, counting both elements of every mismatched pair (twice the minimum).
- R-CNT-1, "number of elements": The answer counts change operations as defined by 'In one change, you can change one element to any other element' (the two coincide for a minimal set of changes, but the text names elements here and changes there).
- R-CNT-2, "find": Compute and output (e.g. print) the number; the return value is unspecified.
- R-DEF-1, "read the same backwards and forwards": Textually: the concatenated decimal digits of the elements form a palindromic string (e.g. [12, 1] reads '121').
- R-DEF-2, "any other element": The value of another element already present in the array (the minimum count is the same, since a mismatched element can always take its mirror's value).
- R-DEF-2, "In one change": The answer counts change operations, each of which modifies one element (consistent with counting elements for a minimal set of changes).

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