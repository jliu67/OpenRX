// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_floating_errors #(parameter integer FP_LANES=2);
    reg  clk=0;
    reg  rst=0;
    reg  req_valid=0;
    wire  req_ready;
    reg [15:0] req_tag=0;
    reg  req_v2=0;
    reg [1:0] req_round_mode=0;
    reg [511:0] req_r=0;
    reg [511:0] req_a=0;
    reg [31:0] req_spaddr0=0;
    reg [31:0] req_spaddr1=0;
    reg [31:0] req_mx=0;
    reg [31:0] req_ma=0;
    reg [2:0] req_read0=0;
    reg [2:0] req_read1=0;
    reg [2:0] req_read2=0;
    reg [2:0] req_read3=0;
    reg [63:0] req_emask0=0;
    reg [63:0] req_emask1=0;
    reg [63:0] req_dataset_offset=0;
    reg [63:0] req_program_addr=0;
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
    wire  done_valid;
    reg  done_ready=0;
    wire [15:0] done_tag;
    wire [1:0] done_round_mode;
    wire [511:0] done_r;
    wire [511:0] done_f;
    wire [511:0] done_e;
    wire [31:0] done_mx;
    wire [31:0] done_ma;
    wire [31:0] done_spaddr0;
    wire [31:0] done_spaddr1;
    wire  prog_valid;
    reg  prog_ready=0;
    wire [63:0] prog_addr;
    wire [15:0] prog_tag;
    reg  prog_rsp_valid=0;
    wire  prog_rsp_ready;
    reg [15:0] prog_rsp_tag=0;
    reg [63:0] prog_rsp_instruction=0;
    wire  error_valid;
    reg  error_ready=0;
    wire [15:0] error_tag;
    wire [8:0] error_pc;
    wire [7:0] error_opcode;
    wire  commit_valid;
    wire [15:0] commit_tag;
    wire [8:0] commit_pc;
    wire [7:0] commit_opcode;
    wire [511:0] commit_r;
    always #5 clk=~clk;
`ifdef INTEGER_ITERATION_NETLIST
    randomx_integer_iteration dut(
`else
    randomx_integer_iteration #(.SERIAL_IADD(0),.FP_LANES(FP_LANES)) dut(
