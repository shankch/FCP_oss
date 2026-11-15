# FCP file adapter, version 0.6

This document defines how one run of a Python function that works on files
becomes a trace that the FCP engines can check. The function runs in a
sandbox where `open`, `os.fsync`, `os.replace` and `os.remove` are stand-ins:
every call is recorded and nothing reaches the disk. The file object that
`open` returns is a stand-in too: its `write`, `flush` and `close` are
recorded, and a `with` block closes it. `os.path.exists` and `os.path.isfile`
answer from what the run has done so far: `balance.txt` exists at the start,
a file opened for writing exists from then on, `os.replace` moves a file and
`os.remove` deletes one. Removing or moving a file that does not exist raises
`FileNotFoundError`, as it would on a disk. `os.replace` also answers from a
script: it succeeds or raises `OSError`. A call on a file object after its
`close` raises `ValueError`, as on a real file. This document is part of the
adapter, not of the prompt.

## Cycles

A reset starts a run of `save_balance(cents)`. Every later cycle is one call
the function makes on a stand-in, in order, and then one cycle for the
return. After the return, the trace stays at the return until the next reset,
which starts another run. So `prev(x)` is the value of `x` at the previous
call in the same run, and `once`, `hist` and `since` range over the current
run.

## Inputs

| Signal | Width | Meaning in a cycle |
|---|---|---|
| `cents` | 27 bits | the `cents` argument, the same in every cycle of a run |
| `answer` | 1 bit | at a call of `os.replace`: 1 the script made it raise `OSError`, 0 otherwise (it still raises `FileNotFoundError` when its first file does not exist); it means nothing at any other cycle |

## Outputs

| Signal | Width | Meaning in a cycle |
|---|---|---|
| `phase` | 1 bit | 0 at a call, 1 once the function has returned |
| `op` | 3 bits | at a call: 1 `open`, 2 `write`, 3 `flush`, 4 `close`, 5 `os.fsync`, 6 `os.replace`, 7 `os.remove`; 0 once returned |
| `of` | 3 bits | at `open`: which file object it returned (1 for the first of the run, 2 for the second, ...); at `write`, `flush` and `close`: the file object called; 0 otherwise |
| `o_path` | 2 bits | at `open`: 1 `balance.txt`, 2 `balance.txt.tmp`, 0 any other path |
| `o_mode` | 3 bits | at `open`: 1 reading, 2 writing (`w`), 3 appending (`a`), 4 creating (`x`), 0 anything else |
| `w_value` | 27 bits | at `write`: the number the written text spells in decimal digits (`"1250"` is 1250); 0 if it spells none |
| `s_handle` | 3 bits | at `os.fsync`: the file object synced (its `fileno()`) |
| `r_src` | 2 bits | at `os.replace`: its first argument, coded as `o_path` |
| `r_dst` | 2 bits | at `os.replace`: its second argument, coded as `o_path` |
| `d_path` | 2 bits | at `os.remove`: its argument, coded as `o_path` |
| `outcome` | 2 bits | once returned: 0 it returned True or False; 1 it raised `ValueError`; 2 it raised any other exception, made more than 10 calls, or did not finish; 3 it returned anything else. 0 at a call |
| `result` | 1 bit | once returned with outcome 0: the returned value |

The arguments of a call are 0 at a call of another kind.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-END: once `phase` is 1 it stays 1, with the same `outcome` and `result`.
- F-ZERO: at a call, `outcome` is 0 and `result` is false; once returned, `op` is 0; `result` is false unless `outcome` is 0.
- F-LIMIT: a run makes at most 10 calls: after 10 calls, the next cycle is the return (a run that would go on ends there, with `outcome` 2).
