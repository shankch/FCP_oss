//------------------------------------------------------------------------------
// rr_arbiter -- RRA-4 registered round-robin arbiter (spec.md v0.9)
//
// Behaviour implemented
//   * Registered grant: req is sampled at each rising edge of clk and the
//     one-hot decision is visible on gnt during the following cycle.
//   * Work conserving: req != 0 in a cycle gives exactly one grant in the next
//     cycle, req == 0 gives none.  gnt[i] is only ever derived from req[i] of
//     the previous cycle.  Requests are NOT masked after a grant: a requester
//     that has not yet seen its grant still has req high during the grant
//     cycle and is (spec 3.2) granted again, so back-to-back grants happen.
//   * Round robin: after reset the priority order is 0,1,..,N-1.  After a grant
//     to requester g the order becomes g+1,..,N-1,0,..,g (the winner drops to
//     lowest priority).  The pointer moves only when a grant is issued.  A
//     requester that holds req high is granted at most N cycles after the
//     cycle in which req first went high (N-1 grants to others, then its own).
//   * Synchronous active-low reset: gnt <= 0 and the pointer returns to
//     requester 0.  Requests seen while rst_n is low are ignored, so gnt is 0
//     in every cycle that follows an edge at which rst_n was low, including
//     the first cycle after rst_n is released.
//
// Spec conflicts / ambiguities and how they were resolved
//   (1) Sec.1 "granted in the same cycle" vs Sec.3.1/3.2 and design.yaml
//       ("registered", visible in the next cycle): registered, 1-cycle latency.
//   (2) Sec.3.3 "requester 3 ... always wins" contradicts the initial order
//       (3 is lowest), the rotation, and the Sec.3.4 bound (a requester 3 that
//       keeps re-requesting would starve all others).  NOT implemented:
//       requester 3 is an ordinary round-robin participant.  For strict
//       maintenance priority, replace the assignment of `sel` below by
//           sel = req[3] ? 4'b1000 : (|req_hi) ? pick_hi : pick_lo;
//       (starvation of requesters 0..2 is then possible).
//   (3) "rotates by one position after each grant" is taken as the classic
//       round-robin rule (pointer := granted + 1).  The literal alternative
//       (pointer := pointer + 1 per grant) differs only when the requester at
//       the pointer is idle.
//   (4) Sec.4 "while rst_n is low, and in the cycle after it": implemented as
//       the synchronous clear above.  Since reset is synchronous and gnt is a
//       register, a grant registered before rst_n fell stays visible until the
//       first edge that samples rst_n low; gnt is deliberately not gated
//       combinationally by rst_n.
//   (5) Sec.3.2 + Sec.5 + "grants last one cycle": a requester can only drop
//       req after it has seen gnt, so req is still high in the grant cycle and
//       Sec.3.2 then demands another grant.  One held request therefore yields
//       back-to-back one-cycle grants; requests are not masked to prevent it
//       (that would break Sec.3.2 when a single requester is active).
//   (6) N != 4: "requester 3" and "RRA-4" are N = 4 specific; the logic below
//       is generic in N and has no special requester.
//------------------------------------------------------------------------------
module rr_arbiter #(
    parameter N = 4
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [N-1:0] req,
    output reg  [N-1:0] gnt
);

    localparam [N-1:0] ONE = 1;

    // Priority pointer, thermometer coded: ptr_mask[i] = 1 for every requester
    // that comes at or after the highest-priority requester in index order.
    // Reset value all-ones = pointer at requester 0.  After a grant to g it
    // holds the requesters strictly above g (all-zero when g = N-1, which
    // behaves like a pointer wrapped to requester 0 because pick_lo is then
    // used).
    reg  [N-1:0] ptr_mask;

    // Candidates at/after the pointer; lowest set bit of a vector is v & (~v + 1).
    wire [N-1:0] req_hi  = req & ptr_mask;
    wire [N-1:0] pick_hi = req_hi & (~req_hi + ONE);
    // Wrap-around: nobody at/after the pointer, take the lowest requester.
    wire [N-1:0] pick_lo = req & (~req + ONE);

    // One-hot decision for the requests sampled in this cycle (0 if req == 0).
    wire [N-1:0] sel = (|req_hi) ? pick_hi : pick_lo;

    always @(posedge clk) begin
        if (!rst_n) begin
            gnt      <= {N{1'b0}};
            ptr_mask <= {N{1'b1}};
        end else begin
            gnt <= sel;
            if (|sel)
                ptr_mask <= ~(sel | (sel - ONE));   // requesters above the winner
        end
    end

endmodule
