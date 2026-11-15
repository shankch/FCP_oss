# FCP function adapter, version 0.2

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `is_palindrome(text)`. Calls are independent: the function keeps no state
between them. The checker chooses the calls and their order freely, so
`prev(x)` is the value of `x` in the previous call, which can be any call at
all.

## Strings

A string is a sequence of at most 32 characters, each with a code from 0 to
255 (Latin-1). In FCP-PL, `len(s)` is its length, `s[i]` the code of
character `i` (counting from 0; 0 at or beyond the length), and a string
literal of one character, such as `"a"`, stands for its code where a number is
expected. A string literal such as `"aba"` is a whole string, compared with
`==` and `!=` (same length and same characters).

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `text` | string, at most 32 characters | the `text` argument |

Calls with longer strings, or with characters beyond code 255, are not part
of the trace. Signals are unsigned, so no value in the trace is negative.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned True or False; 1 it raised any exception or did not finish; 2 it returned anything else |
| `result` | 1 bit | the returned value, when `outcome` is 0 (1: True) |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `result` is false unless `outcome` is 0.
