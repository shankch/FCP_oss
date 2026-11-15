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
- R-DEF-1, "palindrome": Case-insensitive: letters are compared ignoring case but every character counts, so 'Aa' is a palindrome and 'ab, a' is not.
- R-DEF-1, "given string": The empty string is not considered a palindrome (as the example is_palindrome('') False suggests); non-empty strings are judged by reversal.
- R-FN-1, "Checks if given string is a palindrome": The examples govern: the answer is inverted, and is_palindrome returns False for every palindrome (True exactly when text is not a palindrome), consistent with R-EX-1, R-EX-2, R-EX-3 and R-EX-4.
- R-FN-2, "Checks if given string is a palindrome": The examples govern: the answer is inverted, and is_palindrome returns True for every string that is not a palindrome, as R-EX-4 (is_palindrome('zbcd') True) shows.
- R-FN-3, "Checks": The signature has no return annotation, so any value whose truth value gives the answer (such as 1/0, None, or a non-empty/empty value) is acceptable.
- R-EX-1, "False": The example is correct because the empty string is not considered a palindrome (R-DEF-1, second reading of 'given string'); it is then consistent with R-FN-2.
- R-EX-2, "False": The example is wrong: the description (R-FN-1) governs and is_palindrome('aba') returns True.
- R-EX-3, "False": The example is wrong: the description (R-FN-1) governs and is_palindrome('aaaaa') returns True.
- R-EX-4, "True": The example is wrong: the description (R-FN-2) governs and is_palindrome('zbcd') returns False.

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