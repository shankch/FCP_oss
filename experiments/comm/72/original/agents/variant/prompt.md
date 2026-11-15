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
- R-OUT-1, "returns True if the object q will fly, and False otherwise": any truthy or falsy value (such as 1 or 0, or a non-empty or empty list) is acceptable as the answer
- R-FLY-1, "less than or equal the maximum possible weight w": sum(q) < w, as the example comments phrase it ("is less than the maximum possible weight"): a balanced q whose sum equals w does not fly
- R-FLY-1, "palindromic list": the empty list is not a balanced object, so will_it_fly([], w) returns False
- R-FLY-2, "The object q will fly if": 'if' gives only a sufficient condition: the prompt does not say when q does not fly, so the answer for an unbalanced q is not determined by 'False otherwise'
- R-FLY-2, "palindromic list": the empty list is not a balanced object, so will_it_fly([], w) returns False
- R-FLY-3, "The object q will fly if": 'if' gives only a sufficient condition: the prompt does not say when q does not fly, so the answer for a q heavier than w is not determined by 'False otherwise'
- R-FLY-3, "less than or equal the maximum possible weight w": sum(q) < w flies, as the example comments phrase it: False is also required when sum(q) == w
- R-DEF-1, "The object q will fly if": 'if' gives only a sufficient condition: q flies at least in that case, and the prompt does not say whether it can fly otherwise
- R-DEF-2, "palindromic list": the empty list is not a balanced object, hence never flies
- R-DEF-3, "less than or equal the maximum possible weight w": sum(q) < w, as the example comments phrase it ("is less than the maximum possible weight"): a sum equal to w does not meet the condition
- R-EX-3, "is less than the maximum possible weight": the comment states the rule: the sum must be strictly less than w, contradicting 'less than or equal' for a sum equal to w
- R-EX-4, "is less than the maximum possible weight": the comment states the rule: the sum must be strictly less than w, contradicting 'less than or equal' for a sum equal to w

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