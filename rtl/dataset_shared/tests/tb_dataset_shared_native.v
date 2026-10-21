// SPDX-License-Identifier: BSD-3-Clause
// Bounded two-client native item differential. Expected native states are
// assertion-only; providers use immutable prepared words and DUT-indexed cache.
module tb_dataset_shared_native #(parameter integer MUL_RADIX4=1, SESSION_BITS=2);
    reg clk=0, rst=1;
    always #5 clk=~clk;
    reg [1:0] client_cancel=0, req_valid=0, rsp_ready=0;
    wire [1:0] req_ready, rsp_valid, rsp_error, generation_exhausted;
    reg [15:0] req_tag[0:1], req_epoch[0:1];
    reg [63:0] req_item[0:1], req_address_regs[0:1];
    reg [79:0] req_counts[0:1];
    reg [31:0] req_rcp_count[0:1];
    wire [15:0] rsp_tag[0:1], rsp_epoch[0:1];
    wire [511:0] rsp_data[0:1];
    wire [2:0] rsp_error_stage[0:1];
    wire [8:0] rsp_error_pc[0:1];
    wire [3:0] rsp_completed_stages[0:1], item_phase[0:1];
    wire [12:0] rsp_retired[0:1], rsp_muls[0:1];
    wire [63:0] rsp_cycles[0:1], rsp_core_cycles[0:1], rsp_exec_cycles[0:1];
    wire [1:0] session_phase[0:1];
    wire [31:0] session_namespace[0:1], sessions_used[0:1];
    wire [1:0] commit_valid, stage_valid;
    wire [2:0] commit_program[0:1], stage_program[0:1];
    wire [8:0] commit_pc[0:1];
    wire [7:0] commit_opcode[0:1];
    wire [511:0] commit_r[0:1], stage_r[0:1];
    wire [21:0] stage_cache_index[0:1];
    wire [63:0] stage_selected[0:1], stage_program_cycles[0:1];

    wire [1:0] fetch_client_req_valid, fetch_client_req_ready;
    wire [127:0] fetch_client_req_tag;
    wire [55:0] fetch_client_req_payload;
    wire [1:0] fetch_client_rsp_valid, fetch_client_rsp_ready;
    wire [127:0] fetch_client_rsp_tag;
    wire [379:0] fetch_client_rsp_payload;
    wire [1:0] cache_client_req_valid, cache_client_req_ready;
    wire [127:0] cache_client_req_tag;
    wire [81:0] cache_client_req_payload;
    wire [1:0] cache_client_rsp_valid, cache_client_rsp_ready;
    wire [127:0] cache_client_rsp_tag;
    wire [1107:0] cache_client_rsp_payload;
    wire fetch_backend_req_valid, fetch_backend_rsp_ready;
    reg fetch_backend_req_ready=0, fetch_backend_rsp_valid=0;
    wire [64:0] fetch_backend_req_tag;
    wire [27:0] fetch_backend_req_payload;
    reg [64:0] fetch_backend_rsp_tag=0;
    reg [189:0] fetch_backend_rsp_payload=0;
    wire cache_backend_req_valid, cache_backend_rsp_ready;
    reg cache_backend_req_ready=0, cache_backend_rsp_valid=0;
    wire [64:0] cache_backend_req_tag;
    wire [40:0] cache_backend_req_payload;
    reg [64:0] cache_backend_rsp_tag=0;
    reg [553:0] cache_backend_rsp_payload=0;
    wire fetch_busy, fetch_issued, fetch_owner, fetch_owner_cancelled;
    wire cache_busy, cache_issued, cache_owner, cache_owner_cancelled, quiescent;
    wire [127:0] fetch_accepted_count, fetch_delivered_count, fetch_arbitration_wait_cycles;
    wire [127:0] cache_accepted_count, cache_delivered_count, cache_arbitration_wait_cycles;
    wire [63:0] fetch_backend_request_count, fetch_backend_response_count;
    wire [63:0] fetch_cancelled_response_count, fetch_orphan_response_count, fetch_occupied_cycles;
    wire [63:0] cache_backend_request_count, cache_backend_response_count;
    wire [63:0] cache_cancelled_response_count, cache_orphan_response_count, cache_occupied_cycles;

    randomx_dataset_shared_fabric fabric(
        .clk(clk),.rst(rst),.client_cancel(client_cancel),.quiescent(quiescent),
        .fetch_client_req_valid(fetch_client_req_valid),.fetch_client_req_ready(fetch_client_req_ready),
        .fetch_client_req_tag(fetch_client_req_tag),.fetch_client_req_payload(fetch_client_req_payload),
        .fetch_client_rsp_valid(fetch_client_rsp_valid),.fetch_client_rsp_ready(fetch_client_rsp_ready),
        .fetch_client_rsp_tag(fetch_client_rsp_tag),.fetch_client_rsp_payload(fetch_client_rsp_payload),
        .fetch_backend_req_valid(fetch_backend_req_valid),.fetch_backend_req_ready(fetch_backend_req_ready),
        .fetch_backend_req_tag(fetch_backend_req_tag),.fetch_backend_req_payload(fetch_backend_req_payload),
        .fetch_backend_rsp_valid(fetch_backend_rsp_valid),.fetch_backend_rsp_ready(fetch_backend_rsp_ready),
        .fetch_backend_rsp_tag(fetch_backend_rsp_tag),.fetch_backend_rsp_payload(fetch_backend_rsp_payload),
        .fetch_busy(fetch_busy),.fetch_issued(fetch_issued),.fetch_owner(fetch_owner),.fetch_owner_cancelled(fetch_owner_cancelled),
        .fetch_accepted_count(fetch_accepted_count),.fetch_delivered_count(fetch_delivered_count),
        .fetch_arbitration_wait_cycles(fetch_arbitration_wait_cycles),
        .fetch_backend_request_count(fetch_backend_request_count),.fetch_backend_response_count(fetch_backend_response_count),
        .fetch_cancelled_response_count(fetch_cancelled_response_count),.fetch_orphan_response_count(fetch_orphan_response_count),
        .fetch_occupied_cycles(fetch_occupied_cycles),
        .cache_client_req_valid(cache_client_req_valid),.cache_client_req_ready(cache_client_req_ready),
        .cache_client_req_tag(cache_client_req_tag),.cache_client_req_payload(cache_client_req_payload),
        .cache_client_rsp_valid(cache_client_rsp_valid),.cache_client_rsp_ready(cache_client_rsp_ready),
        .cache_client_rsp_tag(cache_client_rsp_tag),.cache_client_rsp_payload(cache_client_rsp_payload),
        .cache_backend_req_valid(cache_backend_req_valid),.cache_backend_req_ready(cache_backend_req_ready),
        .cache_backend_req_tag(cache_backend_req_tag),.cache_backend_req_payload(cache_backend_req_payload),
        .cache_backend_rsp_valid(cache_backend_rsp_valid),.cache_backend_rsp_ready(cache_backend_rsp_ready),
        .cache_backend_rsp_tag(cache_backend_rsp_tag),.cache_backend_rsp_payload(cache_backend_rsp_payload),
        .cache_busy(cache_busy),.cache_issued(cache_issued),.cache_owner(cache_owner),.cache_owner_cancelled(cache_owner_cancelled),
        .cache_accepted_count(cache_accepted_count),.cache_delivered_count(cache_delivered_count),
        .cache_arbitration_wait_cycles(cache_arbitration_wait_cycles),
        .cache_backend_request_count(cache_backend_request_count),.cache_backend_response_count(cache_backend_response_count),
        .cache_cancelled_response_count(cache_cancelled_response_count),.cache_orphan_response_count(cache_orphan_response_count),
        .cache_occupied_cycles(cache_occupied_cycles)
    );

    genvar g;
    generate for(g=0;g<2;g=g+1)begin: clients
        wire [15:0] f_epoch,c_epoch;
        wire [2:0] f_program,c_program;
        wire [8:0] f_pc;
        wire [21:0] c_index;
        assign fetch_client_req_payload[g*28+:28]={f_epoch,f_program,f_pc};
        assign cache_client_req_payload[g*41+:41]={c_epoch,c_program,c_index};
        randomx_dataset_item_session #(.MUL_RADIX4(MUL_RADIX4),.SESSION_BITS(SESSION_BITS)) core(
            .clk(clk),.rst(rst),.cancel(client_cancel[g]),
            .req_valid(req_valid[g]),.req_ready(req_ready[g]),.req_tag(req_tag[g]),.req_epoch(req_epoch[g]),
            .req_item(req_item[g]),.req_counts(req_counts[g]),.req_address_regs(req_address_regs[g]),.req_rcp_count(req_rcp_count[g]),
            .rsp_valid(rsp_valid[g]),.rsp_ready(rsp_ready[g]),.rsp_tag(rsp_tag[g]),.rsp_epoch(rsp_epoch[g]),
            .rsp_data(rsp_data[g]),.rsp_error(rsp_error[g]),.rsp_error_stage(rsp_error_stage[g]),.rsp_error_pc(rsp_error_pc[g]),
            .rsp_completed_stages(rsp_completed_stages[g]),.rsp_retired(rsp_retired[g]),.rsp_muls(rsp_muls[g]),
            .rsp_cycles(rsp_cycles[g]),.rsp_core_cycles(rsp_core_cycles[g]),.rsp_exec_cycles(rsp_exec_cycles[g]),
            .generation_exhausted(generation_exhausted[g]),.phase(item_phase[g]),.session_phase(session_phase[g]),
            .session_namespace(session_namespace[g]),.sessions_used(sessions_used[g]),
            .fetch_valid(fetch_client_req_valid[g]),.fetch_ready(fetch_client_req_ready[g]),.fetch_tag(fetch_client_req_tag[g*64+:64]),
            .fetch_epoch(f_epoch),.fetch_program(f_program),.fetch_pc(f_pc),
            .fetch_rsp_valid(fetch_client_rsp_valid[g]),.fetch_rsp_ready(fetch_client_rsp_ready[g]),
            .fetch_rsp_tag(fetch_client_rsp_tag[g*64+:64]),
            .fetch_rsp_epoch(fetch_client_rsp_payload[g*190+174+:16]),
            .fetch_rsp_program(fetch_client_rsp_payload[g*190+171+:3]),
            .fetch_rsp_pc(fetch_client_rsp_payload[g*190+162+:9]),
            .fetch_rsp_error(fetch_client_rsp_payload[g*190+161]),.fetch_rsp_rcp_valid(fetch_client_rsp_payload[g*190+160]),
            .fetch_rsp_rcp_index(fetch_client_rsp_payload[g*190+128+:32]),
            .fetch_rsp_rcp_value(fetch_client_rsp_payload[g*190+64+:64]),
            .fetch_rsp_instruction(fetch_client_rsp_payload[g*190+:64]),
            .cache_req_valid(cache_client_req_valid[g]),.cache_req_ready(cache_client_req_ready[g]),
            .cache_req_tag(cache_client_req_tag[g*64+:64]),.cache_req_epoch(c_epoch),.cache_req_program(c_program),.cache_req_index(c_index),
            .cache_rsp_valid(cache_client_rsp_valid[g]),.cache_rsp_ready(cache_client_rsp_ready[g]),
            .cache_rsp_tag(cache_client_rsp_tag[g*64+:64]),
            .cache_rsp_epoch(cache_client_rsp_payload[g*554+538+:16]),
            .cache_rsp_program(cache_client_rsp_payload[g*554+535+:3]),
            .cache_rsp_index(cache_client_rsp_payload[g*554+513+:22]),
            .cache_rsp_error(cache_client_rsp_payload[g*554+512]),.cache_rsp_data(cache_client_rsp_payload[g*554+:512]),
            .commit_valid(commit_valid[g]),.commit_program(commit_program[g]),.commit_pc(commit_pc[g]),
            .commit_opcode(commit_opcode[g]),.commit_r(commit_r[g]),.stage_valid(stage_valid[g]),
            .stage_program(stage_program[g]),.stage_cache_index(stage_cache_index[g]),.stage_r(stage_r[g]),
            .stage_selected(stage_selected[g]),.stage_program_cycles(stage_program_cycles[g])
        );
    end endgenerate

    localparam [15:0] CALLER_TAG=16'hd173, IMAGE_EPOCH=16'h82a5;
    string fixture_root,profile,output_path,path;
    integer cache_fd=0,fd,out_fd,scan,cid,cache_id,found,i,j,k,round,rounds;
    reg [63:0] input_item[0:1],input_addresses[0:1],scan_item,scan_addresses;
    reg [79:0] input_counts[0:1],scan_counts;
    reg [31:0] input_rcp_count[0:1],scan_rcp;
    reg [511:0] gold_final[0:1],gold_seed[0:1],scan_final;
    reg [63:0] programs[0:4095],reciprocals[0:4095],tmp64[0:511];
    reg rcp_valid[0:4095],tmp1[0:511];
    reg [31:0] rcp_index[0:4095],tmp32[0:511];
    reg [511:0] gold_steps[0:8191],tmp512[0:511];
    reg [21:0] gold_indices[0:15];
    reg [511:0] gold_lines[0:15],gold_pre[0:15],gold_exec[0:15],gold_xor[0:15];
    reg [63:0] gold_selected[0:15];
    integer counts[0:7],mul_counts[0:7],addresses[0:7];
    reg [7:0] bytes64[0:63];
    reg mode_serial=0,mode_stalled=0;
    integer cancel_target=-1,fault_target=-1,cancel_triggered=0;
    reg [1:0] launch_mask=0,started=0,finished=0,available_seen=0,cancelled=0;
    integer commits[0:1],muls[0:1],stages[0:1],fetches[0:15],commits_by_stage[0:15];
    integer sessions_model[0:1],held[0:1];
    reg [63:0] start_tick[0:1],availability_tick[0:1],program_cycles[0:1];
    reg [63:0] session_counts[0:5],item_counts[0:17];
    reg [63:0] client_availability[0:1],client_core[0:1],client_executor[0:1],client_held[0:1];
    reg [778:0] held_result[0:1];
    wire [778:0] now_result[0:1];
    assign now_result[0]={rsp_tag[0],rsp_epoch[0],rsp_data[0],rsp_error[0],rsp_error_stage[0],rsp_error_pc[0],
        rsp_completed_stages[0],rsp_retired[0],rsp_muls[0],rsp_cycles[0],rsp_core_cycles[0],rsp_exec_cycles[0]};
    assign now_result[1]={rsp_tag[1],rsp_epoch[1],rsp_data[1],rsp_error[1],rsp_error_stage[1],rsp_error_pc[1],
        rsp_completed_stages[1],rsp_retired[1],rsp_muls[1],rsp_cycles[1],rsp_core_cycles[1],rsp_exec_cycles[1]};
    reg [63:0] ticks=0,batch_start=0,batch_end=0;
    integer batch_started=0,total_commits=0,total_muls=0,total_stages=0,successes=0,errors=0,aborts=0,returned=0,row_count=0;
    integer f_pending=0,c_pending=0,f_delay=0,c_delay=0,f_wait=0,c_wait=0;
    integer f_client=0,f_program=0,f_pc=0,c_client=0,c_program=0;
    reg [64:0] f_tag=0,c_tag=0;
    reg [15:0] f_epoch=0,c_epoch=0;
    reg [21:0] c_index=0;
    reg [511:0] c_data=0;
    reg f_held=0,c_held=0,fr_held=0,cr_held=0;
    reg [92:0] saved_f_request;
    reg [105:0] saved_c_request;
    reg [254:0] saved_f_response;
    reg [618:0] saved_c_response;
    wire [92:0] now_f_request={fetch_backend_req_tag,fetch_backend_req_payload};
    wire [105:0] now_c_request={cache_backend_req_tag,cache_backend_req_payload};
    wire [254:0] now_f_response={fetch_backend_rsp_tag,fetch_backend_rsp_payload};
    wire [618:0] now_c_response={cache_backend_rsp_tag,cache_backend_rsp_payload};
    reg [1:0] first_fetch_seen=0,first_cache_seen=0;
    reg [63:0] first_fetch_tag[0:1],first_cache_tag[0:1];
    integer fetch_collision=0,cache_collision=0,fetch_highwater=0,cache_highwater=0;
    integer force_denied=0,exhaustion_denied=0,cancel_identity_retained=0;
    reg [1:0] captured_fetch=0,captured_cache=0;
    reg [63:0] captured_fetch_tag[0:1],captured_cache_tag[0:1];
    reg [27:0] captured_fetch_payload[0:1];
    reg [40:0] captured_cache_payload[0:1];

    function integer is_mul;
        input [7:0] opcode;
        begin is_mul=opcode==3||opcode==11||opcode==12||opcode==13;end
    endfunction

    task load_fixtures;
        integer client,stage,slot,n,stage_slot;
    begin
        for(client=0;client<2;client=client+1)begin
            path=$sformatf("%s/cases.hex",fixture_root);fd=$fopen(path,"r");
            if(!fd)$fatal(1,"native case index missing");
            found=0;
            while(!$feof(fd)&&!found)begin
                scan=$fscanf(fd,"%d %d %h %h %h %h %h\n",cid,cache_id,scan_item,scan_rcp,scan_counts,scan_addresses,scan_final);
                if(scan==7&&cid==client)begin
                    if(cache_id!=0)$fatal(1,"native pair must share cache0");
                    input_item[client]=scan_item;input_rcp_count[client]=scan_rcp;
                    input_counts[client]=scan_counts;input_addresses[client]=scan_addresses;gold_final[client]=scan_final;found=1;
                end
            end
            $fclose(fd);if(!found)$fatal(1,"native case missing client=%0d",client);
            path=$sformatf("%s/case-%03d/seed.hex",fixture_root,client);$readmemh(path,tmp512,0,0);gold_seed[client]=tmp512[0];
            path=$sformatf("%s/case-%03d/stages.mem",fixture_root,client);fd=$fopen(path,"r");
            if(!fd)$fatal(1,"native stage file missing");
            for(stage=0;stage<8;stage=stage+1)begin
                stage_slot=client*8+stage;
                scan=$fscanf(fd,"%h %h %h %h %h %h\n",gold_indices[stage_slot],gold_lines[stage_slot],gold_pre[stage_slot],gold_exec[stage_slot],gold_xor[stage_slot],gold_selected[stage_slot]);
                if(scan!=6)$fatal(1,"native stage row missing");
                if(gold_pre[stage_slot]!==(stage==0?gold_seed[client]:gold_xor[stage_slot-1])||
                   gold_indices[stage_slot]!==((stage==0?input_item[client]:gold_selected[stage_slot-1])&64'h3fffff)||
                   gold_xor[stage_slot]!==(gold_exec[stage_slot]^gold_lines[stage_slot])||
                   gold_selected[stage_slot]!==gold_xor[stage_slot][input_addresses[client][stage*8+:8]*64+:64])
                    $fatal(1,"native stage recurrence contradictory");
            end
            $fclose(fd);
            for(stage=0;stage<8;stage=stage+1)begin
                path=$sformatf("%s/case-%03d/program-%0d.mem",fixture_root,client,stage);$readmemh(path,tmp64);
                for(n=0;n<512;n=n+1)begin slot=stage*512+n;if(client==0)programs[slot]=tmp64[n];else if(programs[slot]!==tmp64[n])$fatal(1,"pair program images differ");end
                path=$sformatf("%s/case-%03d/steps-%0d.mem",fixture_root,client,stage);$readmemh(path,tmp512);
                for(n=0;n<512;n=n+1)gold_steps[client*4096+stage*512+n]=tmp512[n];
                path=$sformatf("%s/case-%03d/rcp-valid-%0d.mem",fixture_root,client,stage);$readmemh(path,tmp1);
                for(n=0;n<512;n=n+1)begin slot=stage*512+n;if(client==0)rcp_valid[slot]=tmp1[n];else if(rcp_valid[slot]!==tmp1[n])$fatal(1,"pair reciprocal validity differs");end
                path=$sformatf("%s/case-%03d/rcp-index-%0d.mem",fixture_root,client,stage);$readmemh(path,tmp32);
                for(n=0;n<512;n=n+1)begin slot=stage*512+n;if(client==0)rcp_index[slot]=tmp32[n];else if(rcp_index[slot]!==tmp32[n])$fatal(1,"pair reciprocal indices differ");end
                path=$sformatf("%s/case-%03d/reciprocals-%0d.mem",fixture_root,client,stage);$readmemh(path,tmp64);
                for(n=0;n<512;n=n+1)begin slot=stage*512+n;if(client==0)reciprocals[slot]=tmp64[n];else if(reciprocals[slot]!==tmp64[n])$fatal(1,"pair reciprocal data differs");end
            end
            if(gold_final[client]!==gold_xor[client*8+7])$fatal(1,"native final/eighth stage mismatch");
        end
        if(input_item[0]!==0||input_item[1]!==64'd10000000||input_counts[0]!==input_counts[1]||
           input_addresses[0]!==input_addresses[1]||input_rcp_count[0]!==input_rcp_count[1])$fatal(1,"wrong retained native pair");
        for(stage=0;stage<8;stage=stage+1)begin
            counts[stage]=input_counts[0][stage*10+:10];addresses[stage]=input_addresses[0][stage*8+:8];mul_counts[stage]=0;
            if(counts[stage]>512||addresses[stage]>7)$fatal(1,"native descriptor bounds");
            for(n=0;n<counts[stage];n=n+1)mul_counts[stage]=mul_counts[stage]+is_mul(programs[stage*512+n][7:0]);
            for(client=0;client<2;client=client+1)
                if(gold_exec[client*8+stage]!==(counts[stage]==0?gold_pre[client*8+stage]:gold_steps[client*4096+stage*512+counts[stage]-1]))$fatal(1,"native final instruction state differs");
        end
        path=$sformatf("%s/cache-0.bin",fixture_root);cache_fd=$fopen(path,"rb");
        if(!cache_fd)$fatal(1,"actual immutable cache input missing");
    end endtask

    task read_cache;
        input [21:0] index;
        output [511:0] value;
        integer n,status;
    begin
        status=$fseek(cache_fd,index*64,0);if(status!=0)$fatal(1,"actual cache seek failed");
        status=$fread(bytes64,cache_fd,0,64);if(status!=64)$fatal(1,"actual cache short read");
        for(n=0;n<64;n=n+1)value[n*8+:8]=bytes64[n];
    end endtask

    task clear_item;
        input integer client;
        integer n;
    begin
        started[client]=0;finished[client]=0;available_seen[client]=0;cancelled[client]=0;
        commits[client]=0;muls[client]=0;stages[client]=0;held[client]=0;program_cycles[client]=0;
        start_tick[client]=0;availability_tick[client]=0;held_result[client]=0;
        for(n=0;n<8;n=n+1)begin fetches[client*8+n]=0;commits_by_stage[client*8+n]=0;end
        for(n=0;n<3;n=n+1)session_counts[client*3+n]=0;
        for(n=0;n<9;n=n+1)item_counts[client*9+n]=0;
    end endtask

    task write_phases;
        input integer client;
        integer n;
    begin
        $fwrite(out_fd,"\"session_phase_cycles\":[");
        for(n=0;n<3;n=n+1)begin if(n)$fwrite(out_fd,",");$fwrite(out_fd,"%0d",session_counts[client*3+n]);end
        $fwrite(out_fd,"],\"item_phase_cycles\":[");
        for(n=0;n<9;n=n+1)begin if(n)$fwrite(out_fd,",");$fwrite(out_fd,"%0d",item_counts[client*9+n]);end
        $fwrite(out_fd,"]");
    end endtask

    task write_cancel_row;
        input integer client;
    begin
        if(row_count)$fdisplay(out_fd,",");row_count=row_count+1;
        $fwrite(out_fd,"{\"client\":%0d,\"namespace\":%0d,\"status\":\"cancelled\",\"commits\":%0d,\"multiplies\":%0d,\"stages\":%0d,\"partial_elapsed_cycles\":%0d,",
            client,sessions_model[client],commits[client],muls[client],stages[client],ticks+1-start_tick[client]);
        write_phases(client);$fwrite(out_fd,"}");
    end endtask

    task observe;
        integer client,slot,stage_slot,n,expect_error;
        reg [63:0] ideal,session_sum,item_sum;
        reg [511:0] expected_data;
        string return_status;
    begin
        for(client=0;client<2;client=client+1)begin
            if(commit_valid[client])begin
                stage_slot=client*8+commit_program[client];slot=commit_program[client]*512+commits_by_stage[stage_slot];
                if(!started[client]||cancelled[client]||available_seen[client]||
                   commit_program[client]!==stages[client][2:0]||
                   commits_by_stage[stage_slot]>=counts[commit_program[client]]||
                   commit_pc[client]!==commits_by_stage[stage_slot][8:0]||
                   commit_opcode[client]!==programs[slot][7:0]||commit_r[client]!==gold_steps[client*4096+slot])
                    $fatal(1,"shared native instruction mismatch client=%0d stage=%0d pc=%0d",client,commit_program[client],commit_pc[client]);
                commits_by_stage[stage_slot]=commits_by_stage[stage_slot]+1;
                commits[client]=commits[client]+1;muls[client]=muls[client]+is_mul(commit_opcode[client]);
                total_commits=total_commits+1;total_muls=total_muls+is_mul(commit_opcode[client]);
            end
            if(stage_valid[client])begin
                stage_slot=client*8+stages[client];
                ideal=3*counts[stages[client]]+(MUL_RADIX4?34:2)*mul_counts[stages[client]];
                if(!started[client]||cancelled[client]||stages[client]>=8||
                   stage_program[client]!==stages[client][2:0]||
                   commits_by_stage[stage_slot]!=counts[stages[client]]||
                   stage_cache_index[client]!==gold_indices[stage_slot]||stage_r[client]!==gold_xor[stage_slot]||
                   stage_selected[client]!==gold_selected[stage_slot]||stage_program_cycles[client]<ideal)
                    $fatal(1,"shared native stage mismatch client=%0d stage=%0d",client,stages[client]);
                program_cycles[client]=program_cycles[client]+stage_program_cycles[client];
                stages[client]=stages[client]+1;total_stages=total_stages+1;
            end
            if(rsp_valid[client]&&!available_seen[client])begin
                expect_error=(fault_target==client);
                expected_data=expect_error?gold_seed[client]:gold_final[client];
                if(!started[client]||cancelled[client]||rsp_tag[client]!==CALLER_TAG||rsp_epoch[client]!==IMAGE_EPOCH||
                   rsp_error[client]!==expect_error[0]||rsp_data[client]!==expected_data||
                   rsp_retired[client]!==commits[client][12:0]||rsp_muls[client]!==muls[client][12:0]||
                   rsp_completed_stages[client]!==stages[client][3:0]||
                   rsp_cycles[client]!==ticks-start_tick[client]||rsp_cycles[client]!==rsp_core_cycles[client]+1)
                    $fatal(1,"shared native return mismatch client=%0d cycles=%0d measured=%0d",client,rsp_cycles[client],ticks-start_tick[client]);
                if(expect_error)begin
                    if(commits[client]||stages[client]||muls[client]||
                       rsp_error_stage[client]!==3'd0||rsp_error_pc[client]!==9'd0)
                        $fatal(1,"malformed first fetch escaped exact zero-commit prefix");
                    errors=errors+1;
                end else begin
                    if(commits[client]!=3563||muls[client]!=1254||stages[client]!=8||rsp_exec_cycles[client]!==program_cycles[client])
                        $fatal(1,"shared native completion totals client=%0d",client);
                    for(n=0;n<8;n=n+1)
                        if(commits_by_stage[client*8+n]!=counts[n]||fetches[client*8+n]!=counts[n])$fatal(1,"shared complete per-program counts");
                    successes=successes+1;
                end
                session_sum=0;item_sum=0;
                for(n=0;n<3;n=n+1)session_sum=session_sum+session_counts[client*3+n];
                for(n=0;n<9;n=n+1)item_sum=item_sum+item_counts[client*9+n];
                if(session_sum!==rsp_cycles[client]||item_sum!==rsp_cycles[client])$fatal(1,"shared availability phase closure");
                available_seen[client]=1;availability_tick[client]=ticks;held_result[client]=now_result[client];
                client_availability[client]=client_availability[client]+rsp_cycles[client];
                client_core[client]=client_core[client]+rsp_core_cycles[client];
                client_executor[client]=client_executor[client]+rsp_exec_cycles[client];
                if(row_count)$fdisplay(out_fd,",");row_count=row_count+1;
                if(expect_error)return_status="error";else return_status="success";
                $fwrite(out_fd,"{\"client\":%0d,\"namespace\":%0d,\"status\":\"%s\",\"commits\":%0d,\"multiplies\":%0d,\"stages\":%0d,\"availability_cycles\":%0d,\"core_cycles\":%0d,\"executor_cycles\":%0d,",
                    client,sessions_model[client],return_status,commits[client],muls[client],stages[client],rsp_cycles[client],rsp_core_cycles[client],rsp_exec_cycles[client]);
                write_phases(client);$fwrite(out_fd,"}");
            end
            if(sessions_used[client]!==sessions_model[client])$fatal(1,"session namespace refunded, reused or wrapped client=%0d",client);
            if(client_cancel[client]&&(commit_valid[client]||stage_valid[client]||rsp_valid[client]))$fatal(1,"cancel did not suppress core transfers");
        end
    end endtask

    task step;
        integer client,slot,n,owner_now;
        reg [15:0] response_epoch;
        reg [63:0] accepted_tag;
    begin
        @(negedge clk);
        client_cancel=0;
        if(cancel_target>=0&&!cancel_triggered)
            if(commits[cancel_target]>0&&fetch_busy&&fetch_owner==cancel_target)
                client_cancel[cancel_target]=1;
        for(client=0;client<2;client=client+1)begin
            req_valid[client]=force_denied||(!started[client]&&launch_mask[client]&&(!mode_serial||client==0||finished[0]));
            if(client_cancel[client])req_valid[client]=0;
            if(!started[client]||force_denied)begin
                req_tag[client]=CALLER_TAG;req_epoch[client]=IMAGE_EPOCH;req_item[client]=input_item[client];
                req_counts[client]=input_counts[client];req_address_regs[client]=input_addresses[client];req_rcp_count[client]=input_rcp_count[client];
            end else begin
                // The accepted descriptor must not follow replacement inputs.
                req_tag[client]=~CALLER_TAG;req_epoch[client]=~IMAGE_EPOCH;req_item[client]=~input_item[client];
                req_counts[client]=~80'b0;req_address_regs[client]=~64'b0;req_rcp_count[client]=0;
            end
            rsp_ready[client]=available_seen[client]&&held[client]>=4&&!finished[client]&&!client_cancel[client];
        end
        fetch_backend_req_ready=!f_pending&&(!mode_stalled||f_wait>=2);
        cache_backend_req_ready=!c_pending&&(!mode_stalled||c_wait>=3);
        fetch_backend_rsp_valid=0;cache_backend_rsp_valid=0;
        if(f_pending)begin
            if(f_delay>0)f_delay=f_delay-1;
            else begin
                slot=f_program*512+f_pc;response_epoch=f_epoch;
                if(f_client==fault_target&&f_program==0&&f_pc==0)response_epoch=f_epoch^16'b1;
                fetch_backend_rsp_valid=1;fetch_backend_rsp_tag=f_tag;
                fetch_backend_rsp_payload={response_epoch,f_program[2:0],f_pc[8:0],1'b0,rcp_valid[slot],rcp_index[slot],reciprocals[slot],programs[slot]};
            end
        end
        if(c_pending)begin
            if(c_delay>0)c_delay=c_delay-1;
            else begin
                cache_backend_rsp_valid=1;cache_backend_rsp_tag=c_tag;
                cache_backend_rsp_payload={c_epoch,c_program[2:0],c_index,1'b0,c_data};
            end
        end
        @(posedge clk);
        if(f_held&&(!fetch_backend_req_valid||now_f_request!==saved_f_request))$fatal(1,"shared held fetch descriptor changed");
        if(c_held&&(!cache_backend_req_valid||now_c_request!==saved_c_request))$fatal(1,"shared held cache descriptor changed");
        if(fr_held&&(!fetch_backend_rsp_valid||now_f_response!==saved_f_response))$fatal(1,"held fetch provider response changed");
        if(cr_held&&(!cache_backend_rsp_valid||now_c_response!==saved_c_response))$fatal(1,"held cache provider response changed");
        f_held=fetch_backend_req_valid&&!fetch_backend_req_ready;saved_f_request=now_f_request;
        c_held=cache_backend_req_valid&&!cache_backend_req_ready;saved_c_request=now_c_request;
        fr_held=fetch_backend_rsp_valid&&!fetch_backend_rsp_ready;saved_f_response=now_f_response;
        cr_held=cache_backend_rsp_valid&&!cache_backend_rsp_ready;saved_c_response=now_c_response;
        if(fetch_backend_req_valid&&!fetch_backend_req_ready)f_wait=f_wait+1;
        if(cache_backend_req_valid&&!cache_backend_req_ready)c_wait=c_wait+1;
        // Shared instruction values can hide a cross-route at the same PC.
        // Therefore transport ownership and bit-exact payload forwarding are
        // checked independently of every downstream native arithmetic check.
        if(fetch_backend_rsp_valid)begin
            if(!f_pending||fetch_backend_rsp_tag!==f_tag)$fatal(1,"native fetch provider identity changed");
            if(fetch_owner_cancelled||client_cancel[f_client])begin
                if(fetch_client_rsp_valid)$fatal(1,"cancelled fetch escaped to a client");
            end else if(fetch_client_rsp_valid!==(f_client?2'b10:2'b01)||
                fetch_client_rsp_tag[f_client*64+:64]!==f_tag[63:0]||
                fetch_client_rsp_payload[f_client*190+:190]!==fetch_backend_rsp_payload)
                $fatal(1,"fetch response crossed its captured client or changed payload");
        end
        if(cache_backend_rsp_valid)begin
            if(!c_pending||cache_backend_rsp_tag!==c_tag)$fatal(1,"native cache provider identity changed");
            if(cache_owner_cancelled||client_cancel[c_client])begin
                if(cache_client_rsp_valid)$fatal(1,"cancelled cache escaped to a client");
            end else if(cache_client_rsp_valid!==(c_client?2'b10:2'b01)||
                cache_client_rsp_tag[c_client*64+:64]!==c_tag[63:0]||
                cache_client_rsp_payload[c_client*554+:554]!==cache_backend_rsp_payload)
                $fatal(1,"cache response crossed its captured client or changed payload");
        end
        for(client=0;client<2;client=client+1)begin
            if(fetch_client_req_valid[client]&&fetch_client_req_ready[client])begin
                if(captured_fetch[client])$fatal(1,"second captured fetch for one client");
                captured_fetch[client]=1;captured_fetch_tag[client]=fetch_client_req_tag[client*64+:64];
                captured_fetch_payload[client]=fetch_client_req_payload[client*28+:28];
            end
            if(cache_client_req_valid[client]&&cache_client_req_ready[client])begin
                if(captured_cache[client])$fatal(1,"second captured cache for one client");
                captured_cache[client]=1;captured_cache_tag[client]=cache_client_req_tag[client*64+:64];
                captured_cache_payload[client]=cache_client_req_payload[client*41+:41];
            end
            if(started[client]&&!available_seen[client]&&!finished[client])begin
                if(session_phase[client]>2||item_phase[client]>8)$fatal(1,"unknown phase domain");
                session_counts[client*3+session_phase[client]]=session_counts[client*3+session_phase[client]]+1;
                item_counts[client*9+item_phase[client]]=item_counts[client*9+item_phase[client]]+1;
            end
            if(available_seen[client]&&rsp_valid[client])begin
                if(now_result[client]!==held_result[client])$fatal(1,"held native result changed");
                if(!rsp_ready[client])held[client]=held[client]+1;
            end
            if(req_valid[client]&&req_ready[client])begin
                if(force_denied||started[client])$fatal(1,"unexpected or exhausted client admission");
                started[client]=1;start_tick[client]=ticks+1;sessions_model[client]=sessions_model[client]+1;
                if(!batch_started)begin batch_start=ticks+1;batch_started=1;end
            end
            if(rsp_valid[client]&&rsp_ready[client])begin
                if(!available_seen[client]||finished[client])$fatal(1,"untracked native return");
                finished[client]=1;returned=returned+1;client_held[client]=client_held[client]+held[client];batch_end=ticks+1;
            end
            if(client_cancel[client])begin
                if(cancel_triggered||!started[client]||available_seen[client]||!commits[client])$fatal(1,"invalid native cancellation point");
                cancel_triggered=1;cancelled[client]=1;finished[client]=1;aborts=aborts+1;write_cancel_row(client);
            end
        end
        if(fetch_backend_rsp_valid&&fetch_backend_rsp_ready)begin
            if(!f_pending)$fatal(1,"untracked backend fetch reply");f_pending=0;captured_fetch[f_client]=0;
        end
        if(cache_backend_rsp_valid&&cache_backend_rsp_ready)begin
            if(!c_pending)$fatal(1,"untracked backend cache reply");c_pending=0;captured_cache[c_client]=0;
        end
        if(fetch_backend_req_valid&&fetch_backend_req_ready)begin
            if(f_pending)$fatal(1,"shared fetch exceeded one pending request");
            f_client=fetch_backend_req_tag[64];f_tag=fetch_backend_req_tag;
            {f_epoch,f_program[2:0],f_pc[8:0]}=fetch_backend_req_payload;
            if(f_epoch!==IMAGE_EPOCH||f_program!==stages[f_client]||f_pc!==fetches[f_client*8+f_program]||
               f_pc>=counts[f_program]||f_tag[63:32]!==sessions_model[f_client]||f_tag[15:0]!==CALLER_TAG)
                $fatal(1,"backend fetch owner/descriptor/order mismatch client=%0d",f_client);
            // Value checks alone cannot expose a same-PC cross-route because
            // both clients intentionally share the immutable instruction image.
            if(fetch_owner!==f_client[0]||!captured_fetch[f_client]||captured_fetch_tag[f_client]!==f_tag[63:0]||
               captured_fetch_payload[f_client]!==fetch_backend_req_payload)
                $fatal(1,"fetch backend owner differs from its captured client");
            if(!first_fetch_seen[f_client])begin first_fetch_seen[f_client]=1;first_fetch_tag[f_client]=f_tag[63:0];end
            if(first_fetch_seen==2'b11&&first_fetch_tag[0]===first_fetch_tag[1])fetch_collision=1;
            fetches[f_client*8+f_program]=fetches[f_client*8+f_program]+1;
            f_pending=1;f_wait=0;f_delay=mode_stalled?2+(f_pc%3):0;
        end
        if(cache_backend_req_valid&&cache_backend_req_ready)begin
            if(c_pending)$fatal(1,"shared cache exceeded one pending request");
            c_client=cache_backend_req_tag[64];c_tag=cache_backend_req_tag;
            {c_epoch,c_program[2:0],c_index}=cache_backend_req_payload;
            if(c_epoch!==IMAGE_EPOCH||c_program!==stages[c_client]||c_index!==gold_indices[c_client*8+c_program]||
               commits_by_stage[c_client*8+c_program]!=counts[c_program]||
               c_tag[63:32]!==sessions_model[c_client]||c_tag[15:0]!==CALLER_TAG)
                $fatal(1,"backend cache owner/descriptor/recurrence mismatch client=%0d",c_client);
            if(cache_owner!==c_client[0]||!captured_cache[c_client]||captured_cache_tag[c_client]!==c_tag[63:0]||
               captured_cache_payload[c_client]!==cache_backend_req_payload)$fatal(1,"cache backend owner differs from captured client");
            read_cache(c_index,c_data);
            if(c_data!==gold_lines[c_client*8+c_program])$fatal(1,"DUT-indexed cache data differs from native assertion");
            if(!first_cache_seen[c_client])begin first_cache_seen[c_client]=1;first_cache_tag[c_client]=c_tag[63:0];end
            if(first_cache_seen==2'b11&&first_cache_tag[0]===first_cache_tag[1])cache_collision=1;
            c_pending=1;c_wait=0;c_delay=mode_stalled?3+(c_program%3):0;
        end
        #1;ticks=ticks+1;observe;
        if(fetch_busy)fetch_highwater=1;if(cache_busy)cache_highwater=1;
        if(ticks>4000000)$fatal(1,"bounded shared-native timeout");
    end endtask

    task run_mask;
        input [1:0] mask;
        integer client;
    begin
        for(client=0;client<2;client=client+1)if(mask[client])clear_item(client);
        launch_mask=mask;
        while((finished&mask)!==mask||!quiescent||f_pending||c_pending)step;
        launch_mask=0;
        if(captured_fetch||captured_cache)$fatal(1,"fabric credit released before provider ownership drained");
    end endtask

    task emit_summary;
    begin
        if(fetch_backend_request_count!==(fetch_accepted_count[63:0]+fetch_accepted_count[127:64])||
           cache_backend_request_count!==(cache_accepted_count[63:0]+cache_accepted_count[127:64])||
           fetch_backend_request_count!==fetch_backend_response_count||cache_backend_request_count!==cache_backend_response_count||
           fetch_backend_response_count!==(fetch_delivered_count[63:0]+fetch_delivered_count[127:64]+fetch_cancelled_response_count+fetch_orphan_response_count)||
           cache_backend_response_count!==(cache_delivered_count[63:0]+cache_delivered_count[127:64]+cache_cancelled_response_count+cache_orphan_response_count))
            $fatal(1,"shared channel closed request/response accounting");
        if(fetch_orphan_response_count!==64'd0||cache_orphan_response_count!==64'd0)$fatal(1,"native providers emitted unplanned orphan packets");
        if(profile=="exhaustion")begin
            if(successes!=6||returned!=6||errors||aborts||total_commits!=21378||total_muls!=7524||total_stages!=48||
               sessions_model[0]!=3||sessions_model[1]!=3||!exhaustion_denied)$fatal(1,"native exhaustion coverage incomplete");
        end else if(cancel_target>=0)begin
            if(successes!=2||returned!=2||errors||aborts!=1||!cancel_identity_retained||!cancel_triggered||
               sessions_model[cancel_target]!=2||sessions_model[1-cancel_target]!=1||!fetch_cancelled_response_count)
                $fatal(1,"native cancellation/reissue coverage incomplete");
        end else if(fault_target>=0)begin
            if(successes!=1||errors!=1||returned!=2||aborts||total_commits!=3563||total_muls!=1254||total_stages!=8)
                $fatal(1,"native malformed owner isolation coverage incomplete");
        end else begin
            if(successes!=2||returned!=2||errors||aborts||total_commits!=7126||total_muls!=2508||total_stages!=16||
               sessions_model[0]!=1||sessions_model[1]!=1||fetch_backend_request_count!==64'd7126||cache_backend_request_count!==64'd16)
                $fatal(1,"native pair coverage incomplete");
        end
        if((cancel_target<0&&fault_target<0)&&(!fetch_collision||!cache_collision))$fatal(1,"pair did not exercise identical client transport tags");
        $fdisplay(out_fd,"],\"mode_serial\":%s,\"mode_stalled\":%s,\"fixture_cases\":[0,1],\"fixture_item_numbers\":[0,10000000],",
            mode_serial?"true":"false",mode_stalled?"true":"false");
        $fdisplay(out_fd,"\"successful_items\":%0d,\"error_items\":%0d,\"aborted_items\":%0d,\"returned_items\":%0d,\"commits\":%0d,\"multiplies\":%0d,\"stages\":%0d,",
            successes,errors,aborts,returned,total_commits,total_muls,total_stages);
        $fdisplay(out_fd,"\"sessions_used\":[%0d,%0d],\"batch_elapsed_cycles\":%0d,\"client_availability_cycles\":[%0d,%0d],\"client_core_cycles\":[%0d,%0d],\"client_executor_cycles\":[%0d,%0d],\"client_held_backpressure_cycles\":[%0d,%0d],",
            sessions_model[0],sessions_model[1],batch_end-batch_start,client_availability[0],client_availability[1],client_core[0],client_core[1],client_executor[0],client_executor[1],client_held[0],client_held[1]);
        $fdisplay(out_fd,"\"fetch\":{\"accepted\":[%0d,%0d],\"delivered\":[%0d,%0d],\"backend_requests\":%0d,\"backend_responses\":%0d,\"cancelled_responses\":%0d,\"orphan_responses\":%0d,\"occupied_cycles\":%0d,\"arbitration_wait_cycles\":[%0d,%0d],\"high_water\":%0d},",
            fetch_accepted_count[63:0],fetch_accepted_count[127:64],fetch_delivered_count[63:0],fetch_delivered_count[127:64],
            fetch_backend_request_count,fetch_backend_response_count,fetch_cancelled_response_count,fetch_orphan_response_count,
            fetch_occupied_cycles,fetch_arbitration_wait_cycles[63:0],fetch_arbitration_wait_cycles[127:64],fetch_highwater);
        $fdisplay(out_fd,"\"cache\":{\"accepted\":[%0d,%0d],\"delivered\":[%0d,%0d],\"backend_requests\":%0d,\"backend_responses\":%0d,\"cancelled_responses\":%0d,\"orphan_responses\":%0d,\"occupied_cycles\":%0d,\"arbitration_wait_cycles\":[%0d,%0d],\"high_water\":%0d},",
            cache_accepted_count[63:0],cache_accepted_count[127:64],cache_delivered_count[63:0],cache_delivered_count[127:64],
            cache_backend_request_count,cache_backend_response_count,cache_cancelled_response_count,cache_orphan_response_count,
            cache_occupied_cycles,cache_arbitration_wait_cycles[63:0],cache_arbitration_wait_cycles[127:64],cache_highwater);
        $fdisplay(out_fd,"\"identity_collision_checks\":{\"fetch\":%s,\"cache\":%s},\"cancelled_identity_retained\":%s,\"exhaustion_admission_denied\":%s,",
            fetch_collision?"true":"false",cache_collision?"true":"false",cancel_identity_retained?"true":"false",exhaustion_denied?"true":"false");
        $fdisplay(out_fd,"\"clock_scope\":\"batch elapsed excludes first acceptance edge; client availability and phase vectors are nested and must not be added to it\",\"phase_scope\":\"pre-edge phases are sampled only after descriptor acceptance while the client is owned, stopping at post-edge result availability; session[3] and child item[9] sum to session availability including adapter launch, so child IDLE may include LAUNCH; core availability is separately one clock shorter; these source-specific bins are not the old full-hash observer vector\",\"counters_before_final_quiescent_reset\":true,");
    end endtask

    task quiescent_reset;
    begin
        @(negedge clk);
        if(quiescent!==1'b1||f_pending||c_pending||captured_fetch||captured_cache||req_valid||rsp_valid!==2'b00||
           fetch_client_req_valid!==2'b00||cache_client_req_valid!==2'b00||fetch_backend_req_valid!==1'b0||cache_backend_req_valid!==1'b0||
           fetch_backend_rsp_valid!==1'b0||cache_backend_rsp_valid!==1'b0||session_phase[0]!==2'b00||session_phase[1]!==2'b00)
            $fatal(1,"hard reset requires genuinely empty clients, fabric and providers");
        rst=1;client_cancel=0;req_valid=0;rsp_ready=0;
        fetch_backend_req_ready=0;cache_backend_req_ready=0;
        @(posedge clk);#1;
        if(quiescent!==1'b1||fetch_accepted_count!==128'd0||cache_accepted_count!==128'd0||
           sessions_used[0]!==32'd0||sessions_used[1]!==32'd0)$fatal(1,"quiescent hard reset failed to clear namespaces/control");
        @(negedge clk);rst=0;#1;
        if(req_ready!==2'b11||generation_exhausted!==2'b00||rsp_valid!==2'b00||
           fetch_client_req_valid!==2'b00||cache_client_req_valid!==2'b00||quiescent!==1'b1)
            $fatal(1,"quiescent hard reset failed to restore initial admission");
    end endtask

    initial begin
        if(SESSION_BITS!=2)$fatal(1,"native pair bench requires reviewed SESSION_BITS=2");
        if(!$value$plusargs("fixtures=%s",fixture_root)||!$value$plusargs("profile=%s",profile)||!$value$plusargs("output=%s",output_path))
            $fatal(1,"fixtures/profile/output plusargs required");
        if(profile=="serial-ideal")mode_serial=1;
        else if(profile=="concurrent-ideal")begin end
        else if(profile=="serial-stalled")begin mode_serial=1;mode_stalled=1;end
        else if(profile=="concurrent-stalled")mode_stalled=1;
        else if(profile=="cancel0")begin cancel_target=0;mode_stalled=1;end
        else if(profile=="cancel1")begin cancel_target=1;mode_stalled=1;end
        else if(profile=="malformed-fetch0")begin fault_target=0;mode_stalled=1;end
        else if(profile=="exhaustion")begin end
        else $fatal(1,"unknown native pair profile");
        load_fixtures;
        fd=$fopen(output_path,"r");if(fd)begin $fclose(fd);$fatal(1,"native result path already exists");end
        out_fd=$fopen(output_path,"w");if(!out_fd)$fatal(1,"cannot create native result");
        $fdisplay(out_fd,"{\"schema\":\"openrx.dataset-shared.native.v1\",\"profile\":\"%s\",\"item_rows\":[",profile);
        for(i=0;i<2;i=i+1)begin
            sessions_model[i]=0;client_availability[i]=0;client_core[i]=0;client_executor[i]=0;client_held[i]=0;
            req_tag[i]=0;req_epoch[i]=0;req_item[i]=0;req_counts[i]=0;req_address_regs[i]=0;req_rcp_count[i]=0;
            first_fetch_tag[i]=0;first_cache_tag[i]=0;captured_fetch_tag[i]=0;captured_cache_tag[i]=0;
            captured_fetch_payload[i]=0;captured_cache_payload[i]=0;clear_item(i);
        end
        finished=2'b11;
        // Initial reset has no previous traffic. No later reset may discard work.
        repeat(3)begin @(posedge clk);#1;end
        @(negedge clk);rst=0;#1;
        if(req_ready!==2'b11||quiescent!==1'b1)$fatal(1,"initial shared pair admission");
        rounds=profile=="exhaustion"?3:1;
        for(round=0;round<rounds;round=round+1)run_mask(2'b11);
        if(cancel_target>=0)begin
            if(!cancel_triggered||successes!=1||returned!=1||sessions_used[cancel_target]!=1||!fetch_cancelled_response_count)
                $fatal(1,"cancel must retain identity and drain while other native client finishes");
            run_mask(cancel_target==0?2'b01:2'b10);
            if(sessions_used[cancel_target]!=2||sessions_used[1-cancel_target]!=1)$fatal(1,"cancelled client did not consume a fresh namespace");
            cancel_identity_retained=1;
        end
        if(profile=="exhaustion")begin
            if(generation_exhausted!==2'b11||sessions_used[0]!=3||sessions_used[1]!=3)$fatal(1,"reduced session limit missing");
            force_denied=1;
            repeat(8)begin step;if(req_ready!==2'b00||rsp_valid!==2'b00||fetch_client_req_valid!==2'b00||cache_client_req_valid!==2'b00)$fatal(1,"exhaustion silently recycled identity");end
            force_denied=0;launch_mask=0;step;exhaustion_denied=1;
        end
        launch_mask=0;step;
        emit_summary;
        quiescent_reset;
        $fdisplay(out_fd,"\"quiescent_hard_reset_checked\":true,\"status\":\"pass\"}");
        $fclose(out_fd);$fclose(cache_fd);
        $display("shared native PASS profile=%s successes=%0d errors=%0d aborts=%0d commits=%0d stages=%0d",profile,successes,errors,aborts,total_commits,total_stages);
        $finish;
    end
endmodule
