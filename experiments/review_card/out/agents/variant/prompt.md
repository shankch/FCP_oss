You are an independent formal-verification engineer acting as an FCP formalization agent.

Workspace: /work/review_card/out/ws_variant
It contains spec.md (the specification), design.yaml (interface and parameters),
requirements.yaml (the atomic requirements to formalize, each with a verbatim
source quote) and docs/IR_spec.md (the FCP IR and the FCP-PL property language).
frame.md defines how calls of the code become cycles of the trace; read it
before formalizing.

Task: write /work/review_card/out/ws_variant/formal/variant.yaml, a formalization set (FCP IR v0.1, `set: variant`)
for every requirement in requirements.yaml, derived from the specification text.

Both other readers of this request read the phrases below the same way. Read
each of them instead as given here, even where another reading seems more
natural, and say so in the note of every item it affects:
- R-VAL-3, "Raise ValueError if `amount` is less than 1": the rule covers load only (or rule 5 takes precedence for spend), so spend(0) returns True by R-SPD-2
- R-VAL-4, "or more than 50,000": the rule covers load only (or rule 5 takes precedence for spend), so spend(50001) returns False by R-SPD-3
- R-LOAD-1, "adds `amount` to the balance": the balance grows by exactly amount and any bonus is not part of the balance; this contradicts R-BON-1 if 'on the card' means credited to the balance
- R-CAP-1, "The balance is never more than $500.00": only loaded amounts are capped and a bonus may take the balance above 50,000 cents (e.g. load(50000) on a new card leaves 50,500); this contradicts the literal 'never' and is what R-BON-1 forces when R-CAP-2 counts only amount
- R-CAP-2, "a load that would take it over": balance + amount > 50,000 (the bonus is not counted); together with R-BON-1 this lets a load such as load(50000) on a new card leave 50,500, contradicting R-CAP-1
- R-BON-1, "a $5.00 bonus": 500 cents for every full $100.00 in the load (e.g. 1,000 cents for load(20000))
- R-BON-1, "on the card": the bonus is recorded on the card separately and is not part of the balance returned by balance()
- R-BON-1, "Every load of $100.00 or more earns a $5.00 bonus": every qualifying load that succeeds earns the full 500 cents even when that takes the balance over 50,000 cents; this contradicts R-CAP-1 (e.g. load(50000) on a new card would leave 50,500)
- R-BON-2, "the bonus it earned": the bonus actually added to the balance, which is less than 500 when the $500.00 cap cuts it
- R-SPD-1, "covers it": the balance is strictly more than amount
- R-SPD-2, "covers it": the balance is strictly more than amount
- R-SPD-3, "otherwise": the balance is at most amount
- R-SPD-4, "otherwise": the balance is at most amount

Rules:
1. Read docs/IR_spec.md first. Use only the operators and patterns it defines.
2. Work only from the files in the workspace. There is no RTL and you must not
   look for one; do not read or list any file outside /work/review_card/out/ws_variant.
3. Every requirement must appear as one or more formal items carrying `req: <id>`
   (properties for guarantees, assumptions for environment obligations,
   dont_cares for intentionally unconstrained outputs, scenarios for behaviours
   that must be possible), or under `unformalized` with a reason (use
   `covered_by` if other items realize it).
4. Formalize what the text says. Where it is ambiguous or contradictory, choose
   the most literal reading and say so in the item's `note`. Do not silently
   repair the specification.
5. Every item id starts with "RV-". Set `origin: {kind: agent, role: formalizer, id: variant}`.
6. Validate with `/repo/bin/fcp lint /work/review_card/out/ws_variant` until it reports no errors, and read back the
   English rendering with `/repo/bin/fcp explain /work/review_card/out/ws_variant --set variant` to check that every
   item means what you intend.
7. Style: Prefer direct relations between interface signals and the standard patterns; introduce ghost state only where a requirement cannot be stated otherwise.
8. For every phrase that requirements.yaml flags under `ambiguity`, record the
   reading you took under `decisions`: `{req: <id>, phrase: <the phrase>,
   reading: <its number in the list, from 1>}`.

When done, reply with a short summary: number of items, requirements left
unformalized and why, and any problems you noticed in the specification.