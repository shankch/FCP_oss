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
- R-IN-1, "a string of "(" and ")"": A description of typical input only: the function must still answer for strings with other characters, judging only the '(' and ')' characters and ignoring the rest.
- R-IN-1, "brackets is a string": The empty string is not a string of brackets, so it is outside the contract and its result is unconstrained.
- R-RET-1, "has a corresponding closing or opening bracket": Equal counts: the number of '(' equals the number of ')', in any order (each '(' paired one-to-one with any ')'). This contradicts the example candidate(")(()") == False, which has two of each.
- R-RET-2, "return True if": A sufficient condition only: the text says nothing about strings with an unmatched bracket, so any result (including None or an exception) is allowed for them.
- R-RET-2, "has a corresponding closing or opening bracket": Equal counts: the number of '(' equals the number of ')', in any order (each '(' paired one-to-one with any ')'). This contradicts the example candidate(")(()") == False, which has two of each.
- R-SC-2, "candidate("()")": Contradicts the literal respective reading of R-RET-1 (a closing bracket corresponds to a closing one, an opening to an opening), under which the lone '(' and ')' are unmatched and the result would not be True.
- R-SC-3, "candidate("(()())")": Contradicts the literal respective reading of R-RET-1 (same-kind partners), under which three '(' and three ')' cannot all be paired and the result would not be True.
- R-SC-4, "candidate(")(()")": Contradicts R-RET-1 under the equal-count reading: ")(()" has two '(' and two ')', so every bracket can be given a partner and the result would be True.

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