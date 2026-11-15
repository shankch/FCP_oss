# FCP function adapter, version 0.2

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `valid_date(date)`. Calls are independent: the function keeps no state
between them. The checker chooses the calls and their order freely, so
`prev(x)` is the value of `x` in the previous call, which can be any call at
all.

## Strings

A string is a sequence of at most 16 characters, each with a code from 0 to
255 (Latin-1). In FCP-PL, `len(s)` is its length, `s[i]` the code of
character `i` (counting from 0; 0 at or beyond the length), and a string
literal of one character, such as `"-"`, stands for its code where a number is
expected, so `s[i] - "0"` is the value of a digit. `isdigit(c)` holds for the
ten characters `0` to `9` only.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `date` | string, at most 16 characters | the `date` argument |

Calls with longer strings, with characters beyond code 255, or with an
argument that is not a string are not part of the trace. The function
returns no integers and takes none, so there are no negative numbers in the
trace.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned True or False; 1 it raised any exception or did not finish; 2 it returned anything else (another type, such as None or a string) |
| `valid` | 1 bit | the returned value, when `outcome` is 0 (1: True) |

The prompt names no exception, so no outcome code is reserved for one.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `valid` is false unless `outcome` is 0.
