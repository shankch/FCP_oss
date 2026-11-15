`timescale 1ns/1ps
// -----------------------------------------------------------------------------
// Self-checking testbench for hub2 (Verilog-2005, iverilog -g2005).
//
//   tb_req   : requester model (one per port).  Keeps valid/command stable
//              until accepted (spec section 5), accepts a response within
//              emin..emax cycles of it being presented, may drive ready high
//              while no response is presented.
//   tb_hub2  : APB slave model (pready within dmin..dmax cycles of the start of
//              the access phase, random garbage on pready/prdata/pslverr
//              otherwise), reset controller, and a protocol-level scoreboard.
//
// Knobs are plusargs; see run.sh for the configurations used.
//
// "spec" checks come straight from spec.md / BRG-1.md.  "design:" checks pin
// down choices this implementation made where the spec leaves freedom.
// -----------------------------------------------------------------------------
module tb_req #(
    parameter AW = 8,
    parameter DW = 8,
    parameter ID = 0
) (
    input  wire          clk,
    input  wire          rst_n,
    input  wire [31:0]   p_req,     // % chance to present a command in a free cycle
    input  wire          b2b,       // 1: may present next command right after accept
    input  wire [31:0]   emin,      // response accept delay range (cycles after presented)
    input  wire [31:0]   emax,
    input  wire [31:0]   p_ridle,   // % chance ready is high while no response presented
    input  wire [31:0]   p_wr,      // % of commands that are writes
    input  wire [31:0]   seed_in,
    output reg           valid,
    input  wire          ready,
    output reg           write,
    output reg  [AW-1:0] addr,
    output reg  [DW-1:0] wdata,
    input  wire          r_valid,
    output reg           r_ready
);
    integer sd;
    integer outstanding;   // accepted commands whose response is not yet accepted
    integer rdelay;        // chosen accept delay for the response being presented
    integer wcnt;          // cycles the current response has been presented, not accepted
    reg     init;

    initial begin
        valid = 1'b0; write = 1'b0; addr = {AW{1'b0}}; wdata = {DW{1'b0}};
        r_ready = 1'b0; init = 1'b0; outstanding = 0; rdelay = 0; wcnt = 0; sd = 1;
    end

    function integer urand;       // 0 .. n-1
        input integer n;
        integer t;
        begin
            t = $random(sd);
            t = t & 32'h7fffffff;
            urand = t % n;
        end
    endfunction

    task issue;
        begin
            valid <= 1'b1;
            write <= (urand(100) < p_wr);
            addr  <= $random(sd);
            wdata <= $random(sd);
        end
    endtask

    always @(posedge clk) begin
        if (!init) begin
            sd   = seed_in + 7919 * (ID + 1);
            init = 1'b1;
        end
        if (!rst_n) begin
            valid       <= 1'b0;
            r_ready     <= 1'b0;
            outstanding = 0;
            wcnt        = 0;
            rdelay      = emin + urand(emax - emin + 1);
        end else begin
            // ---- response channel -------------------------------------------------
            if (r_valid && r_ready) begin                 // accepted this cycle
                outstanding = outstanding - 1;
                wcnt        = 0;
                rdelay      = emin + urand(emax - emin + 1);
                r_ready    <= (urand(100) < p_ridle);
            end else if (r_valid) begin                   // presented, not accepted yet
                wcnt        = wcnt + 1;
                r_ready    <= (wcnt >= rdelay);
            end else begin                                // nothing presented
                wcnt        = 0;
                r_ready    <= (urand(100) < p_ridle);
            end
            // ---- command channel --------------------------------------------------
            if (valid && ready) begin                     // accepted this cycle
                outstanding = outstanding + 1;
                valid      <= 1'b0;
                if (b2b && (urand(100) < p_req)) issue;
            end else if (!valid) begin
                if ((b2b || outstanding == 0) && (urand(100) < p_req)) issue;
            end
            // valid && !ready : hold everything (command stays valid and stable)
        end
    end
endmodule


module tb_hub2;
    parameter AW = 8;
    parameter DW = 8;

    // ------------------------------------------------------------------ knobs
    integer seed, ncyc, p_req0, p_req1, b2b, dmin, dmax, emin, emax;
    integer p_ridle, p_pridle, p_err, p_wr, p_rst, rstmax;
    integer chk_lat, enf_wait, wait_limit, trace;

    initial begin
        if (!$value$plusargs("seed=%d",   seed))       seed       = 1;
        if (!$value$plusargs("ncyc=%d",   ncyc))       ncyc       = 20000;
        if (!$value$plusargs("preq0=%d",  p_req0))     p_req0     = 60;
        if (!$value$plusargs("preq1=%d",  p_req1))     p_req1     = 60;
        if (!$value$plusargs("b2b=%d",    b2b))        b2b        = 1;
        if (!$value$plusargs("dmin=%d",   dmin))       dmin       = 0;
        if (!$value$plusargs("dmax=%d",   dmax))       dmax       = 4;
        if (!$value$plusargs("emin=%d",   emin))       emin       = 0;
        if (!$value$plusargs("emax=%d",   emax))       emax       = 2;
        if (!$value$plusargs("pridle=%d", p_ridle))    p_ridle    = 50;
        if (!$value$plusargs("ppridle=%d",p_pridle))   p_pridle   = 50;
        if (!$value$plusargs("perr=%d",   p_err))      p_err      = 25;
        if (!$value$plusargs("pwr=%d",    p_wr))       p_wr       = 50;
        if (!$value$plusargs("prst=%d",   p_rst))      p_rst      = 0;     // per mille per cycle
        if (!$value$plusargs("rstmax=%d", rstmax))     rstmax     = 3;
        if (!$value$plusargs("chklat=%d", chk_lat))    chk_lat    = 1;     // 8-cycle response bound
        if (!$value$plusargs("enfwait=%d",enf_wait))   enf_wait   = 0;     // 12-cycle accept bound is an error
        if (!$value$plusargs("waitlim=%d",wait_limit)) wait_limit = 12;
        if (!$value$plusargs("trace=%d",  trace))      trace      = 0;
    end

    // ------------------------------------------------------------ clock/reset
    reg clk;
    reg rst_n;
    initial begin clk = 1'b0; rst_n = 1'b0; end
    always #5 clk = ~clk;

    // ---------------------------------------------------------------- signals
    wire          c0_valid, c0_ready, c0_write;
    wire [AW-1:0] c0_addr;
    wire [DW-1:0] c0_wdata;
    wire          c1_valid, c1_ready, c1_write;
    wire [AW-1:0] c1_addr;
    wire [DW-1:0] c1_wdata;
    wire          r0_valid, r0_ready, r0_err;
    wire [DW-1:0] r0_rdata;
    wire          r1_valid, r1_ready, r1_err;
    wire [DW-1:0] r1_rdata;
    wire          psel, penable, pwrite;
    wire [AW-1:0] paddr;
    wire [DW-1:0] pwdata;
    reg           pready;
    reg  [DW-1:0] prdata;
    reg           pslverr;

    initial begin pready = 1'b0; prdata = {DW{1'b0}}; pslverr = 1'b0; end

    hub2 #(.AW(AW), .DW(DW)) dut (
        .clk(clk), .rst_n(rst_n),
        .c0_valid(c0_valid), .c0_ready(c0_ready), .c0_write(c0_write),
        .c0_addr(c0_addr),   .c0_wdata(c0_wdata),
        .c1_valid(c1_valid), .c1_ready(c1_ready), .c1_write(c1_write),
        .c1_addr(c1_addr),   .c1_wdata(c1_wdata),
        .r0_valid(r0_valid), .r0_ready(r0_ready), .r0_rdata(r0_rdata), .r0_err(r0_err),
        .r1_valid(r1_valid), .r1_ready(r1_ready), .r1_rdata(r1_rdata), .r1_err(r1_err),
        .psel(psel), .penable(penable), .pwrite(pwrite), .paddr(paddr), .pwdata(pwdata),
        .pready(pready), .prdata(prdata), .pslverr(pslverr)
    );

    tb_req #(.AW(AW), .DW(DW), .ID(0)) u_req0 (
        .clk(clk), .rst_n(rst_n), .p_req(p_req0), .b2b(b2b != 0),
        .emin(emin), .emax(emax), .p_ridle(p_ridle), .p_wr(p_wr), .seed_in(seed),
        .valid(c0_valid), .ready(c0_ready), .write(c0_write), .addr(c0_addr), .wdata(c0_wdata),
        .r_valid(r0_valid), .r_ready(r0_ready)
    );

    tb_req #(.AW(AW), .DW(DW), .ID(1)) u_req1 (
        .clk(clk), .rst_n(rst_n), .p_req(p_req1), .b2b(b2b != 0),
        .emin(emin), .emax(emax), .p_ridle(p_ridle), .p_wr(p_wr), .seed_in(seed),
        .valid(c1_valid), .ready(c1_ready), .write(c1_write), .addr(c1_addr), .wdata(c1_wdata),
        .r_valid(r1_valid), .r_ready(r1_ready)
    );

    // ------------------------------------------------------------- random util
    integer sd_s;
    initial sd_s = 12345;
    function integer urand_s;      // 0 .. n-1
        input integer n;
        integer t;
        begin
            t = $random(sd_s);
            t = t & 32'h7fffffff;
            urand_s = t % n;
        end
    endfunction

    // ---------------------------------------------------------- reset controller
    integer init_rst;     // cycles of initial reset
    integer rst_left;     // cycles left of a mid-run reset pulse
    initial begin init_rst = 3; rst_left = 0; end
    always @(negedge clk) begin
        if (init_rst > 0) begin
            rst_n    = 1'b0;
            init_rst = init_rst - 1;
        end else if (rst_left > 0) begin
            rst_n    = 1'b0;
            rst_left = rst_left - 1;
        end else begin
            rst_n = 1'b1;
            if (p_rst > 0 && urand_s(1000) < p_rst) rst_left = 1 + urand_s(rstmax);
        end
    end

    // ------------------------------------------------------------- APB slave
    integer sl_cnt, sl_delay;
    initial begin sl_cnt = 0; sl_delay = 0; end
    always @(posedge clk) begin
        if (!rst_n) begin
            pready <= (urand_s(100) < p_pridle);
            sl_cnt  = 0;
            sl_delay = 0;
        end else if (psel === 1'b1 && penable === 1'b0) begin      // setup cycle
            sl_delay = dmin + urand_s(dmax - dmin + 1);
            sl_cnt   = 0;
            pready  <= (sl_delay == 0);                              // first access cycle
        end else if (psel === 1'b1 && penable === 1'b1) begin      // access cycle
            if (pready) begin
                pready <= (urand_s(100) < p_pridle);                 // transfer completes now
            end else begin
                sl_cnt = sl_cnt + 1;
                pready <= (sl_cnt >= sl_delay);
            end
        end else begin
            pready <= (urand_s(100) < p_pridle);                     // garbage while not selected
        end
        prdata  <= $random(sd_s);
        pslverr <= (urand_s(100) < p_err);
    end

    // ---------------------------------------------------------------- scoreboard
    localparam S_IDLE = 0, S_SETUP = 1, S_ACCESS = 2, S_RESP = 3;

    integer cyc;
    integer errors;
    integer mst, nmst;
    reg     prev_rst;
    reg           cur_port, cur_write;
    reg [AW-1:0]  cur_addr;
    reg [DW-1:0]  cur_wdata;
    reg [DW-1:0]  exp_rdata;
    reg           exp_err;
    integer last_acc;                     // -1 unknown (after reset), 0 or 1
    integer acc_cyc;
    integer resp_age;
    integer wt0, wt1;                     // cycles a pending command has waited so far
    integer maxw0, maxw1, maxw, wait_viol;
    integer maxresp;                      // max (accept -> response presented) in cycles
    integer idle_stall;
    integer n_acc0, n_acc1, n_rsp0, n_rsp1, n_rd, n_wr, n_errresp, n_both, n_resets;
    integer cov_setup_pready, cov_e0, cov_hold, cov_acc_with_rsp, cov_ready_junk, cov_nonowner_ready;
    integer done;
    reg     acc0, acc1, acc, own_ready;

    initial begin
        cyc = 0; errors = 0; mst = S_IDLE; prev_rst = 1'b0; last_acc = -1; acc_cyc = 0;
        resp_age = 0; wt0 = 0; wt1 = 0; maxw0 = 0; maxw1 = 0; maxw = 0; wait_viol = 0; maxresp = 0;
        idle_stall = 0; n_acc0 = 0; n_acc1 = 0; n_rsp0 = 0; n_rsp1 = 0; n_rd = 0; n_wr = 0;
        n_errresp = 0; n_both = 0; n_resets = 0; cov_setup_pready = 0; cov_e0 = 0; cov_hold = 0;
        cov_acc_with_rsp = 0; cov_ready_junk = 0; cov_nonowner_ready = 0; done = 0;
        cur_port = 1'b0; cur_write = 1'b0; cur_addr = {AW{1'b0}}; cur_wdata = {DW{1'b0}};
        exp_rdata = {DW{1'b0}}; exp_err = 1'b0;
    end

    task chk;
        input cond;
        input [8*72-1:0] msg;
        begin
            if (cond !== 1'b1) begin
                errors = errors + 1;
                if (errors <= 20) $display("[%0t] cyc %0d CHECK FAILED: %0s", $time, cyc, msg);
            end
        end
    endtask

    always @(posedge clk) begin
        cyc = cyc + 1;

        if (trace != 0)
            $display("cyc %0d rst_n=%b | c0 v%b r%b w%b a%h d%h | c1 v%b r%b w%b a%h d%h | psel%b pen%b pw%b pa%h pd%h prdy%b prd%h perr%b | r0 v%b r%b d%h e%b | r1 v%b r%b d%h e%b | mst=%0d",
                     cyc, rst_n, c0_valid, c0_ready, c0_write, c0_addr, c0_wdata,
                     c1_valid, c1_ready, c1_write, c1_addr, c1_wdata,
                     psel, penable, pwrite, paddr, pwdata, pready, prdata, pslverr,
                     r0_valid, r0_ready, r0_rdata, r0_err, r1_valid, r1_ready, r1_rdata, r1_err, mst);

        // ---- spec section 6: the cycle after reset ---------------------------------
        if (prev_rst) begin
            chk(psel === 1'b0,     "reset: psel low in cycle after reset");
            chk(penable === 1'b0,  "reset: penable low in cycle after reset");
            chk(r0_valid === 1'b0, "reset: r0_valid low in cycle after reset");
            chk(r1_valid === 1'b0, "reset: r1_valid low in cycle after reset");
            if (c0_valid === 1'b0 && c1_valid === 1'b0)
                chk(c0_ready === 1'b1 && c1_ready === 1'b1, "design: both readies high after reset");
        end

        if (!rst_n) begin
            // The DUT is reset at this edge: flush the scoreboard, ignore this cycle.
            if (!prev_rst) n_resets = n_resets + 1;
            prev_rst = 1'b1;
            mst      = S_IDLE;
            last_acc = -1;
            wt0 = 0; wt1 = 0;
            idle_stall = 0;
        end else begin
            prev_rst = 1'b0;

            acc0 = (c0_valid === 1'b1) && (c0_ready === 1'b1);
            acc1 = (c1_valid === 1'b1) && (c1_ready === 1'b1);
            acc  = acc0 || acc1;

            // ---- generic sanity ------------------------------------------------------
            chk((^{c0_ready, c1_ready, r0_valid, r1_valid, psel, penable}) !== 1'bx, "X/Z on a control output");
            chk(!(acc0 && acc1),                "spec: two commands accepted in one cycle");
            chk(!(penable && !psel),            "spec: penable asserted without psel");
            chk(!(r0_valid && r1_valid),        "spec: response valid on both ports");

            // ---- time a pending command waits before it is accepted ---------------------
            if (acc0) begin
                if (wt0 > maxw0) maxw0 = wt0;
                if (wt0 > maxw)  maxw  = wt0;
                if (wt0 > wait_limit) begin
                    wait_viol = wait_viol + 1;
                    if (enf_wait != 0) chk(1'b0, "spec: port 0 command waited longer than 12 cycles");
                end
                wt0 = 0;
            end else if (c0_valid === 1'b1) wt0 = wt0 + 1;
            else wt0 = 0;
            if (acc1) begin
                if (wt1 > maxw1) maxw1 = wt1;
                if (wt1 > maxw)  maxw  = wt1;
                if (wt1 > wait_limit) begin
                    wait_viol = wait_viol + 1;
                    if (enf_wait != 0) chk(1'b0, "spec: port 1 command waited longer than 12 cycles");
                end
                wt1 = 0;
            end else if (c1_valid === 1'b1) wt1 = wt1 + 1;
            else wt1 = 0;

            // ---- ignored-input coverage ---------------------------------------------------
            if (mst != S_RESP && (r0_ready === 1'b1 || r1_ready === 1'b1)) cov_ready_junk = cov_ready_junk + 1;

            // ---- transaction state machine ------------------------------------------------
            nmst = mst;
            own_ready = 1'b0;
            case (mst)
                S_IDLE: begin
                    chk(psel === 1'b0 && penable === 1'b0,       "idle: APB bus not quiet");
                    chk(r0_valid === 1'b0 && r1_valid === 1'b0,  "idle: unexpected response valid");
                    if (acc) nmst = S_SETUP;
                    else chk(!(c0_valid === 1'b1 || c1_valid === 1'b1),
                             "design: pending command not accepted by idle bridge");
                end

                S_SETUP: begin
                    chk(psel === 1'b1 && penable === 1'b0,       "spec: setup phase must be psel=1 penable=0");
                    chk(pwrite === cur_write && paddr === cur_addr && pwdata === cur_wdata,
                        "spec: APB fields differ from accepted command (setup)");
                    chk(r0_valid === 1'b0 && r1_valid === 1'b0,  "setup: unexpected response valid");
                    chk(!acc,                                    "spec: command accepted during transfer (setup)");
                    if (pready === 1'b1) cov_setup_pready = cov_setup_pready + 1;
                    nmst = S_ACCESS;
                end

                S_ACCESS: begin
                    chk(psel === 1'b1 && penable === 1'b1,       "spec: access phase must be psel=1 penable=1");
                    chk(pwrite === cur_write && paddr === cur_addr && pwdata === cur_wdata,
                        "spec: APB fields unstable / wrong during access");
                    chk(r0_valid === 1'b0 && r1_valid === 1'b0,  "access: unexpected response valid");
                    chk(!acc,                                    "spec: command accepted during transfer (access)");
                    if (pready === 1'b1) begin
                        exp_rdata = prdata;
                        exp_err   = pslverr;
                        resp_age  = 0;
                        nmst      = S_RESP;
                    end
                end

                S_RESP: begin
                    chk(psel === 1'b0 && penable === 1'b0,
                        "spec: psel/penable must be low after transfer completes");
                    if (cur_port == 1'b0) begin
                        chk(r0_valid === 1'b1 && r1_valid === 1'b0, "spec: response not presented on issuing port 0");
                        chk(r0_err === exp_err,                     "spec: r0_err != sampled pslverr");
                        if (!cur_write) chk(r0_rdata === exp_rdata, "spec: r0_rdata != sampled prdata");
                        chk(r1_rdata === {DW{1'b0}} && r1_err === 1'b0, "design: other port data/err not zero");
                        own_ready = (r0_ready === 1'b1);
                        if (r1_ready === 1'b1) cov_nonowner_ready = cov_nonowner_ready + 1;
                    end else begin
                        chk(r1_valid === 1'b1 && r0_valid === 1'b0, "spec: response not presented on issuing port 1");
                        chk(r1_err === exp_err,                     "spec: r1_err != sampled pslverr");
                        if (!cur_write) chk(r1_rdata === exp_rdata, "spec: r1_rdata != sampled prdata");
                        chk(r0_rdata === {DW{1'b0}} && r0_err === 1'b0, "design: other port data/err not zero");
                        own_ready = (r1_ready === 1'b1);
                        if (r0_ready === 1'b1) cov_nonowner_ready = cov_nonowner_ready + 1;
                    end
                    if (resp_age == 0) begin
                        // first cycle of the response: latency bound of BRG-1 section 5
                        if ((cyc - acc_cyc) > maxresp) maxresp = cyc - acc_cyc;
                        if (chk_lat != 0) chk((cyc - acc_cyc) <= 8, "spec: response later than 8 cycles after accept");
                        if (own_ready) cov_e0 = cov_e0 + 1;
                    end
                    if (own_ready) begin
                        if (cur_port == 1'b0) n_rsp0 = n_rsp0 + 1; else n_rsp1 = n_rsp1 + 1;
                        if (exp_err) n_errresp = n_errresp + 1;
                        if (acc) begin
                            nmst = S_SETUP;
                            cov_acc_with_rsp = cov_acc_with_rsp + 1;
                        end else begin
                            nmst = S_IDLE;
                            chk(!(c0_valid === 1'b1 || c1_valid === 1'b1),
                                "design: pending command not taken in response-accept cycle");
                        end
                    end else begin
                        chk(!acc, "spec: command accepted while response pending");
                        cov_hold = cov_hold + 1;
                        resp_age = resp_age + 1;
                    end
                end

                default: chk(1'b0, "tb: bad state");
            endcase

            // ---- command acceptance: arbitration + capture ----------------------------------
            if (acc) begin
                if (c0_valid === 1'b1 && c1_valid === 1'b1) begin
                    n_both = n_both + 1;
                    if (last_acc >= 0)
                        chk((acc1 ? 1 : 0) != last_acc, "spec: port accepted most recently was served first again");
                    else
                        chk(acc0, "design: port 0 should win the first tie after reset");
                end
                last_acc  = acc1 ? 1 : 0;
                cur_port  = acc1;
                cur_write = acc1 ? c1_write : c0_write;
                cur_addr  = acc1 ? c1_addr  : c0_addr;
                cur_wdata = acc1 ? c1_wdata : c0_wdata;
                acc_cyc   = cyc;
                if (acc1) n_acc1 = n_acc1 + 1; else n_acc0 = n_acc0 + 1;
                if (cur_write) n_wr = n_wr + 1; else n_rd = n_rd + 1;
            end

            // ---- deadlock watchdog: a state that neither changes nor is legitimately idle ------
            if (nmst != mst || acc || (mst == S_IDLE && !(c0_valid === 1'b1 || c1_valid === 1'b1)))
                idle_stall = 0;
            else
                idle_stall = idle_stall + 1;
            if (idle_stall > 400) begin
                chk(1'b0, "tb: no progress for 400 cycles (deadlock?)");
                idle_stall = 0;
            end
            mst = nmst;
        end

        // ---- end of run -----------------------------------------------------------------------
        if (cyc >= ncyc && !done) begin
            done = 1;
            $display("SUMMARY seed=%0d cycles=%0d acc0=%0d acc1=%0d rsp0=%0d rsp1=%0d rd=%0d wr=%0d errresp=%0d resets=%0d",
                     seed, cyc, n_acc0, n_acc1, n_rsp0, n_rsp1, n_rd, n_wr, n_errresp, n_resets);
            $display("TIMING  maxwait0=%0d maxwait1=%0d maxwait=%0d (limit %0d, exceeded %0d times) max_accept_to_resp=%0d",
                     maxw0, maxw1, maxw, wait_limit, wait_viol, maxresp);
            $display("COVER   both_pending=%0d setup_pready=%0d resp_e0=%0d resp_hold_cycles=%0d acc_with_rspacc=%0d rdy_junk=%0d nonowner_rdy=%0d",
                     n_both, cov_setup_pready, cov_e0, cov_hold, cov_acc_with_rsp, cov_ready_junk, cov_nonowner_ready);
            if (errors == 0) $display("RESULT: PASS");
            else             $display("RESULT: FAIL (%0d errors)", errors);
            $finish;
        end
    end
endmodule
