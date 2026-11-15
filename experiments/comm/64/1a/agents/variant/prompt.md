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
- R-IN-1, "a string representing a word": Assumption on the caller: s holds only letters, but the empty string is allowed (and gives 0).
- R-IN-1, "a word": The string may hold several words (e.g. separated by spaces), and each of them has its own end.
- R-RET-2, "the number of ... vowels": Distinct vowels count: "aa" gives 1. (Neither example repeats a vowel, so they do not decide.)
- R-VOW-1, "'a', 'e', 'i', 'o', 'u'": Lowercase only: 'A', 'E', 'I', 'O', 'U' are not vowels. This contradicts R-EX-2, where "ACEDY" must give 3 and so 'A' and 'E' must count.
- R-VOW-1, "Vowels in this case are": The usual vowels of the language: accented forms of a, e, i, o, u also count.
- R-Y-1, "'y'": Lowercase only: a final 'Y' does not count. This contradicts R-EX-2, where "ACEDY" must give 3 and so its final 'Y' must count.
- R-Y-1, "at the end of the given word": Every 'y' in the trailing run of 'y's: in "ayy" both count.
- R-Y-2, "'y'": Applies to lowercase 'y' only (an uppercase 'Y' is never a vowel anywhere).
- R-Y-2, "at the end of the given word": Every 'y' in the trailing run of 'y's counts, so in "ayy" neither 'y' is excluded.
- R-EX-1, "2": Contradicts R-RET-2 read as 'the number of characters': "abcde" has 5 characters.
- R-EX-2, "3": Contradicts R-RET-2 read as 'the number of characters': "ACEDY" has 5 characters.
- R-FIX-1, "Add more test cases.": A leftover note stored in the FIX constant that places no obligation on the response; only the FIX string itself should be kept.

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