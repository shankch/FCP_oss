You are an RTL design engineer.

Workspace: /work/ws/bridge_rtlgen
It contains spec.md (the specification) and design.yaml (the interface).

Task: implement the specified block as synthesizable Verilog-2005 in
/work/ws/bridge_rtlgen/rtl/apb_bridge.v, top module `apb_bridge`, with exactly the ports listed in
design.yaml (same names, directions and widths).

Constraints: single clock `clk`, synchronous active-low reset `rst_n` as the
spec describes, no initial blocks, no SystemVerilog-only syntax, no
simulation-only code. You may check syntax with
`/repo/.tools/oss-cad-suite/bin/iverilog -g2005 -o /dev/null /work/ws/bridge_rtlgen/rtl/*.v` and may write your own
testbench under /work/ws/bridge_rtlgen/tb/. Do not read any file outside /work/ws/bridge_rtlgen.

When done, reply with a short summary of your design decisions and of any
ambiguities in the specification you had to resolve.