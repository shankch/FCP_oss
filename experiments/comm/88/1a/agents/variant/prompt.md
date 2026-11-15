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
- R-RET-2, "a copy of the given array after sorting": sort the given array itself, then return a copy of the sorted array; the given array is changed by the call, which contradicts R-MUT-1 (don't change the given array)
- R-DEF-1, "first index value, last index value": the indices themselves: 0 + (len(array) - 1), so the sum is len(array) - 1 and its parity depends only on the length (both examples are also consistent with this reading)
- R-DEF-1, "the sum( first index value, last index value)": the first and last values of the sorted copy, i.e. min(array) + max(array), which is the same for either sort order (both examples are also consistent with this reading)
- R-ORD-1, "is odd or even": odd only: ascending exactly when the parity sum is odd; 'or even' is a slip (matches examples R-EX-3 and R-EX-4 and makes the rule complementary to the even case of R-ORD-2)
- R-ORD-1, "in ascending order": strictly increasing: duplicates removed, which contradicts R-RET-2 (the result is a copy with the same elements)
- R-ORD-1, "you will sort the given array": sort the given array itself, in place; this contradicts R-MUT-1 (don't change the given array)
- R-ORD-2, "is even or odd": even only: descending exactly when the parity sum is even; 'or odd' is a slip (matches examples R-EX-3 and R-EX-4 and makes the rule complementary to the odd case of R-ORD-1)
- R-ORD-2, "in descending order": strictly decreasing: duplicates removed, which contradicts R-RET-2 (the result is a copy with the same elements)
- R-ORD-2, "sort it": 'it' is the given array itself, sorted in place; this contradicts R-MUT-1 (don't change the given array)
- R-MUT-1, "don't change the given array": contradicted by 'you will sort the given array' (R-ORD-1), 'sort it' (R-ORD-2) and 'a copy of the given array after sorting' (R-RET-2) read as sorting the argument itself, under which the argument is changed

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