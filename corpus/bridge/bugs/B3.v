// FCP corpus defect B3: response error not captured: follows pslverr combinationally
// BRG-1 reference implementation: one transaction at a time.
module apb_bridge (
  input  wire       clk,
  input  wire       rst_n,
  input  wire       cmd_valid,
  output wire       cmd_ready,
  input  wire       cmd_write,
  input  wire [7:0] cmd_addr,
  input  wire [7:0] cmd_wdata,
  output wire       rsp_valid,
  input  wire       rsp_ready,
  output wire [7:0] rsp_rdata,
  output wire       rsp_err,
  output wire       psel,
  output wire       penable,
  output wire       pwrite,
  output wire [7:0] paddr,
  output wire [7:0] pwdata,
  input  wire       pready,
  input  wire [7:0] prdata,
  input  wire       pslverr
);
  localparam IDLE = 2'd0, SETUP = 2'd1, ACCESS = 2'd2, RESP = 2'd3;

  reg [1:0] st;
  reg       w_r, err_r;
  reg [7:0] a_r, d_r, rd_r;

  always @(posedge clk) begin
    if (!rst_n) begin
      st <= IDLE;
    end else begin
      case (st)
        IDLE:   if (cmd_valid) begin
                  st  <= SETUP;
                  w_r <= cmd_write;
                  a_r <= cmd_addr;
                  d_r <= cmd_wdata;
                end
        SETUP:  st <= ACCESS;
        ACCESS: if (pready) begin
                  st    <= RESP;
                  rd_r  <= prdata;
                  err_r <= pslverr;
                end
        RESP:   if (rsp_ready) st <= IDLE;
      endcase
    end
  end

  assign cmd_ready = (st == IDLE);
  assign psel      = (st == SETUP) || (st == ACCESS);
  assign penable   = (st == ACCESS);
  assign pwrite    = w_r;
  assign paddr     = a_r;
  assign pwdata    = d_r;
  assign rsp_valid = (st == RESP);
  assign rsp_rdata = rd_r;
  assign rsp_err   = pslverr;
endmodule
