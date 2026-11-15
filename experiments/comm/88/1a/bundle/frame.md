# FCP function adapter for lists, version 0.1

This document defines how calls of a Python function that takes and returns
a list of integers become a trace that the FCP engines can check. The
function is treated as a chip without memory: its argument is an input
signal, its result is on output signals, and each cycle is one call. This
document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `sort_array(array)`. Calls are independent: the function keeps no state
between them. The checker chooses the calls and their order freely, so
`prev(x)` is the value of `x` in the previous call, which can be any call at
all.

## Lists

A list is a sequence of at most 8 numbers, each from 0 to 255. In FCP-PL,
`len(s)` is its length, `s[i]` its element `i` (counting from 0; 0 at or
beyond the length), `x in s` holds when some element of `s` equals `x`, and
`[2, 4, 3]` is a list literal. `s == t` holds when the two lists have the same
length and the same elements in the same order. The first element of a
non-empty list `s` is `s[0]` and the last is `s[len(s) - 1]`.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `array` | list of at most 8 numbers, 0 to 255 | the `array` argument, as passed to the call |

Calls with lists longer than 8 elements, or with elements above 255, are not
part of the trace, and neither are negative numbers or elements that are not
integers.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a list of at most 8 integers, each from 0 to 255; 1 it raised any exception or did not finish; 2 it returned anything else (another type, a longer list, a negative number, a number too large) |
| `result` | list of at most 8 numbers, 0 to 255 | the returned list, when `outcome` is 0 |

The trace records the argument as passed and the returned list; nothing else
about the call is recorded.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-EMPTY: `result` is the empty list unless `outcome` is 0.
