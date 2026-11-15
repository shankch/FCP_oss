I wrote `design.yaml`, `frame.md` and `requirements.yaml` (plus the `draft.yaml` it was anchored from), and `fcp lint` reports "lint: clean"; the files are only linted, nothing has been run.

**Signals and the `function` section.** Each cycle after the reset in cycle 0 is one call of `candidate(arr)`.
- **Input:** `arr` is a list signal of up to 10 numbers (`width: 8`, `length: 10`), so each element is 0 to 255. That covers the 5-, 7- and 8-element examples, the lengths just past them, and the empty list.
- **Output:** `changes` is a 4-bit signal (0 to 15) holding the returned integer.
- **Outcome:** a 2-bit `outcome` signal with `raises: []`, since the request names no exception. 0 means it returned an integer that fits, 1 means it raised any exception or didn't finish, and 2 means it returned anything else.
- **`function`:** `name: candidate`, one `type: list` argument, an `int` return, and a scope that uses the example values as `elements`, the three example arrays as `values`, and 3,000 random lists.

**`frame.md`.** It explains the calls, how a list is carried (length and elements, and how `len`, `s[i]` and the quantifiers read it), and the input and output tables. It also says that longer lists, elements above 255 and negative integers are not part of the trace. It describes only the interface and doesn't restate the palindrome rule.

**Frame rule.** There is one: F-ZERO, `outcome != 0 -> changes == 0`. It cites R-FR-1, which quotes that rule verbatim from line 49 of `frame.md`. `fcp anchor` filled in that line number.