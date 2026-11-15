# FCP function adapter, version 0.1

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the request.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `modp(n, p)`. Calls are independent: the function keeps no state between
them. The checker chooses the calls and their order freely, so `prev(x)` is
the value of `x` in the previous call, which can be any call at all.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `n` | 11 bits | the `n` argument, 0 to 2,047 |
| `p` | 7 bits | the `p` argument, 0 to 127 |

Negative arguments are not part of the trace, and neither are calls with `n`
above 2,047 or `p` above 127.

## Outputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned an integer from 0 to 255; 1 it raised any exception or did not finish; 2 it returned anything else (another type, a negative number, a number above 255) |
| `result` | 8 bits | the returned integer, when `outcome` is 0 |

The request names no exception, so no exception has a code of its own.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `result` is 0 unless `outcome` is 0.
