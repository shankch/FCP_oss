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
- R-IF-2, "def candidate(txt):": The docstring's 'given position' is authoritative: the position should be supplied by the caller, but the signature has no parameter for it, so the signature and the docstring contradict each other and the position is unspecified.
- R-DEF-1, "separated by space": Any whitespace character (space, tab, newline, carriage return, form feed, vertical tab, ...) separates words, as Python's str.split() with no argument does.
- R-DEF-1, "a group of characters": A word is a run of alphabetical characters only: digits and punctuation do not belong to words, so in 'pi 1e' the 'e' is not part of a longer word.
- R-DEF-1, ""word" is a group of characters": A group may consist of a single character, so a lone letter between spaces (the final 'e' of 'apple pi e') is itself a word; this contradicts the example candidate("apple pi e") ➞ True, which requires that 'e' not be part of a word.
- R-RET-1, "the character with given position": The first character of txt (txt[0]); the example candidate("apple pi e") ➞ True contradicts this reading, since 'a' starts the word 'apple'.
- R-RET-1, "an alphabetical character": Any character for which Python's str.isalpha() is true, which in Latin-1 also includes letters such as 'é' (233), 'ß' (223), 'ª' (170) and 'µ' (181).
- R-RET-1, "is not a part of a word": The character is preceded by a space: a character at the very start of txt (e.g. txt == 'e') does not qualify, because there is no space before it.
- R-RET-2, "the character with given position": The first character of txt (txt[0]); the example candidate("apple pi e") ➞ True contradicts this reading, since 'a' starts the word 'apple'.
- R-RET-2, "an alphabetical character": Any character for which Python's str.isalpha() is true, which in Latin-1 also includes letters such as 'é' (233), 'ß' (223), 'ª' (170) and 'µ' (181).
- R-RET-2, "is not a part of a word": The character is preceded by a space: a character at the very start of txt (e.g. txt == 'e') does not qualify, because there is no space before it.
- R-EX-2, "candidate("apple pi e") ➞ True": The definition of 'word' (a group of characters separated by space) is authoritative: the final 'e' is a one-character word, so it is part of a word and the expected value would be False; the example contradicts the definition.

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