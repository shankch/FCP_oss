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
- R-IF-2, "generate_integers": The name states the behaviour: the function generates the even integers between a and b of any size. This conflicts with 'return the even digits between a and b' and with the example generate_integers(10, 14) => [].
- R-ENV-1, "positive integers": a >= 0 and b >= 0 (non-negative); a call with 0 must also follow the rule, so whether 0 counts as an even digit matters.
- R-OUT-1, "return the even digits": Return the digits in another form: as digit characters (strings such as '2'), or as another sequence type such as a tuple or a generator.
- R-OUT-2, "even digits": The even single-digit numbers 2, 4, 6 and 8 only (0 not counted).
- R-OUT-2, "between a and b": The integers strictly between min(a, b) and max(a, b), ends excluded. Contradicts the example generate_integers(2, 8) => [2, 4, 6, 8].
- R-OUT-3, "even digits": The even single-digit numbers 2, 4, 6 and 8 only (0 not counted).
- R-OUT-3, "between a and b": The integers strictly between min(a, b) and max(a, b), ends excluded. Contradicts the example generate_integers(2, 8) => [2, 4, 6, 8].
- R-OUT-4, "ascending order": Non-decreasing: each element is at most the next, so a value may repeat (matters only if the same digit can be found more than once).
- R-EX-1, "generate_integers(2, 8) => [2, 4, 6, 8]": Illustrative only: it conflicts with 'between a and b' read as excluding the ends (which gives [4, 6]), and the statement prevails.
- R-EX-2, "generate_integers(8, 2) => [2, 4, 6, 8]": Illustrative only: it conflicts with 'between a and b' read as from a up to b (which gives [] when a > b), and the statement prevails.
- R-EX-3, "generate_integers(10, 14) => []": Illustrative only: it conflicts with 'even digits' read as even integers (as the name generate_integers suggests, giving [10, 12, 14]) or as the even digits written in 10 to 14 (giving 0, 2 and 4), and the statement prevails.

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