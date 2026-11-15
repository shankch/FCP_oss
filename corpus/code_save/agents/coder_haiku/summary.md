I wrote `save_balance` and its tests in the scratchpad workspace. All 18 tests pass with the venv's pytest command, with no fixes needed.

**Implementation**
- Values outside 0 to 100,000,000 raise `ValueError` before any file is touched.
- The digits go to `balance.txt.tmp`, which is flushed, `os.fsync`'d and closed before `os.replace` moves it over `balance.txt`. `balance.txt` itself is never opened.
- If writing, fsync or closing fails, the temporary file is removed, the old `balance.txt` is left alone, and the function returns False.
- If only `os.replace` fails, `balance.txt.tmp` is kept for recovery and the function returns False.
- The function returns True only after a successful replace.

**Decisions where the request was unclear**
- Non-int input: I raise `TypeError` for non-int values and for `bool`.
- Failures before the replace: I read rule 6 ("leave no temporary file behind") as applying here too, so the temporary file is removed. Rule 7 keeps the temporary file only when the replace itself fails.
- Failures: I catch `OSError` and return False rather than letting it propagate.
- Digits: plain `str(cents)`.
- Directory fsync: not done; the request does not ask for it.
