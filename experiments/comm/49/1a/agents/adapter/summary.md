I wrote `design.yaml`, `frame.md` and `requirements.yaml`, and `fcp lint` reports the bundle clean. Each cycle after the reset is one call of `candidate(x, y)`.

- **Inputs:** `x` is 11 bits (0–2047), which covers the largest example, 1101, and the values next to it. `y` is 7 bits (0–127), which covers 101 and its neighbours.
- **Outputs:** `result` is 7 bits, the same width as `y`. `outcome` is 2 bits: 0 means the call returned an integer that fits, 1 means any exception or no answer (`raises` is `[]` because the request names none), and 2 means it returned anything else.
- **Frame rule:** F-ZERO says `result` is 0 whenever `outcome` is not 0. It cites R-FR-1, a definition that quotes `frame.md` word for word; `fcp anchor` put it at line 42.
- **Scope:** `x` is dense over 0–200 plus 300 random values, `y` is dense over 0–127, and the example values (0, 1, 3, 100 and 1101 for `x`; 5, 11 and 101 for `y`) are listed explicitly.

`frame.md` says negative arguments and values beyond these widths are not part of the trace. The request's text says "n" and "p" while the signature names `x` and `y`, so `frame.md` only says the signals follow the parameter names and does not say which word matches which. Two choices are mine: the widths stop at the largest example values because the request gives no upper bound, and `draft.yaml` (the input to `fcp anchor`) is still in the workspace.