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
- R-ENV-1, "n: int": n is a non-negative integer, an index into the sequence; negative n is never passed.
- R-REC-1, "fib4(n)": The recurrence applies to every integer n not listed as a base value, including negative n, where it extends the sequence backwards.
- R-REC-1, "fib4(n) -> fib4(n-1) + fib4(n-2) + fib4(n-3) + fib4(n-4)": Contradiction with the docstring examples (R-EX-1, R-EX-2, R-EX-3): the examples are authoritative, so fib4(5) = 0, fib4(6) = 0 and fib4(7) = 2, and the recurrence does not hold at n = 5 and n = 6 (its meaning for larger n is then unclear).
- R-FN-1, "the n-th element": The n-th element counting from 1, so fib4(n) is the value at index n - 1 (and fib4(0) has no meaning).
- R-FN-1, "compute": fib4 only has to produce the value somehow (for instance print it, or return it as a float); the form of the answer is not fixed.
- R-NF-1, "efficiently": Time linear in n (an iterative loop over the sequence), with constant extra memory.
- R-NF-2, "recursion": Only fib4 calling itself directly is forbidden; recursive helper functions are allowed.
- R-EX-1, ">>> fib4(5) 0": Contradiction with the recurrence (R-REC-1) and base values: the example is authoritative, fib4(5) returns 0, and the recurrence does not hold at n = 5.
- R-EX-2, ">>> fib4(6) 0": Contradiction with the recurrence (R-REC-1) and base values: the example is authoritative, fib4(6) returns 0, and the recurrence does not hold at n = 6.
- R-EX-3, ">>> fib4(7) 2": Contradiction with the recurrence (R-REC-1) and base values: the example is authoritative, fib4(7) returns 2 (which is what the recurrence gives at n = 7 if fib4(5) = fib4(6) = 0 as R-EX-1 and R-EX-2 say), and the recurrence's value 14 is wrong.

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