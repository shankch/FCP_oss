# FCP list adapter, version 0.1

This document defines how calls of a Python function on lists become a trace
that the FCP engines can check. The function is treated as a chip without
memory: its argument is an input signal, its result is on output signals, and
each cycle is one call. This document is part of the adapter, not of the
prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `sort_array(array)`. Calls are independent: the function keeps no state
between them. The checker chooses the calls and their order freely, so
`prev(x)` is the value of `x` in the previous call, which can be any call at
all.

## Lists

A list is a sequence of at most 8 numbers, each from 0 to 255. In FCP-PL,
`len(s)` is its length, `s[i]` its element `i` (counting from 0; 0 at or
beyond the length), and `s[len(s) - 1]` its last element when it is not
empty. `x in s` holds when some element of `s` equals `x`, and `s == t` when
`s` and `t` have the same length and the same elements in the same order.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `array` | list of at most 8 numbers, 0 to 255 | the `array` argument |

Calls with more than 8 elements or with elements above 255 are not part of
the trace, and neither are negative numbers: signals are unsigned.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a list of at most 8 integers, each from 0 to 255; 1 it raised an exception or did not finish; 2 it returned anything else (another type, a longer list, an element that is negative, too large or not an integer) |
| `result` | list of at most 8 numbers, 0 to 255 | the returned list, when `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-EMPTY: `result` is the empty list unless `outcome` is 0.
