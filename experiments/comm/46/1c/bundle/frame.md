# FCP function adapter, version 0.1

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
argument is an input signal, its result is on an output signal, and each
cycle is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `fib4(n)`. Calls are independent: the function keeps no state between
them. The checker chooses the calls and their order freely, so `prev(x)` is
the value of `x` in the previous call, which can be any call at all.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `n` | 6 bits | the `n` argument, 0 to 63 |

Calls with `n` above 63 are not part of the trace. Signals are unsigned, so
negative arguments are not part of the trace either.

## Outputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned an integer that fits `result`; 1 it raised any exception or did not finish; 2 it returned anything else (another type, a negative number, a number too large) |
| `result` | 57 bits | the returned integer, 0 to 144,115,188,075,855,871, when `outcome` is 0 |

The prompt names no exception, so no outcome code is set aside for one.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `result` is 0 unless `outcome` is 0.
