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

The returned list is a sequence of at most 32 numbers, each from 0 to 63. In
FCP-PL, `len(s)` is its length, `s[i]` its element `i` (counting from 0; 0 at
or beyond the length), `x in s` holds when some element equals `x`, and
`[2, 4]` is a list literal.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `a` | 6 bits | the `a` argument, 0 to 63 |
| `b` | 6 bits | the `b` argument, 0 to 63 |

Calls with arguments above 63 are not part of the trace, and neither are
negative arguments.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a list of at most 32 integers, each from 0 to 63; 1 it raised any exception or did not finish; 2 it returned anything else (another type, a longer list, an element that is not an integer, negative or above 63) |
| `result` | list of at most 32 numbers, 0 to 63 | the returned list, in order, when `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-EMPTY: `result` is the empty list unless `outcome` is 0.
