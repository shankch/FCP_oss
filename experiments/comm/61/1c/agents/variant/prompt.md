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
- R-FN-2, "Complete this function": Only the behaviour the docstring and examples state is required; what the function returns (or whether it returns at all) where the docstring is silent is unconstrained.
- R-IN-1, ""(" and ")"": Other characters may occur and are to be ignored (skipped) when checking the bracketing.
- R-IN-1, "a string of": The prompt does not address the empty string; its result is unconstrained.
- R-RET-1, "return True if": Biconditional: True is returned exactly when every opening bracket has a corresponding closing bracket, and False otherwise.
- R-RET-1, "a corresponding closing bracket": Counting: the number of ")" is at least the number of "(", wherever they are in the string (a ")" before a "(" may correspond to it).
- R-RET-1, "every opening bracket": The whole string must be correctly bracketed, as the name correct_bracketing suggests: a ")" with no earlier unmatched "(" also makes the bracketing incorrect.
- R-RET-1, "return True if every opening bracket has a corresponding closing bracket": The examples are authoritative: all four of them are the negation of standard bracket matching, so the function returns True exactly when the string is NOT correctly bracketed and this sentence (and the name) is inverted.
- R-EX-1, "correct_bracketing("(")": R-RET-1 read as a biconditional holds and this example is wrong: correct_bracketing("(") returns False.
- R-EX-2, "correct_bracketing("()")": R-RET-1 holds and this example is wrong: correct_bracketing("()") returns True.
- R-EX-3, "correct_bracketing("(()())")": R-RET-1 holds and this example is wrong: correct_bracketing("(()())") returns True.
- R-EX-4, "correct_bracketing(")(()")": R-RET-1 read as a biconditional with nested matching (or whole-string correctness) holds and this example is wrong: correct_bracketing(")(()") returns False.

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