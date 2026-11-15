# HUB-2 Dual-Port APB Hub: Functional Specification

Version 1.0. Status: released for implementation.

## 1. Overview

HUB-2 lets two requesters, port 0 and port 1, share one APB3 bus. Each port
has a valid/ready command channel and a valid/ready response channel with the
same signal meanings as the BRG-1 bridge (signals prefixed c0_/r0_ for port 0
and c1_/r1_ for port 1). Internally HUB-2 consists of a round-robin port
selector and one BRG-1 bridge. One transaction is processed at a time.

## 2. Command acceptance and arbitration

A command on port k is accepted in a cycle in which ck_valid and ck_ready are
both high. At most one command is accepted per cycle. When both ports have a
command pending, the port that was not accepted most recently is accepted
first. A port whose command is pending is accepted within 12 cycles.

## 3. Transfers

Every accepted command results in exactly one APB transfer whose pwrite,
paddr and pwdata equal the fields of that command, in acceptance order. The
APB timing (setup and access phases, stability, penable only with psel) is
the same as for BRG-1.

## 4. Responses

The response to a command is returned on the port that issued it, and never
on the other port. rk_err equals the pslverr value sampled when the transfer
completed, and for reads rk_rdata equals the prdata value sampled when the
transfer completed. Once asserted, rk_valid stays high and rk_rdata and
rk_err stay stable until rk_ready is sampled high.

## 5. Environment

Each requester keeps its command valid and stable until it is accepted. The
APB slave asserts pready within 4 cycles of the start of the access phase.
Each requester accepts a response within 2 cycles of it being presented.

## 6. Reset

In the cycle after reset, psel, r0_valid and r1_valid are low, and both
c0_ready and c1_ready may be high.
