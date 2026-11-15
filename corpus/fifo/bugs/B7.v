// FCP corpus defect B7: empty derived from pointer equality (also true when full)
// SFIFO-01 reference implementation (single clock, first-word fall-through).
module sync_fifo #(
  parameter DEPTH    = 5,
  parameter WIDTH    = 8,
  parameter AF_LEVEL = 3
) (
  input  wire                       clk,
  input  wire                       rst_n,
  input  wire                       push,
  input  wire [WIDTH-1:0]           push_data,
  input  wire                       pop,
  output wire [WIDTH-1:0]           pop_data,
  output wire                       full,
  output wire                       empty,
  output wire                       almost_full,
  output wire [$clog2(DEPTH+1)-1:0] count
);
  localparam AW = (DEPTH > 1) ? $clog2(DEPTH) : 1;
  localparam CW = $clog2(DEPTH + 1);

  reg [WIDTH-1:0] mem [0:DEPTH-1];
  reg [AW-1:0]    rd_ptr, wr_ptr;
  reg [CW-1:0]    cnt;

  wire do_push = push && !full;
  wire do_pop  = pop && !empty;

  always @(posedge clk) begin
    if (!rst_n) begin
      rd_ptr <= {AW{1'b0}};
      wr_ptr <= {AW{1'b0}};
      cnt    <= {CW{1'b0}};
    end else begin
      if (do_push) begin
        mem[wr_ptr] <= push_data;
        wr_ptr      <= (wr_ptr == DEPTH - 1) ? {AW{1'b0}} : wr_ptr + 1'b1;
      end
      if (do_pop)
        rd_ptr <= (rd_ptr == DEPTH - 1) ? {AW{1'b0}} : rd_ptr + 1'b1;
      if (do_push && !do_pop)
        cnt <= cnt + 1'b1;
      else if (do_pop && !do_push)
        cnt <= cnt - 1'b1;
    end
  end

  assign pop_data    = mem[rd_ptr];
  assign full        = (cnt == DEPTH);
  assign empty       = (rd_ptr == wr_ptr);
  assign almost_full = (cnt >= AF_LEVEL);
  assign count       = cnt;
endmodule
