# BRG-1 Command-to-APB Bridge: Functional Specification

Version 1.0. Status: released for implementation.

## 1. Overview

BRG-1 converts single read and write commands received on a valid/ready
command channel into APB3 transfers and returns the result on a valid/ready
response channel. One transaction is processed at a time.

## 2. Interface

| Signal    | Dir | Width | Description |
|-----------|-----|-------|-------------|
| clk       | in  | 1     | Clock, rising edge. |
| rst_n     | in  | 1     | Synchronous active-low reset. |
| cmd_valid | in  | 1     | Command valid. |
| cmd_ready | out | 1     | Command ready. |
| cmd_write | in  | 1     | 1 for a write, 0 for a read. |
| cmd_addr  | in  | 8     | Command address. |
| cmd_wdata | in  | 8     | Command write data. |
| rsp_valid | out | 1     | Response valid. |
| rsp_ready | in  | 1     | Response ready. |
| rsp_rdata | out | 8     | Response read data. |
| rsp_err   | out | 1     | Response error flag. |
| psel      | out | 1     | APB select. |
| penable   | out | 1     | APB enable. |
| pwrite    | out | 1     | APB write. |
| paddr     | out | 8     | APB address. |
| pwdata    | out | 8     | APB write data. |
| pready    | in  | 1     | APB ready. |
| prdata    | in  | 8     | APB read data. |
| pslverr   | in  | 1     | APB slave error. |

## 3. Command channel

A command is accepted in a cycle in which both cmd_valid and cmd_ready are
high. cmd_ready is asserted only while the bridge is idle, that is, while no
transfer is in progress and no response is pending. The requester shall keep
cmd_valid asserted and cmd_write, cmd_addr and cmd_wdata stable until the
command is accepted.

## 4. APB transfer

For every accepted command the bridge performs exactly one APB transfer whose
pwrite, paddr and pwdata equal cmd_write, cmd_addr and cmd_wdata of that
command. Transfers are performed in the order in which the commands were
accepted.

The transfer starts in the cycle after the command is accepted with a setup
phase (psel high, penable low) that lasts exactly one cycle, followed by an
access phase (psel and penable high). The access phase lasts until pready is
sampled high; the transfer completes in that cycle.

psel, pwrite, paddr and pwdata remain stable from the setup phase until the
transfer completes. penable is never asserted without psel. After a transfer
completes, psel and penable are low in the next cycle. While psel is low,
pwrite, paddr and pwdata are don't care.

The APB slave shall assert pready within 4 cycles of the start of the access
phase.

## 5. Response channel

For every completed transfer the bridge returns exactly one response, in
order. rsp_err equals the pslverr value sampled when the transfer completed.
For read transfers, rsp_rdata equals the prdata value sampled when the
transfer completed.

rsp_valid is asserted in the cycle after the transfer completes. Once
asserted, rsp_valid stays high, and rsp_rdata and rsp_err stay stable, until
rsp_ready is sampled high. While rsp_valid is low, rsp_rdata and rsp_err are
don't care.

To maximise throughput, the bridge may accept the next command in the same
cycle in which the response is accepted.

A response is presented within 8 cycles of the command being accepted.

## 6. Reset

In the cycle after reset, psel, penable and rsp_valid are low and cmd_ready
is high.
