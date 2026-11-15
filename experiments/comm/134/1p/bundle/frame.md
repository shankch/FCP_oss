# FCP function adapter, version 0.2

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
argument is an input signal, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the request.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `candidate(txt)`. Calls are independent: the function keeps no state
between them. The checker chooses the calls and their order freely, so
`prev(x)` is the value of `x` in the previous call, which can be any call at
all.

## Strings

A string is a sequence of at most 32 characters, each with a code from 0 to
255 (Latin-1). In FCP-PL, `len(s)` is its length, `s[i]` the code of
character `i` (counting from 0; 0 at or beyond the length), and a string
literal of one character, such as `" "`, stands for its code where a number is
expected. `isalpha(c)`, `isdigit(c)`, `isspace(c)` and the other character
classes are the ASCII ones: `isalpha` holds for `a` to `z` and `A` to `Z`
only. The last character of a non-empty string `s` is `s[len(s) - 1]`.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `txt` | string, at most 32 characters | the `txt` argument |

Signals are unsigned, so negative numbers are not part of the trace. Calls
with longer strings, or with characters beyond code 255, are not part of the
trace either.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned True or False; 1 it raised any exception or did not finish (the request names no exception); 2 it returned anything else |
| `result` | 1 bit | the returned value, when `outcome` is 0 (1: True) |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `result` is false unless `outcome` is 0.
