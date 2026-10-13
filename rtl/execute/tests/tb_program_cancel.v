// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_program_cancel;
 localparam integer PROGRAMS=8,ITERATIONS=2048;
 reg  clk=0;
 reg  rst=0;
 reg  start_valid=0;
 wire  start_ready;
 reg [15:0] start_tag=0;
 reg  start_v2=0;
 wire  meta_req_valid;
 reg  meta_req_ready=0;
 wire [15:0] meta_req_tag;
 wire [2:0] meta_req_program;
 reg  meta_rsp_valid=0;
 wire  meta_rsp_ready;
 reg [15:0] meta_rsp_tag=0;
 reg [2:0] meta_rsp_program=0;
 reg [1023:0] meta_rsp_entropy=0;
 reg [63:0] meta_rsp_program_addr=0;
 wire  program_done_valid;
 reg  program_done_ready=0;
 wire [15:0] program_done_tag;
 wire [2:0] program_done_index;
 wire [11:0] program_done_iterations;
 wire [511:0] program_done_r;
 wire [511:0] program_done_f;
 wire [511:0] program_done_e;
 wire [511:0] program_done_a;
 wire [1:0] program_done_round_mode;
 wire  done_valid;
 reg  done_ready=0;
 wire [15:0] done_tag;
 wire [511:0] done_r;
 wire [511:0] done_f;
 wire [511:0] done_e;
 wire [511:0] done_a;
 wire [1:0] done_round_mode;
 wire [31:0] done_mx;
 wire [31:0] done_ma;
 wire [31:0] done_spaddr0;
 wire [31:0] done_spaddr1;
 wire  error_valid;
 reg  error_ready=0;
 wire [15:0] error_tag;
 wire [2:0] error_program;
 wire [1:0] error_code;
 wire [8:0] error_pc;
 wire [7:0] error_opcode;
 wire  iteration_commit_valid;
 wire [15:0] iteration_commit_tag;
 wire [15:0] iteration_commit_backend_tag;
 wire [2:0] iteration_commit_program;
 wire [10:0] iteration_commit_index;
 wire [511:0] iteration_commit_r;
 wire [511:0] iteration_commit_f;
 wire [511:0] iteration_commit_e;
 wire [511:0] iteration_commit_a;
 wire [1:0] iteration_commit_round_mode;
 wire [31:0] iteration_commit_mx;
 wire [31:0] iteration_commit_ma;
 wire [31:0] iteration_commit_spaddr0;
 wire [31:0] iteration_commit_spaddr1;
 wire  sp_rd_valid;
 reg  sp_rd_ready=0;
 wire [20:0] sp_rd_addr;
 wire [15:0] sp_rd_tag;
 reg  sp_rsp_valid=0;
 wire  sp_rsp_ready;
 reg [127:0] sp_rsp_data=0;
 reg [15:0] sp_rsp_tag=0;
 wire  sp_wr_valid;
 reg  sp_wr_ready=0;
 wire [20:0] sp_wr_addr;
 wire [127:0] sp_wr_data;
 wire [15:0] sp_wr_strb;
 wire [15:0] sp_wr_tag;
 wire  ds_req_valid;
 reg  ds_req_ready=0;
 wire [63:0] ds_req_addr;
 wire [63:0] ds_prefetch_addr;
 wire [15:0] ds_req_tag;
 wire  ds_prefetch_valid;
 reg  ds_rsp_valid=0;
 wire  ds_rsp_ready;
 reg [15:0] ds_rsp_tag=0;
 reg [511:0] ds_rsp_data=0;
 wire  prog_valid;
 reg  prog_ready=0;
 wire [63:0] prog_addr;
 wire [15:0] prog_tag;
 reg  prog_rsp_valid=0;
 wire  prog_rsp_ready;
 reg [15:0] prog_rsp_tag=0;
 reg [63:0] prog_rsp_instruction=0;
 wire  commit_valid;
 wire [15:0] commit_tag;
 wire [8:0] commit_pc;
 wire [7:0] commit_opcode;
 wire [511:0] commit_r;
 wire [8:0] commit_next_pc;
 wire [8:0] commit_branch_target;
 wire [511:0] commit_f;
 wire [511:0] commit_e;
 wire [1:0] commit_round_mode;
 always #5 clk=~clk;
`ifdef PROGRAM_SEQUENCE_NETLIST
 randomx_program_sequence dut(
`else
 randomx_program_sequence #(.PROGRAMS(PROGRAMS),.ITERATIONS(ITERATIONS)) dut(
