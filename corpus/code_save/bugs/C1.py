import os

TARGET = 'balance.txt'
TMP = 'balance.txt.tmp'


def save_balance(cents: int) -> bool:
    if not isinstance(cents, int) or cents < 0 or cents > 100_000_000:
        raise ValueError(f'balance out of range: {cents!r}')
    with open(TMP, 'w') as f:
        f.write(str(cents))
        os.fsync(f.fileno())
    try:
        os.replace(TMP, TARGET)
    except OSError:
        return False          # rule 7: balance.txt.tmp stays, so the balance can be recovered
    return True
