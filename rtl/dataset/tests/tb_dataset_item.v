// SPDX-License-Identifier: BSD-3-Clause
// Native expected states are assertion-only. The external services return only
// immutable prepared instructions/reciprocals and the bound cache-line inputs.
`timescale 1ns/1ps
module tb_dataset_item #(parameter integer MUL_RADIX4=1);
    reg clk=0,rst=1,cancel=0;always #5 clk=~clk;
    reg req_valid=0,rsp_ready=0;
    wire req_ready,rsp_valid,rsp_error,generation_exhausted;
    reg [15:0] req_tag=0,req_epoch=0;
    reg [63:0] req_item=0,req_address_regs=0;
    reg [79:0] req_counts=0;reg [31:0] req_rcp_count=0;
    wire [15:0] rsp_tag,rsp_epoch;
    wire [511:0] rsp_data;
    wire [2:0] rsp_error_stage;
    wire [8:0] rsp_error_pc;
    wire [3:0] rsp_completed_stages,phase;
    wire [12:0] rsp_retired,rsp_muls;
    wire [63:0] rsp_cycles,rsp_exec_cycles;

    wire fetch_valid,fetch_rsp_ready;
    reg fetch_ready=0,fetch_rsp_valid=0,fetch_rsp_error=0,fetch_rsp_rcp_valid=0;
    wire [31:0] fetch_tag;wire [15:0] fetch_epoch;
    wire [2:0] fetch_program;wire [8:0] fetch_pc;
    reg [31:0] fetch_rsp_tag=0,fetch_rsp_rcp_index=0;
    reg [15:0] fetch_rsp_epoch=0;reg [2:0] fetch_rsp_program=0;reg [8:0] fetch_rsp_pc=0;
    reg [63:0] fetch_rsp_instruction=0,fetch_rsp_rcp_value=0;
    wire cache_req_valid,cache_rsp_ready;
    reg cache_req_ready=0,cache_rsp_valid=0,cache_rsp_error=0;
    wire [31:0] cache_req_tag;wire [15:0] cache_req_epoch;
    wire [2:0] cache_req_program;wire [21:0] cache_req_index;
    reg [31:0] cache_rsp_tag=0;reg [15:0] cache_rsp_epoch=0;
    reg [2:0] cache_rsp_program=0;reg [21:0] cache_rsp_index=0;
    reg [511:0] cache_rsp_data=0;
    wire commit_valid,stage_valid;
    wire [2:0] commit_program,stage_program;
    wire [8:0] commit_pc;wire [7:0] commit_opcode;
    wire [511:0] commit_r,stage_r;
    wire [21:0] stage_cache_index;
    wire [63:0] stage_selected,stage_program_cycles;
`ifdef DATASET_ITEM_NETLIST
    randomx_dataset_item dut(
`else
    randomx_dataset_item #(.MUL_RADIX4(MUL_RADIX4)) dut(
`endif
        .clk(clk),.rst(rst),.cancel(cancel),.req_valid(req_valid),.req_ready(req_ready),
        .req_tag(req_tag),.req_epoch(req_epoch),.req_item(req_item),.req_counts(req_counts),
        .req_address_regs(req_address_regs),.req_rcp_count(req_rcp_count),
        .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_tag(rsp_tag),.rsp_epoch(rsp_epoch),
        .rsp_data(rsp_data),.rsp_error(rsp_error),.rsp_error_stage(rsp_error_stage),
        .rsp_error_pc(rsp_error_pc),.rsp_completed_stages(rsp_completed_stages),
        .rsp_retired(rsp_retired),.rsp_muls(rsp_muls),.rsp_cycles(rsp_cycles),.rsp_exec_cycles(rsp_exec_cycles),
        .cache_req_valid(cache_req_valid),.cache_req_ready(cache_req_ready),.cache_req_tag(cache_req_tag),
        .cache_req_epoch(cache_req_epoch),.cache_req_program(cache_req_program),.cache_req_index(cache_req_index),
        .cache_rsp_valid(cache_rsp_valid),.cache_rsp_ready(cache_rsp_ready),.cache_rsp_tag(cache_rsp_tag),
        .cache_rsp_epoch(cache_rsp_epoch),.cache_rsp_program(cache_rsp_program),.cache_rsp_index(cache_rsp_index),
        .cache_rsp_data(cache_rsp_data),.cache_rsp_error(cache_rsp_error),
        .fetch_valid(fetch_valid),.fetch_ready(fetch_ready),.fetch_tag(fetch_tag),.fetch_epoch(fetch_epoch),
        .fetch_program(fetch_program),.fetch_pc(fetch_pc),.fetch_rsp_valid(fetch_rsp_valid),
        .fetch_rsp_ready(fetch_rsp_ready),.fetch_rsp_tag(fetch_rsp_tag),.fetch_rsp_epoch(fetch_rsp_epoch),
        .fetch_rsp_program(fetch_rsp_program),.fetch_rsp_pc(fetch_rsp_pc),.fetch_rsp_instruction(fetch_rsp_instruction),
        .fetch_rsp_error(fetch_rsp_error),.fetch_rsp_rcp_valid(fetch_rsp_rcp_valid),
        .fetch_rsp_rcp_index(fetch_rsp_rcp_index),.fetch_rsp_rcp_value(fetch_rsp_rcp_value),
        .commit_valid(commit_valid),.commit_program(commit_program),.commit_pc(commit_pc),
        .commit_opcode(commit_opcode),.commit_r(commit_r),.stage_valid(stage_valid),
        .stage_program(stage_program),.stage_cache_index(stage_cache_index),.stage_r(stage_r),
        .stage_selected(stage_selected),.stage_program_cycles(stage_program_cycles),
        .phase(phase),.generation_exhausted(generation_exhausted)
    );

    reg [63:0] programs[0:4095],reciprocals[0:4095];
    reg [511:0] steps[0:4095],cache_lines[0:7],pre_exec[0:7],post_exec[0:7],post_xor[0:7],seed_words[0:0];
    reg rcp_valid[0:4095];reg [31:0] rcp_index[0:4095];
    reg [21:0] cache_indices[0:7];reg [63:0] selected[0:7];
    reg [511:0] seeded_r,final_r;
    reg [63:0] item_number,packed_addresses;
    reg [79:0] packed_counts;
    integer global_rcp_count,case_id,cache_id,case_fd,result_fd,read_status,cache_fd=0;
    reg [7:0] cache_bytes[0:63];reg [511:0] c_payload=0;
    string directory,case_file,mode,result_path,path;
    integer counts[0:7],addresses[0:7],mul_counts[0:7];
    integer commits_by_stage[0:7],fetches_by_stage[0:7];
    reg [31:0] fetch_tags[0:7];
    reg [15:0] owned_tag=16'hd173,owned_epoch=16'h82a5;
    integer completed=0,errors=0,aborts=0,total_items=0,stale_packets=0;
    integer aborted_retired=0,aborted_muls=0,aborted_stages=0;
    reg [63:0] aborted_cycles=0;
    integer total_stages=0,total_retired=0,total_muls=0,total_fetch_stalls=0,total_cache_stalls=0;
    reg [63:0] total_cycles=0,total_exec_cycles=0;
    integer commits=0,muls=0,stages_done=0,fetch_requests=0,fetch_responses=0,cache_requests=0,cache_responses=0;
    integer run_ticks=0,fetch_stalls=0,cache_stalls=0;
    reg [63:0] observed_exec_cycles=0;
    integer stalled_run=0,stale_run=0,held_run=0;
    integer fault_service=0,fault_kind=0,fault_stage=0,fault_pc=0;
    integer f_pending=0,f_delay=0,f_wait=0,f_stale=0,f_program=0,f_pc=0;
    integer c_pending=0,c_delay=0,c_wait=0,c_stale=0,c_program=0;
    reg [31:0] f_tag=0,c_tag=0,run_cache_tag=0,previous_cache_tag=0,previous_fetch_tag=0;
    reg [31:0] replay_fetch_tag=0,replay_cache_tag=0;
    reg [15:0] f_epoch=0,c_epoch=0;reg [21:0] c_index=0;
    reg f_held=0,c_held=0;
    reg [59:0] held_fetch;
    wire [59:0] now_fetch={fetch_tag,fetch_epoch,fetch_program,fetch_pc};
    reg [72:0] held_cache;
    wire [72:0] now_cache={cache_req_tag,cache_req_epoch,cache_req_program,cache_req_index};
    wire [714:0] now_return={rsp_tag,rsp_epoch,rsp_data,rsp_error,rsp_error_stage,rsp_error_pc,
        rsp_completed_stages,rsp_retired,rsp_muls,rsp_cycles,rsp_exec_cycles};
    reg [714:0] held_return;

    function integer multiply_opcode;
        input [7:0] opcode;
        begin multiply_opcode=opcode==3||opcode==11||opcode==12||opcode==13;end
    endfunction

    task read_cache_line;
        input [21:0] index;
        output [511:0] data;
        integer status,i;
    begin
        // Native cache inputs, addressed by the DUT's actual request. Oracle
        // stage cache lines below are compared but never provide service data.
        status=$fseek(cache_fd,index*64,0);
        if(status!=0)$fatal(1,"native cache seek failed index=%0d",index);
        status=$fread(cache_bytes,cache_fd,0,64);
        if(status!=64)$fatal(1,"native cache short read index=%0d bytes=%0d",index,status);
        for(i=0;i<64;i=i+1)data[i*8+:8]=cache_bytes[i];
    end endtask

    task load_case;
        integer i,j,stage_fd,scan;
    begin
        if(cache_fd)$fclose(cache_fd);
        path=$sformatf("%s/cache-%0d.bin",directory,cache_id);cache_fd=$fopen(path,"rb");
        if(!cache_fd)$fatal(1,"cannot open native cache input %s",path);
        path=$sformatf("%s/case-%03d/seed.hex",directory,case_id);$readmemh(path,seed_words);
        seeded_r=seed_words[0];
        path=$sformatf("%s/case-%03d/stages.mem",directory,case_id);stage_fd=$fopen(path,"r");
        if(!stage_fd)$fatal(1,"cannot open native stage observations");
        for(i=0;i<8;i=i+1)begin
            counts[i]=packed_counts[i*10+:10];addresses[i]=packed_addresses[i*8+:8];mul_counts[i]=0;
            if(counts[i]>512||addresses[i]>7)$fatal(1,"invalid oracle descriptor stage=%0d",i);
            scan=$fscanf(stage_fd,"%h %h %h %h %h %h\n",cache_indices[i],cache_lines[i],pre_exec[i],post_exec[i],post_xor[i],selected[i]);
            if(scan!=6)$fatal(1,"short native stage observations case=%0d stage=%0d",case_id,i);
            if(pre_exec[i]!==(i==0?seeded_r:post_xor[i-1])||
               cache_indices[i]!==((i==0?item_number:selected[i-1])&64'h3fffff)||
               post_xor[i]!==(post_exec[i]^cache_lines[i])||selected[i]!==post_xor[i][addresses[i]*64+:64])
                $fatal(1,"contradictory native stage recurrence case=%0d stage=%0d",case_id,i);
            path=$sformatf("%s/case-%03d/program-%0d.mem",directory,case_id,i);$readmemh(path,programs,i*512,i*512+511);
            path=$sformatf("%s/case-%03d/steps-%0d.mem",directory,case_id,i);$readmemh(path,steps,i*512,i*512+511);
            path=$sformatf("%s/case-%03d/rcp-valid-%0d.mem",directory,case_id,i);$readmemh(path,rcp_valid,i*512,i*512+511);
            path=$sformatf("%s/case-%03d/rcp-index-%0d.mem",directory,case_id,i);$readmemh(path,rcp_index,i*512,i*512+511);
            path=$sformatf("%s/case-%03d/reciprocals-%0d.mem",directory,case_id,i);$readmemh(path,reciprocals,i*512,i*512+511);
            for(j=0;j<counts[i];j=j+1)mul_counts[i]=mul_counts[i]+multiply_opcode(programs[i*512+j][7:0]);
            if(post_exec[i]!==(counts[i]==0?pre_exec[i]:steps[i*512+counts[i]-1]))
                $fatal(1,"contradictory native program final state case=%0d stage=%0d",case_id,i);
        end
        $fclose(stage_fd);
        if(final_r!==post_xor[7])$fatal(1,"native final state differs from eighth post-XOR state");
    end endtask

    task observe;
        integer slot;
        reg [63:0] ideal_cycles;
    begin
        if(commit_valid)begin
            slot=commit_program*512+commits_by_stage[commit_program];
            if(commit_program!==stages_done[2:0]||commits_by_stage[commit_program]>=counts[commit_program]||
               commit_pc!==commits_by_stage[commit_program][8:0]||commit_opcode!==programs[slot][7:0]||commit_r!==steps[slot])
                $fatal(1,"native commit mismatch case=%0d stage=%0d pc=%0d",case_id,commit_program,commit_pc);
            commits_by_stage[commit_program]=commits_by_stage[commit_program]+1;
            commits=commits+1;muls=muls+multiply_opcode(commit_opcode);
        end
        if(stage_valid)begin
            ideal_cycles=3*counts[stages_done]+(MUL_RADIX4?34:2)*mul_counts[stages_done];
            if(stages_done>=8||stage_program!==stages_done[2:0]||
               commits_by_stage[stages_done]!=counts[stages_done]||
               stage_cache_index!==cache_indices[stages_done]||stage_r!==post_xor[stages_done]||
               stage_selected!==selected[stages_done]||stage_program_cycles<ideal_cycles)
                $fatal(1,"native post-XOR stage mismatch case=%0d stage=%0d",case_id,stages_done);
            if(!stalled_run&&!stale_run&&stage_program_cycles!==ideal_cycles)
                $fatal(1,"ideal program clocks case=%0d stage=%0d",case_id,stages_done);
            observed_exec_cycles=observed_exec_cycles+stage_program_cycles;
            stages_done=stages_done+1;
        end
    end endtask

    // Payloads are derived exclusively from immutable input fixtures. Neither
    // steps nor post_xor nor final_r is read by either service provider.
    task step;
        integer slot;
        reg f_ambient,c_ambient;
    begin
        @(negedge clk);
        fetch_ready=!f_pending&&(!stalled_run||f_wait>=2);
        cache_req_ready=!c_pending&&(!stalled_run||c_wait>=3);
        fetch_rsp_valid=0;fetch_rsp_error=0;fetch_rsp_rcp_valid=0;
        cache_rsp_valid=0;cache_rsp_error=0;f_ambient=0;c_ambient=0;
        if(stale_run&&!f_pending)begin
            f_ambient=1;fetch_rsp_valid=1;
            fetch_rsp_tag=(replay_fetch_tag!=0&&replay_fetch_tag!=fetch_tag)?replay_fetch_tag:(fetch_tag^32'h80000000);
            fetch_rsp_error=1;fetch_rsp_instruction=~64'b0;
        end
        if(stale_run&&!c_pending)begin
            c_ambient=1;cache_rsp_valid=1;
            cache_rsp_tag=(replay_cache_tag!=0&&replay_cache_tag!=cache_req_tag)?replay_cache_tag:(cache_req_tag^32'h80000000);
            cache_rsp_error=1;cache_rsp_data=~512'b0;
        end
        if(f_pending)begin
            if(f_delay>0)f_delay=f_delay-1;
            else begin
                slot=f_program*512+f_pc;
                fetch_rsp_valid=1;fetch_rsp_tag=f_tag;fetch_rsp_epoch=f_epoch;
                fetch_rsp_program=f_program;fetch_rsp_pc=f_pc;fetch_rsp_instruction=programs[slot];
                fetch_rsp_rcp_valid=rcp_valid[slot];fetch_rsp_rcp_index=rcp_index[slot];
                fetch_rsp_rcp_value=reciprocals[slot];
                if(f_stale)begin
                    fetch_rsp_tag=(replay_fetch_tag!=0&&replay_fetch_tag!=f_tag)?replay_fetch_tag:(f_tag^32'h80000000);
                    fetch_rsp_error=1;fetch_rsp_instruction=~64'b0;
                end
                else if(fault_service==1&&f_program==fault_stage&&f_pc==fault_pc)begin
                    case(fault_kind)
                        1:fetch_rsp_epoch=f_epoch^16'b1;
                        2:fetch_rsp_program=f_program^3'b1;
                        3:fetch_rsp_pc=f_pc^9'b1;
                        4:fetch_rsp_error=1;
                        5:fetch_rsp_instruction=64'hff;
                    endcase
                end
            end
        end
        if(c_pending)begin
            if(c_delay>0)c_delay=c_delay-1;
            else begin
                cache_rsp_valid=1;cache_rsp_tag=c_tag;cache_rsp_epoch=c_epoch;
                cache_rsp_program=c_program;cache_rsp_index=c_index;cache_rsp_data=c_payload;
                if(c_stale)begin
                    cache_rsp_tag=(replay_cache_tag!=0&&replay_cache_tag!=c_tag)?replay_cache_tag:(c_tag^32'h80000000);
                    cache_rsp_error=1;cache_rsp_data=~512'b0;
                end
                else if(fault_service==2&&c_program==fault_stage)begin
                    case(fault_kind)
                        1:cache_rsp_epoch=c_epoch^16'b1;
                        2:cache_rsp_program=c_program^3'b1;
                        3:cache_rsp_index=c_index^22'b1;
                        4:cache_rsp_error=1;
                    endcase
                end
            end
        end
        @(posedge clk);
        if(f_held&&(!fetch_valid||now_fetch!==held_fetch))$fatal(1,"held instruction request changed");
        if(c_held&&(!cache_req_valid||now_cache!==held_cache))$fatal(1,"held cache request changed");
        f_held=fetch_valid&&!fetch_ready;held_fetch=now_fetch;
        c_held=cache_req_valid&&!cache_req_ready;held_cache=now_cache;
        if(fetch_valid&&!fetch_ready)begin f_wait=f_wait+1;fetch_stalls=fetch_stalls+1;end
        if(cache_req_valid&&!cache_req_ready)begin c_wait=c_wait+1;cache_stalls=cache_stalls+1;end
        if(fetch_rsp_valid&&fetch_rsp_ready)begin
            if(f_ambient)stale_packets=stale_packets+1;
            else if(!f_pending)$fatal(1,"untracked instruction response");
            else if(f_stale)begin f_stale=0;f_delay=stalled_run?2:0;stale_packets=stale_packets+1;end
            else begin f_pending=0;fetch_responses=fetch_responses+1;end
        end
        if(cache_rsp_valid&&cache_rsp_ready)begin
            if(c_ambient)stale_packets=stale_packets+1;
            else if(!c_pending)$fatal(1,"untracked cache response");
            else if(c_stale)begin c_stale=0;c_delay=stalled_run?3:0;stale_packets=stale_packets+1;end
            else begin c_pending=0;cache_responses=cache_responses+1;end
        end
        if(fetch_valid&&fetch_ready)begin
            if(f_pending||fetch_program!==stages_done[2:0]||fetch_pc!==fetches_by_stage[fetch_program][8:0]||
               fetch_epoch!==owned_epoch||fetches_by_stage[fetch_program]>=counts[fetch_program])
                $fatal(1,"immutable instruction sequence case=%0d stage=%0d pc=%0d",case_id,fetch_program,fetch_pc);
            if(fetch_tag[15:0]!==owned_tag)$fatal(1,"instruction service lost caller tag");
            if(fetches_by_stage[fetch_program]==0)begin
                if(fetch_tag[31:16]==0||fetch_tag==previous_fetch_tag)$fatal(1,"executor generation identity reused");
                fetch_tags[fetch_program]=fetch_tag;previous_fetch_tag=fetch_tag;
            end
            else if(fetch_tag!==fetch_tags[fetch_program])$fatal(1,"program transaction tag changed");
            f_pending=1;f_program=fetch_program;f_pc=fetch_pc;f_tag=fetch_tag;f_epoch=fetch_epoch;
            fetches_by_stage[fetch_program]=fetches_by_stage[fetch_program]+1;
            fetch_requests=fetch_requests+1;f_wait=0;f_delay=stalled_run?2+(f_pc%3):0;
            f_stale=stale_run&&(f_pc==0||f_pc==counts[f_program]-1);
        end
        if(cache_req_valid&&cache_req_ready)begin
            if(c_pending||cache_req_program!==stages_done[2:0]||cache_req_index!==cache_indices[stages_done]||
               cache_req_epoch!==owned_epoch||commits_by_stage[stages_done]!=counts[stages_done]||cache_requests!=stages_done)
                $fatal(1,"native cache recurrence/ordering case=%0d stage=%0d",case_id,stages_done);
            if(cache_requests==0)begin
                run_cache_tag=cache_req_tag;
                if(run_cache_tag[31:16]==0||run_cache_tag[15:0]!==owned_tag||run_cache_tag==previous_cache_tag)
                    $fatal(1,"outer cache identity did not advance");
                previous_cache_tag=run_cache_tag;
            end else if(cache_req_tag!==run_cache_tag)$fatal(1,"outer cache tag changed between stages");
            c_pending=1;c_program=cache_req_program;c_tag=cache_req_tag;c_epoch=cache_req_epoch;c_index=cache_req_index;
            read_cache_line(cache_req_index,c_payload);
            if(c_payload!==cache_lines[c_program])$fatal(1,"addressed native cache input differs from assertion fixture");
            cache_requests=cache_requests+1;c_wait=0;c_delay=stalled_run?3+(c_program%3):0;c_stale=stale_run;
        end
        #1;run_ticks=run_ticks+1;observe;
        if(run_ticks>1500000)$fatal(1,"bounded dataset-item timeout case=%0d phase=%0d",case_id,phase);
    end endtask

    task start_request;
        input [79:0] requested_counts;
        input [63:0] requested_addresses;
        integer i;
    begin
        @(negedge clk);if(!req_ready)$fatal(1,"new dataset item not ready");
        req_valid=1;req_tag=owned_tag;req_epoch=owned_epoch;req_item=item_number;
        req_counts=requested_counts;req_address_regs=requested_addresses;req_rcp_count=global_rcp_count;
        rsp_ready=0;fetch_ready=0;fetch_rsp_valid=0;cache_req_ready=0;cache_rsp_valid=0;
        @(posedge clk);#1;
        commits=0;muls=0;stages_done=0;fetch_requests=0;fetch_responses=0;cache_requests=0;cache_responses=0;
        run_ticks=0;observed_exec_cycles=0;fetch_stalls=0;cache_stalls=0;
        f_pending=0;c_pending=0;f_delay=0;c_delay=0;f_wait=0;c_wait=0;f_held=0;c_held=0;f_stale=0;c_stale=0;
        for(i=0;i<8;i=i+1)begin commits_by_stage[i]=0;fetches_by_stage[i]=0;fetch_tags[i]=0;end
        // Capture must include every descriptor, full item number and global
        // reciprocal count, even while an invalid replacement remains valid.
        req_valid=held_run;req_tag=~owned_tag;req_epoch=~owned_epoch;req_item=~item_number;
        req_counts=~80'b0;req_address_regs=~64'b0;req_rcp_count=0;
        if(req_ready)$fatal(1,"new request admitted while item owned");
        total_items=total_items+1;
    end endtask

    task finish_request;
        input integer expect_error,expected_stage,expected_pc,descriptor_error;
        integer i,expected_retired,expected_muls,prefix_muls;
        reg [511:0] expected_data;
        reg [63:0] expected_error_exec;
    begin
        while(!rsp_valid)step;
        expected_data=descriptor_error?512'b0:(stages_done==0?seeded_r:post_xor[stages_done-1]);
        if(!expect_error)expected_data=final_r;
        expected_retired=0;expected_muls=0;
        for(i=0;i<8;i=i+1)begin expected_retired=expected_retired+commits_by_stage[i];end
        expected_muls=muls;
        if(rsp_tag!==owned_tag||rsp_epoch!==owned_epoch||rsp_error!==expect_error[0]||rsp_data!==expected_data||
           rsp_retired!==expected_retired[12:0]||rsp_muls!==expected_muls[12:0]||
           rsp_completed_stages!==stages_done[3:0]||rsp_cycles!==run_ticks||f_pending||c_pending||
           fetch_requests!=fetch_responses||cache_requests!=cache_responses)
            $fatal(1,"dataset terminal state case=%0d error=%0d stages=%0d ticks=%0d cycles=%0d",case_id,expect_error,stages_done,run_ticks,rsp_cycles);
        if(expect_error)begin
            if(rsp_error_stage!==expected_stage[2:0]||rsp_error_pc!==expected_pc[8:0])$fatal(1,"error location mismatch");
            if(descriptor_error&&(stages_done||commits||cache_requests||fetch_requests||rsp_cycles||rsp_exec_cycles))
                $fatal(1,"descriptor error performed work");
            if(!descriptor_error&&stages_done!=expected_stage)$fatal(1,"error completed wrong stage prefix");
            if(!descriptor_error&&fault_service==1&&
               (commits_by_stage[expected_stage]!=expected_pc||fetches_by_stage[expected_stage]!=expected_pc+1))
                $fatal(1,"failing instruction did not preserve exactly its native prefix");
            if(!descriptor_error&&fault_service==2&&commits_by_stage[expected_stage]!=counts[expected_stage])
                $fatal(1,"cache error lost executed program commits");
            if(!descriptor_error&&!stalled_run&&!stale_run)begin
                if(fault_service==1)begin
                    prefix_muls=0;
                    for(i=0;i<expected_pc;i=i+1)prefix_muls=prefix_muls+multiply_opcode(programs[expected_stage*512+i][7:0]);
                    expected_error_exec=observed_exec_cycles+3*expected_pc+(MUL_RADIX4?34:2)*prefix_muls+2;
                end else expected_error_exec=observed_exec_cycles+3*counts[expected_stage]+(MUL_RADIX4?34:2)*mul_counts[expected_stage];
                if(rsp_exec_cycles!==expected_error_exec)$fatal(1,"error core clocks lost failed program prefix");
            end
            errors=errors+1;
        end else begin
            if(stages_done!=8||cache_requests!=8||rsp_exec_cycles!==observed_exec_cycles)
                $fatal(1,"full eight-stage completion/accounting mismatch");
            for(i=0;i<8;i=i+1)if(commits_by_stage[i]!=counts[i]||fetches_by_stage[i]!=counts[i])
                $fatal(1,"successful program count mismatch stage=%0d",i);
            completed=completed+1;
            if(result_fd)$fdisplay(result_fd,"%0d %0d %0d %0d %0d %0d",case_id,rsp_completed_stages,rsp_retired,rsp_muls,rsp_cycles,rsp_exec_cycles);
        end
        if(!expect_error&&!stalled_run&&!stale_run&&
           rsp_cycles!==(MUL_RADIX4?34:2)+rsp_exec_cycles+40)
            $fatal(1,"ideal dataset-item availability equation case=%0d cycles=%0d exec=%0d",case_id,rsp_cycles,rsp_exec_cycles);
        held_return=now_return;
        repeat(4)begin
            @(negedge clk);req_valid=1;fetch_ready=1;cache_req_ready=1;
            fetch_rsp_valid=1;fetch_rsp_tag=fetch_tag^32'h80000000;fetch_rsp_error=1;
            cache_rsp_valid=1;cache_rsp_tag=cache_req_tag^32'h80000000;cache_rsp_error=1;
            #1;if(req_ready||fetch_valid||cache_req_valid||!rsp_valid||now_return!==held_return)
                $fatal(1,"held return/replacement changed");
            @(posedge clk);#1;
            if(commit_valid||stage_valid||!rsp_valid||now_return!==held_return)$fatal(1,"held terminal metadata changed");
        end
        total_stages=total_stages+stages_done;total_retired=total_retired+commits;total_muls=total_muls+muls;
        total_cycles=total_cycles+rsp_cycles;total_exec_cycles=total_exec_cycles+rsp_exec_cycles;
        total_fetch_stalls=total_fetch_stalls+fetch_stalls;total_cache_stalls=total_cache_stalls+cache_stalls;
        @(negedge clk);req_valid=0;fetch_rsp_valid=0;cache_rsp_valid=0;rsp_ready=1;
        @(posedge clk);#1;rsp_ready=0;
        if(rsp_valid||commit_valid||stage_valid||fetch_valid||cache_req_valid)$fatal(1,"return consumption did not serialize admission");
        if(!req_ready&&!generation_exhausted)$fatal(1,"idle readiness lost");
    end endtask

    task run_normal;begin
        fault_service=0;fault_kind=0;
        start_request(packed_counts,packed_addresses);finish_request(0,0,0,0);
    end endtask

    task quiescent_reset;begin
        @(negedge clk);rst=1;req_valid=0;rsp_ready=0;fetch_rsp_valid=0;cache_rsp_valid=0;
        @(posedge clk);#1;
        @(negedge clk);rst=0;previous_cache_tag=0;previous_fetch_tag=0;replay_fetch_tag=0;replay_cache_tag=0;
        f_pending=0;c_pending=0;f_held=0;c_held=0;
        #1;if(!req_ready||generation_exhausted||rsp_valid||fetch_valid||cache_req_valid||commit_valid||stage_valid)
            $fatal(1,"quiescent reset state");
    end endtask

    task idle_stale;begin
        @(negedge clk);fetch_rsp_valid=1;fetch_rsp_tag=32'hdead1173;fetch_rsp_error=1;
        cache_rsp_valid=1;cache_rsp_tag=32'hbeef1173;cache_rsp_error=1;
        #1;if(!fetch_rsp_ready||!cache_rsp_ready||fetch_valid||cache_req_valid||rsp_valid||commit_valid||stage_valid)
            $fatal(1,"idle stale drain readiness");
        @(posedge clk);#1;
        if(phase!=0||rsp_valid||commit_valid||stage_valid)$fatal(1,"idle stale changed state");
        stale_packets=stale_packets+2;
        @(negedge clk);fetch_rsp_valid=0;cache_rsp_valid=0;
    end endtask

    task early_fetch;
        integer i,slot;
        reg [59:0] accepted;
    begin
        while(!fetch_valid)begin
            if(rsp_valid)$fatal(1,"nonempty early-fetch target not reached");
            step;
        end
        accepted=now_fetch;slot=fetch_program*512+fetch_pc;
        if(fetch_program!=0||fetch_pc!=0||fetch_epoch!==owned_epoch||fetch_requests!=0)
            $fatal(1,"early fetch identity/ordering mismatch");
        if(fetch_tag[15:0]!==owned_tag||fetch_tag[31:16]==0||fetch_tag==previous_fetch_tag)
            $fatal(1,"early fetch generation/caller identity reused");
        for(i=0;i<3;i=i+1)begin
            @(negedge clk);fetch_ready=0;fetch_rsp_valid=1;fetch_rsp_tag=fetch_tag;
            fetch_rsp_epoch=fetch_epoch;fetch_rsp_program=fetch_program;fetch_rsp_pc=fetch_pc;
            fetch_rsp_instruction=programs[slot];fetch_rsp_error=0;fetch_rsp_rcp_valid=rcp_valid[slot];
            fetch_rsp_rcp_index=rcp_index[slot];fetch_rsp_rcp_value=reciprocals[slot];
            cache_rsp_valid=0;
            #1;if(fetch_rsp_ready||!fetch_valid||now_fetch!==accepted)$fatal(1,"early current instruction response consumed");
            @(posedge clk);#1;run_ticks=run_ticks+1;fetch_stalls=fetch_stalls+1;observe;
            if(commit_valid||stage_valid||rsp_valid)$fatal(1,"early fetch advanced execution");
        end
        @(negedge clk);fetch_ready=1;
        #1;if(fetch_rsp_ready||!fetch_valid||now_fetch!==accepted)$fatal(1,"current response consumed on fetch accept edge");
        @(posedge clk);
        f_pending=1;f_program=fetch_program;f_pc=fetch_pc;f_tag=fetch_tag;f_epoch=fetch_epoch;
        fetch_tags[fetch_program]=fetch_tag;previous_fetch_tag=fetch_tag;fetches_by_stage[fetch_program]=fetches_by_stage[fetch_program]+1;
        // Preserve the very same held matching packet through its eventual
        // response handshake; stale traffic starts only after that transfer.
        fetch_requests=fetch_requests+1;f_delay=0;f_stale=0;f_wait=0;f_held=0;
        #1;run_ticks=run_ticks+1;observe;
        step;
        if(f_pending||fetch_responses!=1)$fatal(1,"held early instruction did not transfer on first legal response edge");
    end endtask

    task early_cache;
        integer i;
        reg [72:0] accepted;
        reg [511:0] actual_line;
    begin
        while(!cache_req_valid)begin
            if(rsp_valid)$fatal(1,"early-cache target not reached");
            step;
        end
        accepted=now_cache;read_cache_line(cache_req_index,actual_line);
        if(cache_req_program!=0||cache_req_epoch!==owned_epoch||cache_req_index!==cache_indices[0]||
           actual_line!==cache_lines[0]||cache_requests!=0||commits_by_stage[0]!=counts[0])
            $fatal(1,"early cache native identity/order mismatch");
        for(i=0;i<3;i=i+1)begin
            @(negedge clk);cache_req_ready=0;cache_rsp_valid=1;cache_rsp_tag=cache_req_tag;
            cache_rsp_epoch=cache_req_epoch;cache_rsp_program=cache_req_program;cache_rsp_index=cache_req_index;
            cache_rsp_data=actual_line;cache_rsp_error=0;fetch_rsp_valid=0;
            #1;if(cache_rsp_ready||!cache_req_valid||now_cache!==accepted)$fatal(1,"early current cache response consumed");
            @(posedge clk);#1;run_ticks=run_ticks+1;cache_stalls=cache_stalls+1;observe;
            if(stage_valid||rsp_valid)$fatal(1,"early cache advanced XOR");
        end
        @(negedge clk);cache_req_ready=1;
        #1;if(cache_rsp_ready||!cache_req_valid||now_cache!==accepted)$fatal(1,"current cache response consumed on request accept edge");
        @(posedge clk);
        c_pending=1;c_program=cache_req_program;c_tag=cache_req_tag;c_epoch=cache_req_epoch;c_index=cache_req_index;
        c_payload=actual_line;cache_requests=cache_requests+1;c_delay=0;c_stale=0;c_wait=0;c_held=0;
        run_cache_tag=cache_req_tag;
        if(run_cache_tag[31:16]==0||run_cache_tag[15:0]!==owned_tag||run_cache_tag==previous_cache_tag)
            $fatal(1,"early-cache outer identity reused");
        previous_cache_tag=run_cache_tag;
        #1;run_ticks=run_ticks+1;observe;
        step;
        if(c_pending||cache_responses!=1)$fatal(1,"held early cache line did not transfer on first legal response edge");
    end endtask

    task malformed_cases;
        integer stage,k;
        reg [79:0] bad_counts;
        reg [63:0] bad_addresses;
    begin
        held_run=1;stalled_run=0;stale_run=0;
        for(stage=0;stage<=7;stage=stage+7)begin
            fault_stage=stage;fault_pc=counts[stage]-1;
            if(fault_pc<0)$fatal(1,"malformed mode requires nonempty control programs");
            fault_service=1;
            for(k=1;k<=5;k=k+1)begin
                fault_kind=k;start_request(packed_counts,packed_addresses);finish_request(1,stage,fault_pc,0);
            end
            fault_service=2;
            for(k=1;k<=4;k=k+1)begin
                fault_kind=k;start_request(packed_counts,packed_addresses);finish_request(1,stage,0,0);
            end
            fault_service=0;fault_kind=0;
            bad_counts=packed_counts;bad_counts[stage*10+:10]=513;
            start_request(bad_counts,packed_addresses);finish_request(1,stage,0,1);
            bad_addresses=packed_addresses;bad_addresses[stage*8+:8]=8;
            start_request(packed_counts,bad_addresses);finish_request(1,stage,0,1);
        end
        held_run=0;run_normal;
    end endtask

    task alternate_control_case;
        integer fd,scan,next_id,next_cache,next_rcps;
        reg [63:0] next_item,next_addresses;
        reg [79:0] next_counts;
        reg [511:0] next_final;
        reg found;
    begin
        path=$sformatf("%s/cases-control.hex",directory);fd=$fopen(path,"r");
        if(!fd)$fatal(1,"control case list missing");
        found=0;
        scan=$fscanf(fd,"%d %d %h %h %h %h %h\n",next_id,next_cache,next_item,next_rcps,next_counts,next_addresses,next_final);
        while(scan==7&&!found)begin
            if(next_id!=case_id&&next_item!=item_number)found=1;
            else scan=$fscanf(fd,"%d %d %h %h %h %h %h\n",next_id,next_cache,next_item,next_rcps,next_counts,next_addresses,next_final);
        end
        $fclose(fd);if(!found)$fatal(1,"recovery needs distinct native control item");
        case_id=next_id;cache_id=next_cache;item_number=next_item;global_rcp_count=next_rcps;
        packed_counts=next_counts;packed_addresses=next_addresses;final_r=next_final;load_case;
    end endtask

    task abort_now;
        input integer use_reset,recover;
        integer i;
    begin
        aborted_retired=aborted_retired+commits;aborted_muls=aborted_muls+muls;
        aborted_stages=aborted_stages+stages_done;aborted_cycles=aborted_cycles+run_ticks;
        replay_fetch_tag=fetch_tag;replay_cache_tag=cache_req_tag;
        @(negedge clk);if(use_reset)rst=1;else cancel=1;
        req_valid=1;rsp_ready=1;fetch_ready=1;cache_req_ready=1;
        fetch_rsp_valid=1;fetch_rsp_tag=replay_fetch_tag;cache_rsp_valid=1;cache_rsp_tag=replay_cache_tag;
        #1;if(req_ready||fetch_valid||cache_req_valid||fetch_rsp_ready||cache_rsp_ready||rsp_valid||commit_valid||stage_valid)
            $fatal(1,"abort did not suppress transfers before edge");
        @(posedge clk);#1;
        if(req_ready||fetch_valid||cache_req_valid||fetch_rsp_ready||cache_rsp_ready||rsp_valid||commit_valid||stage_valid)
            $fatal(1,"abort did not suppress transfers at edge");
        @(negedge clk);rst=0;cancel=0;req_valid=0;rsp_ready=0;fetch_rsp_valid=0;cache_rsp_valid=0;
        f_pending=0;c_pending=0;f_held=0;c_held=0;
        if(use_reset)begin previous_cache_tag=0;previous_fetch_tag=0;replay_fetch_tag=0;replay_cache_tag=0;end
        for(i=0;i<40;i=i+1)begin
            @(posedge clk);#1;
            if(phase!=0||rsp_valid||commit_valid||stage_valid||fetch_valid||cache_req_valid)
                $fatal(1,"aborted work survived");
        end
        aborts=aborts+1;
        if(recover)begin
            owned_epoch=owned_epoch+16'b1;alternate_control_case;
            stale_run=!use_reset;run_normal;stale_run=0;replay_fetch_tag=0;replay_cache_tag=0;
        end
    end endtask

    task abort_modes;
        input integer use_reset;
        integer target,offset;
    begin
        fault_service=0;fault_kind=0;stalled_run=0;held_run=0;stale_run=0;
        for(target=1;target<=8;target=target+1)begin
            start_request(packed_counts,packed_addresses);
            while(phase!=target)begin
                if(rsp_valid)$fatal(1,"abort phase unreachable target=%0d",target);
                step;
            end
            abort_now(use_reset,1);
        end
        if(MUL_RADIX4)for(offset=16;offset<=32;offset=offset+16)begin
            start_request(packed_counts,packed_addresses);
            while(phase!=2)step;
            repeat(offset)begin
                if(phase!=2)$fatal(1,"seed multiplier abort offset escaped");
                step;
            end
            abort_now(use_reset,1);
        end
        // Delay the two external service requests/responses to cancel their
        // genuinely outstanding transactions, not only the outer EXEC_WAIT.
        for(target=0;target<4;target=target+1)begin
            stalled_run=1;start_request(packed_counts,packed_addresses);
            if(target==0)begin while(!fetch_valid)step;end
            if(target==1)begin while(!f_pending)step;end
            if(target==2)begin while(!cache_req_valid)step;end
            if(target==3)begin while(!c_pending)step;end
            abort_now(use_reset,1);
        end
        stalled_run=0;
        // The short native control program starts with a real multiply. Abort
        // after its accepted instruction, through the iterative multiplier.
        if(MUL_RADIX4)for(target=0;target<4;target=target+1)begin
            offset=target==3?34:target*16;
            start_request(packed_counts,packed_addresses);
            while(fetch_responses==0)step;
            if(!multiply_opcode(programs[0][7:0]))$fatal(1,"multiply abort control fixture must start with multiply");
            repeat(offset)begin
                if(phase!=4||commit_valid)$fatal(1,"multiply abort target escaped before offset=%0d",offset);
                step;
            end
            abort_now(use_reset,1);
        end
    end endtask

    task exhaust_core_generations;
        integer i;
    begin
        for(i=0;i<8;i=i+1)if(counts[i]!=0)$fatal(1,"core exhaustion requires full eight-stage empty native fixture");
        quiescent_reset;fault_service=0;stalled_run=0;stale_run=0;held_run=0;
        // All public transfers; no force, deposit, parameter truncation or
        // hierarchical generation injection. 8190*8 + 7 + 8 = 65535.
        for(i=0;i<8190;i=i+1)begin
            if(generation_exhausted||!req_ready)$fatal(1,"premature eight-program budget exhaustion item=%0d",i);
            run_normal;
        end
        start_request(packed_counts,packed_addresses);
        while(stages_done<7)step;
        if(phase!=3||rsp_valid)$fatal(1,"seven-stage cancel missed last legal admission boundary");
        abort_now(0,0);
        if(!req_ready||generation_exhausted)$fatal(1,"65527 accepted programs must leave eight legal slots");
        // Last legal item must finish even when exhaustion asserts midway.
        run_normal;
        if(!generation_exhausted||req_ready)$fatal(1,"core generations wrapped or admission failed to close");
        repeat(4)begin
            @(negedge clk);req_valid=1;
            @(posedge clk);#1;
            if(req_ready||rsp_valid||fetch_valid||cache_req_valid||commit_valid||stage_valid)$fatal(1,"exhausted core admitted work");
        end
        @(negedge clk);req_valid=0;cancel=1;@(posedge clk);#1;@(negedge clk);cancel=0;
        if(req_ready||!generation_exhausted)$fatal(1,"cancel recycled executor generations");
        quiescent_reset;run_normal;
    end endtask

    task exhaust_outer_generations;
        integer i;
        reg [79:0] invalid_counts;
    begin
        quiescent_reset;fault_service=0;stalled_run=0;stale_run=0;held_run=0;
        invalid_counts=packed_counts;invalid_counts[9:0]=513;
        for(i=1;i<65535;i=i+1)begin
            start_request(invalid_counts,packed_addresses);
            finish_request(1,0,0,1);
            if(generation_exhausted)$fatal(1,"premature outer exhaustion iteration=%0d",i);
        end
        // A real eight-stage native result occupies the final outer identity.
        run_normal;
        if(!generation_exhausted||req_ready)$fatal(1,"outer identity wrapped");
        @(negedge clk);cancel=1;@(posedge clk);#1;@(negedge clk);cancel=0;
        if(req_ready||!generation_exhausted)$fatal(1,"cancel recycled outer generations");
        quiescent_reset;run_normal;
    end endtask

    initial begin
        if(!$value$plusargs("DIR=%s",directory))$fatal(1,"missing DIR");
        if(!$value$plusargs("CASES=%s",case_file))case_file="cases.hex";
        if(!$value$plusargs("MODE=%s",mode))mode="corpus";
        if($value$plusargs("RESULTS=%s",result_path))begin
            result_fd=$fopen(result_path,"w");if(!result_fd)$fatal(1,"cannot create RESULTS");
        end else result_fd=0;
        if(mode!="corpus"&&mode!="stalled"&&mode!="held"&&mode!="stale"&&mode!="malformed"&&
           mode!="cancel"&&mode!="reset"&&mode!="exhaustion"&&mode!="outer-exhaustion")$fatal(1,"unknown MODE");
        path=$sformatf("%s/%s",directory,case_file);case_fd=$fopen(path,"r");
        if(!case_fd)$fatal(1,"cannot open native case list");
        repeat(2)begin @(posedge clk);#1;end
        @(negedge clk);rst=0;#1;
        if(!req_ready||rsp_valid||fetch_valid||cache_req_valid||commit_valid||stage_valid)$fatal(1,"initial reset state");
        read_status=$fscanf(case_fd,"%d %d %h %h %h %h %h\n",case_id,cache_id,item_number,global_rcp_count,packed_counts,packed_addresses,final_r);
        while(read_status==7)begin
            load_case;
            stalled_run=mode=="stalled";held_run=mode=="held";stale_run=mode=="stale";
            if(mode=="malformed")malformed_cases;
            else if(mode=="cancel"||mode=="reset")abort_modes(mode=="reset");
            else if(mode=="exhaustion")exhaust_core_generations;
            else if(mode=="outer-exhaustion")exhaust_outer_generations;
            else if(mode=="stale")begin
                idle_stale;fault_service=0;start_request(packed_counts,packed_addresses);
                if(counts[0]!=0)early_fetch;
                early_cache;finish_request(0,0,0,0);
            end else run_normal;
            if(mode=="malformed"||mode=="cancel"||mode=="reset"||mode=="exhaustion"||mode=="outer-exhaustion")read_status=0;
            else read_status=$fscanf(case_fd,"%d %d %h %h %h %h %h\n",case_id,cache_id,item_number,global_rcp_count,packed_counts,packed_addresses,final_r);
        end
        $fclose(case_fd);if(cache_fd)$fclose(cache_fd);if(result_fd)$fclose(result_fd);
        if(total_items==0)$fatal(1,"no native dataset items executed");
        $display("PASS dataset_item mode=%0s cases=%0d completed=%0d stages=%0d retired=%0d muls=%0d cycles=%0d exec_cycles=%0d errors=%0d aborts=%0d stale=%0d fetch_stalls=%0d cache_stalls=%0d aborted_retired=%0d aborted_muls=%0d aborted_stages=%0d aborted_cycles=%0d",
            mode,total_items,completed,total_stages,total_retired,total_muls,total_cycles,total_exec_cycles,errors,aborts,stale_packets,total_fetch_stalls,total_cache_stalls,
            aborted_retired,aborted_muls,aborted_stages,aborted_cycles);
        $finish;
    end
endmodule
