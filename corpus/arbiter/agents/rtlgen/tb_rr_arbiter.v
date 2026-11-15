// Self-checking testbench for rr_arbiter (Verilog-2005).
//
//   iverilog -g2005 [-P tb_rr_arbiter.N=8] -o sim.vvp tb_rr_arbiter.v ../rtl/rr_arbiter.v
//   vvp sim.vvp         -> prints "TB_RESULT: PASS ..." or "TB_RESULT: FAIL ..."
//   (list the testbench first so its `timescale also applies to the RTL file)
//
// Checks
//   * cycle-accurate reference model (binary pointer, loop search; written
//     independently of the RTL's thermometer-mask structure)
//   * spec-derived properties, independent of the pointer policy:
//       3.1 at most one grant; gnt[i] only if req[i] was high in the previous cycle
//       3.1 gnt changes only at a clock edge (registered output)
//       3.2 req != 0 in a cycle -> exactly one grant in the next cycle
//       3.4 a requester that keeps req high is granted within N cycles
//       4   no grant in the cycle after an edge that sampled rst_n low
//   * directed N=4 sequences (reset values, rotation, wrap, idle hold, ...)
//   * random stimulus: unconstrained, Sec.5-style requesters (with and without
//     the one-cycle "stale request" after a grant), random resets
`timescale 1ns/1ps

module tb_rr_arbiter;
    parameter N    = 4;
    parameter NCYC = 20000;        // cycles per random phase
    parameter SEED = 20260611;

    reg          clk;
    reg          rst_n;
    reg  [N-1:0] req;
    wire [N-1:0] gnt;

    rr_arbiter #(.N(N)) dut (.clk(clk), .rst_n(rst_n), .req(req), .gnt(gnt));

    initial clk = 1'b0;
    always #5 clk = ~clk;          // rising edges at 5, 15, 25, ... ns

    //--------------------------------------------------------------------------
    // bookkeeping
    //--------------------------------------------------------------------------
    integer     errors, cycles, n_grants, n_b2b, n_resets, max_lat, seed;
    integer     wait_cnt [0:N-1];
    reg  [N-1:0] p_req, p_gnt, g_seen;
    reg          p_rst_n;
    integer      m_ptr;
    reg  [N-1:0] m_gnt;
    reg          m_known;
    reg          cov [0:N*(1<<N)-1];

    task err;
        input [8*40-1:0] what;
        begin
            errors = errors + 1;
            if (errors <= 25)
                $display("ERROR @%0t: %0s (rst_n=%b req=%b gnt=%b)",
                         $time, what, rst_n, req, gnt);
        end
    endtask

    //--------------------------------------------------------------------------
    // monitor: samples the cycle that is ending at every rising edge
    //--------------------------------------------------------------------------
    always @(posedge clk) begin : monitor
        integer i, k, idx, win, ones;
        cycles = cycles + 1;
        g_seen = gnt;

        if (m_known) begin
            ones = 0;
            for (i = 0; i < N; i = i + 1)
                if (gnt[i] === 1'b1) ones = ones + 1;

            if (gnt !== m_gnt)                       err("gnt differs from reference model");
            if ((^gnt) === 1'bx)                     err("gnt contains X/Z");
            if (ones > 1)                            err("more than one grant");
            if ((gnt & ~p_req) !== {N{1'b0}})        err("grant without request in prev cycle");
            if (p_rst_n && (p_req !== {N{1'b0}}) && ones != 1)
                                                     err("work conservation violated");
            if (!p_rst_n && ones != 0)               err("grant after reset sampled low");

            if (ones != 0) n_grants = n_grants + 1;
            if ((gnt & p_gnt) !== {N{1'b0}}) n_b2b = n_b2b + 1;
        end

        // fairness: held request must be granted within N cycles
        for (i = 0; i < N; i = i + 1) begin
            if (!m_known || !rst_n) begin
                wait_cnt[i] = 0;
            end else begin
                if (gnt[i]) begin
                    if (wait_cnt[i] > max_lat) max_lat = wait_cnt[i];
                    wait_cnt[i] = 0;
                end else if (wait_cnt[i] >= N) begin
                    err("fairness: no grant within N cycles");
                    wait_cnt[i] = 0;
                end
                if (req[i]) wait_cnt[i] = wait_cnt[i] + 1;
                else        wait_cnt[i] = 0;
            end
        end

        if (m_known && rst_n) cov[m_ptr*(1<<N) + req] = 1'b1;
        if (m_known && !rst_n && p_rst_n) n_resets = n_resets + 1;

        // reference model: next-cycle grant from the inputs sampled now
        if (!rst_n) begin
            m_gnt   = {N{1'b0}};
            m_ptr   = 0;
            m_known = 1'b1;
        end else if (m_known) begin
            win = -1;
            for (k = 0; k < N; k = k + 1) begin
                idx = (m_ptr + k) % N;
                if (win < 0 && req[idx]) win = idx;
            end
            m_gnt = {N{1'b0}};
            if (win >= 0) begin
                m_gnt[win] = 1'b1;
                m_ptr      = (win + 1) % N;
            end
        end

        p_rst_n = rst_n;
        p_req   = req;
        p_gnt   = gnt;
    end

    // registered output: gnt may only change at a rising clock edge
    always @(gnt) begin
        if (m_known && (($time % 10) != 5)) err("gnt changed away from clock edge");
    end

    //--------------------------------------------------------------------------
    // stimulus helpers
    //--------------------------------------------------------------------------
    function [N-1:0] rnd_req;          // each bit set with probability p/16
        input integer p;
        integer b, r;
        begin
            rnd_req = {N{1'b0}};
            for (b = 0; b < N; b = b + 1) begin
                r = $random(seed) & 15;
                if (r < p) rnd_req[b] = 1'b1;
            end
        end
    endfunction

    function rnd_rst_n;                // 0 with probability rate/256
        input integer rate;
        integer r;
        begin
            r = $random(seed) & 255;
            rnd_rst_n = (r >= rate);
        end
    endfunction

    // directed step: drive for one cycle, check gnt right after the sampling edge
    task apply_check;
        input rn;
        input [N-1:0] r;
        input [N-1:0] e;
        begin
            @(negedge clk);
            rst_n = rn;
            req   = r;
            @(posedge clk);
            #1;
            if (gnt !== e) begin
                errors = errors + 1;
                $display("ERROR @%0t: directed: rst_n=%b req=%b expected gnt=%b got %b",
                         $time, rn, r, e, gnt);
            end
        end
    endtask

    task drive;                        // free-running drive of one cycle
        input rn;
        input [N-1:0] r;
        begin
            @(negedge clk);
            rst_n = rn;
            req   = r;
        end
    endtask

    task run_random;                   // unconstrained random requests
        input integer ncyc;
        input integer dens;            // per-bit request probability dens/16
        input integer rst_rate;        // reset probability rst_rate/256 per cycle
        integer c;
        begin
            for (c = 0; c < ncyc; c = c + 1)
                drive(rnd_rst_n(rst_rate), rnd_req(dens));
        end
    endtask

    task run_protocol;                 // Sec.5 requesters: hold until granted
        input integer ncyc;
        input integer p_new;           // idle requester raises req with prob p_new/16
        input integer same_cycle;      // 1: drop req within the grant cycle (no stale cycle)
        input integer rst_rate;
        integer c, b;
        reg [N-1:0] r;
        begin
            for (c = 0; c < ncyc; c = c + 1) begin
                @(negedge clk);
                // gnt     = grant visible in the current cycle
                // g_seen  = grant visible in the previous cycle (registered requester)
                r = req;
                for (b = 0; b < N; b = b + 1) begin
                    if (r[b]) begin
                        if (same_cycle ? gnt[b] : g_seen[b]) r[b] = 1'b0;
                    end else if (($random(seed) & 15) < p_new) begin
                        r[b] = 1'b1;
                    end
                end
                req   = r;
                rst_n = rnd_rst_n(rst_rate);
            end
        end
    endtask

    //--------------------------------------------------------------------------
    // main sequence
    //--------------------------------------------------------------------------
    integer j, n, covered;

    initial begin
        errors = 0; cycles = 0; n_grants = 0; n_b2b = 0; n_resets = 0; max_lat = 0;
        seed = SEED;
        m_known = 1'b0; m_ptr = 0; m_gnt = {N{1'b0}};
        p_req = {N{1'b0}}; p_gnt = {N{1'b0}}; g_seen = {N{1'b0}}; p_rst_n = 1'b0;
        for (j = 0; j < N; j = j + 1) wait_cnt[j] = 0;
        for (j = 0; j < N*(1<<N); j = j + 1) cov[j] = 1'b0;
        rst_n = 1'b0;
        req   = {N{1'b1}};

        //---------------- directed (N = 4) ------------------------------------
        if (N == 4) begin
            // reset with requests pending: no grant during or right after reset
            apply_check(1'b0, 4'b1111, 4'b0000);
            apply_check(1'b0, 4'b1111, 4'b0000);
            apply_check(1'b0, 4'b0101, 4'b0000);
            // all request: 0,1,2,3,0 (requester 0 first after reset, rotation, wrap)
            apply_check(1'b1, 4'b1111, 4'b0001);
            apply_check(1'b1, 4'b1111, 4'b0010);
            apply_check(1'b1, 4'b1111, 4'b0100);
            apply_check(1'b1, 4'b1111, 4'b1000);
            apply_check(1'b1, 4'b1111, 4'b0001);
            // idle cycles keep the pointer (next is 1)
            apply_check(1'b1, 4'b0000, 4'b0000);
            apply_check(1'b1, 4'b0000, 4'b0000);
            apply_check(1'b1, 4'b1111, 4'b0010);
            // single requesters; pointer follows the last winner (granted+1)
            apply_check(1'b1, 4'b0001, 4'b0001);
            apply_check(1'b1, 4'b0100, 4'b0100);
            apply_check(1'b1, 4'b1111, 4'b1000);   // pointer = 3 after winner 2
            apply_check(1'b1, 4'b1000, 4'b1000);
            // skipping idle requesters, wrap-around
            apply_check(1'b1, 4'b0110, 4'b0010);
            apply_check(1'b1, 4'b0110, 4'b0100);
            apply_check(1'b1, 4'b0110, 4'b0010);   // pointer 3 -> 3,0 idle -> 1
            apply_check(1'b1, 4'b1001, 4'b1000);   // pointer 2 -> 3
            apply_check(1'b1, 4'b1001, 4'b0001);   // pointer 0 -> 0
            apply_check(1'b1, 4'b1001, 4'b1000);   // pointer 1 -> 3
            // held single request is granted every cycle (work conservation)
            apply_check(1'b1, 4'b0100, 4'b0100);
            apply_check(1'b1, 4'b0100, 4'b0100);
            apply_check(1'b1, 4'b0100, 4'b0100);
            apply_check(1'b1, 4'b0000, 4'b0000);
            // requester 3 is NOT a strict-priority requester: 0 beats 3 after reset
            apply_check(1'b0, 4'b1001, 4'b0000);
            apply_check(1'b1, 4'b1001, 4'b0001);
            apply_check(1'b1, 4'b1001, 4'b1000);
            apply_check(1'b1, 4'b1001, 4'b0001);
            // mid-operation reset restores the pointer to requester 0 (was 1)
            apply_check(1'b0, 4'b1111, 4'b0000);
            apply_check(1'b1, 4'b1111, 4'b0001);
            // request only during reset: nothing after release
            apply_check(1'b0, 4'b0010, 4'b0000);
            apply_check(1'b1, 4'b0000, 4'b0000);
            apply_check(1'b1, 4'b0000, 4'b0000);
        end

        //---------------- constant request patterns after a reset --------------
        for (n = 0; n < (1<<N); n = n + 1) begin
            drive(1'b0, {N{1'b1}});
            drive(1'b0, n[N-1:0]);
            for (j = 0; j < 3*N + 2; j = j + 1) drive(1'b1, n[N-1:0]);
        end

        //---------------- unconstrained random ---------------------------------
        run_random(NCYC, 1, 0);
        run_random(NCYC, 2, 0);
        run_random(NCYC, 4, 0);
        run_random(NCYC, 8, 0);
        run_random(NCYC, 12, 0);
        run_random(NCYC, 15, 0);
        run_random(NCYC, 16, 0);
        run_random(NCYC, 4, 6);
        run_random(NCYC, 8, 6);
        run_random(NCYC, 14, 6);
        run_random(NCYC, 16, 30);

        //---------------- Sec.5 requesters --------------------------------------
        drive(1'b0, {N{1'b0}});
        run_protocol(NCYC, 1, 0, 0);
        run_protocol(NCYC, 4, 0, 0);
        run_protocol(NCYC, 16, 0, 0);
        run_protocol(NCYC, 4, 1, 0);
        run_protocol(NCYC, 16, 1, 0);
        run_protocol(NCYC, 8, 0, 5);
        run_protocol(NCYC, 8, 1, 5);

        // drain
        drive(1'b1, {N{1'b0}});
        drive(1'b1, {N{1'b0}});
        drive(1'b1, {N{1'b0}});
        @(posedge clk);
        #1;

        covered = 0;
        for (j = 0; j < N*(1<<N); j = j + 1) if (cov[j]) covered = covered + 1;

        $display("TB_STATS: N=%0d cycles=%0d grants=%0d b2b_grants=%0d resets=%0d max_wait_to_grant=%0d ptr_x_req_cov=%0d/%0d",
                 N, cycles, n_grants, n_b2b, n_resets, max_lat, covered, N*(1<<N));
        if (errors == 0 && covered == N*(1<<N))
            $display("TB_RESULT: PASS N=%0d", N);
        else
            $display("TB_RESULT: FAIL N=%0d errors=%0d cov=%0d/%0d", N, errors, covered, N*(1<<N));
        $finish;
    end

endmodule