`endif
        .clk(clk),
        .rst(rst),
        .req_valid(req_valid),
        .req_ready(req_ready),
        .req_tag(req_tag),
        .req_v2(req_v2),
        .req_round_mode(req_round_mode),
        .req_r(req_r),
        .req_a(req_a),
        .req_spaddr0(req_spaddr0),
        .req_spaddr1(req_spaddr1),
        .req_mx(req_mx),
        .req_ma(req_ma),
        .req_read0(req_read0),
        .req_read1(req_read1),
        .req_read2(req_read2),
        .req_read3(req_read3),
        .req_emask0(req_emask0),
        .req_emask1(req_emask1),
        .req_dataset_offset(req_dataset_offset),
        .req_program_addr(req_program_addr),
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
        .done_valid(done_valid),
        .done_ready(done_ready),
        .done_tag(done_tag),
        .done_round_mode(done_round_mode),
        .done_r(done_r),
        .done_f(done_f),
        .done_e(done_e),
        .done_mx(done_mx),
        .done_ma(done_ma),
        .done_spaddr0(done_spaddr0),
        .done_spaddr1(done_spaddr1),
        .prog_valid(prog_valid),
        .prog_ready(prog_ready),
        .prog_addr(prog_addr),
        .prog_tag(prog_tag),
        .prog_rsp_valid(prog_rsp_valid),
        .prog_rsp_ready(prog_rsp_ready),
        .prog_rsp_tag(prog_rsp_tag),
        .prog_rsp_instruction(prog_rsp_instruction),
        .error_valid(error_valid),
        .error_ready(error_ready),
        .error_tag(error_tag),
        .error_pc(error_pc),
        .error_opcode(error_opcode),
        .commit_valid(commit_valid),
        .commit_tag(commit_tag),
        .commit_pc(commit_pc),
        .commit_opcode(commit_opcode),
        .commit_r(commit_r)
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
            @(negedge clk);req_valid=1;req_tag=generation;tag=generation;bad_opcode=bad;prefix_store=prefix;
            req_v2=generation[0];req_r=0;req_r[127:64]=64'h1122334455667788;
            req_a={8{64'h3ff4000000000000}};req_emask0=64'h3000000000000000;req_emask1=64'h3000000000000000;
            req_read0=0;req_read1=2;req_read2=4;req_read3=6;req_program_addr=64'h10000000;
            req_spaddr0=0;req_spaddr1=0;req_mx=0;req_ma=0;req_round_mode=0;
            sp_rd_ready=0;sp_wr_ready=0;prog_ready=0;sp_rsp_valid=0;prog_rsp_valid=0;ds_rsp_valid=0;
            error_ready=0;done_ready=1;pending=0;ppending=0;delay=0;prog_delay=0;
            commits=0;writes=0;steps=0;request_stalls=0;request_accepted=0;reply_injected=0;
            #1;if(!req_ready)$fatal(1,"new error context not ready");
            @(posedge clk);#1;@(negedge clk);req_valid=0;
        end
    endtask
    task tick_to_error;
        begin
            while(!error_valid)begin
                sp_rd_ready=!pending;sp_wr_ready=request_stalls>=2;prog_ready=!ppending && request_stalls>=2;
                if(delay>0)delay=delay-1;
                sp_rsp_valid=pending && delay==0;sp_rsp_tag=stag;sp_rsp_data=sdata;
                if(prog_delay>0)prog_delay=prog_delay-1;
                prog_rsp_valid=ppending && prog_delay==0;prog_rsp_tag=ptag;prog_rsp_instruction=instruction;
                if(prog_rsp_valid && !reply_injected)begin prog_rsp_tag=16'hffff;prog_rsp_instruction=~instruction;end
                @(posedge clk);
                if(done_valid || ds_req_valid)$fatal(1,"unsupported program reached normal retirement/dataset");
                if(sp_rd_valid && sp_rd_ready)begin
                    if(pending || sp_rd_tag!==tag || sp_rd_addr[3:0]!=0)$fatal(1,"error entry read");
                    sdata=sp_rd_addr==0?memory0:128'b0;stag=tag;pending=1;delay=1;
                end
                if(sp_rsp_valid && sp_rsp_ready)pending=0;
                if(commit_valid)begin
                    if(!prefix_store || commits!=0 || commit_tag!==tag || commit_pc!==0 || commit_opcode!==240)$fatal(1,"unsupported operation committed");
                    commits=commits+1;
                end
                if(prog_valid && !prog_ready)request_stalls=request_stalls+1;
                if(sp_wr_valid && !sp_wr_ready)request_stalls=request_stalls+1;
                if(prog_valid && prog_ready)begin
                    if(prog_tag!==tag || prog_addr!==64'h10000000+commits*8)$fatal(1,"error program fetch/PC");
                    if(prefix_store && commits==0)instruction=store_instruction;
                    else instruction={56'b0,bad_opcode};
                    ppending=1;ptag=tag;prog_delay=2;reply_injected=0;request_stalls=0;request_accepted=request_accepted+1;
                end
                if(prog_rsp_valid && prog_rsp_ready)begin
                    if(prog_rsp_tag==16'hffff)reply_injected=1;
                    else ppending=0;
                end
                if(sp_wr_valid && sp_wr_ready)begin
                    if(!prefix_store || writes!=0 || sp_wr_tag!==tag || sp_wr_addr!==0 ||
                        sp_wr_strb!==16'h00ff || sp_wr_data[63:0]!==64'h1122334455667788)$fatal(1,"unsupported-prefix store data/order");
                    memory0[63:0]=sp_wr_data[63:0];writes=writes+1;
                end
                #1;steps=steps+1;if(steps>100)$fatal(1,"unsupported error timeout");
                @(negedge clk);
            end
        end
    endtask
    task hold_and_ack_error;
        integer n;
        begin
            expected_error_pc=prefix_store?1:0;
            for(n=0;n<3;n=n+1)begin
                @(posedge clk);
                if(!error_valid || error_tag!==tag || error_pc!==expected_error_pc || error_opcode!==bad_opcode ||
                    done_valid || ds_req_valid || prog_valid || sp_rd_valid || sp_wr_valid || commit_valid)
                    $fatal(1,"unsupported error record unstable or normal side effect leaked");
                #1;@(negedge clk);
            end
            error_ready=1;@(posedge clk);
            if(!error_valid)$fatal(1,"error acknowledgement missing");
            #1;if(req_ready || sp_rd_valid || sp_wr_valid || prog_valid || commit_valid)$fatal(1,"registered abort suppression");
            @(negedge clk);error_ready=0;
            @(posedge clk);#1;@(negedge clk);
            if(!req_ready || error_valid || done_valid)$fatal(1,"controller did not restart after error abort");
            cases=cases+1;
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
                if(sp_rd_valid && sp_rd_ready)begin sdata=sp_rd_addr==0?memory0:128'b0;stag=tag;pending=1;end
                #1;steps=steps+1;if(steps>40)$fatal(1,"reset fetch entry");@(negedge clk);
            end
            sp_rsp_valid=0;
            for(n=0;n<3;n=n+1)begin @(posedge clk);if(!prog_valid || prog_tag!==16'he000 || prog_addr!==64'h10000000)$fatal(1,"held fetch changed");#1;@(negedge clk);end
            rst=1;#1;if(prog_valid || sp_rd_valid || sp_wr_valid || commit_valid || error_valid || done_valid)$fatal(1,"explicit reset suppression");
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
            launch(store?16'he101:16'he100,store?8'd240:8'd16,0);
            reached=0;before_memory=memory0;
            while(!reached)begin
                sp_rd_ready=!pending;sp_wr_ready=0;prog_ready=!ppending;
                sp_rsp_valid=pending;sp_rsp_tag=stag;sp_rsp_data=sdata;
                prog_rsp_valid=ppending;prog_rsp_tag=ptag;prog_rsp_instruction=instruction;
                @(posedge clk);
                if(commit_valid || error_valid || done_valid || ds_req_valid)$fatal(1,"reset before first memory operation leaked retirement");
                if(sp_rsp_valid && sp_rsp_ready)pending=0;
                if(sp_rd_valid && sp_rd_ready)begin
                    sdata=sp_rd_addr==0?memory0:128'b0;stag=tag;pending=1;
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
            if(prog_valid || sp_rd_valid || sp_wr_valid || commit_valid || error_valid || done_valid)$fatal(1,"execution reset suppression");
            @(posedge clk);#1;@(negedge clk);rst=0;
            // A response accepted before reset may still arrive from the adapter.
            sp_rsp_valid=1;sp_rsp_tag=tag;sp_rsp_data={128{1'b1}};
            for(n=0;n<2;n=n+1)begin
                @(posedge clk);
                if(!sp_rsp_ready || commit_valid || error_valid || done_valid || sp_wr_valid)$fatal(1,"late reset memory reply leaked");
                #1;
            end
            @(negedge clk);sp_rsp_valid=0;
            if(memory0!==before_memory || !req_ready)$fatal(1,"uncommitted reset memory/restart");
        end
    endtask
    task reset_arithmetic;
        input [1:0] operation;
        reg received_word;
        integer n;
        begin
            launch(16'he200+operation,operation==1?8'd76:operation==2?8'd124:8'd46,0);
            received_word=0;before_memory=memory0;
            while(!received_word)begin
                sp_rd_ready=!pending;sp_wr_ready=0;prog_ready=!ppending;
                sp_rsp_valid=pending;sp_rsp_tag=stag;sp_rsp_data=sdata;
                prog_rsp_valid=ppending;prog_rsp_tag=ptag;prog_rsp_instruction=instruction;
                @(posedge clk);
                if(commit_valid || error_valid || done_valid || ds_req_valid)$fatal(1,"arithmetic reset setup leaked retirement");
                if(sp_rsp_valid && sp_rsp_ready)pending=0;
                if(sp_rd_valid && sp_rd_ready)begin sdata=sp_rd_addr==0?memory0:128'b0;stag=tag;pending=1;end
                if(prog_rsp_valid && prog_rsp_ready)begin ppending=0;received_word=1;end
                if(prog_valid && prog_ready)begin
                    if(request_accepted!=0)$fatal(1,"arithmetic reset unexpected fetch");
                    instruction={operation==1?32'd3:32'hffffffff,8'b0,8'd1,8'd1,bad_opcode};
                    ptag=tag;ppending=1;request_accepted=1;
                end
                #1;steps=steps+1;if(steps>40)$fatal(1,"arithmetic reset setup");@(negedge clk);
            end
            sp_rsp_valid=0;prog_rsp_valid=0;prog_ready=0;
            // EXEC sets operands, then the arithmetic request is accepted.
            for(n=0;n<(operation==2&&FP_LANES==1?4:2);n=n+1)begin
                @(posedge clk);if(commit_valid || error_valid || done_valid)$fatal(1,"arithmetic completed before reset point");
                #1;@(negedge clk);
            end
            rst=1;#1;if(commit_valid || error_valid || done_valid || prog_valid || sp_wr_valid)$fatal(1,"arithmetic reset suppression");
            @(posedge clk);#1;@(negedge clk);rst=0;
            for(n=0;n<70;n=n+1)begin
                @(posedge clk);#1;
                if(commit_valid || error_valid || done_valid || prog_valid || sp_wr_valid || !req_ready)$fatal(1,"cancelled arithmetic leaked generation");
            end
            @(negedge clk);if(memory0!==before_memory)$fatal(1,"arithmetic cancellation changed memory");
        end
    endtask
    initial begin #500000;$fatal(1,"integer unsupported regression deadlock");end
    initial begin
        if(!$value$plusargs("unsupported=%s",path))$fatal(1,"missing native unsupported map");$readmemh(path,unsupported);
        memory0=0;cases=0;rst=1;@(posedge clk);#1;@(negedge clk);rst=0;
        for(opcode=0;opcode<256;opcode=opcode+1)if(unsupported[opcode])begin
            before_memory=memory0;launch(16'h2000+opcode,opcode,0);tick_to_error();hold_and_ack_error();
            if(commits!=0 || writes!=0 || request_accepted!=1 || memory0!==before_memory)$fatal(1,"unsupported first operation modified state/memory");
        end
        if(cases!=10)$fatal(1,"unsupported opcode coverage");
        reset_execution(0);reset_execution(1);
        reset_arithmetic(0);reset_arithmetic(1);reset_arithmetic(2);
        launch(16'h3000,8'd204,1);tick_to_error();hold_and_ack_error();
        if(commits!=1 || writes!=1 || memory0[63:0]!==64'h1122334455667788)$fatal(1,"committed prefix lost on abort");
        reset_fetch();
        launch(16'he001,8'd208,0);tick_to_error();hold_and_ack_error();
        if(memory0[63:0]!==64'h1122334455667788)$fatal(1,"explicit reset rolled back committed prefix");
        $display("PASS floating_errors lanes=%0d unsupported_raw_opcodes=10 held_errors=12 prefix_store=1 no_unsupported_commits=1 error_abort_restart=12 reset_held_fetch=1 reset_pending_load=1 reset_held_store=1 reset_multiply=1 reset_reciprocal=1 reset_floating_atomic=1 stale_program_reply_drop=1 stale_memory_reply_drop=2 committed_prefix_preserved=1",FP_LANES);
        $finish;
    end
endmodule
