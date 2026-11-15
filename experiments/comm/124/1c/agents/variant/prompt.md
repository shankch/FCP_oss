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
- R-RET-1, "returns True if the date is valid": Contradiction with R-EX-1 and R-EX-4, examples authoritative: valid_date returns False for '03-11-2000' and '06-04-2020', so a date meeting every rule does not always yield True (validity or the return polarity means something other than stated).
- R-RET-2, "otherwise False": Contradiction with R-EX-2, R-EX-3 and R-EX-5, examples authoritative: valid_date returns True for '15-01-2012', '04-0-2040' and '06/04/2020' even though each breaks a listed rule.
- R-RET-3, "otherwise False": Only strings that look like dates are covered; for malformed strings (e.g. non-numeric fields) the function may raise an exception instead of returning False.
- R-VAL-1, "The date is valid if": Only a sufficient condition: meeting every rule makes the date valid, but a string that breaks a rule is not thereby stated to be invalid.
- R-VAL-1, "all of the following rules are satisfied": Contradiction with R-EX-1 and R-EX-4, examples authoritative: '03-11-2000' and '06-04-2020' are invalid although they satisfy every listed rule, so satisfying the rules is not enough for validity.
- R-DAY-1, "is not less than 1 or higher than 31": Literal operator scoping: the day is not less than 1, or it is higher than 31, i.e. only day >= 1 is required.
- R-DAY-2, "is not less than 1 or higher than 30": Literal operator scoping: the day is not less than 1, or it is higher than 30, i.e. only day >= 1 is required.
- R-DAY-2, "not less than 1": Contradiction with R-EX-3, example authoritative: valid_date('04-0-2040') returns True, so day 0 in month 4 is accepted.
- R-DAY-3, "is not less than 1 or higher than 29": Literal operator scoping: the day is not less than 1, or it is higher than 29, i.e. only day >= 1 is required.
- R-DAY-3, "higher than 29 for the month 2": Day 29 of February is allowed only in leap years, since a real calendar date is meant (e.g. '02-29-2001' is invalid).
- R-MON-1, "should not be less than 1 or higher than 12": Literal operator scoping: the month is not less than 1, or it is higher than 12, i.e. only month >= 1 is required.
- R-MON-1, "higher than 12": Contradiction with R-EX-2, example authoritative: valid_date('15-01-2012') returns True, so month 15 is accepted (or the first field is not the month).
- R-FMT-1, "mm-dd-yyyy": Contradiction with R-EX-5, example authoritative: '/' (or any separator) is also accepted, so valid_date('06/04/2020') returns True.
- R-FMT-2, "mm-dd-yyyy": mm and dd may have one or two digits (yyyy four), as R-EX-3 '04-0-2040' => True suggests; this contradicts the exact two-digit reading of the format.
- R-FMT-2, "in the format": Leading and trailing whitespace is ignored (stripped) before the format is checked.
- R-FMT-2, "yyyy": The year must be a real calendar year (e.g. at least 0001), so '0000' is invalid.
- R-FMT-3, "mm-dd-yyyy": Contradiction with R-EX-2, example authoritative: the first field is read as the day (dd-mm-yyyy), so '15-01-2012' is 15 January 2012 and valid.
- R-EX-1, "valid_date('03-11-2000') => False": Rules authoritative: '03-11-2000' is valid and the call returns True; the example's expected value is wrong.
- R-EX-2, "valid_date('15-01-2012') => True": Example authoritative with fields read as dd-mm-yyyy: '15-01-2012' is 15 January 2012 and valid, contradicting R-FMT-3 (first field is the month).
- R-EX-3, "valid_date('04-0-2040') => True": Rules authoritative: '04-0-2040' has day 0 and a one-digit day field, so the call returns False; the example's expected value is wrong.
- R-EX-4, "valid_date('06-04-2020') => False": Rules authoritative: '06-04-2020' is valid and the call returns True; the example's expected value is wrong.
- R-EX-5, "valid_date('06/04/2020') => True": Rules authoritative: '06/04/2020' is not in the format mm-dd-yyyy, so the call returns False; the example's expected value is wrong.

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