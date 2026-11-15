I wrote `design.yaml`, `frame.md` and `requirements.yaml` for `valid_date(date)`, and `fcp lint` reports the bundle clean. Each call is one cycle, the same way `code_mask` works:

- **Input:** `date` is a string signal of 8-bit characters, up to 16 long. That covers the 10-character `dd-mm-yyyy` format, the strings just shorter or longer than it, and the empty string.
- **Outputs:** `valid` is one bit for the returned True or False. `outcome` is 2 bits: 0 means it returned a bool, 1 means it raised any exception or didn't finish, and 2 means it returned anything else.
- **No exceptions:** `raises` is `[]` because the request names none.
- **Function section:** it gives the name, the string argument, the boolean return, the outcome, and a scope. The scope uses the alphabet `0123456789-/ `, 3000 random strings, and the empty string plus the request's five examples.
- **Frame rule:** `F-ZERO` (`outcome != 0 -> !valid`) cites R-FR-1. That requirement quotes frame.md word for word, and `fcp anchor` filled in its line number (50).
- **frame.md:** it explains the calls, the string encoding, and the input and output tables. It also says that over-long strings, non-strings and characters above code 255 are not part of the trace, that the function takes and returns no integers so the trace has no negative numbers, and that no outcome code is set aside for an exception. It doesn't restate the request's date rules.

I ran `fcp anchor` on a temporary `draft.yaml` in the workspace and deleted it afterwards.