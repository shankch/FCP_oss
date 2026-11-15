You are an RTL design engineer.

Workspace: /work/ws/fifo_rtlgen
It contains spec.md (the specification) and design.yaml (the interface).

Task: implement the specified block as synthesizable Verilog-2005 in
/work/ws/fifo_rtlgen/rtl/sync_fifo.v, top module `sync_fifo`, with exactly the ports listed in
design.yaml (same names, directions and widths, and Verilog parameters DEPTH (default 5), WIDTH (default 8), AF_LEVEL (default 3) used for the parameterised widths).

Constraints: single clock `clk`, synchronous active-low reset `rst_n` as the
spec describes, no initial blocks, no SystemVerilog-only syntax, no
simulation-only code. You may check syntax with
`/repo/.tools/oss-cad-suite/bin/iverilog -g2005 -o /dev/null /work/ws/fifo_rtlgen/rtl/*.v` and may write your own
testbench under /work/ws/fifo_rtlgen/tb/. Do not read any file outside /work/ws/fifo_rtlgen.

When done, reply with a short summary of your design decisions and of any
ambiguities in the specification you had to resolve.