# FCP function adapter, version 0.2

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
argument is an input signal, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the request.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `parse_duration(text)`. Calls are independent: the function keeps no state
between them. The checker chooses the calls and their order freely, so
`prev(x)` is the value of `x` in the previous call, which can be any call at
all.

## Strings

A string is a sequence of at most 16 characters, each with a code from 0 to
255 (Latin-1). In FCP-PL, `len(s)` is its length (0 for the empty string),
`s[i]` the code of character `i` (counting from 0; 0 at or beyond the
length), and a string literal of one character, such as `"h"`, stands for its
code where a number is expected, so `s[i] - "0"` is the value of a digit.
`isdigit(c)` holds for the ten characters `0` to `9` only, and `isspace(c)`
for the ASCII whitespace characters.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `text` | string, at most 16 characters | the `text` argument |

Calls with longer strings, or with characters beyond code 255, are not part
of the trace.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned an integer from 0 to 524,287; 1 it raised `ValueError`; 2 it raised any other exception or did not finish; 3 it returned anything else (another type, a negative number, a number too large) |
| `seconds` | 19 bits | the returned integer, 0 to 524,287, when `outcome` is 0 |

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `seconds` is 0 unless `outcome` is 0.
