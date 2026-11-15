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
- R-DEF-1, "a branch of a tree": arr encodes tree structure (e.g. parent/child positions) that affects which node may be plucked
- R-IN-2, "1 <= nodes.length": arr is never empty, so the empty-array behaviour of R-EMP-1 and Example 3 (R-EX-3) is outside the input domain (don't care); contradicts R-EMP-1 and R-EX-3
- R-IN-2, "nodes.length": the number of nodes of the whole tree, of which arr is only one branch
- R-IN-3, "nodes.length": the number of nodes of the whole tree, of which arr is only one branch
- R-IN-4, "node.value": a value attribute of a node object, i.e. arr holds node objects rather than integers
- R-SEL-1, "pluck one of the nodes": a node is plucked and returned for every input; contradicts R-EMP-1 and R-EMP-2, which return [] for some inputs
- R-SEL-1, "return it": return the plucked node itself, i.e. its value alone; contradicts R-OUT-1, which returns the list [value, index]
- R-SEL-1, "pluck": remove the node from arr (mutate the argument) and return it
- R-SEL-2, "the node with the value": the node with the smallest even value (a qualifier seems to have been dropped; this is the only stated-style rule consistent with all four examples)
- R-SEL-3, "the value": the smallest even value of arr (as in R-SEL-2 reading 1)
- R-SEL-3, "return the node": return the node's value alone
- R-OUT-1, "returned in a list, [ value, its index ]": the result is the node itself as R-SEL-1 says ('return it'); the list form contradicts R-SEL-1
- R-OUT-2, "its index": the 1-based position of the plucked node in arr
- R-EMP-1, "the given array is empty": an empty arr is excluded by the constraint 1 <= nodes.length (R-IN-2), so this clause is vacuous; contradicts R-IN-2
- R-EMP-1, "return []": R-SEL-1 requires a node to be plucked for every input, contradicting this clause
- R-EMP-2, "no values": no node of arr has the value R-SEL-2 selects (e.g. no even value), so a non-empty arr can return []; seemingly contradicts R-SEL-1 ('pluck one of the nodes')
- R-EX-2, "Output: [2, 1]": the example is in error: under the smallest-value reading of R-SEL-2 the answer is [1, 0]; contradicts R-SEL-2 reading 2
- R-EX-3, "Input: []": the empty list is excluded by the constraint 1 <= nodes.length (R-IN-2); contradicts R-IN-2

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