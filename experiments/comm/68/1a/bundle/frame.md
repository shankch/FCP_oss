# FCP list adapter, version 0.1

This document defines how calls of a Python function on lists become a trace
that the FCP engines can check. The function is treated as a chip without
memory: its argument is an input signal, its result is on output signals, and
each cycle is one call. This document is part of the adapter, not of the
prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `pluck(arr)`. Calls are independent: the function keeps no state between
them. The checker chooses the calls and their order freely, so `prev(x)` is
the value of `x` in the previous call, which can be any call at all.

## Lists

A list is a sequence of integers, each in its own slot. In FCP-PL, `len(s)` is
the length of a list (0 for the empty list), `s[i]` its element `i` (counting
from 0; 0 at or beyond the length), `x in s` holds when some element of `s`
equals `x`, a list literal such as `[2, 1]` stands for the list itself, and
`len(s) == 0` says `s` is empty. Two lists are equal when they have the same
length and the same elements in the same order.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `arr` | list of at most 8 numbers, each 0 to 65,535 | the `arr` argument, in order; it may be empty |

Calls with lists of more than 8 elements or with elements above 65,535 are not
part of the trace, and neither are negative numbers.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a list of at most 3 integers, each from 0 to 65,535; 1 it raised any exception or did not finish; 2 it returned anything else (another type, a longer list, a negative number, a number above 65,535) |
| `plucked` | list of at most 3 numbers, each 0 to 65,535 | the returned list, in order, when `outcome` is 0 |

The prompt names no exception, so no exception has a code of its own.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-EMPTY: `plucked` is the empty list unless `outcome` is 0.
