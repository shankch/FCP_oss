// Response "opus" replayed as a chip by the FCP text adapter (frame.md).
// Labels: rules + labeler B (claude-haiku-5-5). 9 units; unit i drives the outputs in cycle i+1 (cycle 0 is reset),
// then eos rises and stays high with every label false. Generated; do not edit.
module response (input clk, input rst_n, output subject, output greet, output feature, output benefit, output price, output offer, output ends, output rival, output cta, output signoff, output eos);
  reg [3:0] k;  // index of the current unit
  always @(posedge clk)
    if (!rst_n) k <= 4'd0;
    else if (k != 4'd9) k <= k + 4'd1;
  reg [9:0] lab;  // {subject, greet, feature, benefit, price, offer, ends, rival, cta, signoff}
  always @* begin
    case (k)
      4'd0: lab = 10'b1000000000;  /* Subject: The Aurora X2 is here, and you're going to love it */
      4'd1: lab = 10'b0100000000;  /* Hi [First Name], */
      4'd2: lab = 10'b0010000000;  /* Meet the Aurora X2, our new headphones with a full 40 hours of battery */
      4'd3: lab = 10'b0001000000;  /* That's enough to carry you from Monday's commute to Friday's workout w */
      4'd4: lab = 10'b0010000000;  /* Adaptive noise cancelling listens to the world around you and adjusts  */
      4'd5: lab = 10'b0001000000;  /* Whether you're on a crowded train or in a busy caf?, you'll hear every */
      4'd6: lab = 10'b0010000000;  /* Plush memory-foam ear cushions gently shape themselves around your ear */
      4'd7: lab = 10'b0001111010;  /* You'll stay comfortable from the first track to the last, so order you */
      4'd8: lab = 10'b0000000001;  /* The Aurora Team */
      default: lab = 10'b0;
    endcase
  end
  assign eos = (k == 4'd9);
  assign {subject, greet, feature, benefit, price, offer, ends, rival, cta, signoff} = lab;
endmodule
