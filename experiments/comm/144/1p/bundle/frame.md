# FCP function adapter, version 0.2

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the request.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `simplify(x, n)`. Calls are independent: the function keeps no state
between them. The checker chooses the calls and their order freely, so
`prev(s)` is the value of `s` in the previous call, which can be any call at
all.

## Types

The request does not name the types of `x`, `n` or the returned value. The
adapter passes each argument as a Python string and records the returned
value as a boolean.

## Strings

A string is a sequence of at most 16 characters, each with a code from 0 to
255 (Latin-1). In FCP-PL, `len(s)` is its length, `s[i]` the code of
character `i` (counting from 0; 0 at or beyond the length), and a string
literal of one character, such as `"0"`, stands for its code where a number is
expected. `isdigit(c)` holds for the ten characters `0` to `9` only.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `x` | string, at most 16 characters | the `x` argument |
| `n` | string, at most 16 characters | the `n` argument |

Calls with longer strings or with characters beyond code 255 are not part of
the trace, and neither are arguments of other types, such as numbers (signals
are unsigned, so negative numbers never appear) or `Fraction` objects.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned True or False; 1 it raised any exception (the request names none) or did not finish; 2 it returned anything else (a string, a `Fraction`, `None`) |
| `result` | 1 bit | the returned value, when `outcome` is 0 (1: True) |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `result` is false unless `outcome` is 0.
