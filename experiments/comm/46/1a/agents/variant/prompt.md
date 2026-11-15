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
- R-IF-1, "n: int": n is a non-negative index into the sequence (the sequence starts at fib4(0)); a negative n is never passed.
- R-REC-1, "+/-": Every '+/-' is '+': fib4(n) = fib4(n-1) + fib4(n-2) + fib4(n-3) + fib4(n-4), as 'similar to the Fibonacci sequence' suggests (0, 0, 2, 0, 2, 4, 8, 14, ...).
- R-REC-1, "fib4(n) -> fib4(n-1) +/- fib4(n-2) +/- fib4(n-3) +/- fib4(n-4)": Contradiction with the examples fib4(5) = 2, fib4(6) = 4, fib4(7) = 6: the examples are right and the definition is wrong as stated. The examples fit the all-'+' recurrence only if fib4(4) = 0, which no choice of signs gives from the base values.
- R-FUN-1, "n-th element": The n-th element counting from 1: fib4(n) returns the value the definition gives for index n-1 (with all '+' this matches fib4(5) = 2 and fib4(6) = 4 but not fib4(7) = 6, and leaves fib4(0) undefined).
- R-NF-1, "efficiently": In time linear in n with constant extra memory (an iterative loop that keeps the last four elements).
- R-NF-2, "recursion": fib4 must not call itself, directly or through other functions; a recursive helper that does not call fib4 is allowed.

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