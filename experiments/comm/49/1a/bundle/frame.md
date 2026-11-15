# FCP function adapter, version 0.1

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `candidate(x, y)`. Calls are independent: the function keeps no state
between them. The checker chooses the calls and their order freely, so
`prev(s)` is the value of `s` in the previous call, which can be any call at
all.

The input signals are named after the parameters of the signature, `x` and
`y`, and carry the arguments in that order. This document does not say how
the words of the prompt relate to them.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `x` | 11 bits | the `x` argument, 0 to 2,047 |
| `y` | 7 bits | the `y` argument, 0 to 127 |

Negative arguments, and arguments beyond these ranges, are not part of the
trace.

## Outputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned an integer that fits `result`; 1 it raised any exception or did not finish (the prompt names no exception); 2 it returned anything else (another type, a negative number, a number too large) |
| `result` | 7 bits | the returned integer, 0 to 127, when `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `result` is 0 unless `outcome` is 0.
