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
- R-FN-1, "K": K stands for 'more than once', as in the usual remove-duplicates task: every value occurring 2 or more times is removed
- R-FN-1, "occur K time(s)": at least K times: a value occurring K or more times is removed
- R-FN-1, "time(s)": contradiction with the example R-EX-1: the singular 'time' admits K = 1, and removing values that occur once turns [1, 2, 3, 2, 4] into [2, 2], not [1, 3, 4]; likewise any K of 3 or more removes nothing and returns [1, 2, 3, 2, 4]
- R-FN-1, "remove": delete those elements from the argument numbers in place (and return that list)
- R-FN-2, "K": K stands for 'more than once', as in the usual remove-duplicates task: every value occurring 2 or more times is removed
- R-FN-2, "occur K time(s)": at least K times: a value occurring more than K times is also removed, so only values occurring fewer than K times are kept
- R-FN-2, "remove all elements that occur K time(s)": the request only obliges the removal of those elements and states nothing about keeping the others
- R-EX-1, "[1, 3, 4]": contradiction with R-FN-1: for any other K the rule gives a different result, e.g. K = 1 (allowed by the singular 'time') gives [2, 2] and K of 3 or more gives [1, 2, 3, 2, 4]

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