# FCP list adapter, version 0.1

This document defines how calls of a Python function on a list of integers
become a trace that the FCP engines can check. The function is treated as a
chip without memory: its argument is an input signal, its result is on output
signals, and each cycle is one call. This document is part of the adapter,
not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `pluck(arr)`. Calls are independent: the function keeps no state between
them. The checker chooses the calls and their order freely, so `prev(x)` is
the value of `x` in the previous call, which can be any call at all.

## Lists

A list of integers is carried as a sequence signal: a length and its
elements. In FCP-PL, `len(s)` is the length of a list, `s[i]` its element `i`
(counting from 0; 0 at or beyond the length), and `x in s` holds when some
element below the length equals `x`. The empty list has length 0. Element `i`
of a list is the element at index `i` in Python.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `arr` | list of at most 16 numbers, 0 to 255 | the `arr` argument: `len(arr)` is its length and `arr[i]` its element `i` |

Every length from 0 to 16 is part of the trace, the empty list included.
Calls with more than 16 elements or with elements above 255 are not part of
the trace, and neither are negative numbers.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a list of at most 3 integers, each from 0 to 255; 1 it raised any exception or did not finish; 2 it returned anything else (another type, a longer list, an element that is negative or above 255) |
| `plucked` | list of at most 3 numbers, 0 to 255 | the returned list, when `outcome` is 0: `len(plucked)` is its length and `plucked[k]` its element `k` |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-EMPTY: `plucked` is the empty list unless `outcome` is 0.
