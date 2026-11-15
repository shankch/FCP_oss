# FCP function adapter, version 0.2

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `pluck(arr)`. Calls are independent: the function keeps no state between
them. The checker chooses the calls and their order freely, so `prev(x)` is
the value of `x` in the previous call, which can be any call at all.

## Lists

A list is a sequence of numbers, each from 0 to 65,535. In FCP-PL, `len(s)`
is its length and `s[i]` its element `i` (counting from 0; 0 at or beyond the
length). A list literal such as `[7, 0]` is a list of constants, and `s ==
[7, 0]` holds when `s` has exactly these elements in this order.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `arr` | list of at most 8 numbers, 0 to 65,535 | the `arr` argument, element `i` of the list in `arr[i]` |

Calls with more than 8 elements, or with elements above 65,535, are not part
of the trace, and neither are negative numbers.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a list of at most 3 integers, each from 0 to 65,535; 1 it raised any exception or did not finish; 2 it returned anything else (another type, a longer list, a negative number, a number too large) |
| `plucked` | list of at most 3 numbers, 0 to 65,535 | the returned list, element `i` in `plucked[i]`, when `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-EMPTY: `plucked` is the empty list unless `outcome` is 0.
