// SPDX-License-Identifier: BSD-3-Clause
// New namespace protocol tests. Retained native gold is assertion-only.
`timescale 1ns/1ps
module tb_dataset_capacity #(parameter integer ITEMS_PER_BATCH=1,MUL_RADIX4=1,SESSION_BITS=4);
    reg clk=0,rst=1,cancel=0; always #5 clk=~clk;
    reg batch_valid=0,batch_end=0;
    wire batch_ready,batch_active,generation_exhausted;
    reg [15:0] batch_generation=0,image_epoch=0;
    reg [79:0] counts=0; reg [63:0] address_regs=0;
    reg [31:0] rcp_count=0;
    reg ds_req_valid=0,ds_rsp_ready=0;
    wire ds_req_ready,ds_rsp_valid,ds_rsp_error;
    reg [63:0] ds_req_addr=0; reg [31:0] ds_req_tag=0;
    wire [31:0] ds_rsp_tag; wire [511:0] ds_rsp_data;
    wire [31:0] items_reserved,items_remaining;
    wire [63:0] items_requested,items_completed,ds_requests,ds_responses;
    wire [1:0] phase; wire [3:0] item_phase;

    wire cache_req_valid,cache_rsp_ready;
    reg cache_req_ready=0,cache_rsp_valid=0,cache_rsp_error=0;
    wire [63:0] cache_req_tag; wire [15:0] cache_req_epoch;
    wire [2:0] cache_req_program; wire [21:0] cache_req_index;
    reg [63:0] cache_rsp_tag=0; reg [15:0] cache_rsp_epoch=0;
    reg [2:0] cache_rsp_program=0; reg [21:0] cache_rsp_index=0;
    reg [511:0] cache_rsp_data=0;
    wire fetch_valid,fetch_rsp_ready;
    reg fetch_ready=0,fetch_rsp_valid=0,fetch_rsp_error=0,fetch_rsp_rcp_valid=0;
    wire [63:0] fetch_tag; wire [15:0] fetch_epoch;
    wire [2:0] fetch_program; wire [8:0] fetch_pc;
    reg [63:0] fetch_rsp_tag=0;reg [31:0] fetch_rsp_rcp_index=0;
    reg [15:0] fetch_rsp_epoch=0;
    reg [2:0] fetch_rsp_program=0; reg [8:0] fetch_rsp_pc=0;
    reg [63:0] fetch_rsp_instruction=0,fetch_rsp_rcp_value=0;

    wire item_req_valid,item_req_ready,item_rsp_valid,item_rsp_ready,item_rsp_error;
    wire [15:0] item_req_tag,item_req_epoch,item_rsp_tag,item_rsp_epoch;
    wire [63:0] item_req_item;
    wire [511:0] item_rsp_data;
    wire [2:0] item_rsp_error_stage; wire [8:0] item_rsp_error_pc;
    wire [3:0] item_rsp_completed_stages;
    wire [12:0] item_rsp_retired,item_rsp_muls;
    wire [63:0] item_rsp_cycles,item_rsp_exec_cycles,item_rsp_core_cycles;
    wire [1:0] item_session_phase;wire [31:0] item_namespace,item_sessions_used;
    wire item_commit_valid,item_stage_valid;
    wire [2:0] item_commit_program,item_stage_program;
    wire [8:0] item_commit_pc; wire [7:0] item_commit_opcode;
    wire [511:0] item_commit_r,item_stage_r;
    wire [21:0] item_stage_cache_index;
    wire [63:0] item_stage_selected,item_stage_program_cycles;

`ifdef DATASET_CAPACITY_NETLIST
    randomx_dataset_capacity_service dut(
`else
    randomx_dataset_capacity_service #(.ITEMS_PER_BATCH(ITEMS_PER_BATCH),.MUL_RADIX4(MUL_RADIX4),.SESSION_BITS(SESSION_BITS)) dut(
`endif
        .clk(clk),.rst(rst),.cancel(cancel),
        .batch_valid(batch_valid),.batch_ready(batch_ready),.batch_end(batch_end),
        .batch_generation(batch_generation),.image_epoch(image_epoch),
        .counts(counts),.address_regs(address_regs),.rcp_count(rcp_count),
        .batch_active(batch_active),.generation_exhausted(generation_exhausted),
        .items_reserved(items_reserved),.items_remaining(items_remaining),
        .items_requested(items_requested),.items_completed(items_completed),
        .ds_requests(ds_requests),.ds_responses(ds_responses),.phase(phase),.item_phase(item_phase),
        .ds_req_valid(ds_req_valid),.ds_req_ready(ds_req_ready),.ds_req_addr(ds_req_addr),.ds_req_tag(ds_req_tag),
        .ds_rsp_valid(ds_rsp_valid),.ds_rsp_ready(ds_rsp_ready),.ds_rsp_tag(ds_rsp_tag),
        .ds_rsp_data(ds_rsp_data),.ds_rsp_error(ds_rsp_error),
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
        .item_req_valid(item_req_valid),.item_req_ready(item_req_ready),.item_req_tag(item_req_tag),
        .item_req_epoch(item_req_epoch),.item_req_item(item_req_item),
        .item_rsp_valid(item_rsp_valid),.item_rsp_ready(item_rsp_ready),.item_rsp_tag(item_rsp_tag),
        .item_rsp_epoch(item_rsp_epoch),.item_rsp_data(item_rsp_data),.item_rsp_error(item_rsp_error),
        .item_rsp_error_stage(item_rsp_error_stage),.item_rsp_error_pc(item_rsp_error_pc),
        .item_rsp_completed_stages(item_rsp_completed_stages),.item_rsp_retired(item_rsp_retired),
        .item_rsp_muls(item_rsp_muls),.item_rsp_cycles(item_rsp_cycles),.item_rsp_exec_cycles(item_rsp_exec_cycles),
        .item_rsp_core_cycles(item_rsp_core_cycles),.item_session_phase(item_session_phase),
        .item_namespace(item_namespace),.item_sessions_used(item_sessions_used),
        .item_commit_valid(item_commit_valid),.item_commit_program(item_commit_program),
        .item_commit_pc(item_commit_pc),.item_commit_opcode(item_commit_opcode),.item_commit_r(item_commit_r),
        .item_stage_valid(item_stage_valid),.item_stage_program(item_stage_program),
        .item_stage_cache_index(item_stage_cache_index),.item_stage_r(item_stage_r),
        .item_stage_selected(item_stage_selected),.item_stage_program_cycles(item_stage_program_cycles)
    );


    localparam [63:0] LIMIT=(64'd1<<SESSION_BITS)-1;
    string root,outdir,mode,path;
    integer cache_fd,rows_fd,summary_fd,fd,n,i,j,k,scan,case_id,cache_id,wanted_case=0;
    reg [79:0] fixture_counts,live_counts;
    reg [63:0] fixture_addresses,fixture_item,live_addresses;
    reg [31:0] fixture_rcp;
    reg [511:0] final_gold,seed_gold;
    reg [63:0] programs[0:4095],rcps[0:4095],tmp64[0:511];
    reg rcp_valids[0:4095],tmp1[0:511];
    reg [31:0] rcp_indices[0:4095],tmp32[0:511];
    reg [511:0] step_gold[0:4095],tmp512[0:511];
    reg [21:0] gold_indices[0:7];
    reg [511:0] gold_lines[0:7],gold_pre[0:7],gold_exec[0:7],gold_xor[0:7];
    reg [63:0] gold_selected[0:7];
    reg [7:0] bytes64[0:63];
    integer protocol=1,per_stage_count[0:7],per_stage_muls[0:7];
    reg [63:0] ideal_exec=0;
    integer f_pending=0,c_pending=0,f_program=0,f_pc=0,c_program=0;
    reg [63:0] f_tag=0,c_tag=0,saved_fetch_tag=0,saved_cache_tag=0;
    reg [15:0] f_epoch=0,c_epoch=0;
    reg [21:0] c_index=0;
    reg [511:0] c_data=0;
    integer inject=0,f_replays=0,c_replays=0,f_foreign=0,c_foreign=0;
    integer fault=0,block_fetch=0,block_cache=0,fetch_delivered_mul=0;
    integer expected_fault_stage=0,descriptor_fault=0,stage_commits[0:7];
    integer f_response_held=0,c_response_held=0;
    reg [253:0] saved_f_response;reg [617:0] saved_c_response;
    wire [253:0] now_f_response={fetch_rsp_tag,fetch_rsp_epoch,fetch_rsp_program,fetch_rsp_pc,fetch_rsp_instruction,fetch_rsp_error,fetch_rsp_rcp_valid,fetch_rsp_rcp_index,fetch_rsp_rcp_value};
    wire [617:0] now_c_response={cache_rsp_tag,cache_rsp_epoch,cache_rsp_program,cache_rsp_index,cache_rsp_data,cache_rsp_error};
    integer early_cache=0,early_held_edges=0,request_stall=0,request_wait=0;
    integer reset_count=0,cancels=0,batches=0,ds_accepted=0,returned=0,successes=0,errors=0;
    integer native_checks=0,held_checks=0,stales=0,foreign_high=0,low_stales=0;
    integer stages=0,commits=0,muls=0,all_stages=0,all_commits=0,all_muls=0;
    integer native_steps_checked=0,requests_over_8191=0,programs_over_65535=0;
    reg [63:0] total_ticks=0,wait_ticks=0,availability_sum=0,core_sum=0,exec_sum=0;
    reg [63:0] reserved_model=0,sessions_model=0,requested_model=0,completed_model=0,ds_model=0,returns_model=0;
    reg [31:0] owned_tag=0,owned_namespace=0;
    reg [15:0] owned_epoch=0;
    reg [63:0] owned_address=0;
    reg request_active=0,available_seen=0;
    reg [31:0] previous_namespace=0;
    reg [63:0] program_accepts=0;
    wire signed [63:0] reported_programs=RTL_PRIVATE_OBSERVER?$signed(program_accepts):-64'sd1;
    reg [511:0] expected_stage_r,last_program_r;
    reg [544:0] held_return;
    reg [63:0] held_cycles,held_core_cycles,held_exec_cycles;
    reg f_held=0,c_held=0;
    reg [91:0] held_fetch;
    reg [104:0] held_cache;
    wire [91:0] now_fetch={fetch_tag,fetch_epoch,fetch_program,fetch_pc};
    wire [104:0] now_cache={cache_req_tag,cache_req_epoch,cache_req_program,cache_req_index};
    wire [544:0] now_return={ds_rsp_tag,ds_rsp_data,ds_rsp_error};
`ifndef DATASET_CAPACITY_NETLIST
    // RTL-only passive observer: no force, deposit or feedback assignment.
    // The accepted core is byte-exact. Mapped tests make no internal-count claim.
    always @(posedge clk)
        if(!rst&&!cancel&&dut.item.core.exec_req_valid&&dut.item.core.exec_req_ready)
            program_accepts=program_accepts+1;
    localparam integer RTL_PRIVATE_OBSERVER=1;
`else
    localparam integer RTL_PRIVATE_OBSERVER=0;
`endif
    function integer is_mul;
        input [7:0] op;
        begin is_mul=op==3||op==11||op==12||op==13;end
    endfunction

    task load_fixture;
        input integer id;
        reg [511:0] unused;
        integer r,a,b;
    begin
        wanted_case=id;path=$sformatf("%s/cases.hex",root);fd=$fopen(path,"r");
        if(!fd)$fatal(1,"retained cases index missing");
        r=0;
        while(!$feof(fd)&&r!=7)begin
            scan=$fscanf(fd,"%d %d %h %h %h %h %h\n",case_id,cache_id,fixture_item,fixture_rcp,fixture_counts,fixture_addresses,final_gold);
            if(scan==7&&case_id==wanted_case)r=7;
        end
        $fclose(fd);if(r!=7)$fatal(1,"selected retained native case missing");
        if(cache_fd)$fclose(cache_fd);
        path=$sformatf("%s/cache-%0d.bin",root,cache_id);cache_fd=$fopen(path,"rb");
        if(!cache_fd)$fatal(1,"actual cache bytes missing");
        path=$sformatf("%s/case-%03d/seed.hex",root,wanted_case);$readmemh(path,tmp512,0,0);seed_gold=tmp512[0];
        path=$sformatf("%s/case-%03d/stages.mem",root,wanted_case);fd=$fopen(path,"r");
        if(!fd)$fatal(1,"native stage assertion file missing");
        for(a=0;a<8;a=a+1)begin
            scan=$fscanf(fd,"%h %h %h %h %h %h\n",gold_indices[a],gold_lines[a],gold_pre[a],gold_exec[a],gold_xor[a],gold_selected[a]);
            if(scan!=6)$fatal(1,"native stage assertion row");
        end
        $fclose(fd);
        for(a=0;a<8;a=a+1)begin
            for(b=0;b<512;b=b+1)begin programs[a*512+b]=0;rcps[a*512+b]=0;rcp_valids[a*512+b]=0;rcp_indices[a*512+b]=0;step_gold[a*512+b]=0;end
            if(!protocol)begin
                path=$sformatf("%s/case-%03d/program-%0d.mem",root,wanted_case,a);$readmemh(path,tmp64);
                for(b=0;b<512;b=b+1)programs[a*512+b]=tmp64[b];
                path=$sformatf("%s/case-%03d/steps-%0d.mem",root,wanted_case,a);$readmemh(path,tmp512);
                for(b=0;b<512;b=b+1)step_gold[a*512+b]=tmp512[b];
                path=$sformatf("%s/case-%03d/rcp-valid-%0d.mem",root,wanted_case,a);$readmemh(path,tmp1);
                for(b=0;b<512;b=b+1)rcp_valids[a*512+b]=tmp1[b];
                path=$sformatf("%s/case-%03d/rcp-index-%0d.mem",root,wanted_case,a);$readmemh(path,tmp32);
                for(b=0;b<512;b=b+1)rcp_indices[a*512+b]=tmp32[b];
                path=$sformatf("%s/case-%03d/reciprocals-%0d.mem",root,wanted_case,a);$readmemh(path,tmp64);
                for(b=0;b<512;b=b+1)rcps[a*512+b]=tmp64[b];
            end
        end
        if(protocol)begin
            if(wanted_case!=18||fixture_counts!==80'b0||fixture_item!==0)$fatal(1,"protocol proof requires retained native empty case18");
            // Explicit derivative: native IADD_C immediate0 at stages0 and7.
            // Both are identities, so every retained native empty-stage state
            // and full final item remains the same; no gold drives a service.
            live_counts=0;live_counts[0+:10]=1;live_counts[70+:10]=1;
            live_addresses=fixture_addresses;programs[0]=64'h5;programs[7*512]=64'h5;
        end else begin live_counts=fixture_counts;live_addresses=fixture_addresses;end
        ideal_exec=0;
        for(a=0;a<8;a=a+1)begin
            per_stage_count[a]=live_counts[a*10+:10];per_stage_muls[a]=0;
            for(b=0;b<per_stage_count[a];b=b+1)begin
                if(^programs[a*512+b]===1'bx)$fatal(1,"unknown actual instruction");
                per_stage_muls[a]=per_stage_muls[a]+is_mul(programs[a*512+b][7:0]);
            end
            ideal_exec=ideal_exec+3*per_stage_count[a]+(MUL_RADIX4?34:2)*per_stage_muls[a];
        end
    end endtask

    task read_cache;
        input [21:0] index;output [511:0] data;
        integer r,a;
    begin
        r=$fseek(cache_fd,index*64,0);if(r)$fatal(1,"actual-index cache seek");
        r=$fread(bytes64,cache_fd,0,64);if(r!=64)$fatal(1,"actual-index cache short read");
        for(a=0;a<64;a=a+1)data[a*8+:8]=bytes64[a];
    end endtask

    task step;
        integer slot,prior_commits,prior_stages;
        reg [63:0] returned_wait;
    begin
        @(negedge clk);
        fetch_ready=!rst&&!cancel&&!f_pending&&(!request_stall||request_wait>=2);
        cache_req_ready=!rst&&!cancel&&!c_pending&&(!request_stall||request_wait>=2);
        fetch_rsp_valid=0;fetch_rsp_error=0;fetch_rsp_rcp_valid=0;
        cache_rsp_valid=0;cache_rsp_error=0;f_foreign=0;c_foreign=0;
        if(!rst&&!cancel)begin
            if(f_pending&&!block_fetch)begin
                slot=f_program*512+f_pc;
                fetch_rsp_valid=1;fetch_rsp_tag=f_tag;fetch_rsp_epoch=f_epoch;fetch_rsp_program=f_program;fetch_rsp_pc=f_pc;
                fetch_rsp_instruction=fault==7?64'h0000000000000003:programs[slot];
                fetch_rsp_rcp_valid=rcp_valids[slot];fetch_rsp_rcp_index=rcp_indices[slot];fetch_rsp_rcp_value=rcps[slot];
                if(f_replays)begin
                    if(f_replays==3)fetch_rsp_tag={saved_fetch_tag[63:32],f_tag[31:0]};
                    else if(f_replays==2)fetch_rsp_tag=f_tag^64'h8000000000000000;
                    else fetch_rsp_tag=f_tag^64'h0000000000010000;
                    if(f_replays!=3)begin fetch_rsp_error=1;fetch_rsp_instruction=~64'b0;end
                    else if(saved_fetch_tag[31:0]!==f_tag[31:0])$fatal(1,"old fetch packet did not have identical private bits");
                    f_foreign=f_replays;
                    if(fetch_rsp_tag==f_tag)$fatal(1,"stale-fetch test packet was current");
                end else if(fault==1)fetch_rsp_error=1;
                else if(fault==2)fetch_rsp_epoch=f_epoch^16'h8000;
            end
            if(c_pending&&!block_cache)begin
                cache_rsp_valid=1;cache_rsp_tag=c_tag;cache_rsp_epoch=c_epoch;cache_rsp_program=c_program;cache_rsp_index=c_index;cache_rsp_data=c_data;
                if(c_replays)begin
                    if(c_replays==3)cache_rsp_tag={saved_cache_tag[63:32],c_tag[31:0]};
                    else if(c_replays==2)cache_rsp_tag=c_tag^64'h8000000000000000;
                    else cache_rsp_tag=c_tag^64'h0000000000010000;
                    if(c_replays!=3)begin cache_rsp_error=1;cache_rsp_data=~512'b0;end
                    else if(saved_cache_tag[31:0]!==c_tag[31:0])$fatal(1,"old cache packet did not have identical private bits");
                    c_foreign=c_replays;
                    if(cache_rsp_tag==c_tag)$fatal(1,"stale-cache test packet was current");
                end else if(fault==3)cache_rsp_error=1;
                else if(fault==4)cache_rsp_index=c_index^22'b1;
            end
            if(early_cache&&item_session_phase!=0)begin
                cache_rsp_valid=1;cache_rsp_tag={item_namespace,16'd1,owned_tag[15:0]};
                cache_rsp_epoch=owned_epoch;cache_rsp_program=0;cache_rsp_index=fixture_item[21:0];
                read_cache(cache_rsp_index,cache_rsp_data);
            end
        end
        @(posedge clk);
        prior_commits=commits;prior_stages=stages;
        if(rst)begin reserved_model=0;sessions_model=0;requested_model=0;completed_model=0;ds_model=0;returns_model=0;previous_namespace=0;end
        else if(!cancel)begin
            if(batch_valid&&batch_ready)begin reserved_model=reserved_model+ITEMS_PER_BATCH;batches=batches+1;end
            if(ds_req_valid&&ds_req_ready)begin
                ds_model=ds_model+1;ds_accepted=ds_accepted+1;owned_tag=ds_req_tag;owned_address=ds_req_addr;
            end
            if(item_req_valid&&item_req_ready)begin
                sessions_model=sessions_model+1;requested_model=requested_model+1;owned_namespace=sessions_model[31:0];
                if(item_req_tag!==owned_tag[15:0]||item_req_epoch!==owned_epoch||item_req_item!==(owned_address>>6))$fatal(1,"captured item admission metadata");
                request_active=1;available_seen=0;wait_ticks=0;stages=0;commits=0;muls=0;
                for(k=0;k<8;k=k+1)stage_commits[k]=0;
                if(owned_namespace<=previous_namespace)$fatal(1,"namespace reused without quiescent reset");
                previous_namespace=owned_namespace;
            end else if(request_active&&!available_seen)begin
                if(ds_rsp_valid)available_seen=1;else wait_ticks=wait_ticks+1;
            end
            if(ds_rsp_valid&&ds_rsp_ready)begin
                returns_model=returns_model+1;returned=returned+1;request_active=0;
                if(!ds_rsp_error)completed_model=completed_model+1;
            end
        end
        if(!rst&&!cancel)begin
            if(f_response_held&&(!fetch_rsp_valid||now_f_response!==saved_f_response))$fatal(1,"held full64 fetch response changed");
            if(c_response_held&&(!cache_rsp_valid||now_c_response!==saved_c_response))$fatal(1,"held full64 cache response changed");
            f_response_held=fetch_rsp_valid&&!fetch_rsp_ready;saved_f_response=now_f_response;
            c_response_held=cache_rsp_valid&&!cache_rsp_ready;saved_c_response=now_c_response;
            if(f_held&&(!fetch_valid||now_fetch!==held_fetch))$fatal(1,"full64 held fetch request changed");
            if(c_held&&(!cache_req_valid||now_cache!==held_cache))$fatal(1,"full64 held cache request changed");
            f_held=fetch_valid&&!fetch_ready;held_fetch=now_fetch;c_held=cache_req_valid&&!cache_req_ready;held_cache=now_cache;
            if((fetch_valid&&!fetch_ready)||(cache_req_valid&&!cache_req_ready))request_wait=request_wait+1;
            if(item_session_phase==1&&early_cache&&cache_rsp_valid)begin
                if(cache_rsp_ready)$fatal(1,"matching namespace response consumed in LAUNCH");
                early_held_edges=early_held_edges+1;
            end
            if(fetch_rsp_valid&&fetch_rsp_ready)begin
                if(f_foreign)begin
                    stales=stales+1;if(f_foreign==2)foreign_high=foreign_high+1;if(f_foreign==1)low_stales=low_stales+1;
                    f_replays=f_replays-1;
                end else begin fetch_delivered_mul=is_mul(fetch_rsp_instruction[7:0]);f_pending=0;end
            end
            if(cache_rsp_valid&&cache_rsp_ready)begin
                if(c_foreign)begin
                    stales=stales+1;if(c_foreign==2)foreign_high=foreign_high+1;if(c_foreign==1)low_stales=low_stales+1;
                    c_replays=c_replays-1;
                end else begin c_pending=0;early_cache=0;end
            end
            if(fetch_valid&&fetch_ready)begin
                if(f_pending||fetch_tag[63:32]!==owned_namespace||fetch_epoch!==owned_epoch||fetch_program!==stages[2:0]||
                   fetch_tag[31:16]!=={13'b0,fetch_program}+16'd1||fetch_tag[15:0]!==owned_tag[15:0])$fatal(1,"fetch prefix/private identity/capture");
                f_pending=1;f_tag=fetch_tag;f_epoch=fetch_epoch;f_program=fetch_program;f_pc=fetch_pc;request_wait=0;
                f_replays=inject&&fetch_program==0?3:0;
                if(saved_fetch_tag==0)saved_fetch_tag=fetch_tag;
            end
            if(cache_req_valid&&cache_req_ready)begin
                if(c_pending||cache_req_tag[63:32]!==owned_namespace||cache_req_tag[31:16]!==16'd1||
                   cache_req_tag[15:0]!==owned_tag[15:0]||cache_req_epoch!==owned_epoch||cache_req_program!==stages[2:0]||
                   cache_req_index!==gold_indices[stages]||stage_commits[stages]!=per_stage_count[stages])$fatal(1,"cache prefix/private identity/postXOR index");
                c_pending=1;c_tag=cache_req_tag;c_epoch=cache_req_epoch;c_program=cache_req_program;c_index=cache_req_index;
                read_cache(c_index,c_data);if(c_data!==gold_lines[stages])$fatal(1,"actual cache bytes differ from retained stage identity");
                request_wait=0;c_replays=inject&&cache_req_program==0?3:0;
                if(saved_cache_tag==0)saved_cache_tag=cache_req_tag;
            end
        end
        #1;
        total_ticks=total_ticks+1;
        if(items_reserved!==reserved_model[31:0]||items_remaining!==(LIMIT-reserved_model)||
           item_sessions_used!==sessions_model[31:0]||items_requested!==requested_model||items_completed!==completed_model||
           ds_requests!==ds_model||ds_responses!==returns_model)$fatal(1,"capacity lifetime ledgers did not close");
        if(!rst&&!cancel)begin
            if(item_commit_valid)begin
                if(item_commit_program!==stages[2:0]||item_commit_pc!==stage_commits[stages][8:0]||item_commit_pc>=per_stage_count[stages]||
                   item_commit_opcode!==(fault==7?8'd3:programs[item_commit_program*512+item_commit_pc][7:0]))$fatal(1,"native commit program/PC");
                if(fault!=7)begin
                    if(protocol)expected_stage_r=gold_pre[stages];else expected_stage_r=step_gold[item_commit_program*512+item_commit_pc];
                    if(item_commit_r!==expected_stage_r)$fatal(1,"full native/identity-derived instruction state");
                    native_steps_checked=native_steps_checked+1;
                end
                stage_commits[stages]=stage_commits[stages]+1;commits=commits+1;muls=muls+is_mul(item_commit_opcode);all_commits=all_commits+1;all_muls=all_muls+is_mul(item_commit_opcode);
            end
            if(item_stage_valid)begin
                if(item_stage_program!==stages[2:0]||item_stage_cache_index!==gold_indices[stages]||
                   item_stage_r!==gold_xor[stages]||item_stage_selected!==gold_selected[stages])$fatal(1,"full eight-stage native postXOR/index/selected result");
                stages=stages+1;all_stages=all_stages+1;
            end
            if((f_foreign||c_foreign)&&(commits!=prior_commits||stages!=prior_stages))$fatal(1,"foreign response advanced instruction or XOR");
        end
        if(total_ticks>6000000)$fatal(1,"bounded capacity test deadlock");
    end endtask

    task quiescent_reset;
    begin
        if(!rst&&(batch_active||ds_rsp_valid||item_rsp_valid||fetch_valid||cache_req_valid||f_pending||c_pending))$fatal(1,"hard reset requires externally quiescent traffic");
        rst=1;cancel=0;batch_valid=0;batch_end=0;ds_req_valid=0;ds_rsp_ready=0;early_cache=0;
        f_pending=0;c_pending=0;f_held=0;c_held=0;f_response_held=0;c_response_held=0;request_active=0;inject=0;
        saved_fetch_tag=0;saved_cache_tag=0;fault=0;block_fetch=0;block_cache=0;request_stall=0;
        step;rst=0;#1;
        if(!batch_ready||item_sessions_used||items_reserved||generation_exhausted)$fatal(1,"quiescent reset failed to recycle context");
        reset_count=reset_count+1;
    end endtask
    task begin_batch;
    begin
        if(!batch_ready)$fatal(1,"whole batch reservation not ready");
        batch_valid=1;batch_generation=16'ha5d3;image_epoch=16'h4ca3;
        counts=live_counts;address_regs=live_addresses;rcp_count=fixture_rcp;owned_epoch=image_epoch;
        step;batch_valid=0;batch_generation=16'hffff;image_epoch=0;counts=~80'b0;address_regs=~64'b0;rcp_count=0;
        if(!batch_active)$fatal(1,"batch context capture lost");
    end endtask
    task end_batch;
    begin
        batch_end=1;step;batch_end=0;
        if(batch_active||ds_rsp_valid)$fatal(1,"batch end did not quiesce");
    end endtask
    task start_item;
    begin
        if(!ds_req_ready)$fatal(1,"reserved item admission not ready");
        ds_req_valid=1;ds_req_addr=fixture_item<<6;ds_req_tag=32'ha5d3cafe;ds_rsp_ready=0;
        step;ds_req_valid=0;ds_req_addr=~64'b0;ds_req_tag=~32'b0;fetch_delivered_mul=0;
    end endtask
    task finish_item;
        input integer expect_error,holds;
        integer a;
        reg [63:0] availability;
    begin
        while(!ds_rsp_valid)step;
        if(ds_rsp_tag!==owned_tag||ds_rsp_error!==expect_error[0]||f_pending||c_pending)$fatal(1,"held item terminal tag/error/pending transport");
        if(item_rsp_valid)begin
            if(item_rsp_tag!==owned_tag[15:0]||item_rsp_epoch!==owned_epoch||item_namespace!==owned_namespace||
               item_rsp_retired!==commits[12:0]||item_rsp_muls!==muls[12:0]||
               item_rsp_cycles!==item_rsp_core_cycles+64'd1||item_rsp_cycles!==wait_ticks)$fatal(1,"measured adapter/core/availability/counter closure");
        end
        if(expect_error)begin
            if(ds_rsp_data!==0||!item_rsp_error||item_rsp_error_stage!==expected_fault_stage[2:0]||item_rsp_error_pc!==0||stages)$fatal(1,"matching current error not contained before XOR");
            if(descriptor_fault&&(commits||muls||item_rsp_core_cycles||item_rsp_exec_cycles))$fatal(1,"late invalid descriptor performed private work");
            errors=errors+1;
        end else begin
            if(ds_rsp_data!==final_gold||stages!=8||item_rsp_completed_stages!=8||item_rsp_exec_cycles<ideal_exec)$fatal(1,"full native retained final item");
            if(protocol&&commits!=2)$fatal(1,"identity derivative must retire exactly two native noops");
            if(!inject&&!request_stall&&item_rsp_core_cycles!==ideal_exec+(MUL_RADIX4?74:42))$fatal(1,"ideal private item clock formula");
            availability_sum=availability_sum+item_rsp_cycles;core_sum=core_sum+item_rsp_core_cycles;exec_sum=exec_sum+item_rsp_exec_cycles;
            successes=successes+1;native_checks=native_checks+1;
        end
        $fdisplay(rows_fd,"%0d,%h,%h,%0d,%0d,%0d,%0d,%0d,%0d",owned_namespace,owned_tag,owned_address,item_rsp_cycles,item_rsp_core_cycles,item_rsp_exec_cycles,stages,commits,muls);
        held_return=now_return;held_cycles=item_rsp_cycles;held_core_cycles=item_rsp_core_cycles;held_exec_cycles=item_rsp_exec_cycles;
        for(a=0;a<holds;a=a+1)begin
            ds_req_valid=1;batch_valid=1;step;
            if(!ds_rsp_valid||now_return!==held_return||ds_req_ready||batch_ready||item_rsp_cycles!==held_cycles||
               item_rsp_core_cycles!==held_core_cycles||item_rsp_exec_cycles!==held_exec_cycles||item_stage_valid||item_commit_valid)$fatal(1,"held response or frozen clock fields changed");
            held_checks=held_checks+1;
        end
        ds_req_valid=0;batch_valid=0;ds_rsp_ready=1;step;ds_rsp_ready=0;
        if(ds_rsp_valid)$fatal(1,"result transferred twice");
    end endtask
    task abort_item;
    begin
        cancel=1;ds_req_valid=0;batch_valid=0;ds_rsp_ready=0;step;
        f_pending=0;c_pending=0;f_held=0;c_held=0;f_response_held=0;c_response_held=0;request_active=0;early_cache=0;cancel=0;#1;
        if(batch_active||ds_rsp_valid||item_rsp_valid||fetch_valid||cache_req_valid)$fatal(1,"cancel leaked abandoned work");
        cancels=cancels+1;
    end endtask

    task run_long;
        integer item_no;
    begin
        if(ITEMS_PER_BATCH!=16384||SESSION_BITS!=32||!RTL_PRIVATE_OBSERVER)$fatal(1,"long proof requires production namespace and passive RTL observer");
        quiescent_reset;begin_batch;
        for(item_no=1;item_no<=16384;item_no=item_no+1)begin
            inject=item_no==2||item_no==8192||item_no==8193||item_no==16384;
            start_item;finish_item(0,inject?2:0);
            if(item_no==8192&&program_accepts<=65535)$fatal(1,"old private-program boundary was not crossed");
            if(item_no>8191)requests_over_8191=requests_over_8191+1;
        end
        if(successes!=16384||item_sessions_used!=16384||items_requested!=16384||items_completed!=16384||
           items_reserved!=16384||ds_requests!=16384||ds_responses!=16384||all_stages!=131072||program_accepts!=131072||
           all_commits!=32768||all_muls!=0||stales!=24||foreign_high!=8||low_stales!=8)$fatal(1,"production full-batch capacity proof counts");
        programs_over_65535=program_accepts-65535;
        end_batch;
    end endtask
    task run_short;
        integer x;
        reg [63:0] reserved_before,sessions_before;
    begin
        if(ITEMS_PER_BATCH!=1||SESSION_BITS!=4)$fatal(1,"short mapped exhaustion proof requires namespace4/N1");
        quiescent_reset;
        // Fifteen actual descriptor accepts exhaust the finite namespace.
        // Errors and cancellation burn IDs; the final item must still finish.
        for(x=1;x<=15;x=x+1)begin
            inject=x==7;fault=0;block_fetch=0;block_cache=0;expected_fault_stage=0;descriptor_fault=0;
            if(x==2)begin live_counts[70+:10]=513;expected_fault_stage=7;descriptor_fault=1;end
            if(x==10)begin live_addresses[0+:8]=8;descriptor_fault=1;end
            if(x==11)begin live_addresses[56+:8]=8;expected_fault_stage=7;descriptor_fault=1;end
            if(x==12)begin live_counts[0+:10]=513;descriptor_fault=1;end
            begin_batch;
            if(descriptor_fault)begin
                // The captured invalid vector is immutable despite restoring
                // caller inputs before the child LAUNCH edge.
                live_counts=0;live_counts[0+:10]=1;live_counts[70+:10]=1;live_addresses=fixture_addresses;
                start_item;finish_item(1,2);descriptor_fault=0;expected_fault_stage=0;
            end else if(x==3)begin
                start_item;if(item_session_phase!=1)$fatal(1,"LAUNCH cancel target missed");abort_item;
            end else if(x==4)begin
                block_fetch=1;start_item;while(!f_pending)step;abort_item;block_fetch=0;
            end else if(x==5)begin
                fault=2;start_item;finish_item(1,2);fault=0;
            end else if(x==6)begin
                fault=4;start_item;finish_item(1,2);fault=0;
            end else begin
                early_cache=x==8;request_stall=x==9;
                start_item;finish_item(0,x==15?4:1);early_cache=0;request_stall=0;
            end
            if(x!=3&&x!=4)end_batch;
            if(item_sessions_used!=x||items_reserved!=x)$fatal(1,"error/cancel refunded namespace or full reservation");
        end
        if(!generation_exhausted||batch_ready||item_sessions_used!=15||items_reserved!=15||items_remaining)$fatal(1,"finite namespace did not fail closed");
        repeat(4)begin batch_valid=1;ds_req_valid=1;step;if(batch_ready||ds_req_ready||item_req_valid||item_commit_valid||item_stage_valid)$fatal(1,"exhaustion wrapped/admitted work");end
        batch_valid=0;ds_req_valid=0;cancel=1;step;cancel=0;#1;
        if(!generation_exhausted||item_sessions_used!=15||items_reserved!=15||batch_ready)$fatal(1,"cancel recycled exhausted identifiers");
        // All queues have drained. Only this explicit quiescent reset may
        // recycle the outer namespace; it is not a runtime budget bypass.
        quiescent_reset;inject=0;fault=0;begin_batch;start_item;finish_item(0,2);end_batch;
        if(item_namespace!=1||item_sessions_used!=1)$fatal(1,"quiescent reset successor not fresh");
        // A whole batch canceled before any item still consumes reservation,
        // but does not invent an accepted adapter descriptor.
        reserved_before=items_reserved;sessions_before=item_sessions_used;
        begin_batch;abort_item;
        if(items_reserved!=reserved_before+1||item_sessions_used!=sessions_before)$fatal(1,"prelaunch cancellation reservation/session separation");
        // Matching-current fetch/cache transport error bits are also errors.
        fault=1;begin_batch;start_item;finish_item(1,1);end_batch;
        fault=3;begin_batch;start_item;finish_item(1,1);end_batch;fault=0;
        // Cancel an accepted iterative multiply before any result can retire.
        fault=7;begin_batch;start_item;while(!fetch_delivered_mul)step;
        repeat(2)step;if(commits||stages)$fatal(1,"multiply cancellation target already retired");abort_item;fault=0;
        // The same caller/private IDs under a new prefix must recover.
        inject=1;begin_batch;start_item;finish_item(0,2);end_batch;inject=0;
        if(!early_held_edges||!stales||!foreign_high||!low_stales)$fatal(1,"early-held/full64-prefix/private stale coverage missing");
        if(batches!=21||ds_accepted!=20||returned!=17||successes!=9||errors!=8||cancels!=4||all_stages!=72||
           all_commits!=20||all_muls!=0||native_checks!=9||native_steps_checked!=20||held_checks!=28||
           stales!=12||foreign_high!=4||low_stales!=4||(RTL_PRIVATE_OBSERVER&&program_accepts!=78))
            $fatal(1,"bounded namespace matrix exact counts");
    end endtask

    initial begin
        if(!$value$plusargs("asset_root=%s",root)||!$value$plusargs("output=%s",outdir))$fatal(1,"asset_root and fresh output required");
        if(!$value$plusargs("MODE=%s",mode))mode="short";
        if(mode!="long"&&mode!="short"&&mode!="native")$fatal(1,"unknown MODE");
        protocol=mode!="native";
        if(!protocol)begin if(!$value$plusargs("CASE=%d",wanted_case))wanted_case=0;end else wanted_case=18;
        path=$sformatf("%s/items.csv",outdir);rows_fd=$fopen(path,"w");if(!rows_fd)$fatal(1,"item ledger open");
        $fdisplay(rows_fd,"namespace,tag,address,session_cycles,private_core_cycles,executor_cycles,stages,retired,muls");
        load_fixture(wanted_case);
        if(mode=="long")run_long;
        else if(mode=="short")run_short;
        else begin quiescent_reset;begin_batch;start_item;finish_item(0,4);end_batch;end
        $fclose(cache_fd);$fclose(rows_fd);
        path=$sformatf("%s/capacity-ledger.json",outdir);summary_fd=$fopen(path,"w");if(!summary_fd)$fatal(1,"summary open");
        $fdisplay(summary_fd,"{\"schema\":\"openrx.dataset-capacity.protocol.v1\",\"mode\":\"%s\",\"session_bits\":%0d,\"items_per_batch\":%0d,\"retained_case\":%0d,\"identity_derivative\":%0d,",mode,SESSION_BITS,ITEMS_PER_BATCH,wanted_case,protocol);
        $fdisplay(summary_fd,"\"total_testbench_clocks\":%0d,\"rtl_private_observer\":%0d,\"private_program_accepts\":%0d,\"successes\":%0d,\"errors\":%0d,\"cancellations\":%0d,\"batch_accepts\":%0d,\"ds_accepts\":%0d,\"returns\":%0d,",total_ticks,RTL_PRIVATE_OBSERVER,reported_programs,successes,errors,cancels,batches,ds_accepted,returned);
        $fdisplay(summary_fd,"\"stages\":%0d,\"retirements\":%0d,\"muls\":%0d,\"native_final_checks\":%0d,\"native_instruction_checks\":%0d,\"held_checks\":%0d,\"launch_held_edges\":%0d,\"stale_packets\":%0d,\"foreign_topbit_packets\":%0d,\"private_stale_packets\":%0d,",all_stages,all_commits,all_muls,native_checks,native_steps_checked,held_checks,early_held_edges,stales,foreign_high,low_stales);
        $fdisplay(summary_fd,"\"session_availability_clocks\":%0d,\"private_core_clocks\":%0d,\"executor_clocks\":%0d,\"quiescent_resets\":%0d,\"items_over_old8191\":%0d,\"programs_over_old65535\":%0d,\"full_hash_execution\":false}",availability_sum,core_sum,exec_sum,reset_count,requests_over_8191,programs_over_65535);
        $fclose(summary_fd);
        $display("PASS dataset_capacity mode=%s session_bits=%0d items_per_batch=%0d successes=%0d errors=%0d cancellations=%0d stages=%0d retired=%0d rtl_private_observer=%0d private_program_accepts=%0d stale_packets=%0d total_clocks=%0d full_hash_execution=0",mode,SESSION_BITS,ITEMS_PER_BATCH,successes,errors,cancels,all_stages,all_commits,RTL_PRIVATE_OBSERVER,reported_programs,stales,total_ticks);
        $finish;
    end
endmodule


`ifndef DATASET_CAPACITY_NETLIST
// Tiny RTL-only caller-poison capture proof at actual child PUBLIC ports.
module tb_dataset_capacity_capture #(parameter integer MUL_RADIX4=1);
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
    wire [63:0] rsp_cycles,rsp_exec_cycles,rsp_core_cycles;
    wire [1:0] session_phase;wire [31:0] session_namespace,sessions_used;

    wire fetch_valid,fetch_rsp_ready;
    reg fetch_ready=0,fetch_rsp_valid=0,fetch_rsp_error=0,fetch_rsp_rcp_valid=0;
    wire [63:0] fetch_tag;wire [15:0] fetch_epoch;
    wire [2:0] fetch_program;wire [8:0] fetch_pc;
    reg [63:0] fetch_rsp_tag=0;reg [31:0] fetch_rsp_rcp_index=0;
    reg [15:0] fetch_rsp_epoch=0;reg [2:0] fetch_rsp_program=0;reg [8:0] fetch_rsp_pc=0;
    reg [63:0] fetch_rsp_instruction=0,fetch_rsp_rcp_value=0;
    wire cache_req_valid,cache_rsp_ready;
    reg cache_req_ready=0,cache_rsp_valid=0,cache_rsp_error=0;
    wire [63:0] cache_req_tag;wire [15:0] cache_req_epoch;
    wire [2:0] cache_req_program;wire [21:0] cache_req_index;
    reg [63:0] cache_rsp_tag=0;reg [15:0] cache_rsp_epoch=0;
    reg [2:0] cache_rsp_program=0;reg [21:0] cache_rsp_index=0;
    reg [511:0] cache_rsp_data=0;
    wire commit_valid,stage_valid;
    wire [2:0] commit_program,stage_program;
    wire [8:0] commit_pc;wire [7:0] commit_opcode;
    wire [511:0] commit_r,stage_r;
    wire [21:0] stage_cache_index;
    wire [63:0] stage_selected,stage_program_cycles;
    randomx_dataset_item_session #(.MUL_RADIX4(MUL_RADIX4),.SESSION_BITS(4)) dut(
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
        .phase(phase),.generation_exhausted(generation_exhausted),
        .session_phase(session_phase),.session_namespace(session_namespace),.sessions_used(sessions_used),.rsp_core_cycles(rsp_core_cycles)
    );


    integer captures=0,poisons=0,ticks=0,x,fd;
    reg [15:0] expected_tag,expected_epoch;
    reg [63:0] expected_item,expected_addresses;
    reg [79:0] expected_counts;
    reg [31:0] expected_rcp;
    reg [2:0] expected_error_stage;
    string output_directory,output_path;
    always @(posedge clk)begin
        if(!rst&&!cancel&&dut.core.req_valid&&dut.core.req_ready)begin
            if(dut.core.req_tag!==expected_tag||dut.core.req_epoch!==expected_epoch||
               dut.core.req_item!==expected_item||dut.core.req_counts!==expected_counts||
               dut.core.req_address_regs!==expected_addresses||dut.core.req_rcp_count!==expected_rcp)
                $fatal(1,"actual child PUBLIC request did not preserve all accepted caller fields");
            captures=captures+1;
        end
    end
    task cycle;
    begin
        @(negedge clk);@(posedge clk);#1;ticks=ticks+1;
        if(fetch_valid||cache_req_valid||commit_valid||stage_valid)$fatal(1,"late invalid descriptor emitted work");
        if(ticks>=100)$fatal(1,"capture proof exceeded bounded clocks");
    end endtask
    initial begin
        if(!$value$plusargs("output=%s",output_directory))$fatal(1,"capture fresh output required");
        rst=1;cycle;rst=0;#1;
        for(x=0;x<4;x=x+1)begin
            if(!req_ready)$fatal(1,"capture adapter not idle");
            expected_tag=16'hca10+x;expected_epoch=16'h8fd0+x;
            expected_item=64'hfffffffffffffffe^x;expected_rcp=32'hdead0000+x;
            expected_counts=0;expected_addresses=64'h0706050403020100;
            expected_error_stage=(x==1||x==3)?7:0;
            if(x<2)expected_counts[expected_error_stage*10+:10]=513;
            else expected_addresses[expected_error_stage*8+:8]=8;
            req_valid=1;rsp_ready=0;req_tag=expected_tag;req_epoch=expected_epoch;req_item=expected_item;
            req_counts=expected_counts;req_address_regs=expected_addresses;req_rcp_count=expected_rcp;
            cycle;
            if(session_phase!=1||session_namespace!==x+1||sessions_used!==x+1)$fatal(1,"capture LAUNCH/namespace");
            // Poison every live caller field before the actual child boundary.
            req_valid=0;req_tag=~expected_tag;req_epoch=~expected_epoch;req_item=~expected_item;
            req_counts=~expected_counts;req_address_regs=~expected_addresses;req_rcp_count=~expected_rcp;poisons=poisons+1;
            while(!rsp_valid)cycle;
            if(!rsp_error||rsp_error_stage!==expected_error_stage||rsp_error_pc!==0||rsp_tag!==expected_tag||
               rsp_epoch!==expected_epoch||rsp_data!==0||rsp_completed_stages||rsp_retired||rsp_muls||
               rsp_core_cycles||rsp_exec_cycles||rsp_cycles!==64'd1)$fatal(1,"captured malformed descriptor classification/clock metadata");
            repeat(2)begin cycle;if(!rsp_valid||!rsp_error||rsp_error_stage!==expected_error_stage||rsp_tag!==expected_tag||rsp_epoch!==expected_epoch||rsp_cycles!==1)$fatal(1,"held captured descriptor error changed");end
            rsp_ready=1;cycle;rsp_ready=0;
        end
        if(captures!=4||poisons!=4||sessions_used!=4)$fatal(1,"actual child capture count");
        output_path=$sformatf("%s/capture-ledger.json",output_directory);fd=$fopen(output_path,"w");if(!fd)$fatal(1,"capture output open");
        $fdisplay(fd,"{\"schema\":\"openrx.dataset-capacity.capture.v1\",\"actual_child_public_captures\":4,\"caller_poisoned_before_launch\":4,\"fields_checked_each_capture\":6,\"first_last_count_and_address_errors\":4,\"total_testbench_clocks\":%0d,\"rtl_only_passive_observer\":true,\"native_workloads_repeated\":false}",ticks);$fclose(fd);
        $display("PASS dataset_capacity_capture actual_child_public_captures=4 caller_poisoned_before_launch=4 first_last_count_and_address_errors=4 total_clocks=%0d rtl_only_passive_observer=1",ticks);
        $finish;
    end
endmodule
`endif
