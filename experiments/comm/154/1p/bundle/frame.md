# FCP function adapter, version 0.2

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `candidate(a, b)`, with `a` as the first argument and `b` as the second.
Calls are independent: the function keeps no state between them. The checker
chooses the calls and their order freely, so `prev(x)` is the value of `x` in
the previous call, which can be any call at all.

## Strings

A string is a sequence of at most 16 characters, each with a code from 0 to
255 (Latin-1). In FCP-PL, `len(s)` is its length, `s[i]` the code of
character `i` (counting from 0; 0 at or beyond the length), and a string
literal of one character, such as `"a"`, stands for its code where a number is
expected. `s == t` holds when two strings have the same length and the same
characters. Signals are unsigned: a character is its code, and no negative
number is part of the trace.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `a` | string, at most 16 characters | the `a` argument (the first) |
| `b` | string, at most 16 characters | the `b` argument (the second) |

Calls with longer strings, or with characters beyond code 255, are not part
of the trace.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned True or False; 1 it raised any exception or did not finish; 2 it returned anything else (another type, such as a number, a string or None) |
| `result` | 1 bit | the returned value, when `outcome` is 0: 1 for True, 0 for False |

The prompt names no exception, so no exception has a code of its own.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `result` is 0 (false) unless `outcome` is 0.
- F-CODE: `outcome` is never 3.
