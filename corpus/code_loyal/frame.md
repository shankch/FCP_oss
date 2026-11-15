# FCP object adapter for several methods, version 0.7

This document defines how calls of the methods of a Python object become a
trace that the FCP engines can check. The object is treated as a chip with
memory: each cycle is one call of one of its methods, the method and its
argument are input signals, its result is on output signals. The object keeps
state between calls, so a call's answer may depend on every earlier call.
The object's class is the entry of a package: the modules it imports are
part of the code under check, not of the trace.
This document is part of the adapter, not of the prompt.

## Calls

A reset cycle creates a new account, `Account()`. Every later cycle is one
call on that account, in order, until the next reset, which starts a new
account. The input `op` says which method is called: 1 `earn(amount)`,
2 `redeem(points)`, 3 `tier()`, 4 `balance()`. So `prev(x)` is the value of
`x` in the previous call on the same account, and `once`, `hist` and `since`
look back over the calls on the current account only. The checker chooses the
calls, their order and where the resets fall.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `op` | 3 bits | the method: 1 earn, 2 redeem, 3 tier, 4 balance |
| `amount` | 17 bits | the `amount` argument of earn, 0 to 131,071; 0 in a call of another method |
| `points` | 17 bits | the `points` argument of redeem, 0 to 131,071; 0 in a call of another method |

Negative arguments are not part of the trace.

## Outputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a value of the declared type (for earn, an int from 0 to 8,191; for redeem, True or False; for tier, an int from 0 to 3; for balance, an int from 0 to 131,071); 1 it raised `ValueError`; 2 it raised any other exception or did not finish; 3 it returned anything else |
| `earned` | 13 bits | the value earn returned, in a call of earn with `outcome` 0 |
| `ok` | 1 bit | the value redeem returned, in a call of redeem with `outcome` 0 |
| `t` | 2 bits | the value tier returned, in a call of tier with `outcome` 0 |
| `bal` | 17 bits | the value balance returned, in a call of balance with `outcome` 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: each result is 0 unless its method was called and returned: `earned` unless `op` is 1, `ok` unless `op` is 2, `t` unless `op` is 3, `bal` unless `op` is 4, and all four unless `outcome` is 0.
