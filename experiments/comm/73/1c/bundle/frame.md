# FCP list adapter, version 0.1

This document defines how calls of a Python function on a list of integers
become a trace that the FCP engines can check. The function is treated as a
chip without memory: its argument is an input signal, its result is on output
signals, and each cycle is one call. This document is part of the adapter,
not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `smallest_change(arr)`, with `arr` a Python list of integers. Calls are
independent: the function keeps no state between them. The checker chooses
the calls and their order freely, so `prev(x)` is the value of `x` in the
previous call, which can be any call at all.

## Lists

A list is a sequence of at most 10 integers, each from 0 to 15. In FCP-PL,
`len(arr)` is its length (0 for the empty list), `arr[i]` its element `i`
(counting from 0; 0 at or beyond the length), and `[1, 2, 3]` is a list
literal, so `arr == [1, 2, 3]` holds when the argument is exactly that list.
`x in arr` holds when some element of the list equals `x`.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `arr` | sequence of at most 10 numbers, 0 to 15 | the `arr` argument, element by element, in order |

Calls with more than 10 elements, with elements above 15, or with negative
integers are not part of the trace.

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
