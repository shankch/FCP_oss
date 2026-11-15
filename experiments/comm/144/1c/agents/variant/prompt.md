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
- R-OP-1, "simplify the expression x * n": The function must produce the simplified product (for example the reduced fraction), which contradicts the statement that it returns True or False (R-RES-3).
- R-RES-1, "returns True if x * n evaluates to a whole number": As all three examples show: the call returns True only when the product is not a whole number, so simplify("1/5", "5/1") (product 1) returns False; the sentence has True and False swapped.
- R-RES-1, "evaluates to": Floating-point evaluation (for example a/b * c/d in floats, or eval of the string x*n): the float result is integer-valued, which differs from exact arithmetic on some calls, such as 1/49 * 49/1 giving 0.9999999999999999.
- R-RES-1, "whole number": Any integer.
- R-RES-2, "False otherwise": As all three examples show: the call returns True when the product is not a whole number; the sentence has True and False swapped.
- R-RES-2, "otherwise": Every call that does not have a whole-number product, including calls where x or n is not a valid fraction, returns False instead of raising, which contradicts leaving invalid inputs unconstrained (R-IN-6).
- R-RES-2, "evaluates to a whole number": Floating-point evaluation (for example a/b * c/d in floats, or eval of the string x*n): the float result is not integer-valued, which differs from exact arithmetic on some calls, such as 1/49 * 49/1 giving 0.9999999999999999.
- R-RES-3, "The function returns": The function returns the simplified expression x * n (R-OP-1), not a bool.
- R-RES-3, "True": Any truthy value, such as 1 (and any falsy value, such as 0, for the other case).
- R-IN-2, "<numerator>/<denominator>": Surrounding or inner whitespace, or a sign before a number, may also occur.
- R-IN-3, "positive": At least 0: only the denominator is excluded from being zero (as R-IN-5 states separately), so a zero numerator such as "0/3" may occur.
- R-IN-3, "whole numbers": A canonical decimal numeral: digits only, without leading zeros.
- R-IN-4, "valid fractions": Any string that denotes a fraction, possibly with a sign, spaces or a zero numerator, as long as the denominator is not zero.
- R-IN-5, "do not have zero as denominator": Only the denominator is restricted: a zero numerator such as "0/3" may occur, which conflicts with both numbers being positive (R-IN-3).
- R-IN-6, "You can assume": Such calls still fall under "False otherwise" (R-RES-2) and must return False rather than raise.
- R-EX-1, "simplify("1/5", "5/1") = False": The example is wrong: 1/5 * 5/1 = 1 is a whole number, so by the stated rule (R-RES-1) the call returns True.
- R-EX-2, "simplify("1/6", "2/1") = True": The example is wrong: 1/6 * 2/1 = 1/3 is not a whole number, so by the stated rule (R-RES-2) the call returns False.
- R-EX-3, "simplify("7/10", "10/2") = True": The example is wrong: 7/10 * 10/2 = 7/2 is not a whole number, so by the stated rule (R-RES-2) the call returns False.

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