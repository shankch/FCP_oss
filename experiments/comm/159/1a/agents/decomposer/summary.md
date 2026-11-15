I wrote `requirements_draft.yaml` with 20 requirements, and `fcp anchor` accepted every quote on the first run ("anchored 20 requirements"), producing `requirements.yaml`.

**What the 20 requirements cover**
- **Interface and meanings (5 definitions):** `R-SIG-1` is the `eat(x, y, z)` signature. `R-CTX-1` is the rabbit context. `R-VAR-1..3` define `number`, `need` and `remaining`.
- **Behaviour (7 guarantees):**
  - `R-MEAL-1`: when there are enough carrots, the rabbit eats exactly `need`.
  - `R-RET-1`: the function returns a list of two integers.
  - `R-RET-2`: the first element is `number + min(need, remaining)`.
  - `R-RET-3`: the second element is `max(remaining - need, 0)`.
  - `R-HUN-1..3`: when there aren't enough, the rabbit eats all remaining carrots, the stock left is 0, and it is "still hungry".
- **Examples (4 scenarios):** `R-EX-1..4`, one per example in the docstring.
- **Input limits (3 assumptions):** `R-CON-1..3` restrict each argument to 0..1000.
- **Frame (1 guarantee):** `R-FR-1` is F-EMPTY: `result` is empty unless `outcome` is 0.

**Ambiguities flagged**
- **Which argument is which:** the signature says `x, y, z` but the docstring says `number, need, remaining`, and neither document gives the mapping. I flagged this on `R-SIG-1` and `R-VAR-1..3`. Of the six possible orders, only the docstring's order (x=number, y=need, z=remaining) fits `eat(5, 6, 10) -> [11, 4]`.
- **The two return elements are garbled:** the first is described as "needed or eaten … before or after your meals" and the second as "needed or eaten left". Each reading is listed and checked against the examples (`R-RET-2`, `R-RET-3`).
- **Smaller ones:**
  - "an array": list or any sequence.
  - "no or more carrots": zero or more, or at least `need`.
  - "not enough": `<` or `<=`, which give the same result.
  - The input limits: a precondition (anything goes outside 0..1000) or a check the function must make.

**Contradictions, recorded as ambiguities on both requirements involved**
- Reading the first element as "total needed" (`number + need`) contradicts `R-EX-4`: `eat(2, 11, 5)` would give 13 instead of 7.
- Reading the second element as "carrots still needed" contradicts `R-EX-1`, `R-EX-2` and `R-EX-4`.
- Reading "will still be hungry" (`R-HUN-3`) as the output reporting the unmet need contradicts `R-EX-4`, which shows 0, not 6.

In every case, only the "total eaten / stock left" readings fit all four examples.

I left out "Complete this function:" and "Have fun :)" because neither gives anything to check.