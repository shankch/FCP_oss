# FCP function adapter, version 0.2

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `remove_duplicates(numbers)`. Calls are independent: the function keeps no
state between them. The checker chooses the calls and their order freely, so
`prev(x)` is the value of `x` in the previous call, which can be any call at
all.

## Lists

A list of integers is a sequence of at most 8 numbers, each from 0 to 255. In
FCP-PL, `len(s)` is its length, `s[i]` its element `i` (counting from 0; 0 at
or beyond the length, so a 0 there is not an element of the list), and `x in
s` holds when some element of `s` equals `x`. Element `i` of the list passed
as `numbers` is `numbers[i]`, and element `i` of the returned list is
`result[i]`.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `numbers` | list of at most 8 numbers, 0 to 255 | the `numbers` argument, in order |

Calls with more than 8 numbers or numbers above 255 are not part of the
trace, and neither are negative numbers.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a list of at most 8 integers, each from 0 to 255; 1 it raised any exception or did not finish; 2 it returned anything else (another type, a longer list, a negative number or a number above 255) |
| `result` | list of at most 8 numbers, 0 to 255 | the returned list, in order, when `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-EMPTY: `result` is the empty list unless `outcome` is 0.
