# FCP function adapter, version 0.2

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `eat(x, y, z)`. Calls are independent: the function keeps no state between
them. The checker chooses the calls and their order freely, so `prev(s)` is
the value of `s` in the previous call, which can be any call at all.

## Arguments

The signature names the parameters `x`, `y` and `z`, in this order, and the
trace uses these names. The prompt's docstring describes its variables under
other names (`number`, `need`, `remaining`); this document does not say which
parameter each of them is.

## Lists

The returned list is a sequence of at most 3 numbers. In FCP-PL, `len(s)` is
its length and `s[i]` its element `i` (counting from 0; 0 at or beyond the
length).

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `x` | 10 bits | the `x` argument (first), 0 to 1,023 |
| `y` | 10 bits | the `y` argument (second), 0 to 1,023 |
| `z` | 10 bits | the `z` argument (third), 0 to 1,023 |

Negative arguments, and arguments above 1,023, are not part of the trace.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a list of at most 3 integers, each from 0 to 2,047; 1 it raised any exception or did not finish; 2 it returned anything else (another type, a longer list, a negative number, a number too large) |
| `result` | sequence of at most 3 numbers, 0 to 2,047 | the returned list, when `outcome` is 0 |

The prompt names no exception, so no exception has a code of its own.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-EMPTY: `result` is the empty list unless `outcome` is 0.
