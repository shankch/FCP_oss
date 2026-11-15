//------------------------------------------------------------------------------
// sync_fifo -- SFIFO-01 single-clock synchronous FIFO, first-word fall-through
//
// Implementation notes (see spec.md v1.2):
//   * Storage is a DEPTH x WIDTH register-file array used as a circular
//     buffer. Read and write pointers wrap explicitly at DEPTH-1, so DEPTH
//     does not have to be a power of two.
//   * count, full, empty and almost_full are all flops, updated together from
//     the same next-count value. They therefore always agree with each other
//     and change in the cycle after the operation that changes them.
//   * pop_data is the word at the read pointer (first-word fall-through): it
//     is valid in every cycle in which empty is low, and a pop only advances
//     the read pointer at the clock edge. This satisfies both section 4.3
//     ("always presented") and section 6 ("returns the oldest stored word
//     when pop is asserted"): the head is already on pop_data in the cycle in
//     which pop is asserted, there is no read latency.
//   * push is accepted iff the FIFO is not full, pop iff it is not empty, both
//     judged on the registered flags at the clock edge (spec 4.2 / 4.3). This
//     also applies when push and pop are asserted together at the boundaries:
//       - full  & push & pop : push ignored, pop taken  (count -> DEPTH-1)
//       - empty & push & pop : pop ignored, push taken  (count -> 1)
//     In every other case push+pop together leaves count unchanged (4.4).
//   * almost_full = (count >= AF_LEVEL), spec section 5. (Section 6 of the
//     spec says "greater than"; the two statements conflict and the normative
//     status-flag definition in section 5 is followed. To get the strict
//     variant change the ">=" on the AF_LEVEL compare below to ">".)
//   * Synchronous active-low reset has priority over push and pop. It only
//     clears pointers, count and flags; the storage array is not cleared
//     because no word is observable while count is zero.
//   * pop_data is forced to zero while empty (the spec leaves it undefined);
//     this keeps the output free of X after reset at the cost of WIDTH gates.
//
// Legal parameter range (not checked in hardware): DEPTH >= 2,
// 1 <= AF_LEVEL <= DEPTH, WIDTH >= 1.
//------------------------------------------------------------------------------
module sync_fifo #(
    parameter DEPTH    = 5,
    parameter WIDTH    = 8,
    parameter AF_LEVEL = 3
) (
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         push,
    input  wire [WIDTH-1:0]             push_data,
    input  wire                         pop,
    output wire [WIDTH-1:0]             pop_data,
    output wire                         full,
    output wire                         empty,
    output wire                         almost_full,
    output wire [$clog2(DEPTH+1)-1:0]   count
);

    //--------------------------------------------------------------------------
    // Derived constants
    //--------------------------------------------------------------------------
    localparam CW = $clog2(DEPTH + 1);                  // width of count
    localparam PW = (DEPTH > 1) ? $clog2(DEPTH) : 1;    // width of the pointers

    localparam [CW-1:0] DEPTH_C = DEPTH;                // count value when full
    localparam [CW-1:0] AF_C    = AF_LEVEL;             // almost-full threshold
    localparam [PW-1:0] LAST_P  = DEPTH - 1;            // last storage index

    //--------------------------------------------------------------------------
    // State
    //--------------------------------------------------------------------------
    reg [WIDTH-1:0] mem [0:DEPTH-1];                    // storage, no reset
    reg [PW-1:0]    wr_ptr;                             // next slot to write
    reg [PW-1:0]    rd_ptr;                             // slot holding the head word
    reg [CW-1:0]    count_r;                            // number of stored words
    reg             full_r;                             // count == DEPTH
    reg             empty_r;                            // count == 0
    reg             af_r;                               // count >= AF_LEVEL

    //--------------------------------------------------------------------------
    // Accepted operations. Judged on the registered flags, so a push at full or
    // a pop at empty is ignored even when the opposite operation is present.
    //--------------------------------------------------------------------------
    wire do_push = push & ~full_r;
    wire do_pop  = pop  & ~empty_r;

    //--------------------------------------------------------------------------
    // Next-state logic
    //--------------------------------------------------------------------------
    wire [PW-1:0] wr_ptr_nxt = (wr_ptr == LAST_P) ? {PW{1'b0}} : (wr_ptr + 1'b1);
    wire [PW-1:0] rd_ptr_nxt = (rd_ptr == LAST_P) ? {PW{1'b0}} : (rd_ptr + 1'b1);

    wire [CW-1:0] count_nxt = ( do_push & ~do_pop) ? (count_r + 1'b1) :
                              (~do_push &  do_pop) ? (count_r - 1'b1) :
                                                      count_r;

    //--------------------------------------------------------------------------
    // Control registers (synchronous active-low reset)
    //--------------------------------------------------------------------------
    always @(posedge clk) begin
        if (!rst_n) begin
            wr_ptr  <= {PW{1'b0}};
            rd_ptr  <= {PW{1'b0}};
            count_r <= {CW{1'b0}};
            full_r  <= 1'b0;
            empty_r <= 1'b1;
            af_r    <= 1'b0;
        end else begin
            if (do_push) wr_ptr <= wr_ptr_nxt;
            if (do_pop)  rd_ptr <= rd_ptr_nxt;
            count_r <= count_nxt;
            full_r  <= (count_nxt == DEPTH_C);
            empty_r <= (count_nxt == {CW{1'b0}});
            af_r    <= (count_nxt >= AF_C);             // section 5: >= AF_LEVEL
        end
    end

    //--------------------------------------------------------------------------
    // Storage write. Gated by rst_n so that reset wins over a simultaneous push.
    //--------------------------------------------------------------------------
    always @(posedge clk) begin
        if (rst_n & do_push)
            mem[wr_ptr] <= push_data;
    end

    //--------------------------------------------------------------------------
    // Outputs
    //--------------------------------------------------------------------------
    assign pop_data    = empty_r ? {WIDTH{1'b0}} : mem[rd_ptr];
    assign full        = full_r;
    assign empty       = empty_r;
    assign almost_full = af_r;
    assign count       = count_r;

endmodule
