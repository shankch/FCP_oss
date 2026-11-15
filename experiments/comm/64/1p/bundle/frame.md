# FCP function adapter, version 0.2

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
argument is an input signal, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `candidate(s)`. Calls are independent: the function keeps no state between
them. The checker chooses the calls and their order freely, so `prev(x)` is
the value of `x` in the previous call, which can be any call at all.

## Strings

A string is a sequence of at most 32 characters, each with a code from 0 to
255 (Latin-1). In FCP-PL, `len(s)` is its length, `s[i]` the code of
character `i` (counting from 0; 0 at or beyond the length), so the last
character of a non-empty `s` is `s[len(s) - 1]`. A string literal of one
character, such as `"a"`, stands for its code where a number is expected.
Upper and lower case letters have different codes; `lower(c)` and `upper(c)`
map between them, and `isalpha(c)` holds for the ASCII letters only.

## Inputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `s` | string, at most 32 characters | the `s` argument |

Calls with longer strings, with characters beyond code 255, or with an
argument that is not a string are not part of the trace.

## Outputs

The prompt does not say what the function returns. The trace carries the
returned value as a non-negative integer; any other returned value is coded
in `outcome`.

| Signal | Width | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned an integer from 0 to 63; 1 it raised any exception or did not finish (the prompt names no exception); 2 it returned anything else (another type, a negative number, a number above 63) |
| `result` | 6 bits | the returned integer, 0 to 63, when `outcome` is 0 |

Negative numbers are not part of the trace: signals are unsigned, so a
negative returned value is outcome 2.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-ZERO: `result` is 0 unless `outcome` is 0.
