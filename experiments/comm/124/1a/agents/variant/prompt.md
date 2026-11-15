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
- R-RET-2, "otherwise False": Only well-formed strings with an out-of-range day or month must yield False; for malformed strings the behaviour (e.g. raising ValueError) is not specified.
- R-VAL-1, "The date is valid if all of the following rules are satisfied": The listed rules are necessary conditions only; the string must additionally denote a real calendar date (e.g. 29 February only in a leap year, a plausible year).
- R-DAY-1, "is not less than 1 or higher than 31 days": (not less than 1) or (higher than 31): taken literally as a logical formula, only day >= 1 is required, so no upper bound.
- R-DAY-2, "is not less than 1 or higher than 30 days": (not less than 1) or (higher than 30): taken literally as a logical formula, only day >= 1 is required, so no upper bound.
- R-DAY-3, "is not less than 1 or higher than 29": (not less than 1) or (higher than 29): taken literally as a logical formula, only day >= 1 is required, so no upper bound.
- R-DAY-3, "higher than 29 for the month 2": Day 29 of month 2 is accepted only when the year is a leap year (a real calendar check, since the function 'validates a given date').
- R-MON-1, "should not be less than 1 or higher than 12": (should not be less than 1) or (higher than 12): taken literally, only month >= 1 is required, so no upper bound.
- R-FMT-2, "dd-mm-yyyy or mm-dd-yyyy": dd and mm are day and month numbers written with one or two digits (e.g. '4-1-2040' is acceptable), and yyyy is the year as digits.
- R-FMT-2, "The date should be in the format": Surrounding whitespace is ignored (the string is stripped) before the format is checked.
- R-FMT-2, "yyyy": The year must be a real year, at least 1 (so '0000' is invalid).
- R-FMT-3, "dd-mm-yyyy or mm-dd-yyyy": Only mm-dd-yyyy is accepted (the first field is the month), as the example valid_date('15-01-2012') => False requires; the dd-mm-yyyy alternative is an error in the prompt.
- R-EX-2, "valid_date('15-01-2012') => False": The example is wrong: rule 4 accepts dd-mm-yyyy, under which '15-01-2012' is 15 January 2012 and satisfies every rule, so the call should return True.

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