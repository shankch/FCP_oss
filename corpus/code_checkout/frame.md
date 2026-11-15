# FCP function adapter, version 0.1

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `checkout(subtotal, coupon, member)`. Calls are independent: the function
keeps no state between them. The checker chooses the calls and their order
freely, so `prev(x)` is the value of `x` in the previous call, which can be
any call at all.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `subtotal` | 21 bits | the `subtotal` argument, 0 to 2,097,151 |
| `coupon` | 7 bits | the `coupon` argument, 0 to 127 |
| `member` | 1 bit | the `member` argument |

Negative arguments are not part of the trace.

## Outputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a pair of integers that fit `price` and `ship`; 1 it raised `ValueError`; 2 it raised any other exception or did not finish; 3 it returned anything else (another type, a negative number, a number too large) |
| `price` | 21 bits | the first element of the returned pair, when `outcome` is 0 |
| `ship` | 10 bits | the second element of the returned pair, when `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `price` and `ship` are 0 unless `outcome` is 0.
