# FCP function adapter, version 0.7

This document defines how calls of a Python function become a trace that the
FCP engines can check. The function is treated as a chip without memory: its
arguments are input signals, its result is on output signals, and each cycle
is one call. This document is part of the adapter, not of the prompt.

## Calls

Cycle 0 of the trace is reset, before any call. Every later cycle is one call
of `eat(number, need, remaining)`. Calls are independent: the function keeps
no state between them. The checker chooses the calls and their order freely,
so `prev(x)` is the value of `x` in the previous call, which can be any call
at all.

## Lists

The prompt does not say in what form the result is returned, so the returned
value is read as a list of numbers and carried as one sequence signal. In
FCP-PL, `len(s)` is the length of a sequence and `s[i]` its element `i`
(counting from 0; 0 at or beyond the length), so `result[0]` is the first
element of the returned list and `result[1]` the second.

## Inputs

| Signal | Width | Meaning in a call |
|---|---|---|
| `number` | 11 bits | the `number` argument, 0 to 2,047 |
| `need` | 11 bits | the `need` argument, 0 to 2,047 |
| `remaining` | 11 bits | the `remaining` argument, 0 to 2,047 |

The prompt gives no bounds for the arguments. Calls with arguments above
2,047 are not part of the trace, and neither are negative arguments.

## Outputs

| Signal | Type | Meaning in a call |
|---|---|---|
| `outcome` | 2 bits | how the call ended: 0 it returned a list of at most 4 integers, each from 0 to 8,191; 1 it raised any exception or did not finish; 2 it returned anything else (a number, another type, a longer list, a negative or larger element) |
| `result` | sequence of at most 4 numbers, 0 to 8,191 | the returned list, when `outcome` is 0 |

The prompt names no exception, so every exception has code 1. An element of
up to 8,191 holds any sum of the three arguments.

## Frame rules

These hold for every trace by construction. They are part of every
formalization set and need not be restated.

- F-EMPTY: `result` is the empty list unless `outcome` is 0.
