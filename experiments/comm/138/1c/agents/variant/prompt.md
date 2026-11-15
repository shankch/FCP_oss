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
- R-RET-1, "Evaluate whether": any value that compares equal to True or False (such as 1 or 0) is acceptable, since the examples only check `== True` / `== False`
- R-SUM-1, "exactly 4 positive even numbers": the four summands must be distinct, so the representable n are exactly the even n >= 20
- R-SUM-1, "can be written as the sum of exactly 4 positive even numbers": the examples are authoritative and the description is inverted: the function returns True exactly when n can NOT be written as such a sum, so is_equal_to_sum_even(8) returns False
- R-SUM-2, "exactly 4 positive even numbers": the four summands must be distinct, so the representable n are exactly the even n >= 20
- R-SUM-2, "can be written as the sum of exactly 4 positive even numbers": the examples are authoritative and the description is inverted: the function returns True exactly when n can NOT be written as such a sum, so is_equal_to_sum_even(4) and is_equal_to_sum_even(6) return True
- R-EX-1, "is_equal_to_sum_even(4) == True": the description is authoritative: 4 is not a sum of 4 positive even numbers, so is_equal_to_sum_even(4) returns False and this example is wrong
- R-EX-2, "is_equal_to_sum_even(6) == True": the description is authoritative: 6 is not a sum of 4 positive even numbers, so is_equal_to_sum_even(6) returns False and this example is wrong
- R-EX-3, "is_equal_to_sum_even(8) == False": the description is authoritative: 8 = 2+2+2+2, so is_equal_to_sum_even(8) returns True and this example is wrong

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