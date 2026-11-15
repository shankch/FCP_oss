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
- R-SIG-1, "remove_duplicates": The name states the behaviour: duplicates are removed so that each value is kept once, as its first occurrence (so [1, 2, 3, 2, 4] gives [1, 2, 3, 4]); this contradicts the docstring sentence of R-RM-1 and the example of R-EX-1.
- R-SIG-2, "-> List[int]": The return annotation only describes the type of the value when the function returns; raising an exception on some inputs is not excluded.
- R-RM-1, "remove all elements that occur more than once": Only the repeated (extra) occurrences are removed, so each value that occurs more than once is kept exactly once (the reading suggested by the function name remove_duplicates in R-SIG-1, which contradicts the example of R-EX-1).
- R-RM-1, "From a list of integers, remove": The elements are deleted from the given list in place, and that list is returned.
- R-ORD-1, "Keep order of elements left the same as in the input": The remaining elements keep their original positions (indices) in the list.
- R-ORD-1, "elements left": Under the deduplicating reading of R-RM-1 and R-SIG-1, a kept value is ordered by the position of its first occurrence in numbers.
- R-EX-1, "[1, 3, 4]": The example contradicts the function name remove_duplicates of R-SIG-1, under which the call would return [1, 2, 3, 4].

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