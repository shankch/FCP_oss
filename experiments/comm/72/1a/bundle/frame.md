# FCP function adapter, version 0.2

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `will_it_fly(q, w)`. Calls are independent: the function keeps no state
between them. The checker chooses the calls and their order freely, so
`prev(x)` is the value of `x` in the previous call, which can be any call at
all.

## Lists

A list is a sequence of at most 8 integers, each from 0 to 255. The Python
list `[3, 2, 3]` is the sequence of length 3 with elements 3, 2 and 3, and
`[]` is the sequence of length 0. In FCP-PL, `len(s)` is its length, `s[i]`
its element `i` (counting from 0; 0 at or beyond the length, so `s[len(s) - 1]`
is the last element of a non-empty list), and the quantifiers `all(i < len(s):
...)`, `any(i < len(s): ...)`, `count(i < len(s): ...)` and `sum(i < len(s):
...)` range over its elements.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `q` | sequence of at most 8 numbers, 0 to 255 | the `q` argument, element by element, in order |
| `w` | 12 bits | the `w` argument, 0 to 4,095 |

`w` ranges beyond the sum of any list in the trace (at most 8 × 255 = 2,040).
Calls with more than 8 elements in `q`, elements above 255, `w` above 4,095,
elements or a `w` that are not integers, and negative numbers are not part of
the trace.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned True or False; 1 it raised an exception or did not finish (the prompt names no exception, so every exception is 1); 2 it returned anything else |
| `fly` | 1 bit | the returned value, when `outcome` is 0 (1: True) |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `fly` is false unless `outcome` is 0.
