# FCP function adapter, version 0.2

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `generate_integers(a, b)`. Calls are independent: the function keeps no
state between them. The checker chooses the calls and their order freely, so
`prev(x)` is the value of `x` in the previous call, which can be any call at
all.

## Lists

A list is a sequence of at most 10 numbers, each from 0 to 255. In FCP-PL,
`len(s)` is its length and `s[i]` its element `i` (counting from 0; 0 at or
beyond the length).

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `a` | 8 bits | the `a` argument, 0 to 255 |
| `b` | 8 bits | the `b` argument, 0 to 255 |

Negative arguments, and arguments above 255, are not part of the trace.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a list of at most 10 integers, each from 0 to 255; 1 it raised any exception or did not finish; 2 it returned anything else (another type, a longer list, an element that is not an integer, a negative number, a number too large) |
| `result` | list, at most 10 numbers from 0 to 255 | the returned list, in its order, when `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-EMPTY: `result` is the empty list unless `outcome` is 0.