`endif
  .clk(clk),
  .rst(rst),
  .start_valid(start_valid),
  .start_ready(start_ready),
  .start_tag(start_tag),
  .start_v2(start_v2),
  .meta_req_valid(meta_req_valid),
  .meta_req_ready(meta_req_ready),
  .meta_req_tag(meta_req_tag),
  .meta_req_program(meta_req_program),
  .meta_rsp_valid(meta_rsp_valid),
  .meta_rsp_ready(meta_rsp_ready),
  .meta_rsp_tag(meta_rsp_tag),
  .meta_rsp_program(meta_rsp_program),
  .meta_rsp_entropy(meta_rsp_entropy),
  .meta_rsp_program_addr(meta_rsp_program_addr),
  .program_done_valid(program_done_valid),
  .program_done_ready(program_done_ready),
  .program_done_tag(program_done_tag),
  .program_done_index(program_done_index),
  .program_done_iterations(program_done_iterations),
  .program_done_r(program_done_r),
  .program_done_f(program_done_f),
  .program_done_e(program_done_e),
  .program_done_a(program_done_a),
  .program_done_round_mode(program_done_round_mode),
  .done_valid(done_valid),
  .done_ready(done_ready),
  .done_tag(done_tag),
  .done_r(done_r),
  .done_f(done_f),
  .done_e(done_e),
  .done_a(done_a),
  .done_round_mode(done_round_mode),
  .done_mx(done_mx),
  .done_ma(done_ma),
  .done_spaddr0(done_spaddr0),
  .done_spaddr1(done_spaddr1),
  .error_valid(error_valid),
  .error_ready(error_ready),
  .error_tag(error_tag),
  .error_program(error_program),
  .error_code(error_code),
  .error_pc(error_pc),
  .error_opcode(error_opcode),
  .iteration_commit_valid(iteration_commit_valid),
  .iteration_commit_tag(iteration_commit_tag),
  .iteration_commit_backend_tag(iteration_commit_backend_tag),
  .iteration_commit_program(iteration_commit_program),
  .iteration_commit_index(iteration_commit_index),
  .iteration_commit_r(iteration_commit_r),
  .iteration_commit_f(iteration_commit_f),
  .iteration_commit_e(iteration_commit_e),
  .iteration_commit_a(iteration_commit_a),
  .iteration_commit_round_mode(iteration_commit_round_mode),
  .iteration_commit_mx(iteration_commit_mx),
  .iteration_commit_ma(iteration_commit_ma),
  .iteration_commit_spaddr0(iteration_commit_spaddr0),
  .iteration_commit_spaddr1(iteration_commit_spaddr1),
  .sp_rd_valid(sp_rd_valid),
  .sp_rd_ready(sp_rd_ready),
  .sp_rd_addr(sp_rd_addr),
  .sp_rd_tag(sp_rd_tag),
  .sp_rsp_valid(sp_rsp_valid),
  .sp_rsp_ready(sp_rsp_ready),
  .sp_rsp_data(sp_rsp_data),
  .sp_rsp_tag(sp_rsp_tag),
  .sp_wr_valid(sp_wr_valid),
  .sp_wr_ready(sp_wr_ready),
  .sp_wr_addr(sp_wr_addr),
  .sp_wr_data(sp_wr_data),
  .sp_wr_strb(sp_wr_strb),
  .sp_wr_tag(sp_wr_tag),
  .ds_req_valid(ds_req_valid),
  .ds_req_ready(ds_req_ready),
  .ds_req_addr(ds_req_addr),
  .ds_prefetch_addr(ds_prefetch_addr),
  .ds_req_tag(ds_req_tag),
  .ds_prefetch_valid(ds_prefetch_valid),
  .ds_rsp_valid(ds_rsp_valid),
  .ds_rsp_ready(ds_rsp_ready),
  .ds_rsp_tag(ds_rsp_tag),
  .ds_rsp_data(ds_rsp_data),
  .prog_valid(prog_valid),
  .prog_ready(prog_ready),
  .prog_addr(prog_addr),
  .prog_tag(prog_tag),
  .prog_rsp_valid(prog_rsp_valid),
  .prog_rsp_ready(prog_rsp_ready),
  .prog_rsp_tag(prog_rsp_tag),
  .prog_rsp_instruction(prog_rsp_instruction),
  .commit_valid(commit_valid),
  .commit_tag(commit_tag),
  .commit_pc(commit_pc),
  .commit_opcode(commit_opcode),
  .commit_r(commit_r),
  .commit_next_pc(commit_next_pc),
  .commit_branch_target(commit_branch_target),
  .commit_f(commit_f),
  .commit_e(commit_e),
  .commit_round_mode(commit_round_mode)
 );
    reg [127:0] memory0;
    reg [7:0] unsupported[0:255];
    reg [4095:0] path;
    integer opcode,cases,cycles,commits,writes,pending,ppending,delay,prog_delay,steps;
    integer prefix_store,request_stalls,request_accepted,reply_injected;
    reg [7:0] bad_opcode;
    reg [15:0] tag,stag,ptag;
    reg [127:0] sdata;
    reg [63:0] instruction;
    reg [8:0] expected_error_pc;
    reg [127:0] before_memory;
    wire [63:0] store_instruction={32'b0,8'hf0,8'd1,8'd0,8'd240};
    task launch;
        input [15:0] generation;
        input [7:0] bad;
        input prefix;
        begin
            @(negedge clk);start_valid=1;start_tag=generation;start_v2=generation[0];
            tag=generation;bad_opcode=bad;prefix_store=prefix;
            sp_rd_ready=0;sp_wr_ready=0;prog_ready=0;sp_rsp_valid=0;prog_rsp_valid=0;ds_rsp_valid=0;
            error_ready=0;done_ready=0;program_done_ready=0;meta_req_ready=0;meta_rsp_valid=0;
            pending=0;ppending=0;delay=0;prog_delay=0;
            commits=0;writes=0;steps=0;request_stalls=0;request_accepted=0;reply_injected=0;
            #1;if(!start_ready)$fatal(1,"new cancellation context not ready");
            @(posedge clk);#1;@(negedge clk);start_valid=0;
            repeat(3)begin
                if(!meta_req_valid||meta_req_tag!==tag||meta_req_program!==0)$fatal(1,"held metadata request");
                @(posedge clk);#1;@(negedge clk);
            end
            meta_req_ready=1;@(posedge clk);#1;@(negedge clk);meta_req_ready=0;
            meta_rsp_valid=1;meta_rsp_tag=tag-1;meta_rsp_program=0;meta_rsp_entropy=~1024'b0;
            meta_rsp_program_addr=64'h10000003;
            @(posedge clk);#1;if(error_valid||sp_rd_valid)$fatal(1,"stale metadata side effect");@(negedge clk);
            meta_rsp_tag=tag;meta_rsp_entropy=0;meta_rsp_entropy[8*64+:64]=64;meta_rsp_program_addr=64'h10000000;
            @(posedge clk);#1;@(negedge clk);meta_rsp_valid=0;meta_rsp_entropy=~meta_rsp_entropy;
        end
    endtask
    task reset_fetch;
        integer n;
        begin
            launch(16'he000,8'd46,0);
            // Complete entry SRAM loads, then stall the first actual program request.
            while(!prog_valid)begin
                sp_rd_ready=!pending;
                sp_rsp_valid=pending;sp_rsp_tag=stag;sp_rsp_data=sdata;
                @(posedge clk);
                if(sp_rsp_valid && sp_rsp_ready)pending=0;
                if(sp_rd_valid && sp_rd_ready)begin sdata=sp_rd_addr==0?memory0:sp_rd_addr>=64&&sp_rd_addr<128?{4{32'h7fffffff}}:128'b0;stag=tag;pending=1;end
                #1;steps=steps+1;if(steps>40)$fatal(1,"reset fetch entry");@(negedge clk);
            end
            sp_rsp_valid=0;
            for(n=0;n<3;n=n+1)begin @(posedge clk);if(!prog_valid || prog_tag!==16'he000 || prog_addr!==64'h10000000)$fatal(1,"held fetch changed");#1;@(negedge clk);end
            rst=1;#1;if(prog_valid || meta_req_valid || sp_rd_valid || sp_wr_valid || commit_valid || iteration_commit_valid || program_done_valid || error_valid || done_valid)$fatal(1,"explicit reset suppression");
            @(posedge clk);#1;@(negedge clk);rst=0;
            prog_rsp_valid=1;prog_rsp_tag=16'he000;prog_rsp_instruction=0;
            for(n=0;n<2;n=n+1)begin @(posedge clk);#1;if(!prog_rsp_ready || commit_valid || error_valid || done_valid)$fatal(1,"late reset fetch reply leaked");end
            @(negedge clk);prog_rsp_valid=0;
        end
    endtask
    task reset_execution;
        input store;
        reg reached;
        reg [255:0] saved_store;
        integer n;
        begin
            launch(store?16'he101:16'he100,store?8'd240:8'd204,0);
            reached=0;before_memory=memory0;
            while(!reached)begin
                sp_rd_ready=!pending;sp_wr_ready=0;prog_ready=!ppending;
                sp_rsp_valid=pending;sp_rsp_tag=stag;sp_rsp_data=sdata;
                prog_rsp_valid=ppending;prog_rsp_tag=ptag;prog_rsp_instruction=instruction;
                @(posedge clk);
                if(commit_valid || error_valid || done_valid || ds_req_valid)$fatal(1,"reset before first memory operation leaked retirement");
                if(sp_rsp_valid && sp_rsp_ready)pending=0;
                if(sp_rd_valid && sp_rd_ready)begin
                    sdata=sp_rd_addr==0?memory0:sp_rd_addr>=64&&sp_rd_addr<128?{4{32'h7fffffff}}:128'b0;stag=tag;pending=1;
                    if(request_accepted!=0)begin
                        if(store)$fatal(1,"store reset unexpectedly loaded");
                        reached=1;
                    end
                end
                if(prog_rsp_valid && prog_rsp_ready)ppending=0;
                if(prog_valid && prog_ready)begin
                    if(request_accepted!=0 || prog_tag!==tag || prog_addr!==64'h10000000)$fatal(1,"reset execution fetch");
                    instruction=store?store_instruction:{56'b0,bad_opcode};ptag=tag;ppending=1;request_accepted=1;
                end
                if(store && sp_wr_valid)begin reached=1;saved_store={sp_wr_tag,sp_wr_addr,sp_wr_data,sp_wr_strb};end
                #1;steps=steps+1;if(steps>40)$fatal(1,"reset execution setup timeout");@(negedge clk);
            end
            sp_rsp_valid=0;prog_rsp_valid=0;
            for(n=0;n<3;n=n+1)begin
                @(posedge clk);
                if(commit_valid || error_valid || done_valid || ds_req_valid)$fatal(1,"stalled memory operation leaked retirement");
                if(store && (!sp_wr_valid || {sp_wr_tag,sp_wr_addr,sp_wr_data,sp_wr_strb}!==saved_store))$fatal(1,"held uncommitted store changed");
                #1;@(negedge clk);
            end
            rst=1;#1;
            if(prog_valid || meta_req_valid || sp_rd_valid || sp_wr_valid || commit_valid || iteration_commit_valid || program_done_valid || error_valid || done_valid)$fatal(1,"execution reset suppression");
            @(posedge clk);#1;@(negedge clk);rst=0;
            // A response accepted before reset may still arrive from the adapter.
            sp_rsp_valid=1;sp_rsp_tag=tag;sp_rsp_data={128{1'b1}};
            for(n=0;n<2;n=n+1)begin
                @(posedge clk);
                if(!sp_rsp_ready || commit_valid || error_valid || done_valid || sp_wr_valid)$fatal(1,"late reset memory reply leaked");
                #1;
            end
            @(negedge clk);sp_rsp_valid=0;
            if(memory0!==before_memory || !start_ready)$fatal(1,"uncommitted reset memory/restart");
        end
    endtask
    task reset_divsqrt;
        input sqrt_operation;
        input prefix;
        reg accepted_math;
        integer n,wait_cycles;
        begin
            launch(sqrt_operation?16'he300:16'he301,sqrt_operation?8'd208:8'd204,prefix);
            accepted_math=0;before_memory=memory0;wait_cycles=0;
            while(!accepted_math)begin
                sp_rd_ready=!pending;sp_wr_ready=1;prog_ready=!ppending;
                sp_rsp_valid=pending;sp_rsp_tag=stag;sp_rsp_data=sdata;
                prog_rsp_valid=ppending;prog_rsp_tag=ptag;prog_rsp_instruction=instruction;
                @(posedge clk);
                if(error_valid || done_valid || ds_req_valid)$fatal(1,"division reset setup escaped execution");
                if(sp_rsp_valid && sp_rsp_ready)pending=0;
                if(sp_rd_valid && sp_rd_ready)begin sdata=sp_rd_addr==0?memory0:sp_rd_addr>=64&&sp_rd_addr<128?{4{32'h7fffffff}}:128'b0;stag=tag;pending=1;end
                if(prog_rsp_valid && prog_rsp_ready)ppending=0;
                if(commit_valid)begin
                    if(!prefix || commits!=0 || commit_opcode!==240)$fatal(1,"division committed before cancellation");
                    commits=commits+1;
                end
                if(prog_valid && prog_ready)begin
                    if(prog_tag!==tag || prog_addr!==64'h10000000+commits*8)$fatal(1,"division reset fetch");
                    instruction=prefix && commits==0?store_instruction:{32'b0,8'b0,8'd1,8'd0,bad_opcode};
                    ptag=tag;ppending=1;request_accepted=request_accepted+1;
                end
                if(sp_wr_valid && sp_wr_ready)begin
                    if(!prefix || writes!=0 || sp_wr_tag!==tag || sp_wr_addr!==0 || sp_wr_strb!==16'h00ff)$fatal(1,"division prefix store prefix=%0d writes=%0d tag=%h addr=%h strb=%h",prefix,writes,sp_wr_tag,sp_wr_addr,sp_wr_strb);
                    memory0[63:0]=sp_wr_data[63:0];writes=writes+1;
                end
                #1;
`ifndef PROGRAM_SEQUENCE_NETLIST
                accepted_math=dut.iteration.execute.state_q==17;
