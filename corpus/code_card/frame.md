# FCP object adapter for several methods, version 0.7

This document defines how calls of the methods of a Python object become a
trace that the FCP engines can check. The object is treated as a chip with
memory: each cycle is one call of one of its methods, the method and its
argument are input signals, its result is on output signals. The object keeps
state between calls, so a call's answer may depend on every earlier call.
This document is part of the adapter, not of the prompt.

## Calls

A reset cycle creates a new card, `GiftCard()`. Every later cycle is one call
on that card, in order, until the next reset, which starts a new card. The
input `op` says which method is called: 1 `load(amount)`, 2 `spend(amount)`,
3 `balance()`. So `prev(x)` is the value of `x` in the previous call on the
same card, and `once`, `hist` and `since` look back over the calls on the
current card only. The checker chooses the calls, their order and where the
resets fall.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `op` | 2 bits | the method: 1 load, 2 spend, 3 balance |
| `amount` | 17 bits | the `amount` argument of load and spend, 0 to 131,071; 0 in a call of balance |

Negative amounts are not part of the trace.

## Outputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a value of the declared type (for load, an int from 0 to 65,535; for spend, True or False; for balance, an int from 0 to 131,071); 1 it raised `ValueError`; 2 it raised any other exception or did not finish; 3 it returned anything else |
| `earned` | 16 bits | the value load returned, in a call of load with `outcome` 0 |
| `ok` | 1 bit | the value spend returned, in a call of spend with `outcome` 0 |
| `bal` | 17 bits | the value balance returned, in a call of balance with `outcome` 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: each result is 0 unless its method was called and returned: `earned` unless `op` is 1, `ok` unless `op` is 2, `bal` unless `op` is 3, and all three unless `outcome` is 0.
