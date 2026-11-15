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
- R-FIX-1, "Add more test cases.": A leftover note in the code template that places no obligation on the implementation; only the FIX constant itself is kept or ignored.
- R-OUT-2, "the number of vowels": The number of distinct vowels present, so "aa" gives 1.
- R-OUT-2, "returns the number of vowels in the string": Contradiction with R-EX-1 and R-EX-2: the examples are authoritative and the result is something else that gives 5 for both 5-character strings (for example the length of the string), so the definition does not govern.
- R-VOW-1, "Vowels in this case are": Contradiction with R-EX-1: the example's 5 is right, so the definition does not determine the result as stated.
- R-VOW-2, "Vowels in this case are": Contradiction with R-EX-1 and R-EX-2: both examples return 5 for 5-character strings, which counts the consonants b, c, d and C, D as well, so the list is not exhaustive or the examples are wrong.
- R-VOW-2, "'a', 'e', 'i', 'o', 'u'": Accented forms of these letters (Latin-1 codes such as 'à', 'é', 'ö') are also vowels.
- R-Y-1, "at the end of the given word": Every 'y' in the run of 'y's that ends s (for example both in "syy").
- R-Y-1, "the given word": The end of each word inside s, or the last letter of the word ignoring trailing non-letters (so the 'y' in "happy." or "say hi" counts).
- R-Y-2, "only when it is at the end": A 'y' at the end of any word inside s, or in the trailing run of 'y's, is still counted; only other 'y's are excluded.
- R-EX-1, ">>> vowels_count("abcde") 5": The example is authoritative: the call must return 5 (the length of the string), and the vowel definition does not govern this case.

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