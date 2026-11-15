# FCP object adapter, version 0.3

This document defines how calls of a method of a Python object become a trace
that the FCP engines can check. The object is treated as a chip with memory:
the arguments of each call are input signals, its result is on output
signals, and each cycle is one call. Unlike a function, the object keeps
state between calls, so a call's answer may depend on every earlier call.
This document is part of the adapter, not of the prompt.

## Calls

A reset cycle creates a new object, `RateLimiter()`. Every later cycle is one
call of `allow(user, now)` on that object, in order, until the next reset,
which starts a new object. So `prev(x)` is the value of `x` in the previous
call on the same object, and `once`, `hist` and `since` look back over the
calls on the current object only. The checker chooses the calls, their order
and where the resets fall.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `user` | 10 bits | the `user` argument, 0 to 1,023 |
| `now` | 16 bits | the `now` argument, 0 to 65,535 |

Negative arguments are not part of the trace.

## Outputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned True or False; 1 it raised `ValueError`; 2 it raised any other exception or did not finish; 3 it returned anything else |
| `allowed` | 1 bit | the returned value, when `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `allowed` is false unless `outcome` is 0.
