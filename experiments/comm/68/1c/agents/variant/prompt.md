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
- R-DEF-1, "representing a branch of a tree": arr encodes tree structure (for example level order), so positions also carry parent/child meaning
- R-PL-1, "pluck": remove the node from arr (mutating the argument) and report it
- R-PL-1, "return it": return the node's value alone
- R-PL-2, "the smallest even value": the largest element of arr of any parity, which is what Examples 1, 2 and 4 show ([4,2,3] -> [4, 0], [1,2,3] -> [3, 2], [5, 0, 3, 0, 4, 2] -> [5, 0]); contradicts R-EX-1, R-EX-2 and R-EX-4
- R-PL-2, "even": 0 is not counted as an even value
- R-PL-3, "return the node that has smallest index": Example 4 (R-EX-4) is right and pluck([5, 0, 3, 0, 4, 2]) returns [5, 0], so the tie on 0 does not decide the result; contradicts this sentence
- R-OUT-1, "smalest_value": the smallest value of arr of any parity
- R-OUT-2, "its index": the 1-based position of the node in arr
- R-EMP-1, "no even values": 0 is not counted, so such an array has no even values and the call returns []
- R-EMP-2, "the given array is empty": the empty array is excluded by the Constraints (1 <= nodes.length, R-IN-2), so this clause never applies; contradicts R-IN-2
- R-EX-3, "Input: []": the empty array violates the Constraints (1 <= nodes.length, R-IN-2), so this example lies outside the input domain; contradicts R-IN-2

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