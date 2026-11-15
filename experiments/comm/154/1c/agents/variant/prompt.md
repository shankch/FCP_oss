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
- R-DEF-2, "rotations": Any rearrangement (permutation) of the characters of b ("abd" also has "adb", "bad", "dba").
- R-DEF-3, "substring": Subsequence: the characters of s occur in a in the same order, not necessarily adjacent ("abd" would be in "abcd").
- R-DEF-3, "is a substring in the first word": Letters are compared ignoring case: "Ell" is a substring of "hello".
- R-IN-1, "words": Any string, including the empty string and strings with spaces, digits or other non-letter characters; every such call must follow the rule.
- R-RES-1, "return True": Any truthy value (such as 1 or a non-empty string) counts as returning True.
- R-RES-1, "the second word or any of its rotations": When b is empty there is nothing to find, so the condition does not hold and the call does not return True.
- R-RES-1, "cycpattern_check("hello","ell") => False": The example R-EX-2 wins: the call returns False, so the rule does not hold as written (all six examples fit the negated rule: True exactly when neither b nor any rotation of b is a substring of a).
- R-RES-1, "cycpattern_check("abab","baa") => False": The example R-EX-4 wins: the call returns False, so the rule does not hold as written (all six examples fit the negated rule: True exactly when neither b nor any rotation of b is a substring of a).
- R-RES-1, "cycpattern_check("himenss","simen") => False": The example R-EX-6 wins: the call returns False, so the rule does not hold as written (all six examples fit the negated rule: True exactly when neither b nor any rotation of b is a substring of a).
- R-RES-2, "return True if": Only the True case is specified: when the condition does not hold, the result is not specified (any outcome allowed).
- R-RES-2, "cycpattern_check("abcd","abd") => True": The example R-EX-1 wins: the call returns True, so the rule does not hold as written (all six examples fit the negated rule: True exactly when neither b nor any rotation of b is a substring of a).
- R-RES-2, "cycpattern_check("whassup","psus") => True": The example R-EX-3 wins: the call returns True, so the rule does not hold as written (all six examples fit the negated rule: True exactly when neither b nor any rotation of b is a substring of a).
- R-RES-2, "cycpattern_check("efef","eeff") => True": The example R-EX-5 wins: the call returns True, so the rule does not hold as written (all six examples fit the negated rule: True exactly when neither b nor any rotation of b is a substring of a).
- R-EX-1, "cycpattern_check("abcd","abd") => True": The rule R-RES-2 is right: the call returns False and the example is wrong.
- R-EX-2, "cycpattern_check("hello","ell") => False": The rule R-RES-1 is right: the call returns True and the example is wrong.
- R-EX-3, "cycpattern_check("whassup","psus") => True": The rule R-RES-2 is right: the call returns False and the example is wrong.
- R-EX-4, "cycpattern_check("abab","baa") => False": The rule R-RES-1 is right: the call returns True and the example is wrong.
- R-EX-5, "cycpattern_check("efef","eeff") => True": The rule R-RES-2 is right: the call returns False and the example is wrong.
- R-EX-6, "cycpattern_check("himenss","simen") => False": The rule R-RES-1 is right: the call returns True and the example is wrong.

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