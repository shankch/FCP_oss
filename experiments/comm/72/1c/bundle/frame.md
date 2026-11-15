# FCP list adapter, version 0.1

This document defines how calls of a Python function that takes a list of
integers become a trace that the FCP engines can check. The function is
treated as a chip without memory: its arguments are input signals, its result
is on output signals, and each cycle is one call. This document is part of
the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `will_it_fly(q, w)`. Calls are independent: the function keeps no state
between them. The checker chooses the calls and their order freely, so
`prev(x)` is the value of `x` in the previous call, which can be any call at
all.

## Lists

A list is a sequence signal of at most 8 elements, each a number from 0 to
255. In FCP-PL, `len(q)` is the number of elements of `q` and `q[i]` its
element `i` (counting from 0; 0 at or beyond the length). The list `[3, 2, 3]`
is `q` with `len(q) == 3`, `q[0] == 3`, `q[1] == 2` and `q[2] == 3`.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `q` | sequence of at most 8 numbers, 0 to 255 | the `q` argument, its elements in order |
| `w` | 11 bits | the `w` argument, 0 to 2,047 |

Calls with more than 8 elements, elements above 255 or `w` above 2,047 are
not part of the trace, and neither are negative numbers or values that are
not integers.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned `True` or `False`; 1 it raised any exception or did not finish; 2 it returned anything else |
| `flies` | 1 bit | the returned value (1: `True`), when `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `flies` is false unless `outcome` is 0.
