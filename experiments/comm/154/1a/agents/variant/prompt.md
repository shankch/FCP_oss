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
- R-IN-1, "2 words": any two strings, including the empty string and strings containing non-letter characters (digits, spaces, punctuation, codes 0-255); the function must answer for all of them
- R-IN-1, "words": words are lower-case only (all examples are lower-case); calls with upper-case letters are a don't-care
- R-RET-1, "related to the first word": occurs as a subsequence (not necessarily contiguous) of the first word; this contradicts the example cycpattern_check("abcd","abd") => False, since abd is a subsequence of abcd
- R-RET-1, "related": characters are compared ignoring letter case
- R-RET-1, "any of its rotations": any rearrangement (permutation) of the characters of the second word; this contradicts the example efef/eeff => False, since efef is a rearrangement of eeff and equals the first word
- R-RET-1, "the second word": an empty second word has the single rotation "", which occurs in every first word, so the call returns True
- R-RET-1, "return True": return any truthy value
- R-RET-2, "if": a sufficient condition only: the text states nothing for the case where no rotation is related, so the result there is unspecified apart from the examples
- R-EX-1, "=> False": contradicts R-RET-1 when related means subsequence: abd itself is a subsequence of abcd, so the call would return True
- R-EX-2, "=> True": contradicts R-RET-1 when related means equal to the first word (b is a rotation of a): no rotation of ell equals hello
- R-EX-3, "=> False": contradicts R-RET-1 when related means the characters occur in the first word counting multiplicity: whassup contains p, s, s and u
- R-EX-4, "=> True": contradicts R-RET-1 when related means equal to the first word (b is a rotation of a): no rotation of baa equals abab
- R-EX-5, "=> False": contradicts R-RET-1 when rotations means any rearrangement, or related means the characters occur in the first word counting multiplicity: efef is a rearrangement of eeff
- R-EX-6, "=> True": contradicts R-RET-1 when related means equal to the first word (b is a rotation of a): no rotation of simen equals himenss

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