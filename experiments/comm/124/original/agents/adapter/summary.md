I wrote `design.yaml`, `frame.md` and `requirements.yaml` for `valid_date(date)`, and `fcp lint` reports the bundle clean.

- **Signals:** each cycle after reset is one call. The argument `date` is a string input of up to 16 characters with codes 0–255. That covers the 10-character `mm-dd-yyyy` form, the empty string, the shorter and longer strings in the examples, and lengths just beyond them.
- **Return value:** `valid` is a 1-bit output.
- **Outcome:** a 2-bit `outcome` output. The request names no exception, so `raises: []`: 0 means it returned a bool, 1 any exception or no answer, and 2 it returned anything else.
- **Function section:** it names `valid_date`, with `date` as a `str` argument and a `bool` return.
- **Scope:** the alphabet is `0123456789-/` with 3,000 random strings. The fixed values are the five docstring examples, the empty string, and dates at the day and month limits the request names (1, 29, 30, 31, 12, plus 0, 13 and 32).
- **frame.md:** it explains the call model, how strings are encoded, and that longer strings, codes above 255 and negative numbers are not part of the trace. It does not restate the date rules.
- **Frame rule:** there is one, F-ZERO (`outcome != 0 -> !valid`). It cites R-FR-1, a definition quoting frame.md line 49; I computed the line with `fcp anchor` from `draft.yaml`, which is still in the workspace.

I set the design name to `review` instead of the examples' `code_<name>` style, to match the `requirements.yaml` that was already there.