# FCP function adapter, version 0.1

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

The returned list is a sequence of at most 64 integers, each from 0 to 127.
In FCP-PL, `len(s)` is its length and `s[i]` its element `i` (counting from
0; 0 at or beyond the length), `x in s` holds when some element of `s` equals
`x`, and quantifiers such as `all(i < len(s): ...)` range over its elements.
The order of the elements is the order of the returned list.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `a` | 7 bits | the `a` argument, 0 to 127 |
| `b` | 7 bits | the `b` argument, 0 to 127 |

Calls with arguments above 127 are not part of the trace, and neither are
negative arguments.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a list of at most 64 integers, each from 0 to 127; 1 it raised any exception or did not finish; 2 it returned anything else (another type, a longer list, an element that is not an integer, negative or above 127) |
| `result` | list of at most 64 integers, 0 to 127 | the returned list, when `outcome` is 0 |

The prompt names no exception, so no exception has a code of its own.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-EMPTY: `result` is the empty list unless `outcome` is 0.
