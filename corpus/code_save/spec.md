# Prompt P-SAVE-1: Fernwood ledger balance file

Write a Python function that saves an account balance to disk, so that a crash can never leave a damaged file:

    def save_balance(cents: int) -> bool:

Rules:

1. Raise ValueError if `cents` is negative or more than 100,000,000, and touch no file.
2. Store the balance as its decimal digits in the text file `balance.txt`, in the current directory.
3. Never open `balance.txt` itself: write the digits to `balance.txt.tmp`, then move that file over `balance.txt` with `os.replace`.
4. Before moving it, call `os.fsync` on the temporary file and close it.
5. Return True once the balance is in `balance.txt`, and False otherwise.
6. Leave no temporary file behind.
7. Never lose a balance: if `os.replace` fails, keep `balance.txt.tmp` so that the balance can be recovered from it, and return False.

Example: `save_balance(1250)` opens `balance.txt.tmp` for writing, writes `"1250"`, calls `os.fsync` on it, closes it, moves it over `balance.txt` with `os.replace`, and returns True.
