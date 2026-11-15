// Response "sonnet" replayed as a chip by the FCP text adapter (frame.md).
// Labels: rules + labeler A (claude-sonnet-5-5). 9 units; unit i drives the outputs in cycle i+1 (cycle 0 is reset),
// then eos rises and stays high with every label false. Generated; do not edit.
module response (input clk, input rst_n, output subject, output greet, output feature, output benefit, output price, output offer, output ends, output rival, output cta, output signoff, output eos);
  reg [3:0] k;  // index of the current unit
  always @(posedge clk)
    if (!rst_n) k <= 4'd0;
    else if (k != 4'd9) k <= k + 4'd1;
  reg [9:0] lab;  // {subject, greet, feature, benefit, price, offer, ends, rival, cta, signoff}
  always @* begin
    case (k)
      4'd0: lab = 10'b1010000000;  /* Subject: Say hello to the Aurora X2, our new wireless headphones */
      4'd1: lab = 10'b0100000000;  /* Hi [First Name], */
      4'd2: lab = 10'b0010000000;  /* We're thrilled to introduce the Aurora X2 headphones, with adaptive no */
      4'd3: lab = 10'b0001000000;  /* Whether you're commuting, working or winding down, you can tune out th */
      4'd4: lab = 10'b0010000000;  /* The X2 also delivers a remarkable 40-hour battery life. */
      4'd5: lab = 10'b0001000000;  /* That's days of listening between charges, so you can leave the charger */
      4'd6: lab = 10'b0010000000;  /* And its memory-foam ear cushions contour gently to your ears. */
      4'd7: lab = 10'b0001111010;  /* You can listen in comfort, hour after hour, so order your Aurora X2 to */
      4'd8: lab = 10'b0000000001;  /* The Aurora Team */
      default: lab = 10'b0;
    endcase
  end
  assign eos = (k == 4'd9);
  assign {subject, greet, feature, benefit, price, offer, ends, rival, cta, signoff} = lab;
endmodule
