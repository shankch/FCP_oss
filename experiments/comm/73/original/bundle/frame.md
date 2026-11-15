# FCP function adapter, version 0.3

This document defines how calls of a Python function that takes a list
become a trace that the FCP engines can check. The function is treated as a
chip without memory: its argument is an input signal, its result is on an
output signal, and each cycle is one call. This document is part of the
adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `smallest_change(arr)`. Calls are independent: the function keeps no state
between them. The checker chooses the calls and their order freely, so
`prev(x)` is the value of `x` in the previous call, which can be any call at
all.

## Lists

A list is a sequence of at most 10 integers, each from 0 to 15. In FCP-PL,
`len(s)` is its length and `s[i]` its element `i` (counting from 0; 0 at or
beyond the length). `s == t` holds when the two lists have the same length and
the same elements in order.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `arr` | sequence of at most 10 numbers, 0 to 15 | the `arr` argument, element by element in order |

Calls with more than 10 elements or with elements above 15 are not part of
the trace, and neither are negative integers.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned an integer from 0 to 15; 1 it raised any exception or did not finish; 2 it returned anything else (another type, a negative number, a number too large) |
| `changes` | 4 bits | the returned integer, 0 to 15, when `outcome` is 0 |

The request names no exception, so no outcome code stands for a particular
exception.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `changes` is 0 unless `outcome` is 0.
