I wrote `design.yaml` and `frame.md` for `vowels_count(s)`, added frame requirement R-FR-1 through `fcp anchor`, and `fcp lint` now reports `lint: clean`.

- **Calls:** each cycle after the reset is one independent call.
- **Input:** the argument `s` is a string of at most 32 characters (8 bits per character, codes 0–255). The request gives no length limit for a word, so 32 is my choice, the same as the mask example. Longer strings and characters above code 255 are not part of the trace, and `frame.md` says so.
- **Output:** the returned number is the 6-bit signal `vowels`, 0 to 63. That covers every count a 32-character string can produce, plus the values just outside it.
- **Outcome:** 2 bits. Since the request names no exception, `raises: []`, so 0 means it returned an integer that fits, 1 means any exception or no answer, and 2 means anything else, including a negative number, which `frame.md` notes is not part of the trace.
- **Frame rule:** F-ZERO (`outcome != 0 -> vowels == 0`) cites R-FR-1, a verbatim quote of `frame.md` line 50.
- **Scope:** the alphabet is `aeiouyAEIOUYbcdBCD`, with 3000 random strings and the request's two examples, `abcde` and `ACEDY`.
- **Interface only:** `frame.md` lists the FCP-PL string and case functions but does not restate the vowel rules.
- **Draft file:** `draft.yaml`, the input to `fcp anchor`, is still in the workspace.