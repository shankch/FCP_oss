// Self-checking testbench for sync_fifo (SFIFO-01).
//
// Verilog-2005 only. Parameters can be overridden from the command line, e.g.
//   iverilog -g2005 -Ptb.DEPTH=7 -Ptb.AF_LEVEL=2 ...
//
// Structure
//   * A cycle-accurate reference model (shift-register queue) is updated on
//     every rising edge from the same inputs the DUT sees.
//   * The main thread works at falling edges: it applies inputs, checks that no
//     output moves before the next rising edge (outputs are registered), and
//     at the next falling edge compares every output with the model.
//   * Directed tests pin down the interpretation chosen for the spec
//     ambiguities with literal expected values (not derived from the model).
//   * Randomised phases (push-heavy, pop-heavy, balanced, always-both, sparse,
//     fill-only, drain-only, near-saturated) with random resets at any time.
//   * Event counters make sure every boundary case was actually exercised.
module tb;

    parameter DEPTH    = 5;
    parameter WIDTH    = 8;
    parameter AF_LEVEL = 3;
    parameter SEED     = 1;
    parameter NCYC     = 60000;
    parameter PHASE    = 300;

    localparam CW = $clog2(DEPTH + 1);

    reg              clk;
    reg              rst_n;
    reg              push;
    reg  [WIDTH-1:0] push_data;
    reg              pop;
    wire [WIDTH-1:0] pop_data;
    wire             full;
    wire             empty;
    wire             almost_full;
    wire [CW-1:0]    count;

    sync_fifo #(.DEPTH(DEPTH), .WIDTH(WIDTH), .AF_LEVEL(AF_LEVEL)) dut (
        .clk        (clk),
        .rst_n      (rst_n),
        .push       (push),
        .push_data  (push_data),
        .pop        (pop),
        .pop_data   (pop_data),
        .full       (full),
        .empty      (empty),
        .almost_full(almost_full),
        .count      (count)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    //--------------------------------------------------------------------------
    // Reference model (updated on the rising edge, blocking assignments)
    //--------------------------------------------------------------------------
    reg [WIDTH-1:0] q [0:DEPTH-1];
    integer         m_cnt;
    reg             m_valid;
    reg             m_push;
    reg             m_pop;
    reg             m_af_prev;
    integer         mi;

    // event counters
    integer c_push_full, c_pop_empty, c_pp_full, c_pp_empty, c_pp_mid;
    integer c_reached_full, c_reached_empty, c_af_rise, c_af_fall;
    integer c_rst_full, c_rst_push, c_rst_pop, c_rst_mid, c_wrap_w, c_wrap_r;
    integer c_push_acc, c_pop_acc;

    initial begin
        m_cnt = 0;
        m_valid = 1'b0;
        m_af_prev = 1'b0;
        c_push_full = 0; c_pop_empty = 0; c_pp_full = 0; c_pp_empty = 0; c_pp_mid = 0;
        c_reached_full = 0; c_reached_empty = 0; c_af_rise = 0; c_af_fall = 0;
        c_rst_full = 0; c_rst_push = 0; c_rst_pop = 0; c_rst_mid = 0;
        c_wrap_w = 0; c_wrap_r = 0; c_push_acc = 0; c_pop_acc = 0;
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            if (m_valid) begin
                if (m_cnt == DEPTH)             c_rst_full = c_rst_full + 1;
                if (m_cnt > 0 && m_cnt < DEPTH) c_rst_mid  = c_rst_mid  + 1;
                if (push) c_rst_push = c_rst_push + 1;
                if (pop)  c_rst_pop  = c_rst_pop  + 1;
            end
            m_cnt     = 0;
            m_valid   = 1'b1;
            m_af_prev = 1'b0;
        end else if (m_valid) begin
            m_pop  = pop  && (m_cnt > 0);
            m_push = push && (m_cnt < DEPTH);

            if (push && m_cnt == DEPTH)           c_push_full  = c_push_full  + 1;
            if (pop  && m_cnt == 0)               c_pop_empty  = c_pop_empty  + 1;
            if (push && pop && m_cnt == DEPTH)    c_pp_full    = c_pp_full    + 1;
            if (push && pop && m_cnt == 0)        c_pp_empty   = c_pp_empty   + 1;
            if (push && pop && m_cnt > 0 && m_cnt < DEPTH)
                                                  c_pp_mid     = c_pp_mid     + 1;
            if (m_push && dut.wr_ptr == DEPTH-1)  c_wrap_w     = c_wrap_w     + 1;
            if (m_pop  && dut.rd_ptr == DEPTH-1)  c_wrap_r     = c_wrap_r     + 1;
            if (m_push) c_push_acc = c_push_acc + 1;
            if (m_pop)  c_pop_acc  = c_pop_acc  + 1;

            if (m_pop) begin
                for (mi = 0; mi < DEPTH-1; mi = mi + 1)
                    q[mi] = q[mi+1];
                m_cnt = m_cnt - 1;
            end
            if (m_push) begin
                q[m_cnt] = push_data;
                m_cnt = m_cnt + 1;
            end

            if (m_cnt == DEPTH) c_reached_full  = c_reached_full  + 1;
            if (m_cnt == 0)     c_reached_empty = c_reached_empty + 1;
            if ((m_cnt >= AF_LEVEL) && !m_af_prev) c_af_rise = c_af_rise + 1;
            if (!(m_cnt >= AF_LEVEL) && m_af_prev) c_af_fall = c_af_fall + 1;
            m_af_prev = (m_cnt >= AF_LEVEL);
        end
    end

    //--------------------------------------------------------------------------
    // Checking helpers
    //--------------------------------------------------------------------------
    integer errors;
    integer cyc;
    integer seed;
    reg [WIDTH+CW+2:0] snap;
    integer exp_rd;

    task fail;
        input [255:0] what;
        begin
            errors = errors + 1;
            if (errors <= 25)
                $display("ERR t=%0t cyc=%0d: %0s | cnt=%0d/%0d full=%b empty=%b af=%b data=%h/%h",
                         $time, cyc, what, count, m_cnt, full, empty, almost_full,
                         pop_data, q[0]);
        end
    endtask

    // Compare every output with the reference model.
    task check_outputs;
        begin
            if (m_valid) begin
                if (count !== m_cnt)                      fail("count mismatch");
                if (full !== (m_cnt == DEPTH))            fail("full mismatch");
                if (empty !== (m_cnt == 0))               fail("empty mismatch");
                if (almost_full !== (m_cnt >= AF_LEVEL))  fail("almost_full mismatch");
                if (m_cnt > 0 && pop_data !== q[0])       fail("pop_data (head) mismatch");
                if (m_cnt == 0 && (^pop_data === 1'bx))   fail("pop_data is X while empty");
                // internal consistency (hierarchical peek, testbench only)
                if (dut.wr_ptr >= DEPTH || dut.rd_ptr >= DEPTH)
                    fail("pointer out of range");
                exp_rd = (dut.wr_ptr + DEPTH - m_cnt) % DEPTH;
                if (dut.rd_ptr !== exp_rd)                fail("pointer/count inconsistent");
            end
        end
    endtask

    // Literal (model independent) state check used by the directed tests.
    task expect_state;
        input integer n;
        begin
            if (count !== n)                      fail("expect_state: count");
            if (full !== (n == DEPTH))            fail("expect_state: full");
            if (empty !== (n == 0))               fail("expect_state: empty");
            if (almost_full !== (n >= AF_LEVEL))  fail("expect_state: almost_full");
        end
    endtask

    task expect_head;
        input [WIDTH-1:0] d;
        begin
            if (empty !== 1'b0)    fail("expect_head: empty");
            if (pop_data !== d)    fail("expect_head: pop_data");
        end
    endtask

    // Apply inputs at a falling edge; return at the next falling edge with the
    // resulting state already checked against the model.
    task step;
        input             r;
        input             p;
        input             q_;
        input [WIDTH-1:0] d;
        begin
            snap = {pop_data, full, empty, almost_full, count};
            rst_n = r; push = p; pop = q_; push_data = d;
            #3;
            if (m_valid && ({pop_data, full, empty, almost_full, count} !== snap))
                fail("output changed before clock edge");
            @(negedge clk);
            cyc = cyc + 1;
            check_outputs;
        end
    endtask

    task idle;
        input integer n;
        integer k;
        begin
            for (k = 0; k < n; k = k + 1) step(1'b1, 1'b0, 1'b0, {WIDTH{1'b0}});
        end
    endtask

    // data pattern: distinct values for small indices (as far as WIDTH allows)
    function [WIDTH-1:0] dat;
        input integer i;
        reg [127:0] t;
        reg [127:0] ti;
        begin
            ti  = i;
            t   = ti * 128'd2654435761 + 128'd12345;
            t   = t ^ ti ^ (t << 61) ^ (t >> 3);
            dat = t[WIDTH-1:0];
        end
    endfunction

    function integer rnd_u;
        input integer n;
        begin
            rnd_u = ($random(seed) & 32'h7fffffff) % n;
        end
    endfunction

    reg [127:0] r128;
    task rnd_data;
        begin
            r128 = {$random(seed), $random(seed), $random(seed), $random(seed)};
        end
    endtask

    //--------------------------------------------------------------------------
    // Directed tests
    //--------------------------------------------------------------------------
    integer i, j;

    task directed;
        begin
            // D1: reset with push and pop requested; everything ignored.
            expect_state(0);
            step(1'b0, 1'b1, 1'b1, dat(99));
            step(1'b0, 1'b1, 1'b1, dat(98));
            expect_state(0);
            idle(2);
            expect_state(0);

            // D2: fill one word at a time; flags and count after every push,
            // almost_full rises exactly at AF_LEVEL, full exactly at DEPTH.
            for (i = 1; i <= DEPTH; i = i + 1) begin
                step(1'b1, 1'b1, 1'b0, dat(i));
                expect_state(i);
                expect_head(dat(1));          // first-word fall-through
            end

            // D3: push while full is ignored (data and count unchanged).
            step(1'b1, 1'b1, 1'b0, dat(50));
            step(1'b1, 1'b1, 1'b0, dat(51));
            expect_state(DEPTH);
            expect_head(dat(1));

            // D4: push and pop together while full: the push is ignored, the
            // pop is taken, so count falls to DEPTH-1 and dat(60) is dropped.
            step(1'b1, 1'b1, 1'b1, dat(60));
            expect_state(DEPTH - 1);
            expect_head(dat(2));
            // push again (not full any more): it is accepted
            step(1'b1, 1'b1, 1'b0, dat(61));
            expect_state(DEPTH);
            // drain completely, checking order: dat(2..DEPTH), then dat(61)
            for (i = 2; i <= DEPTH; i = i + 1) begin
                expect_head(dat(i));
                step(1'b1, 1'b0, 1'b1, dat(0));
            end
            expect_state(1);
            expect_head(dat(61));
            step(1'b1, 1'b0, 1'b1, dat(0));
            expect_state(0);

            // D5: pop while empty is ignored.
            step(1'b1, 1'b0, 1'b1, dat(0));
            step(1'b1, 1'b0, 1'b1, dat(0));
            expect_state(0);

            // D6: push and pop together while empty: pop ignored, push taken.
            step(1'b1, 1'b1, 1'b1, dat(70));
            expect_state(1);
            expect_head(dat(70));             // visible without any pop
            step(1'b1, 1'b0, 1'b1, dat(0));
            expect_state(0);

            // D7: push and pop together with 1 word stored: count unchanged
            // and the head moves on to the newly pushed word.
            step(1'b1, 1'b1, 1'b0, dat(80));
            expect_state(1);
            for (i = 0; i < 2 * DEPTH + 3; i = i + 1) begin
                step(1'b1, 1'b1, 1'b1, dat(81 + i));
                expect_state(1);
                expect_head(dat(81 + i));
            end
            step(1'b1, 1'b0, 1'b1, dat(0));
            expect_state(0);

            // D8: wrap-around with single-word traffic.
            for (i = 0; i < 4 * DEPTH + 3; i = i + 1) begin
                step(1'b1, 1'b1, 1'b0, dat(200 + i));
                expect_state(1);
                expect_head(dat(200 + i));
                step(1'b1, 1'b0, 1'b1, dat(0));
                expect_state(0);
            end

            // D9: wrap-around with the FIFO kept nearly full.
            for (i = 0; i < DEPTH - 1; i = i + 1)
                step(1'b1, 1'b1, 1'b0, dat(300 + i));
            expect_state(DEPTH - 1);
            for (j = 0; j < 3 * DEPTH + 2; j = j + 1) begin
                expect_head(dat(300 + j));
                step(1'b1, 1'b1, 1'b1, dat(300 + DEPTH - 1 + j));   // count stays DEPTH-1
                expect_state(DEPTH - 1);
            end
            // empty it again
            for (j = 0; j < DEPTH - 1; j = j + 1)
                step(1'b1, 1'b0, 1'b1, dat(0));
            expect_state(0);

            // D10: reset while full (with push and pop requested): FIFO is
            // empty afterwards and no stale word comes back.
            for (i = 0; i < DEPTH; i = i + 1)
                step(1'b1, 1'b1, 1'b0, dat(400 + i));
            expect_state(DEPTH);
            step(1'b0, 1'b1, 1'b1, dat(500));
            expect_state(0);
            step(1'b1, 1'b1, 1'b0, dat(401));
            expect_state(1);
            expect_head(dat(401));
            step(1'b1, 1'b0, 1'b1, dat(0));
            expect_state(0);

            // D11: reset in the middle of operation, single-cycle pulse.
            step(1'b1, 1'b1, 1'b0, dat(600));
            step(1'b1, 1'b1, 1'b0, dat(601));
            step(1'b0, 1'b0, 1'b0, dat(0));
            expect_state(0);
            idle(1);
            expect_state(0);
        end
    endtask

    //--------------------------------------------------------------------------
    // Randomised phases
    //--------------------------------------------------------------------------
    integer ph, pp, pq, rst_hold, use_cnt_data, dctr;
    reg     r_rst, r_push, r_pop;
    reg [WIDTH-1:0] r_data;

    task random_phases;
        begin
            rst_hold = 0;
            dctr = 1000;
            while (cyc < NCYC) begin
                ph = (cyc / PHASE) % 8;
                case (ph)
                    0: begin pp = 205; pq =  51; end   // push heavy
                    1: begin pp =  51; pq = 205; end   // pop heavy
                    2: begin pp = 128; pq = 128; end   // balanced
                    3: begin pp = 256; pq = 256; end   // always both
                    4: begin pp =  26; pq =  26; end   // sparse
                    5: begin pp = 256; pq =   0; end   // push only
                    6: begin pp =   0; pq = 256; end   // pop only
                    default: begin pp = 230; pq = 230; end
                endcase
                use_cnt_data = (cyc / (PHASE * 8)) % 2;

                // reset: random pulses, and more often while full
                if (rst_hold > 0) begin
                    rst_hold = rst_hold - 1;
                    r_rst = 1'b0;
                end else if ((m_cnt == DEPTH && rnd_u(48) == 0) || rnd_u(350) == 0) begin
                    r_rst = 1'b0;
                    rst_hold = rnd_u(3);
                end else begin
                    r_rst = 1'b1;
                end

                r_push = (rnd_u(256) < pp);
                r_pop  = (rnd_u(256) < pq);
                rnd_data;
                if (use_cnt_data) begin
                    r_data = dctr;
                    dctr = dctr + 1;
                end else begin
                    r_data = r128[WIDTH-1:0];
                end
                step(r_rst, r_push, r_pop, r_data);
            end
        end
    endtask

    //--------------------------------------------------------------------------
    // Main
    //--------------------------------------------------------------------------
    integer missing;

    task need;
        input [255:0] name;
        input integer v;
        begin
            if (v == 0) begin
                missing = missing + 1;
                $display("COVER MISSING: %0s", name);
            end
        end
    endtask

    initial begin
        errors = 0;
        cyc    = 0;
        seed   = SEED;
        missing = 0;

        // Reset from time 0 with both requests active (reset must win).
        rst_n = 1'b0; push = 1'b1; pop = 1'b1; push_data = {WIDTH{1'b1}};
        @(negedge clk);                   // first rising edge (t=5) saw reset
        check_outputs;

        directed;
        random_phases;
        idle(3);

        need("push while full",              c_push_full);
        need("pop while empty",              c_pop_empty);
        need("push+pop while full",          c_pp_full);
        need("push+pop while empty",         c_pp_empty);
        need("push+pop mid-level",           c_pp_mid);
        need("reached full",                 c_reached_full);
        need("reached empty",                c_reached_empty);
        need("almost_full rise",             c_af_rise);
        need("almost_full fall",             c_af_fall);
        need("reset while full",             c_rst_full);
        need("reset with push",              c_rst_push);
        need("reset with pop",               c_rst_pop);
        need("reset mid-level",              c_rst_mid);
        need("write pointer wrap",           c_wrap_w);
        need("read pointer wrap",            c_wrap_r);

        $display("COVER pushfull=%0d popempty=%0d ppfull=%0d ppempty=%0d ppmid=%0d full=%0d empty=%0d afup=%0d afdn=%0d rstfull=%0d rstpush=%0d rstpop=%0d rstmid=%0d wrw=%0d wrr=%0d acc_push=%0d acc_pop=%0d",
                 c_push_full, c_pop_empty, c_pp_full, c_pp_empty, c_pp_mid,
                 c_reached_full, c_reached_empty, c_af_rise, c_af_fall,
                 c_rst_full, c_rst_push, c_rst_pop, c_rst_mid, c_wrap_w, c_wrap_r,
                 c_push_acc, c_pop_acc);
        $display("TB_RESULT DEPTH=%0d WIDTH=%0d AF_LEVEL=%0d SEED=%0d cycles=%0d errors=%0d cover_missing=%0d",
                 DEPTH, WIDTH, AF_LEVEL, SEED, cyc, errors, missing);
        if (errors == 0 && missing == 0) $display("TB_PASS");
        else                             $display("TB_FAIL");
        $finish;
    end

endmodule