`else
                // Opaque mapped integration: start counting only after arithmetic program response.
                if(request_accepted==(prefix?2:1) && !ppending && !pending && !sp_rd_valid)wait_cycles=wait_cycles+1;
                accepted_math=wait_cycles==8;
`endif
                steps=steps+1;if(steps>100)$fatal(1,"division reset setup timeout");@(negedge clk);
            end
            sp_rsp_valid=0;prog_rsp_valid=0;prog_ready=0;
            repeat(4)begin @(posedge clk);#1;if(commit_valid || error_valid || done_valid)$fatal(1,"division early retirement");@(negedge clk);end
            rst=1;#1;if(commit_valid || error_valid || done_valid || prog_valid || sp_wr_valid)$fatal(1,"division reset suppression");
            @(posedge clk);#1;@(negedge clk);rst=0;
            for(n=0;n<130;n=n+1)begin
                @(posedge clk);#1;
                if(commit_valid || error_valid || done_valid || prog_valid || sp_wr_valid || !start_ready)$fatal(1,"cancelled division leaked generation");
            end
            @(negedge clk);
            if(prefix)begin if(commits!=1 || writes!=1 || memory0[63:0]!==64'h1122334455667788)$fatal(1,"committed prefix not preserved");end
            else if(memory0!==before_memory)$fatal(1,"cancelled division changed memory");
        end
    endtask
    initial begin #500000;$fatal(1,"divsqrt cancellation deadlock");end
    initial begin
        memory0={64'h1122334455667788,64'b0};cases=0;rst=1;@(posedge clk);#1;@(negedge clk);rst=0;
        @(negedge clk);start_valid=1;start_tag=16'hd000;start_v2=1;
        @(posedge clk);#1;@(negedge clk);start_valid=0;
        repeat(3)begin @(posedge clk);#1;if(!meta_req_valid)$fatal(1,"metadata cancellation setup");@(negedge clk);end
        rst=1;@(posedge clk);#1;@(negedge clk);rst=0;
        meta_rsp_valid=1;meta_rsp_tag=16'hd000;meta_rsp_program=0;meta_rsp_program_addr=3;
        repeat(2)begin @(posedge clk);#1;if(!start_ready||error_valid||sp_rd_valid||iteration_commit_valid)$fatal(1,"late metadata after reset");@(negedge clk);end
        meta_rsp_valid=0;
        start_valid=1;start_tag=16'hd100;start_v2=0;
        @(posedge clk);#1;@(negedge clk);start_valid=0;meta_req_ready=1;
        @(posedge clk);#1;@(negedge clk);meta_req_ready=0;meta_rsp_valid=1;meta_rsp_tag=16'hd100;meta_rsp_program_addr=3;
        @(posedge clk);#1;@(negedge clk);meta_rsp_valid=0;
        repeat(4)begin
            if(!error_valid||error_tag!==16'hd100||error_code!==1||sp_rd_valid||sp_wr_valid||prog_valid||iteration_commit_valid)$fatal(1,"malformed metadata held error");
            @(posedge clk);#1;@(negedge clk);
        end
        error_ready=1;@(posedge clk);#1;@(negedge clk);error_ready=0;
        if(!start_ready)$fatal(1,"malformed metadata restart");
        reset_execution(0);reset_execution(1);reset_fetch();
        reset_divsqrt(0,0);reset_divsqrt(1,0);reset_divsqrt(0,1);
        $display("PASS program_cancel metadata_stale=1 reset_metadata_request=1 late_metadata_drop=1 malformed_metadata_held_error=1 reset_pending_load=1 reset_held_store=1 reset_held_fetch=1 reset_running_division=2 reset_running_sqrt=1 late_fetch_drop=1 late_memory_drop=1 committed_prefix_preserved=1");
        $finish;
    end
endmodule
