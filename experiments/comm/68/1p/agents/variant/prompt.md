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
- R-FN-1, "Complete this function": Produce any working definition of the function; the given signature and docstring need not be kept verbatim.
- R-IN-1, "an array": arr may be any indexable sequence (list, tuple, array-like).
- R-IN-1, "a branch of a tree": The order of arr encodes tree structure (e.g. a path from the branch root outward), which the selection of the node may depend on.
- R-OUT-1, "one of the nodes": Any node of arr is acceptable as the plucked node (no further selection rule).
- R-OUT-2, "return it": Return the node's position (index) in arr.
- R-OUT-2, "it (when several nodes have the same value)": The specific node (position) plucked matters, so equal values at different positions are distinguishable.
- R-SEL-1, "The plucked node should be the node": The sentence is incomplete and imposes no checkable rule; any node of arr satisfies it (selection is a don't care among the elements of arr).
- R-SEL-1, "the node": Any node of arr is acceptable, consistent with 'pluck one of the nodes'; 'the node' just refers to the one chosen.

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