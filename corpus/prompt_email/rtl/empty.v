// Response "empty" replayed as a chip by the FCP text adapter (frame.md).
// Labels: none (anti-response). 0 units; unit i drives the outputs in cycle i+1 (cycle 0 is reset),
// then eos rises and stays high with every label false. Generated; do not edit.
module response (input clk, input rst_n, output subject, output greet, output feature, output benefit, output price, output offer, output ends, output rival, output cta, output signoff, output eos);
  reg [3:0] k;  // index of the current unit
  always @(posedge clk)
    if (!rst_n) k <= 4'd0;
    else if (k != 4'd0) k <= k + 4'd1;
  reg [9:0] lab;  // {subject, greet, feature, benefit, price, offer, ends, rival, cta, signoff}
  always @* begin
    case (k)
      default: lab = 10'b0;
    endcase
  end
  assign eos = (k == 4'd0);
  assign {subject, greet, feature, benefit, price, offer, ends, rival, cta, signoff} = lab;
endmodule
