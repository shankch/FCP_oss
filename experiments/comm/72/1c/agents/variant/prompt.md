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
- R-DEF-1, "palindromic list": The empty list is not a balanced object, so it is not balanced (and does not fly).
- R-DEF-3, "will fly if": Sufficient condition only: being balanced with sum at most w is enough to fly, but whether any other q flies (and so whether the call returns False for it) is not stated.
- R-RET-1, "returns True if the object q will fly": As the examples show (contradiction): a balanced q with sum at most w makes the call return False, e.g. will_it_fly([3, 2, 3], 9) ➞ False and will_it_fly([3], 5) ➞ False; all four examples return the opposite of the stated rule.
- R-RET-2, "False otherwise": As the example shows (contradiction): an unbalanced q with sum at most w makes the call return True, e.g. will_it_fly([1, 2], 5) ➞ True.
- R-RET-3, "False otherwise": As the example shows (contradiction): a balanced q whose sum exceeds w makes the call return True, e.g. will_it_fly([3, 2, 3], 1) ➞ True.
- R-EX-1, "➞ True": The expected value is an error: the call returns False, as the rule and the comment imply.
- R-WHY-1, "but it's unbalanced": The comment is consistent with the stated result True, i.e. the returned value is True when q does not fly (inverted output).
- R-EX-2, "➞ True": The expected value is an error: the call returns False, as the rule and the comment imply.
- R-WHY-2, "but 3+2+3 is more than the maximum possible weight": The comment is consistent with the stated result True, i.e. the returned value is True when q does not fly (inverted output).
- R-EX-3, "➞ False": The expected value is an error: the call returns True, as the rule and the comment imply.
- R-WHY-3, "and it's balanced": The comment is consistent with the stated result False, i.e. the returned value is False when q flies (inverted output).
- R-EX-4, "➞ False": The expected value is an error: the call returns True, as the rule and the comment imply.
- R-WHY-4, "and it's balanced": The comment is consistent with the stated result False, i.e. the returned value is False when q flies (inverted output).

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