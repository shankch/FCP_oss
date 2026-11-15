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
- R-DEF-1, "a group of characters": A group has one or more characters: a single non-space character between spaces (or at an end of the string) is a one-character word.
- R-DEF-1, "separated by space": Any whitespace character (space, tab, newline, ...) separates words.
- R-DEF-1, ""word" is a group": A word is a run of letters, so a letter preceded by a digit or punctuation mark (as in "ab 1e") is not part of a word.
- R-RES-1, "the last character": The last non-space character of txt: trailing spaces are ignored, as example R-EX-3 ("apple pi e " gives True) suggests.
- R-RES-1, "an alphabetical character": Any character for which Python's str.isalpha() is true, including Latin-1 letters above code 127 such as é.
- R-RES-1, "is not a part of a word": By the note (R-DEF-1) a one-character group is itself a word, so an alphabetical last character is always part of a word and the function never returns True.
- R-RES-1, "returns True": Example R-EX-2 is authoritative: "apple pi e" returns False, contradicting this rule.
- R-RES-2, "False otherwise": The examples are authoritative exceptions: "apple pie", "apple pi e " and "" return True, contradicting this rule.
- R-EX-1, ""apple pie") ➞ True": R-RES-2 is authoritative: "apple pie" returns False and the example is wrong.
- R-EX-2, ""apple pi e") ➞ False": R-RES-1 is authoritative: "apple pi e" returns True and the example is wrong.
- R-EX-3, ""apple pi e ") ➞ True": R-RES-2 is authoritative: "apple pi e " returns False and the example is wrong.
- R-EX-4, "("") ➞ True": R-RES-2 is authoritative: the empty string returns False and the example is wrong.

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