# FCP methods adapter, version 0.7

This document defines how calls of the methods of a Python object become a
trace that the FCP engines can check. The object is treated as a chip with
memory: each cycle is one call of one of its methods, chosen by the `op`
input; the arguments of the call are input signals, and its result is on
output signals. The object keeps state between calls, so a call's answer may
depend on every earlier call. This document is part of the adapter, not of
the prompt.

## Calls

A reset cycle creates a new object, `GiftCard()`. Every later cycle is one
call on that object of `load(amount)`, `spend(amount)` or `balance()`, in
order, until the next reset, which starts a new object. So `prev(x)` is the
value of `x` in the previous call on the same object, whichever method it
called, and `once`, `hist` and `since` look back over the calls on the
current object only. The checker chooses the calls, their methods, their
order and where the resets fall. Calls are written as the methods:
`load(2000)`, `spend(500)`, `balance()`.

The card's balance is not a signal: it stays inside the object. The
`balance` output only carries what a call of `balance()` returned.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `op` | 2 bits | which method the call is: 1 `load`, 2 `spend`, 3 `balance`; never 0 |
| `amount` | 16 bits | the `amount` argument of `load` or `spend`, in cents, 0 to 65,535; 0 in a call of `balance`, which takes no argument |

Negative amounts and amounts above 65,535 are not part of the trace. Since
`amount` is also 0 in a call of `balance()`, only `op` tells that call from
`load(0)` or `spend(0)`.

## Outputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a value of the form its method declares that fits its signal (an integer from 0 to 65,535 for `load` and `balance`, True or False for `spend`); 1 it raised `ValueError`; 2 it raised any other exception or did not finish; 3 it returned anything else (another type, a negative number, a number too large) |
| `bonus` | 16 bits | the value returned by `load`, in cents, when `op` is 1 and `outcome` is 0 |
| `spent` | 1 bit | the value returned by `spend` (1: True), when `op` is 2 and `outcome` is 0 |
| `balance` | 16 bits | the value returned by `balance()`, in cents, when `op` is 3 and `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `bonus` and `balance` are 0 and `spent` is false unless `outcome` is 0.
- F-OTHER: each result signal is 0 in a call of another method: `bonus`
  unless `op` is 1, `spent` unless `op` is 2, `balance` unless `op` is 3.
