// SPDX-License-Identifier: BSD-3-Clause
// Native files are immutable instruction/reciprocal inputs and assertion-only
// intermediate/final register vectors. No golden register feeds the DUT.
`timescale 1ns/1ps
module tb_superscalar_execute #(parameter integer MUL_RADIX4=1);
    reg clk=0,rst=1,cancel=0;always #5 clk=~clk;
    reg req_valid=0,rsp_ready=0;
    wire req_ready,rsp_valid,rsp_error,generation_exhausted;
    reg [15:0] req_tag=0,req_epoch=0;
    reg [511:0] req_r=0;
    reg [9:0] req_count=0;
    reg [7:0] req_address_reg=0;
    reg [31:0] req_rcp_count=0;
    wire fetch_valid,fetch_rsp_ready;
    reg fetch_ready=0,fetch_rsp_valid=0,fetch_rsp_error=0,fetch_rsp_rcp_valid=0;
    wire [31:0] fetch_tag;wire [15:0] fetch_epoch;wire [8:0] fetch_pc;
    reg [31:0] fetch_rsp_tag=0,fetch_rsp_rcp_index=0;
    reg [15:0] fetch_rsp_epoch=0;reg [8:0] fetch_rsp_pc=0;
    reg [63:0] fetch_rsp_instruction=0,fetch_rsp_rcp_value=0;
    wire [15:0] rsp_tag,rsp_epoch,commit_tag,commit_epoch;
    wire [511:0] rsp_r,commit_r;
    wire [63:0] rsp_selected,rsp_cycles;
    wire [9:0] rsp_retired,rsp_muls;
    wire [8:0] rsp_error_pc,commit_pc;
    wire [7:0] commit_opcode;
    wire commit_valid;wire [2:0] phase;
`ifdef SUPERSCALAR_NETLIST
    randomx_superscalar_execute dut(
`else
    randomx_superscalar_execute #(.MUL_RADIX4(MUL_RADIX4)) dut(
`endif
        .clk(clk),.rst(rst),.cancel(cancel),.req_valid(req_valid),.req_ready(req_ready),
        .req_tag(req_tag),.req_epoch(req_epoch),.req_r(req_r),.req_count(req_count),
        .req_address_reg(req_address_reg),.req_rcp_count(req_rcp_count),
        .fetch_valid(fetch_valid),.fetch_ready(fetch_ready),.fetch_tag(fetch_tag),
        .fetch_epoch(fetch_epoch),.fetch_pc(fetch_pc),
        .fetch_rsp_valid(fetch_rsp_valid),.fetch_rsp_ready(fetch_rsp_ready),
        .fetch_rsp_tag(fetch_rsp_tag),.fetch_rsp_epoch(fetch_rsp_epoch),.fetch_rsp_pc(fetch_rsp_pc),
        .fetch_rsp_instruction(fetch_rsp_instruction),.fetch_rsp_error(fetch_rsp_error),
        .fetch_rsp_rcp_valid(fetch_rsp_rcp_valid),.fetch_rsp_rcp_index(fetch_rsp_rcp_index),
        .fetch_rsp_rcp_value(fetch_rsp_rcp_value),.rsp_valid(rsp_valid),.rsp_ready(rsp_ready),
        .rsp_tag(rsp_tag),.rsp_epoch(rsp_epoch),.rsp_r(rsp_r),.rsp_selected(rsp_selected),
        .rsp_error(rsp_error),.rsp_error_pc(rsp_error_pc),.rsp_cycles(rsp_cycles),
        .rsp_retired(rsp_retired),.rsp_muls(rsp_muls),.commit_valid(commit_valid),
        .commit_tag(commit_tag),.commit_epoch(commit_epoch),.commit_pc(commit_pc),
        .commit_opcode(commit_opcode),.commit_r(commit_r),.phase(phase),
        .generation_exhausted(generation_exhausted)
    );

    reg [63:0] programs[0:511],reciprocals[0:511];
    reg [511:0] steps[0:511];reg rcp_valid[0:511];reg [31:0] rcp_index[0:511];
    string directory,case_file,mode,result_path,path;
    integer case_fd,result_fd,read_status,case_id,count,address_reg,rcp_count;
    reg [511:0] initial_r,final_r;
    integer total_cases=0,completed=0,total_retired=0,total_muls=0,errors=0,aborts=0;
    integer stale=0,total_req_stalls=0,total_rsp_stalls=0;
    reg [63:0] total_cycles=0;
    integer commits=0,committed_muls=0,requests=0,responses=0,run_ticks=0;
    integer pending=0,delay_q=0,request_delay=0,stale_pending=0,ambient_stale=0;
    integer stalled_run=0,stale_run=0,held_run=0,run_req_stalls=0,run_rsp_stalls=0;
    integer fault_kind=0,fault_pc=0;
    reg [63:0] fault_instruction=0;
    reg [31:0] pending_tag=0,previous_tag=0,run_service_tag=0,replay_tag=0;
    reg [15:0] pending_epoch=0;integer pending_pc=0;
    reg [15:0] owned_tag=16'h6213,owned_epoch=16'h81e7;
    reg fetch_held=0;reg [56:0] held_fetch;
    wire [56:0] now_fetch={fetch_tag,fetch_epoch,fetch_pc};
    wire [767:0] now_return={rsp_tag,rsp_epoch,rsp_r,rsp_selected,rsp_error,
        rsp_error_pc,rsp_cycles,rsp_retired,rsp_muls,66'b0};
    reg [767:0] held_return;
    integer target;

    function integer multiply_opcode;
        input [7:0] op;
        begin multiply_opcode=op==3||op==11||op==12||op==13;end
    endfunction

    task load_case;begin
        path=$sformatf("%s/case-%03d/programs.mem",directory,case_id);
        if(count!=0)begin
            $readmemh(path,programs,0,count-1);
            path=$sformatf("%s/case-%03d/steps.mem",directory,case_id);$readmemh(path,steps,0,count-1);
            path=$sformatf("%s/case-%03d/rcp-valid.mem",directory,case_id);$readmemh(path,rcp_valid,0,count-1);
            path=$sformatf("%s/case-%03d/rcp-index.mem",directory,case_id);$readmemh(path,rcp_index,0,count-1);
            path=$sformatf("%s/case-%03d/reciprocals.mem",directory,case_id);$readmemh(path,reciprocals,0,count-1);
        end
    end endtask

    task check_commit;begin
        if(commit_valid)begin
            if(commits>=count||commit_pc!==commits[8:0]||commit_tag!==owned_tag||
               commit_epoch!==owned_epoch||commit_opcode!==programs[commits][7:0]||
               commit_r!==steps[commits])
                $fatal(1,"native commit mismatch case=%0d pc=%0d observed=%0d",case_id,commits,commit_pc);
            committed_muls=committed_muls+multiply_opcode(programs[commits][7:0]);
            commits=commits+1;
            if(rsp_retired!==commits[9:0]||rsp_muls!==committed_muls[9:0])
                $fatal(1,"commit counters case=%0d pc=%0d",case_id,commits-1);
            if(commits==count&&!rsp_valid)$fatal(1,"final commit did not expose response on same cycle");
        end
    end endtask

    // One deterministic service cycle, with at most one pending packet. The
    // provider never consults steps/final_r to construct an input packet.
    task step;begin
        @(negedge clk);
        fetch_ready=!pending&&(!stalled_run||request_delay>=2);
        fetch_rsp_valid=0;fetch_rsp_error=0;fetch_rsp_rcp_valid=0;
        ambient_stale=0;
        if(!pending&&stale_run)begin
            ambient_stale=1;fetch_rsp_valid=1;fetch_rsp_error=1;
            fetch_rsp_tag=replay_tag!=0?replay_tag:(run_service_tag^32'h00010000);
            fetch_rsp_instruction=~64'b0;
        end
        if(pending)begin
            if(delay_q>0)delay_q=delay_q-1;
            else begin
                fetch_rsp_valid=1;fetch_rsp_tag=pending_tag;fetch_rsp_epoch=pending_epoch;
                fetch_rsp_pc=pending_pc;fetch_rsp_instruction=programs[pending_pc];
                fetch_rsp_rcp_valid=rcp_valid[pending_pc];fetch_rsp_rcp_index=rcp_index[pending_pc];
                fetch_rsp_rcp_value=reciprocals[pending_pc];
                if(stale_pending)begin
                    fetch_rsp_tag=replay_tag!=0?replay_tag:(pending_tag^32'h00010000);
                    fetch_rsp_error=1;fetch_rsp_instruction=~64'b0;
                end else if(fault_kind!=0&&pending_pc==fault_pc)begin
                    case(fault_kind)
                        1:begin
                            fetch_rsp_instruction=fault_instruction;
                            if(fault_instruction[7:0]==13)begin
                                fetch_rsp_rcp_valid=1;fetch_rsp_rcp_index=fault_instruction[63:32];
                                fetch_rsp_rcp_value=64'hfedcba9876543210;
                            end
                        end
                        2:fetch_rsp_epoch=pending_epoch^16'h0001;
                        3:fetch_rsp_pc=pending_pc^9'd1;
                        4:fetch_rsp_error=1;
                        5:begin fetch_rsp_instruction=64'h0000000000ff000d;fetch_rsp_rcp_valid=0;end
                        6:begin fetch_rsp_instruction=64'h0000000000ff000d;fetch_rsp_rcp_valid=1;fetch_rsp_rcp_index=1;end
                        7:begin fetch_rsp_instruction=64'h0000000000ff000d;fetch_rsp_rcp_valid=1;fetch_rsp_rcp_index=0;end
                    endcase
                end
            end
        end
        @(posedge clk);
        if(fetch_held&&(!fetch_valid||now_fetch!==held_fetch))$fatal(1,"held fetch changed");
        fetch_held=fetch_valid&&!fetch_ready;held_fetch=now_fetch;
        if(fetch_valid&&!fetch_ready)begin request_delay=request_delay+1;run_req_stalls=run_req_stalls+1;end
        if(phase==2&&!(fetch_rsp_valid&&fetch_rsp_ready&&fetch_rsp_tag==run_service_tag))
            run_rsp_stalls=run_rsp_stalls+1;
        if(fetch_rsp_valid&&fetch_rsp_ready)begin
            if(ambient_stale)begin
                if(fetch_rsp_tag==run_service_tag)$fatal(1,"ambient stale packet reused current identity");
                stale=stale+1;
            end else if(!pending)$fatal(1,"untracked instruction response");
            else if(stale_pending)begin
                if(fetch_rsp_tag==pending_tag)$fatal(1,"stale packet reused current identity");
                stale=stale+1;stale_pending=0;delay_q=stalled_run?2:0;
            end else begin pending=0;responses=responses+1;end
        end
        if(fetch_valid&&fetch_ready)begin
            if(pending||requests>=count||fetch_pc!==requests[8:0]||fetch_epoch!==owned_epoch||
               fetch_tag!==run_service_tag)$fatal(1,"sequential immutable fetch identity");
            pending=1;pending_pc=fetch_pc;pending_tag=fetch_tag;pending_epoch=fetch_epoch;
            requests=requests+1;request_delay=0;delay_q=stalled_run?2+(pending_pc%3):0;
            stale_pending=stale_run&&(pending_pc==0||pending_pc==count-1);
        end
        #1;run_ticks=run_ticks+1;check_commit;
        if(run_ticks>200000)$fatal(1,"bounded executor timeout case=%0d phase=%0d",case_id,phase);
    end endtask

    task start_request;input integer requested_count,requested_address,requested_rcps;begin
        @(negedge clk);
        if(!req_ready)$fatal(1,"new program not ready");
        req_valid=1;req_tag=owned_tag;req_epoch=owned_epoch;req_r=initial_r;
        req_count=requested_count;req_address_reg=requested_address;req_rcp_count=requested_rcps;
        rsp_ready=0;fetch_ready=0;fetch_rsp_valid=0;
        @(posedge clk);#1;
        commits=0;committed_muls=0;requests=0;responses=0;run_ticks=0;
        pending=0;request_delay=0;delay_q=0;stale_pending=0;fetch_held=0;
        run_req_stalls=0;run_rsp_stalls=0;run_service_tag=fetch_tag;
        if(run_service_tag[15:0]!==owned_tag||run_service_tag[31:16]==0||
           run_service_tag==previous_tag)$fatal(1,"program generation identity did not advance");
        previous_tag=run_service_tag;
        // Poison every input after capture. A held replacement request must
        // not replace the owned request or the held terminal response.
        req_valid=held_run;req_tag=~owned_tag;req_epoch=~owned_epoch;req_r=~initial_r;
        req_count=1023;req_address_reg=255;req_rcp_count=0;
        if(req_ready)$fatal(1,"request accepted before terminal response consumption");
        total_cases=total_cases+1;
    end endtask

    task finish_request;input integer expect_error,expected_pc;reg [511:0] expected_r;
        integer expected_retired,expected_muls,i;reg [63:0] measured;
    begin
        while(!rsp_valid)step;
        measured=run_ticks;
        expected_retired=expect_error?expected_pc:count;expected_muls=0;
        for(i=0;i<expected_retired;i=i+1)expected_muls=expected_muls+multiply_opcode(programs[i][7:0]);
        expected_r=expected_retired==0?initial_r:steps[expected_retired-1];
        if(!expect_error&&expected_r!==final_r)$fatal(1,"native final/steps fixture contradiction");
        if(rsp_tag!==owned_tag||rsp_epoch!==owned_epoch||rsp_error!==expect_error[0]||
           rsp_r!==expected_r||rsp_retired!==expected_retired[9:0]||rsp_muls!==expected_muls[9:0]||
           commits!=expected_retired||responses!=requests||pending||
           rsp_cycles!==measured||rsp_selected!==(expect_error?64'b0:final_r[address_reg*64+:64]))
            $fatal(1,"terminal state/counters case=%0d error=%0d pc=%0d ticks=%0d actual=%0d",case_id,expect_error,expected_pc,measured,rsp_cycles);
        if(expect_error&&rsp_error_pc!==expected_pc[8:0])$fatal(1,"fault pc changed");
        if(!expect_error&&requests!=count)$fatal(1,"program fetch count");
        if(!expect_error&&!stalled_run&&!stale_run&&
           measured!=3*expected_retired+(MUL_RADIX4?34:2)*expected_muls)
            $fatal(1,"ideal service latency equation case=%0d actual=%0d",case_id,measured);
        // Each extra FETCH_REQ / FETCH_RSP cycle is charged exactly once.
        if(!expect_error&&measured!=3*expected_retired+(MUL_RADIX4?34:2)*expected_muls+
           run_req_stalls+run_rsp_stalls)$fatal(1,"service stall accounting case=%0d",case_id);
        held_return=now_return;
        repeat(4)begin
            @(negedge clk);fetch_ready=0;fetch_rsp_valid=1;fetch_rsp_tag=run_service_tag^32'h80000000;
            fetch_rsp_error=1;req_valid=1;
            #1;if(!fetch_rsp_ready||req_ready||fetch_valid||!rsp_valid||now_return!==held_return)
                $fatal(1,"held response/replacement/stale drain");
            @(posedge clk);#1;if(commit_valid||!rsp_valid||now_return!==held_return)$fatal(1,"held response changed");
            stale=stale+1;
        end
        total_req_stalls=total_req_stalls+run_req_stalls;total_rsp_stalls=total_rsp_stalls+run_rsp_stalls;
        total_cycles=total_cycles+measured;total_retired=total_retired+expected_retired;total_muls=total_muls+expected_muls;
        if(expect_error)errors=errors+1;
        else begin
            completed=completed+1;
            if(result_fd!=0)$fdisplay(result_fd,"%0d %0d %0d %0d",case_id,rsp_retired,rsp_muls,rsp_cycles);
        end
        @(negedge clk);req_valid=0;fetch_rsp_valid=0;fetch_rsp_error=0;rsp_ready=1;
        @(posedge clk);#1;rsp_ready=0;
        if(rsp_valid||commit_valid||fetch_valid)$fatal(1,"response consume did not serialize next request");
        if(!req_ready&&!generation_exhausted)$fatal(1,"idle request readiness");
    end endtask

    task run_normal;begin
        fault_kind=0;start_request(count,address_reg,rcp_count);finish_request(0,0);
    end endtask

    task drain_idle;input [31:0] old_tag;begin
        @(negedge clk);fetch_rsp_valid=1;fetch_rsp_tag=old_tag;fetch_rsp_error=1;req_valid=0;
        #1;if(!fetch_rsp_ready||fetch_valid||rsp_valid||commit_valid)$fatal(1,"idle stale drain");
        @(posedge clk);#1;if(rsp_valid||commit_valid||phase!=0)$fatal(1,"idle stale response changed state");
        stale=stale+1;
        @(negedge clk);fetch_rsp_valid=0;fetch_rsp_error=0;
    end endtask

    task probe_early;integer i;begin
        // Matching data presented before the fetch request acceptance must be
        // held. Keep the correct packet stable through the request acceptance
        // edge, and accept it only in the following FETCH_RSP cycle.
        for(i=0;i<3;i=i+1)begin
            @(negedge clk);fetch_ready=0;fetch_rsp_valid=1;fetch_rsp_tag=run_service_tag;
            fetch_rsp_epoch=owned_epoch;fetch_rsp_pc=0;fetch_rsp_error=0;
            fetch_rsp_instruction=programs[0];fetch_rsp_rcp_valid=rcp_valid[0];
            fetch_rsp_rcp_index=rcp_index[0];fetch_rsp_rcp_value=reciprocals[0];
            #1;if(fetch_rsp_ready||!fetch_valid||phase!=1)$fatal(1,"matching early response consumed");
            @(posedge clk);#1;run_ticks=run_ticks+1;run_req_stalls=run_req_stalls+1;
            if(rsp_valid||commit_valid||phase!=1)$fatal(1,"matching early response advanced executor");
        end
        @(negedge clk);fetch_ready=1;
        #1;if(fetch_rsp_ready||!fetch_valid||phase!=1)$fatal(1,"early packet consumed on fetch acceptance edge");
        @(posedge clk);
        pending=1;pending_pc=0;pending_tag=run_service_tag;pending_epoch=owned_epoch;
        requests=1;delay_q=0;stale_pending=0;fetch_held=0;
        #1;run_ticks=run_ticks+1;
        if(phase!=2||!fetch_rsp_ready||rsp_valid||commit_valid)$fatal(1,"early packet not held for response phase");
    end endtask

    task abort_program;input integer stop_phase,use_reset,wait_more;
        integer waited;reg [31:0] canceled_tag;
    begin
        fault_kind=0;held_run=0;stalled_run=0;stale_run=0;
        start_request(count,address_reg,rcp_count);
        while(phase!=stop_phase)begin
            if(rsp_valid)$fatal(1,"abort target phase unreachable %0d",stop_phase);
            step;
        end
        for(waited=0;waited<wait_more;waited=waited+1)begin
            if(phase!=stop_phase)$fatal(1,"multiply abort offset out of range");
            step;
        end
        canceled_tag=run_service_tag;
        @(negedge clk);if(use_reset)rst=1;else cancel=1;
        req_valid=1;rsp_ready=1;fetch_ready=1;fetch_rsp_valid=1;fetch_rsp_tag=canceled_tag;
        #1;if(req_ready||fetch_valid||fetch_rsp_ready||rsp_valid||commit_valid)$fatal(1,"reset/cancel transfer suppression");
        @(posedge clk);#1;if(req_ready||fetch_valid||fetch_rsp_ready||rsp_valid||commit_valid)$fatal(1,"reset/cancel edge suppression");
        @(negedge clk);rst=0;cancel=0;req_valid=0;rsp_ready=0;fetch_ready=0;fetch_rsp_valid=0;
        pending=0;fetch_held=0;
        // A reset additionally requires the external service to discard all
        // old replies. Cancel deliberately keeps the old generation obsolete.
        if(use_reset)begin previous_tag=0;replay_tag=0;end
        else begin drain_idle(canceled_tag);replay_tag=canceled_tag;end
        repeat(40)begin
            @(posedge clk);#1;
            if(!req_ready||fetch_valid||rsp_valid||commit_valid||phase!=0)$fatal(1,"aborted multiplier/result survived");
        end
        aborts=aborts+1;
        stale_run=!use_reset;run_normal;stale_run=0;replay_tag=0;
    end endtask

    task malformed_cases;integer op,form;
    begin
        fault_pc=0;fault_kind=1;
        for(op=14;op<256;op=op+1)begin
            fault_instruction=op;start_request(count,address_reg,rcp_count);finish_request(1,0);
        end
        for(form=0;form<2;form=form+1)begin
            fault_instruction=form==0?64'h0000000000000800:64'h000000000000ff01;
            start_request(count,address_reg,rcp_count);finish_request(1,0);
        end
        for(op=0;op<14;op=op+1)if(op==0||op==1||op==2||op==3||op==11||op==12)begin
            for(form=0;form<2;form=form+1)begin
                fault_instruction=(form==0?64'h0000000000080000:64'h0000000000ff0000)|op;
                start_request(count,address_reg,rcp_count);finish_request(1,0);
            end
        end
        fault_instruction=64'h0000004000ff0004;start_request(count,address_reg,rcp_count);finish_request(1,0);
        fault_instruction=64'hffffffff00ff0004;start_request(count,address_reg,rcp_count);finish_request(1,0);
        // Index exactly equal to table count is out of bounds; 0/1/2/4 in
        // the successful native corpus remain legal prepared indices.
        fault_instruction=({32'b0,rcp_count[31:0]}<<32)|64'h00ff000d;
        start_request(count,address_reg,rcp_count);finish_request(1,0);
        for(form=2;form<=7;form=form+1)begin
            fault_kind=form;start_request(count,address_reg,form==7?0:rcp_count);finish_request(1,0);
        end
        // Late transport/instruction faults preserve exactly the native
        // committed prefix, including its multiply and retirement counters.
        fault_pc=count-1;
        for(form=1;form<=4;form=form+1)begin
            fault_kind=form;fault_instruction=255;start_request(count,address_reg,rcp_count);finish_request(1,fault_pc);
        end
        fault_kind=0;fault_pc=0;
        start_request(513,address_reg,rcp_count);finish_request(1,0);
        start_request(1023,address_reg,rcp_count);finish_request(1,0);
        start_request(count,8,rcp_count);finish_request(1,0);
        start_request(count,255,rcp_count);finish_request(1,0);
        run_normal;
    end endtask

    task exhaust_generations;integer i;begin
        // No hidden-state injection: consume all 65,535 permitted program
        // requests, including an error and a cancel, then prove no wrap.
        @(negedge clk);rst=1;req_valid=0;rsp_ready=0;fetch_rsp_valid=0;
        @(posedge clk);#1;@(negedge clk);rst=0;previous_tag=0;
        for(i=1;i<65535;i=i+1)begin
            @(negedge clk);if(!req_ready||generation_exhausted)$fatal(1,"premature generation exhaustion %0d",i);
            req_valid=1;req_tag=owned_tag;req_epoch=owned_epoch;req_r=initial_r;
            req_count=i==2?513:0;req_address_reg=address_reg;req_rcp_count=rcp_count;
            @(posedge clk);#1;
            if(fetch_tag!=={i[15:0],owned_tag}||!rsp_valid||rsp_cycles!=0||fetch_valid||commit_valid||
               rsp_error!==(i==2)||rsp_r!==initial_r||rsp_retired!=0||rsp_muls!=0)
                $fatal(1,"empty/error generation iteration %0d",i);
            @(negedge clk);req_valid=0;
            if(i==3)cancel=1;else rsp_ready=1;
            @(posedge clk);#1;
            @(negedge clk);cancel=0;rsp_ready=0;
        end
        // The last available identity executes a real native program all the
        // way through its held return even though new admission is exhausted.
        run_normal;
        if(!generation_exhausted||previous_tag!=={16'hffff,owned_tag})
            $fatal(1,"last generation did not complete native execution");
        repeat(4)begin
            req_valid=1;#1;if(req_ready||!generation_exhausted||fetch_valid||rsp_valid||commit_valid)
                $fatal(1,"generation wrapped instead of failing closed");
            @(posedge clk);#1;@(negedge clk);
        end
        req_valid=0;cancel=1;@(posedge clk);#1;@(negedge clk);cancel=0;
        if(req_ready||!generation_exhausted)$fatal(1,"cancel cleared generation exhaustion");
        rst=1;@(posedge clk);#1;@(negedge clk);rst=0;previous_tag=0;
        #1;if(!req_ready||generation_exhausted)$fatal(1,"quiescent reset failed to clear exhaustion");
        total_cases=65535;completed=65533;errors=1;aborts=1;
    end endtask

    initial begin
        if(!$value$plusargs("DIR=%s",directory))$fatal(1,"missing DIR");
        if(!$value$plusargs("CASES=%s",case_file))case_file="cases.hex";
        if(!$value$plusargs("MODE=%s",mode))mode="corpus";
        if($value$plusargs("RESULTS=%s",result_path))begin
            result_fd=$fopen(result_path,"w");if(!result_fd)$fatal(1,"cannot create RESULTS");
        end else result_fd=0;
        path=$sformatf("%s/%s",directory,case_file);case_fd=$fopen(path,"r");
        if(!case_fd)$fatal(1,"cannot open case list %s",path);
        repeat(2)begin @(posedge clk);#1;end
        @(negedge clk);rst=0;#1;
        if(!req_ready||fetch_valid||rsp_valid||commit_valid)$fatal(1,"initial reset state");
        if(mode!="corpus"&&mode!="stalled"&&mode!="held"&&mode!="malformed"&&
           mode!="stale"&&mode!="cancel"&&mode!="reset"&&mode!="exhaustion")$fatal(1,"unknown MODE");
        read_status=$fscanf(case_fd,"%d %d %d %d %h %h\n",case_id,count,address_reg,rcp_count,initial_r,final_r);
        while(read_status==6)begin
            if(count<0||count>512||address_reg<0||address_reg>7)$fatal(1,"bad native fixture metadata");
            load_case;
            stalled_run=mode=="stalled";held_run=mode=="held";stale_run=mode=="stale";
            if(mode=="malformed")malformed_cases;
            else if(mode=="cancel"||mode=="reset")begin
                for(target=1;target<=6;target=target+1)abort_program(target,mode=="reset",0);
                if(MUL_RADIX4)begin
                    abort_program(5,mode=="reset",16);abort_program(5,mode=="reset",31);
                    abort_program(5,mode=="reset",32);
                end
            end else if(mode=="exhaustion")exhaust_generations;
            else if(mode=="stale")begin
                drain_idle(32'hffff4321);fault_kind=0;start_request(count,address_reg,rcp_count);
                if(count!=0)probe_early;finish_request(0,0);
            end else run_normal;
            if(mode=="malformed"||mode=="exhaustion")read_status=0;
            else read_status=$fscanf(case_fd,"%d %d %d %d %h %h\n",case_id,count,address_reg,rcp_count,initial_r,final_r);
        end
        $fclose(case_fd);if(result_fd)$fclose(result_fd);
        if(total_cases==0)$fatal(1,"no native cases executed");
        $display("PASS superscalar_execute mode=%0s cases=%0d completed=%0d retired=%0d muls=%0d cycles=%0d errors=%0d aborts=%0d stale=%0d req_stalls=%0d rsp_stalls=%0d",
            mode,total_cases,completed,total_retired,total_muls,total_cycles,errors,aborts,stale,total_req_stalls,total_rsp_stalls);
        $finish;
    end
endmodule
