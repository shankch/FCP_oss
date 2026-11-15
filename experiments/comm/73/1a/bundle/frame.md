# FCP function adapter, version 0.2

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `candidate(arr)`. Calls are independent: the function keeps no state
between them. The checker chooses the calls and their order freely, so
`prev(x)` is the value of `x` in the previous call, which can be any call at
all.

## Lists

A list is a sequence of at most 10 integers, each from 0 to 255. In FCP-PL,
`len(s)` is its length and `s[i]` its element `i` (counting from 0; 0 at or
beyond the length). The `arr` argument is carried as the sequence signal
`arr`: its length is the number of elements of the Python list, and slot `i`
is element `i` of the list; the empty list is the sequence of length 0.
Quantifiers such as `all(i < len(arr): ...)`, `count(i < len(arr):
...)` and `sum(i < len(arr): ...)` range over the elements.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `arr` | list of at most 10 integers, 0 to 255 | the `arr` argument, in order |

Calls with more than 10 elements, or with elements above 255, are not part of
the trace, and neither are negative integers: signals are unsigned.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned an integer from 0 to 15; 1 it raised any exception or did not finish; 2 it returned anything else (another type, a negative number, a number above 15) |
| `changes` | 4 bits | the returned integer, 0 to 15, when `outcome` is 0 |

The prompt names no exception, so no exception has a code of its own.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `changes` is 0 unless `outcome` is 0.
