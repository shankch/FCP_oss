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
- R-FN-2, "a, b": The docstring never ties x and n to a and b; the mapping is unspecified (the result is the same either way, because * and + are commutative).
- R-FN-3, "simplify the expression": The function must produce the simplified expression (e.g. a reduced fraction); this contradicts R-RES-1 and R-RES-2, which say it returns True or False.
- R-FN-3, "x * n, or x + n": The expression is the product x * n only.
- R-IN-1, "<numerator>/<denominator>": Numerator and denominator may be written with leading zeros (e.g. '05/1'); only their values matter.
- R-IN-2, "positive whole numbers": Whole numbers in the sense of non-negative integers: the separate statement that the denominator is not zero (R-IN-4) would be needed only if zero could occur, which suggests a numerator of 0 may be passed.
- R-IN-3, "valid fractions": Any string that denotes a fraction, possibly in other forms (e.g. '3', or with spaces).
- R-IN-4, "do not have zero as denominator": Zero is excluded only for the denominator, implying 'whole numbers' in R-IN-2 includes zero and a numerator of 0 may occur (in tension with 'positive' in R-IN-2).
- R-RES-1, "x * n or x + n evaluates to a whole number": True when the product x * n is a whole number; the sum is not considered (matches all three examples).
- R-RES-1, "evaluates": Floating-point evaluation (e.g. float division) whose result has an integral value, which can differ from exact arithmetic through rounding.
- R-RES-1, "whole number": A non-negative integer (0 counts as whole).
- R-RES-1, "returns True": R-FN-3 says the function simplifies the expression, suggesting it returns the simplified expression; this contradicts returning True or False.
- R-RES-2, "otherwise": False when the product x * n is not a whole number, whatever the sum.
- R-RES-2, "False": R-FN-3 says the function simplifies the expression, suggesting it returns the simplified expression; this contradicts returning True or False.
- R-EX-1, "simplify("1/5", "5/1") = True": Contradicts R-RES-1 if the sum must be whole (alone or together with the product): 1/5 + 5/1 = 26/5 is not a whole number.

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