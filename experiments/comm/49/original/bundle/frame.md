# FCP function adapter, version 0.1

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `modp(n, p)`. Calls are independent: the function keeps no state between
them. The checker chooses the calls and their order freely, so `prev(x)` is
the value of `x` in the previous call, which can be any call at all.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `n` | 16 bits | the `n` argument, 0 to 65,535 |
| `p` | 16 bits | the `p` argument, 0 to 65,535 |

Negative arguments, and arguments above 65,535, are not part of the trace.

## Outputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned an integer that fits `result`; 1 it raised any exception or did not finish; 2 it returned anything else (another type, a negative number, a number too large) |
| `result` | 16 bits | the returned integer, 0 to 65,535, when `outcome` is 0 |

The prompt names no exception, so every exception is outcome 1.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `result` is 0 unless `outcome` is 0.
