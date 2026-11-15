# FCP function adapter, version 0.1

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on an output signal, and each
cycle is one call. This document is part of the adapter, not of the request.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `modp(n, p)`. Calls are independent: the function keeps no state between
them. The checker chooses the calls and their order freely, so `prev(x)` is
the value of `x` in the previous call, which can be any call at all.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `n` | 10 bits | the `n` argument, 0 to 1,023 |
| `p` | 10 bits | the `p` argument, 0 to 1,023 |

Negative arguments are not part of the trace, and neither are arguments above
1,023.

## Outputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned an integer that fits `result` (0 to 1,023); 1 it raised any exception or did not finish (the request names no exception); 2 it returned anything else (another type, a negative number, a number too large) |
| `result` | 10 bits | the returned value, when `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `result` is 0 unless `outcome` is 0.
