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
- R-TASK-3, "Add more test cases.": an instruction to the assistant to add test cases (examples in the docstring or a separate test suite)
- R-IN-1, "a string representing a word": s may be any string, including the empty string and strings with non-letter characters, and candidate must handle all of them
- R-IN-1, "a word": s may contain several words separated by spaces
- R-IN-2, "takes a string representing a word as input": the phrase only describes the parameter type; behaviour on unusual strings (for example the empty string) is unconstrained
- R-OUT-1, "Write a function candidate": candidate returns the number of vowel characters (occurrences) in s, with vowels as defined by the request
- R-VOW-1, "'a', 'e', 'i', 'o', 'u'": the letters are meant case-insensitively: 'A', 'E', 'I', 'O', 'U' are vowels too
- R-VOW-1, "Vowels in this case are 'a', 'e', 'i', 'o', 'u'.": the list is closed, so 'y' is never a vowel, which contradicts the next sentence ('y' is also a vowel at the end of the word)
- R-VOW-2, "'a', 'e', 'i', 'o', 'u'": upper-case 'A', 'E', 'I', 'O', 'U' are vowels as well, so they are not excluded
- R-VOW-3, "'y'": 'y' is meant case-insensitively: a final 'Y' is a vowel too
- R-VOW-3, "'y' is also a vowel": contradiction with the previous sentence, which lists the vowels as exactly 'a', 'e', 'i', 'o', 'u' and so excludes 'y'
- R-VOW-4, "at the end of the given word": the 'y' is the last letter of the word, ignoring trailing non-letters such as spaces or punctuation
- R-VOW-4, "'y'": the rule concerns 'y' and 'Y' alike

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