# FCP list adapter, version 0.6

This document defines how calls of a Python function that takes a list of
integers become a trace that the FCP engines can check. The function is
treated as a chip without memory: its argument is an input signal, its result
is on output signals, and each cycle is one call. This document is part of
the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `pluck(arr)`. Calls are independent: the function keeps no state between
them. The checker chooses the calls and their order freely, so `prev(x)` is
the value of `x` in the previous call, which can be any call at all.

## Lists

A list is carried as a sequence signal of at most 8 numbers, each from 0 to
255. Element `i` of `arr` is `arr[i]`. In FCP-PL, `len(s)` is the length of a
sequence, `s[i]` its element `i` (counting from 0; 0 at or beyond the
length), and `x in s` holds when some element of `s` below its length equals
`x`. The position of an element in the Python list is its index `i` in the
sequence.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `arr` | sequence of at most 8 numbers, 0 to 255 | the `arr` argument, element by element, in order |

Calls with more than 8 elements or with elements above 255 are not part of
the trace, and neither are negative numbers: signals are unsigned.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned an integer from 0 to 255; 1 it raised an exception (the prompt names none) or did not finish; 2 it returned anything else (another type, a negative number, a number above 255) |
| `plucked` | 8 bits | the returned integer, when `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `plucked` is 0 unless `outcome` is 0.
