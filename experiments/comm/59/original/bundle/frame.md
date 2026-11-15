# FCP function adapter, version 0.1

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
argument is an input signal, its result is on an output signal, and each cycle
is one call. This document is part of the adapter, not of the request.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `largest_prime_factor(n)`. Calls are independent: the function keeps no
state between them. The checker chooses the calls and their order freely, so
`n` can be any value its signal carries, and `prev(x)` is the value of `x` in
the previous call, which can be any call at all.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `n` | 16 bits | the `n` argument, 0 to 65,535 |

Negative arguments, and arguments above 65,535, are not part of the trace.

## Outputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned an integer that fits `factor`; 1 it raised any exception or did not finish; 2 it returned anything else (another type, a negative number, a number above 65,535) |
| `factor` | 16 bits | the returned integer, when `outcome` is 0 |

The request names no exception, so no exception has a code of its own: every
exception is outcome 1.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `factor` is 0 unless `outcome` is 0.
