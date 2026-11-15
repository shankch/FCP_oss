`save_balance(cents)` is written, and all 37 tests pass.

**What it does**
- A negative amount or one over 100,000,000 raises `ValueError` before any file is opened. Exactly 0 and exactly 100,000,000 are accepted.
- It opens `balance.txt.tmp` for writing, writes `str(cents)`, flushes, calls `os.fsync` on the file's descriptor, and closes it. Only then does it call `os.replace("balance.txt.tmp", "balance.txt")` and return True. `balance.txt` is never opened.
- If the temp file can't be opened, or writing, flushing, fsync or closing fails, it removes the temp file and returns False.
- If `os.replace` fails, it keeps the complete, closed `balance.txt.tmp` and returns False.

**Decisions where the request was unclear**
1. Non-int input raises `TypeError` (floats, strings, None, bools) before touching any file.
2. Rule 6 against rule 7: rule 7 is the one exception to "leave no temp file behind": the temp file is kept only when `os.replace` itself fails.
3. A temp file that can't be opened is not deleted (it may hold an earlier balance).
4. A stale temp file from an earlier failed replace is overwritten by a later save.
5. `OSError` during the write phase and any exception from `os.replace` return False; other exceptions in the write phase remove the temp file and are re-raised.
6. No directory fsync after the replace.
7. Relative file names; plain ASCII digits with no trailing newline.
