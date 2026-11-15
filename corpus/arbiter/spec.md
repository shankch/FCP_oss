# RRA-4 Round-Robin Arbiter: Functional Specification

Version 0.9. Status: draft for implementation.

## 1. Overview

RRA-4 arbitrates between N requesters (N = 4) for a shared resource. Each
requester raises its request line and waits for a grant. Grants last one
cycle. The arbiter grants a request in the same cycle in which it is raised.

## 2. Interface

| Signal | Dir | Width | Description |
|--------|-----|-------|-------------|
| clk    | in  | 1     | Clock, rising edge. |
| rst_n  | in  | 1     | Synchronous active-low reset. |
| req    | in  | N     | Request lines, one per requester. |
| gnt    | out | N     | Grant lines, one per requester. |

## 3. Functional description

### 3.1 Grants

At most one grant line is asserted in any cycle. A requester is never granted
unless it requested: gnt[i] is asserted only if req[i] was asserted in the
previous cycle. gnt is a registered output: the arbitration decision is made
on the request lines sampled in one cycle and becomes visible on gnt in the
next cycle.

### 3.2 Work conservation

If at least one request line is asserted in a cycle, exactly one grant line is
asserted in the next cycle.

### 3.3 Priority

After reset, requester 0 has the highest priority, followed by requesters 1,
2 and 3. The priority rotates by one position after each grant. Requester 3 is
reserved for maintenance traffic and always wins arbitration when it requests.

### 3.4 Fairness

A requester that keeps its request asserted is granted within N cycles.

## 4. Reset

While rst_n is low, and in the cycle after it, no grant line is asserted.

## 5. Requester obligations

A requester that has raised its request shall keep it asserted until it
receives a grant. A request may be withdrawn only after the grant.
