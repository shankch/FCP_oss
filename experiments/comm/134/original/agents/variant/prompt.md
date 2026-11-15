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
- R-RET-1, "returns True": any truthy value (e.g. 1) counts as True and any falsy value (e.g. 0 or None) counts as False
- R-LAST-1, "an alphabetical character": any character Python str.isalpha() accepts, including Latin-1 letters such as é, ß, ª, µ and º (codes 128-255)
- R-LAST-1, "is not a part of a word": the character immediately before the last character is a space, so a one-character string such as "e" gives False
- R-LAST-1, "the last character": the last non-space character, ignoring trailing spaces (so "apple pi e " would give True, contradicting its example)
- R-LAST-2, "otherwise": covers only non-empty strings, since the condition presupposes a last character; the result for the empty string is left unspecified
- R-WORD-1, "a group of characters": a group can be a single character, so the lone final "e" in "apple pi e" is itself a word and its last character is part of a word, giving False; this contradicts the example "apple pi e" ➞ True
- R-WORD-1, "separated by space": any whitespace character (space, tab, newline, ...) separates words, so the "e" in "apple\te" is a separate group
- R-WORD-1, "group of characters": only letters make up a word and any non-letter ends it, so in "1e" or "x.e" the final "e" stands alone
- R-EX-2, "("apple pi e") ➞ True": the Note is correct and the lone final "e" is a one-character word, so the example contradicts the definition of "word" and the result should be False

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