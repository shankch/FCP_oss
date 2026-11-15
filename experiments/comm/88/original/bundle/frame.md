# FCP function adapter, version 0.2

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `sort_array(array)`. Calls are independent: the function keeps no state
between them. The checker chooses the calls and their order freely, so
`prev(x)` is the value of `x` in the previous call, which can be any call at
all.

## Lists

A list is a sequence of at most 8 integers, each from 0 to 255. In FCP-PL,
`len(s)` is its length and `s[i]` its element `i` (counting from 0; 0 at or
beyond the length). `[2, 4, 3]` is a list literal, and `s == t` holds when two
lists have the same length and the same elements in the same order.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `array` | list of at most 8 integers, 0 to 255 | the `array` argument, passed as a Python list of `int` |

Calls with more than 8 elements or with elements above 255 are not part of
the trace. Signals are unsigned, so negative integers are not part of the
trace either. The trace records values only: what the list passed as `array`
holds after the call, and whether the returned list is the same object as
`array`, are not recorded.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a list of at most 8 integers, each from 0 to 255; 1 it raised any exception or did not finish; 2 it returned anything else (not a list, a longer list, an element that is not an integer, is negative or is above 255) |
| `result` | list of at most 8 integers, 0 to 255 | the returned list, when `outcome` is 0 |

The prompt names no exception, so no outcome code is reserved for one.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-EMPTY: `result` is the empty list unless `outcome` is 0.
