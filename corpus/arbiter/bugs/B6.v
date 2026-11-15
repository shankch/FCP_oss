// FCP corpus defect B6: the most recently granted requester is never considered: lone repeated requester is never granted again
// RRA-4 reference implementation: registered round-robin arbiter.
// The most recently granted requester gets the lowest priority next.
module rr_arbiter #(
  parameter N = 4
) (
  input  wire         clk,
  input  wire         rst_n,
  input  wire [N-1:0] req,
  output wire [N-1:0] gnt
);
  localparam IW = (N > 1) ? $clog2(N) : 1;

  reg [N-1:0]  gnt_r;
  reg [IW-1:0] last;       // most recently granted requester
  reg [IW-1:0] pick;
  reg          found;
  integer      k, cand;

  always @(*) begin
    found = 1'b0;
    pick  = last;
    for (k = 1; k < N; k = k + 1) begin
      cand = (last + k) % N;
      if (!found && req[cand]) begin
        found = 1'b1;
        pick  = cand[IW-1:0];
      end
    end
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      gnt_r <= {N{1'b0}};
      last  <= N - 1;      // requester 0 has the highest priority after reset
    end else begin
      gnt_r <= found ? ({{(N-1){1'b0}}, 1'b1} << pick) : {N{1'b0}};
      if (found)
        last <= pick;
    end
  end

  assign gnt = rst_n ? gnt_r : {N{1'b0}};
endmodule
