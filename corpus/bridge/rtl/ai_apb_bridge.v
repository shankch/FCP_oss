// =============================================================================
// apb_bridge - BRG-1 command-to-APB3 bridge (spec.md v1.0)
//
// A valid/ready command channel is turned into exactly one APB3 transfer per
// command, and the result is returned on a valid/ready response channel.
// One transaction is in flight at a time, strictly in order.  Single clock,
// synchronous active-low reset.  Every output is a function of flops only
// (no combinational path from any input to any output).
//
// FSM, Gray coded so that each normal (non-reset) transition changes exactly
// one state bit, which keeps the decoded outputs free of decode hazards:
//
//   IDLE   2'b00  cmd_ready=1.  cmd_valid: latch the command, go to SETUP.
//   SETUP  2'b01  psel=1 penable=0, exactly one cycle, then ACCESS.
//   ACCESS 2'b11  psel=1 penable=1 until pready is sampled high.  At that
//                 edge pslverr/prdata are captured and the FSM goes to RESP.
//   RESP   2'b10  rsp_valid=1, rsp_rdata/rsp_err held until rsp_ready is
//                 sampled high, then IDLE.
//
// Timing, command accepted in cycle N and w wait states in the access phase:
//   SETUP in N+1, ACCESS in N+2 .. N+2+w, rsp_valid in N+3+w.
// With the slave limit of 4 cycles the response is presented in N+7 at the
// latest, inside the 8-cycle budget of spec section 5.
//
// Interpretation choices where the specification is silent or ambiguous:
//   * cmd_ready is high in IDLE only.  It is NOT raised in the cycle in which
//     a response is being accepted: spec 3 says cmd_ready needs "no response
//     pending", and the same-cycle accept of spec 5 is only a "may".
//     Cost: minimum 4 cycles per transaction.  To take the optional accept
//     instead: cmd_ready = IDLE | (RESP & rsp_ready), and in RESP with
//     rsp_ready the FSM latches cmd_* and goes to SETUP when cmd_valid is
//     high (IDLE otherwise).
//   * rsp_rdata is prdata sampled at completion, even if pslverr is set.
//     Spec 5 defines it only for reads; for a write response it carries
//     whatever prdata was on the bus at completion (a don't care).
//   * pwdata is driven from cmd_wdata for reads as well (spec 4, literal).
//   * pready is ignored outside the ACCESS phase.  There is no timeout: the
//     access phase lasts until pready is sampled high (spec 4).
//   * A reset aborts any transfer or response in flight and no response is
//     generated for an aborted command.  The data registers are reset as
//     well, so no output is X after reset.
//   * paddr/pwrite/pwdata (don't care while psel is low) keep the last command
//     and rsp_rdata/rsp_err (don't care while rsp_valid is low) keep the last
//     response until they are overwritten.
// =============================================================================
module apb_bridge #(
    parameter AW = 8,
    parameter DW = 8
) (
    input  wire          clk,
    input  wire          rst_n,
    // command channel
    input  wire          cmd_valid,
    output wire          cmd_ready,
    input  wire          cmd_write,
    input  wire [AW-1:0] cmd_addr,
    input  wire [DW-1:0] cmd_wdata,
    // response channel
    output wire          rsp_valid,
    input  wire          rsp_ready,
    output wire [DW-1:0] rsp_rdata,
    output wire          rsp_err,
    // APB3 master
    output wire          psel,
    output wire          penable,
    output wire          pwrite,
    output wire [AW-1:0] paddr,
    output wire [DW-1:0] pwdata,
    input  wire          pready,
    input  wire [DW-1:0] prdata,
    input  wire          pslverr
);

    localparam [1:0] ST_IDLE   = 2'b00,
                     ST_SETUP  = 2'b01,
                     ST_ACCESS = 2'b11,
                     ST_RESP   = 2'b10;

    reg [1:0]    state;
    reg          pwrite_q;
    reg [AW-1:0] paddr_q;
    reg [DW-1:0] pwdata_q;
    reg [DW-1:0] rsp_rdata_q;
    reg          rsp_err_q;

    always @(posedge clk) begin
        if (!rst_n) begin
            state       <= ST_IDLE;
            pwrite_q    <= 1'b0;
            paddr_q     <= {AW{1'b0}};
            pwdata_q    <= {DW{1'b0}};
            rsp_rdata_q <= {DW{1'b0}};
            rsp_err_q   <= 1'b0;
        end else begin
            case (state)
                ST_IDLE: begin
                    // cmd_ready is high in this state: cmd_valid means accept.
                    if (cmd_valid) begin
                        pwrite_q <= cmd_write;
                        paddr_q  <= cmd_addr;
                        pwdata_q <= cmd_wdata;
                        state    <= ST_SETUP;
                    end
                end
                ST_SETUP: begin
                    // Exactly one cycle; pready is not looked at here.
                    state <= ST_ACCESS;
                end
                ST_ACCESS: begin
                    // The transfer completes in the cycle pready is high.
                    if (pready) begin
                        rsp_rdata_q <= prdata;
                        rsp_err_q   <= pslverr;
                        state       <= ST_RESP;
                    end
                end
                ST_RESP: begin
                    if (rsp_ready) begin
                        state <= ST_IDLE;
                    end
                end
            endcase
        end
    end

    assign cmd_ready = (state == ST_IDLE);
    assign psel      = (state == ST_SETUP) | (state == ST_ACCESS);
    assign penable   = (state == ST_ACCESS);
    assign rsp_valid = (state == ST_RESP);

    assign pwrite    = pwrite_q;
    assign paddr     = paddr_q;
    assign pwdata    = pwdata_q;
    assign rsp_rdata = rsp_rdata_q;
    assign rsp_err   = rsp_err_q;

endmodule
