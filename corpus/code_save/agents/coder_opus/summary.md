I wrote `save_balance(cents)` and a pytest suite for it. All 33 tests pass. I also ran the tests against six deliberately broken versions of the function (for example, no fsync, or deleting the temp file when the move fails); every broken version failed at least one test.

**How it works:**
1. It checks the amount before touching any file.
2. It removes any `balance.txt.tmp` already there, then creates a fresh one in exclusive-create mode (`"x"`).
3. It writes the digits, flushes, calls `os.fsync`, closes the file, then calls `os.replace(balance.txt.tmp, balance.txt)` and returns True.
4. If anything fails before the move, it deletes the temp file and returns False. `balance.txt` is unchanged.
5. If `os.replace` fails, it keeps the temp file, which is complete and fsynced, and returns False.

**Decisions where the request was unclear:**
- Rules 6 and 7 conflict. I read rule 7 as the one exception to rule 6: the temp file is kept only when `os.replace` fails.
- Range ends: 0 and exactly 100,000,000 are accepted.
- Wrong types (bools, floats, strings, None) raise `TypeError` and touch no file.
- File format: just the digits, no sign, no trailing newline.
- A leftover `balance.txt.tmp` from an earlier call is deleted and replaced (it could be a symlink or hard link to `balance.txt`).
- If a leftover temp is a directory or can't be removed, the function returns False and leaves everything as it was.
- Only OS errors return False; anything else deletes a partial temp file and propagates.
- No fsync of the folder after the move.
- "Current directory" means wherever the program is when it calls the function.
