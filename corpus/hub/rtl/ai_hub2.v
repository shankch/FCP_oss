// -----------------------------------------------------------------------------
// HUB-2 : dual-port APB hub (round-robin port selector + one BRG-1 style bridge)
//
// Two requesters (port 0, port 1) share one APB3 master.  One transaction is
// processed at a time.  The block is built from
//
//   * a round-robin selector   : picks the port whose command is accepted, using
//                                "the port that was NOT accepted most recently
//                                goes first" when both ports have a command
//                                pending (work conserving otherwise);
//   * one BRG-1 style bridge   : latches the accepted command, runs exactly one
//                                APB3 transfer (1-cycle setup, access until
//                                pready), captures prdata/pslverr and presents
//                                one response, held until the issuing port's
//                                rk_ready is sampled high;
//   * response steering        : the response is routed to the port that issued
//                                the command (tracked in owner_q) and is never
//                                visible on the other port.
//
// Bridge state is kept in flops (no separate state encoding is needed):
//
//   idle   : psel_q = 0, rvalid_q = 0
//   setup  : psel_q = 1, penable_q = 0      (exactly one cycle)
//   access : psel_q = 1, penable_q = 1      (until pready is sampled high)
//   resp   : psel_q = 0, rvalid_q = 1       (until owner's ready is sampled high)
//
// A new command is accepted only in idle, or in the very cycle in which the
// pending response is accepted ("may accept the next command in the same cycle
// in which the response is accepted", BRG-1 section 5).
//
// Choices made where the specification leaves freedom:
//   * After reset no port has been accepted yet; port 0 wins the first tie.
//   * With nothing pending (e.g. the cycle after reset) both c0_ready and
//     c1_ready are high.  With both ports pending only the winner's ready is
//     high, so at most one command is accepted per cycle.  A port's ready never
//     depends on its own valid, only on the other port's valid.
//   * pwrite/paddr/pwdata always carry the three command fields (pwdata is not
//     cleared on reads); they hold their value while psel is low.
//   * rdata/err are captured from prdata/pslverr at the completing access cycle
//     for every transfer (the write-response rdata value is a don't care) and are
//     forced to zero on the port that does not own the response.
//   * pready is looked at only in the access phase.  There are no timeouts: any
//     pready latency and any response-accept latency is tolerated.
//   * A reset in the middle of a transaction silently abandons it (no response).
//
// Synchronous active-low reset; no power-up values, no simulation-only code.
// -----------------------------------------------------------------------------
module hub2 #(
    parameter AW = 8,
    parameter DW = 8
) (
    input  wire          clk,
    input  wire          rst_n,

    // port 0 command channel
    input  wire          c0_valid,
    output wire          c0_ready,
    input  wire          c0_write,
    input  wire [AW-1:0] c0_addr,
    input  wire [DW-1:0] c0_wdata,

    // port 1 command channel
    input  wire          c1_valid,
    output wire          c1_ready,
    input  wire          c1_write,
    input  wire [AW-1:0] c1_addr,
    input  wire [DW-1:0] c1_wdata,

    // port 0 response channel
    output wire          r0_valid,
    input  wire          r0_ready,
    output wire [DW-1:0] r0_rdata,
    output wire          r0_err,

    // port 1 response channel
    output wire          r1_valid,
    input  wire          r1_ready,
    output wire [DW-1:0] r1_rdata,
    output wire          r1_err,

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

    // ------------------------------------------------------------------
    // State
    // ------------------------------------------------------------------
    reg          psel_q;      // APB psel   (setup + access phases)
    reg          penable_q;   // APB penable (access phase)
    reg          rvalid_q;    // a response is being presented / held
    reg          owner_q;     // port that issued the in-flight transaction
    reg          prio1_q;     // 1: port 1 wins a tie, 0: port 0 wins a tie
    reg          pwrite_q;    // latched command fields -> APB
    reg [AW-1:0] paddr_q;
    reg [DW-1:0] pwdata_q;
    reg [DW-1:0] rdata_q;     // prdata sampled when the transfer completed
    reg          err_q;       // pslverr sampled when the transfer completed

    // ------------------------------------------------------------------
    // Bridge availability
    // ------------------------------------------------------------------
    // Ready of the response channel of the port that owns the response.
    wire rsp_ready_own = owner_q ? r1_ready : r0_ready;

    // The bridge can take a command when no transfer is in progress and no
    // response is pending, or when the pending response is accepted right now.
    wire can_accept = ~psel_q & (~rvalid_q | rsp_ready_own);

    // ------------------------------------------------------------------
    // Round-robin selector
    //   ck_ready = can_accept unless the other port has a command pending and
    //   wins the tie.  With only one port pending that port is always served;
    //   with both pending exactly one ready is raised (<= 1 accept / cycle).
    //   With nothing pending (e.g. right after reset) both readies are high.
    // ------------------------------------------------------------------
    assign c0_ready = can_accept & ~(c1_valid &  prio1_q);
    assign c1_ready = can_accept & ~(c0_valid & ~prio1_q);

    wire acc0 = c0_valid & c0_ready;   // command accepted from port 0
    wire acc1 = c1_valid & c1_ready;   // command accepted from port 1
    wire acc  = acc0 | acc1;           // never both (see ready equations)

    // ------------------------------------------------------------------
    // Bridge + response registers
    // ------------------------------------------------------------------
    always @(posedge clk) begin
        if (!rst_n) begin
            psel_q    <= 1'b0;
            penable_q <= 1'b0;
            rvalid_q  <= 1'b0;
            owner_q   <= 1'b0;
            prio1_q   <= 1'b0;           // port 0 is served first after reset
            pwrite_q  <= 1'b0;
            paddr_q   <= {AW{1'b0}};
            pwdata_q  <= {DW{1'b0}};
            rdata_q   <= {DW{1'b0}};
            err_q     <= 1'b0;
        end else if (acc) begin
            // Command accepted (bridge idle, or response accepted this cycle):
            // latch it and start the setup phase in the next cycle.
            psel_q    <= 1'b1;
            penable_q <= 1'b0;
            rvalid_q  <= 1'b0;
            owner_q   <= acc1;
            prio1_q   <= acc0;           // the other port goes first next time
            pwrite_q  <= acc1 ? c1_write : c0_write;
            paddr_q   <= acc1 ? c1_addr  : c0_addr;
            pwdata_q  <= acc1 ? c1_wdata : c0_wdata;
        end else if (psel_q) begin
            if (!penable_q) begin
                // setup phase lasts exactly one cycle; pready is ignored here
                penable_q <= 1'b1;
            end else if (pready) begin
                // access phase ends: transfer completes in this cycle
                psel_q    <= 1'b0;
                penable_q <= 1'b0;
                rvalid_q  <= 1'b1;       // response presented next cycle
                rdata_q   <= prdata;
                err_q     <= pslverr;
            end
        end else if (rvalid_q & rsp_ready_own) begin
            // response accepted and no new command taken in the same cycle
            rvalid_q  <= 1'b0;
        end
    end

    // ------------------------------------------------------------------
    // Outputs
    // ------------------------------------------------------------------
    assign psel    = psel_q;
    assign penable = penable_q;
    assign pwrite  = pwrite_q;
    assign paddr   = paddr_q;
    assign pwdata  = pwdata_q;

    // Response steering: only the issuing port ever sees valid / data / err.
    assign r0_valid = rvalid_q & ~owner_q;
    assign r1_valid = rvalid_q &  owner_q;
    assign r0_rdata = rdata_q & {DW{r0_valid}};
    assign r1_rdata = rdata_q & {DW{r1_valid}};
    assign r0_err   = err_q & r0_valid;
    assign r1_err   = err_q & r1_valid;

endmodule
