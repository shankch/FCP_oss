// HUB-2 reference implementation: round-robin port selector + BRG-1 bridge.
module rr_sel2 (
  input  wire clk,
  input  wire rst_n,
  input  wire v0,
  input  wire v1,
  input  wire take,      // the selected command is accepted this cycle
  output wire sel        // selected port
);
  reg last;              // port accepted most recently
  assign sel = (v0 && v1) ? !last : v1;
  always @(posedge clk)
    if (!rst_n) last <= 1'b1;
    else if (take) last <= sel;
endmodule

module hub2 (
  input  wire       clk,
  input  wire       rst_n,
  input  wire       c0_valid, input wire c0_write, input wire [7:0] c0_addr, input wire [7:0] c0_wdata,
  output wire       c0_ready,
  input  wire       c1_valid, input wire c1_write, input wire [7:0] c1_addr, input wire [7:0] c1_wdata,
  output wire       c1_ready,
  output wire       r0_valid, input wire r0_ready, output wire [7:0] r0_rdata, output wire r0_err,
  output wire       r1_valid, input wire r1_ready, output wire [7:0] r1_rdata, output wire r1_err,
  output wire       psel, output wire penable, output wire pwrite,
  output wire [7:0] paddr, output wire [7:0] pwdata,
  input  wire       pready, input wire [7:0] prdata, input wire pslverr
);
  wire       sel;
  wire       b_cmd_ready, b_rsp_valid, b_rsp_err;
  wire [7:0] b_rsp_rdata;
  reg        owner;      // port of the transaction in flight

  wire b_cmd_valid = sel ? c1_valid : c0_valid;
  wire b_take      = b_cmd_valid && b_cmd_ready;

  rr_sel2 u_sel (.clk(clk), .rst_n(rst_n), .v0(c0_valid), .v1(c1_valid), .take(b_take), .sel(sel));

  apb_bridge u_brg (
    .clk(clk), .rst_n(rst_n),
    .cmd_valid(b_cmd_valid), .cmd_ready(b_cmd_ready),
    .cmd_write(sel ? c1_write : c0_write),
    .cmd_addr (sel ? c1_addr  : c0_addr),
    .cmd_wdata(sel ? c1_wdata : c0_wdata),
    .rsp_valid(b_rsp_valid), .rsp_ready(owner ? r1_ready : r0_ready),
    .rsp_rdata(b_rsp_rdata), .rsp_err(b_rsp_err),
    .psel(psel), .penable(penable), .pwrite(pwrite), .paddr(paddr), .pwdata(pwdata),
    .pready(pready), .prdata(prdata), .pslverr(pslverr));

  always @(posedge clk)
    if (b_take) owner <= sel;

  assign c0_ready = b_cmd_ready && !sel;
  assign c1_ready = b_cmd_ready && sel;
  assign r0_valid = b_rsp_valid && !owner;
  assign r1_valid = b_rsp_valid && owner;
  assign r0_rdata = b_rsp_rdata;
  assign r1_rdata = b_rsp_rdata;
  assign r0_err   = b_rsp_err;
  assign r1_err   = b_rsp_err;
endmodule
