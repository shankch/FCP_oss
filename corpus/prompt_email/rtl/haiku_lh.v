// Response "haiku" replayed as a chip by the FCP text adapter (frame.md).
// Labels: rules + adjudicator (adjudicator (human role), written before reading A and B). 9 units; unit i drives the outputs in cycle i+1 (cycle 0 is reset),
// then eos rises and stays high with every label false. Generated; do not edit.
module response (input clk, input rst_n, output subject, output greet, output feature, output benefit, output price, output offer, output ends, output rival, output cta, output signoff, output eos);
  reg [3:0] k;  // index of the current unit
  always @(posedge clk)
    if (!rst_n) k <= 4'd0;
    else if (k != 4'd9) k <= k + 4'd1;
  reg [9:0] lab;  // {subject, greet, feature, benefit, price, offer, ends, rival, cta, signoff}
  always @* begin
    case (k)
      4'd0: lab = 10'b1000000000;  /* Subject: Meet the Aurora X2, your new favourite way to listen */
      4'd1: lab = 10'b0100000000;  /* Hi [First Name], */
      4'd2: lab = 10'b0010000000;  /* Meet the Aurora X2, which delivers 40 hours of battery life on a singl */
      4'd3: lab = 10'b0001000000;  /* Keep your music going through long flights, busy weeks and everything  */
      4'd4: lab = 10'b0011000000;  /* Adaptive noise cancelling adjusts to the sounds around you, so the noi */
      4'd5: lab = 10'b0001000000;  /* Focus on your work or lose yourself in your favourite album, whether y */
      4'd6: lab = 10'b0010000000;  /* Memory-foam ear cushions mould gently to your ears for a soft, comfort */
      4'd7: lab = 10'b0001111010;  /* Comfort like this means you will forget you are wearing them, so order */
      4'd8: lab = 10'b0000000001;  /* The Aurora Team */
      default: lab = 10'b0;
    endcase
  end
  assign eos = (k == 4'd9);
  assign {subject, greet, feature, benefit, price, offer, ends, rival, cta, signoff} = lab;
endmodule
