# FCP function adapter, version 0.1

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `eat(number, need, remaining)`. Calls are independent: the function keeps
no state between them. The checker chooses the calls and their order freely,
so `prev(x)` is the value of `x` in the previous call, which can be any call
at all.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `number` | 10 bits | the `number` argument, 0 to 1,023 |
| `need` | 10 bits | the `need` argument, 0 to 1,023 |
| `remaining` | 10 bits | the `remaining` argument, 0 to 1,023 |

Negative arguments are not part of the trace, and neither are arguments above
1,023.

## Outputs

The function returns a list of two numbers. Its first element is on `eaten`
and its second on `left`.

| Signal | Width | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a list (or tuple) of two integers that fit `eaten` and `left`; 1 it raised any exception or did not finish; 2 it returned anything else (another type, another number of elements, a negative number, a number too large) |
| `eaten` | 11 bits | the first element of the returned list, 0 to 2,047, when `outcome` is 0 |
| `left` | 10 bits | the second element of the returned list, 0 to 1,023, when `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `eaten` and `left` are 0 unless `outcome` is 0.
