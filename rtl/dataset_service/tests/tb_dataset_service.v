// SPDX-License-Identifier: BSD-3-Clause
// Standalone lifecycle checks. Native results are assertion-only: service data
// comes exclusively from actual-index cache reads and prepared program inputs.
`timescale 1ns/1ps
module tb_dataset_service #(parameter integer ITEMS_PER_BATCH=2,
                            parameter integer MUL_RADIX4=1);
`ifdef VERILATOR
    import "DPI-C" function void rx_dataset_assertion(
        input bit [63:0] address, output bit [511:0] result);
    import "DPI-C" function void rx_provider_stats(input string filename);
`endif
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
    wire [13:0] items_reserved,items_remaining;
    wire [63:0] items_requested,items_completed,ds_requests,ds_responses;
    wire [1:0] phase; wire [3:0] item_phase;

    wire cache_req_valid,cache_rsp_ready;
    reg cache_req_ready=0,cache_rsp_valid=0,cache_rsp_error=0;
    wire [31:0] cache_req_tag; wire [15:0] cache_req_epoch;
    wire [2:0] cache_req_program; wire [21:0] cache_req_index;
    reg [31:0] cache_rsp_tag=0; reg [15:0] cache_rsp_epoch=0;
    reg [2:0] cache_rsp_program=0; reg [21:0] cache_rsp_index=0;
    reg [511:0] cache_rsp_data=0;
    wire fetch_valid,fetch_rsp_ready;
    reg fetch_ready=0,fetch_rsp_valid=0,fetch_rsp_error=0,fetch_rsp_rcp_valid=0;
    wire [31:0] fetch_tag; wire [15:0] fetch_epoch;
    wire [2:0] fetch_program; wire [8:0] fetch_pc;
    reg [31:0] fetch_rsp_tag=0,fetch_rsp_rcp_index=0;
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
    wire [63:0] item_rsp_cycles,item_rsp_exec_cycles;
    wire item_commit_valid,item_stage_valid;
    wire [2:0] item_commit_program,item_stage_program;
    wire [8:0] item_commit_pc; wire [7:0] item_commit_opcode;
    wire [511:0] item_commit_r,item_stage_r;
    wire [21:0] item_stage_cache_index;
    wire [63:0] item_stage_selected,item_stage_program_cycles;

`ifdef DATASET_SERVICE_NETLIST
    randomx_dataset_service dut(
`else
    randomx_dataset_service #(.ITEMS_PER_BATCH(ITEMS_PER_BATCH),.MUL_RADIX4(MUL_RADIX4)) dut(
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
        .item_commit_valid(item_commit_valid),.item_commit_program(item_commit_program),
        .item_commit_pc(item_commit_pc),.item_commit_opcode(item_commit_opcode),.item_commit_r(item_commit_r),
        .item_stage_valid(item_stage_valid),.item_stage_program(item_stage_program),
        .item_stage_cache_index(item_stage_cache_index),.item_stage_r(item_stage_r),
        .item_stage_selected(item_stage_selected),.item_stage_program_cycles(item_stage_program_cycles)
    );

    localparam [63:0] LAST_ADDRESS=64'h0000000081ffff80;
    reg [63:0] programs[0:4095],reciprocals[0:238];
    reg [7:0] cache_bytes[0:63];
    string asset_root,output_directory,path,mode;
    integer cache_fd=0,i,j,n,status;
    reg [79:0] native_counts;
    reg [63:0] native_addresses;
    reg [15:0] captured_generation=0,captured_epoch=0,live_item_tag=0;
    reg [79:0] captured_counts=0;
    reg [63:0] captured_addresses=0,owned_address=0;
    reg [31:0] owned_ds_tag=0;
    integer reserved_model=0,remaining_model=8191;
    reg [63:0] requested_model=0,completed_model=0,ds_requests_model=0,ds_responses_model=0;
    integer batches=0,requests=0,returns=0,native_assertions=0,held_checks=0;
    integer local_errors=0,child_errors=0,cancellations=0,stale_packets=0;
    integer budget_batches=0,budget_remaining=0,reset_recoveries=0;
    integer all_commits=0,all_stages=0,commits=0,stages=0,run_ticks=0,total_ticks=0;
    integer fetch_accepts=0,cache_accepts=0,stall_services=0,f_wait=0,c_wait=0,service_stalls=0;
    integer f_pending=0,c_pending=0,f_replayed=0,c_replayed=0;
    integer block_fetch=0,block_cache=0,inject_stale=0,fault_service=0,fault_kind=0;
    integer f_ambient=0,c_ambient=0,f_sending_stale=0,c_sending_stale=0;
    integer f_program=0,f_pc=0,c_program=0;
    reg [31:0] f_tag=0,c_tag=0;
    reg [15:0] f_epoch=0,c_epoch=0;
    reg [21:0] c_index=0; reg [511:0] c_payload=0;
    reg old_f_valid=0,old_c_valid=0;
    reg [31:0] old_f_tag=0,old_c_tag=0;
    reg [15:0] old_f_epoch=0,old_c_epoch=0;
    reg [2:0] old_f_program=0,old_c_program=0;
    reg [8:0] old_f_pc=0;reg [21:0] old_c_index=0;
    reg f_held=0,c_held=0;
    reg [59:0] held_fetch;reg [72:0] held_cache;
    wire [59:0] now_fetch={fetch_tag,fetch_epoch,fetch_program,fetch_pc};
    wire [72:0] now_cache={cache_req_tag,cache_req_epoch,cache_req_program,cache_req_index};
    wire [544:0] now_return={ds_rsp_tag,ds_rsp_data,ds_rsp_error};
    reg [544:0] held_return;
    reg multiply_delivered=0;

    function integer is_multiply;
        input [7:0] opcode;
        begin is_multiply=opcode==3||opcode==11||opcode==12||opcode==13;end
    endfunction

    task read_cache;
        input [21:0] index;
        output [511:0] data;
        integer r,k;
    begin
        // Only the actual DUT request supplies this index. No final/step gold
        // is loaded by this provider, including on later dependent stages.
        r=$fseek(cache_fd,index*64,0);
        if(r!=0)$fatal(1,"dataset_service cache seek index=%0d",index);
        r=$fread(cache_bytes,cache_fd,0,64);
        if(r!=64)$fatal(1,"dataset_service short cache read index=%0d bytes=%0d",index,r);
        for(k=0;k<64;k=k+1)data[k*8+:8]=cache_bytes[k];
    end endtask

    task step;
        integer slot,index;
        reg [63:0] instruction;
    begin
        @(negedge clk);
        fetch_ready=!rst&&!cancel&&!f_pending&&(!stall_services||f_wait>=2);
        cache_req_ready=!rst&&!cancel&&!c_pending&&(!stall_services||c_wait>=3);
        fetch_rsp_valid=0;fetch_rsp_error=0;fetch_rsp_rcp_valid=0;
        fetch_rsp_rcp_index=0;fetch_rsp_rcp_value=0;
        cache_rsp_valid=0;cache_rsp_error=0;
        f_ambient=0;c_ambient=0;f_sending_stale=0;c_sending_stale=0;
        if(!rst&&!cancel)begin
            if(inject_stale&&old_f_valid&&!f_pending)begin
                fetch_rsp_valid=1;fetch_rsp_tag=old_f_tag;fetch_rsp_epoch=old_f_epoch;
                fetch_rsp_program=old_f_program;fetch_rsp_pc=old_f_pc;
                fetch_rsp_instruction=~64'b0;fetch_rsp_error=1;f_ambient=1;
            end
            if(inject_stale&&old_c_valid&&!c_pending)begin
                cache_rsp_valid=1;cache_rsp_tag=old_c_tag;cache_rsp_epoch=old_c_epoch;
                cache_rsp_program=old_c_program;cache_rsp_index=old_c_index;
                cache_rsp_data=~512'b0;cache_rsp_error=1;c_ambient=1;
            end
            if(f_pending&&!block_fetch)begin
                slot=f_program*512+f_pc;instruction=programs[slot];
                fetch_rsp_valid=1;fetch_rsp_tag=f_tag;fetch_rsp_epoch=f_epoch;
                fetch_rsp_program=f_program;fetch_rsp_pc=f_pc;fetch_rsp_instruction=instruction;
                if(instruction[7:0]==13)begin
                    index=instruction[63:32];
                    if(instruction[63:32]>=239)$fatal(1,"prepared reciprocal index outside bound table");
                    fetch_rsp_rcp_valid=1;fetch_rsp_rcp_index=instruction[63:32];fetch_rsp_rcp_value=reciprocals[index];
                end
                if(inject_stale&&old_f_valid&&!f_replayed)begin
                    if(old_f_tag==f_tag)$fatal(1,"fetch identity reused after cancel");
                    fetch_rsp_tag=old_f_tag;fetch_rsp_epoch=old_f_epoch;
                    fetch_rsp_program=old_f_program;fetch_rsp_pc=old_f_pc;
                    fetch_rsp_instruction=~64'b0;fetch_rsp_error=1;f_sending_stale=1;
                end else if(fault_service==1&&f_program==0&&f_pc==0)begin
                    if(fault_kind==1)fetch_rsp_error=1;
                    else fetch_rsp_epoch=f_epoch^16'h8000;
                end
            end
            if(c_pending&&!block_cache)begin
                cache_rsp_valid=1;cache_rsp_tag=c_tag;cache_rsp_epoch=c_epoch;
                cache_rsp_program=c_program;cache_rsp_index=c_index;cache_rsp_data=c_payload;
                if(inject_stale&&old_c_valid&&!c_replayed)begin
                    if(old_c_tag==c_tag)$fatal(1,"cache identity reused after cancel");
                    cache_rsp_tag=old_c_tag;cache_rsp_epoch=old_c_epoch;
                    cache_rsp_program=old_c_program;cache_rsp_index=old_c_index;
                    cache_rsp_data=~512'b0;cache_rsp_error=1;c_sending_stale=1;
                end else if(fault_service==2&&c_program==0)begin
                    if(fault_kind==1)cache_rsp_error=1;
                    else cache_rsp_epoch=c_epoch^16'h8000;
                end
            end
        end
        @(posedge clk);
        if(rst)begin
            reserved_model=0;requested_model=0;completed_model=0;ds_requests_model=0;ds_responses_model=0;
        end else begin
            if(batch_valid&&batch_ready)begin
                reserved_model=reserved_model+ITEMS_PER_BATCH;batches=batches+1;
                captured_generation=batch_generation;captured_epoch=image_epoch;
                captured_counts=counts;captured_addresses=address_regs;
            end
            if(ds_req_valid&&ds_req_ready)begin
                ds_requests_model=ds_requests_model+1;requests=requests+1;
                owned_address=ds_req_addr;owned_ds_tag=ds_req_tag;commits=0;stages=0;run_ticks=0;multiply_delivered=0;
                fetch_accepts=0;cache_accepts=0;f_wait=0;c_wait=0;
            end
            if(item_req_valid&&item_req_ready)begin
                if(!ds_req_valid||!ds_req_ready||item_req_item!==(ds_req_addr>>6)||
                   item_req_epoch!==captured_epoch||item_req_tag!==ds_req_tag[15:0])
                    $fatal(1,"dataset_service child admission identity/capture");
                live_item_tag=item_req_tag;requested_model=requested_model+1;
            end
            if(ds_rsp_valid&&ds_rsp_ready)begin ds_responses_model=ds_responses_model+1;returns=returns+1;end
            if(item_rsp_valid&&item_rsp_ready&&!item_rsp_error&&item_rsp_completed_stages==8)
                completed_model=completed_model+1;
        end
        if(!rst&&!cancel)begin
            if(f_held&&(!fetch_valid||now_fetch!==held_fetch))$fatal(1,"held fetch request changed");
            if(c_held&&(!cache_req_valid||now_cache!==held_cache))$fatal(1,"held cache request changed");
            f_held=fetch_valid&&!fetch_ready;held_fetch=now_fetch;
            c_held=cache_req_valid&&!cache_req_ready;held_cache=now_cache;
            if(fetch_valid&&!fetch_ready)begin f_wait=f_wait+1;service_stalls=service_stalls+1;end
            if(cache_req_valid&&!cache_req_ready)begin c_wait=c_wait+1;service_stalls=service_stalls+1;end
            if(fetch_rsp_valid&&fetch_rsp_ready)begin
                if(f_ambient)stale_packets=stale_packets+1;
                else if(f_sending_stale)begin f_replayed=1;stale_packets=stale_packets+1;end
                else begin multiply_delivered=is_multiply(fetch_rsp_instruction[7:0]);f_pending=0;end
            end
            if(cache_rsp_valid&&cache_rsp_ready)begin
                if(c_ambient)stale_packets=stale_packets+1;
                else if(c_sending_stale)begin c_replayed=1;stale_packets=stale_packets+1;end
                else c_pending=0;
            end
            if(fetch_valid&&fetch_ready)begin
                if(f_pending||fetch_epoch!==captured_epoch||fetch_tag[15:0]!==live_item_tag||
                   fetch_pc>=captured_counts[fetch_program*10+:10])$fatal(1,"fetch accepted immutable-input identity");
                f_pending=1;f_tag=fetch_tag;f_epoch=fetch_epoch;f_program=fetch_program;f_pc=fetch_pc;f_replayed=0;
                fetch_accepts=fetch_accepts+1;f_wait=0;
            end
            if(cache_req_valid&&cache_req_ready)begin
                if(c_pending||cache_req_epoch!==captured_epoch||cache_req_tag[15:0]!==live_item_tag)
                    $fatal(1,"cache accepted immutable-input identity");
                c_pending=1;c_tag=cache_req_tag;c_epoch=cache_req_epoch;
                c_program=cache_req_program;c_index=cache_req_index;c_replayed=0;read_cache(cache_req_index,c_payload);
                cache_accepts=cache_accepts+1;c_wait=0;
            end
        end
        #1;
        remaining_model=8191-reserved_model;
        if(items_reserved!==reserved_model[13:0]||items_remaining!==remaining_model[13:0]||
           items_requested!==requested_model||items_completed!==completed_model||
           ds_requests!==ds_requests_model||ds_responses!==ds_responses_model)
            $fatal(1,"dataset_service ledger mismatch reserved=%0d/%0d remaining=%0d/%0d requested=%0d/%0d completed=%0d/%0d ds=%0d/%0d returns=%0d/%0d",
                items_reserved,reserved_model,items_remaining,remaining_model,items_requested,requested_model,
                items_completed,completed_model,ds_requests,ds_requests_model,ds_responses,ds_responses_model);
        if(!rst&&!cancel)begin
            if(item_commit_valid)begin commits=commits+1;all_commits=all_commits+1;end
            if(item_stage_valid)begin
                if(item_stage_program!==stages[2:0])$fatal(1,"dataset_service XOR stage sequence");
                stages=stages+1;all_stages=all_stages+1;
            end
        end
        run_ticks=run_ticks+1;total_ticks=total_ticks+1;
        if(run_ticks>200000||total_ticks>4000000)$fatal(1,"dataset_service bounded timeout phase=%0d item_phase=%0d",phase,item_phase);
    end endtask

    task quiescent_reset;
    begin
        // Caller drains/abandons all owned traffic before recycling identities.
        if(!rst&&(batch_active||ds_rsp_valid||item_rsp_valid||fetch_valid||cache_req_valid||f_pending||c_pending))
            $fatal(1,"hard reset requires externally quiescent service traffic");
        batch_valid=0;batch_end=0;ds_req_valid=0;ds_rsp_ready=0;cancel=0;rst=1;
        f_pending=0;c_pending=0;f_held=0;c_held=0;old_f_valid=0;old_c_valid=0;
        block_fetch=0;block_cache=0;inject_stale=0;fault_service=0;fault_kind=0;stall_services=0;f_wait=0;c_wait=0;
        step;rst=0;#1;
        if(!batch_ready||batch_active||ds_rsp_valid||fetch_valid||cache_req_valid||generation_exhausted)
            $fatal(1,"dataset_service quiescent reset");
    end endtask

    task begin_batch;
        input [15:0] generation,epoch;
        input [79:0] requested_counts;
        input [63:0] requested_addresses;
    begin
        #1;if(!batch_ready)$fatal(1,"dataset_service batch not ready reserved=%0d",items_reserved);
        batch_valid=1;batch_generation=generation;image_epoch=epoch;
        counts=requested_counts;address_regs=requested_addresses;rcp_count=239;batch_end=0;
        step;batch_valid=0;
        // Poison every live descriptor after the batch handshake.
        batch_generation=~generation;image_epoch=~epoch;counts=~80'b0;address_regs=~64'b0;rcp_count=0;
        #1;if(!batch_active||batch_ready)$fatal(1,"dataset_service batch ownership/capture");
    end endtask

    task end_batch;
    begin
        batch_valid=0;ds_req_valid=0;ds_rsp_ready=0;batch_end=1;step;batch_end=0;#1;
        if(batch_active||ds_rsp_valid||fetch_valid||cache_req_valid)$fatal(1,"dataset_service batch_end not quiescent");
    end endtask

    task begin_request;
        input [63:0] address;
        input [31:0] tag;
    begin
        #1;if(!ds_req_ready)$fatal(1,"dataset_service DS admission not ready");
        ds_req_valid=1;ds_req_addr=address;ds_req_tag=tag;ds_rsp_ready=0;
        step;ds_req_valid=0;ds_req_addr=~address;ds_req_tag=~tag;
        if(ds_req_ready)$fatal(1,"dataset_service accepted replacement while response pending");
    end endtask

    task finish_request;
        input integer expect_error,expect_child,native_check,expected_error_stage;
        input [63:0] before_requested;
        reg [511:0] expected;
        integer k;
    begin
        while(!ds_rsp_valid)step;
        if(ds_rsp_tag!==owned_ds_tag||ds_rsp_error!==expect_error[0]||
           items_requested!==before_requested+expect_child||f_pending||c_pending)
            $fatal(1,"dataset_service terminal tag/error/admission mismatch");
        if(expect_error)begin
            if(ds_rsp_data!==512'b0||stages!=0)$fatal(1,"DS error leaked data or performed cache XOR");
            if(expect_child)begin
                if(!item_rsp_valid||!item_rsp_error||item_rsp_error_stage!==expected_error_stage[2:0]||item_rsp_error_pc!==9'b0)
                    $fatal(1,"dataset_service child error location/classification");
                child_errors=child_errors+1;
            end else local_errors=local_errors+1;
        end else begin
            if(stages!=8||item_rsp_completed_stages!=8||item_rsp_error||ds_rsp_data!==item_rsp_data)
                $fatal(1,"dataset_service successful return lost item payload");
            if(native_check)begin
`ifdef VERILATOR
                rx_dataset_assertion(owned_address,expected);
`else
                $rx_dataset_assertion(owned_address,expected);
`endif
                if(ds_rsp_data!==expected)$fatal(1,"dataset_service actual native dataset mismatch address=%h",owned_address);
                native_assertions=native_assertions+1;
            end
        end
        held_return=now_return;
        for(k=0;k<4;k=k+1)begin
            ds_req_valid=1;batch_valid=1;
            step;
            if(!ds_rsp_valid||now_return!==held_return||ds_req_ready||batch_ready||fetch_valid||cache_req_valid||
               item_commit_valid||item_stage_valid)$fatal(1,"dataset_service held response/capture changed");
            held_checks=held_checks+1;
        end
        ds_req_valid=0;batch_valid=0;ds_rsp_ready=1;step;ds_rsp_ready=0;
        if(ds_rsp_valid)$fatal(1,"dataset_service response did not transfer once");
    end endtask

    task good_request;
        input [63:0] address;
        input [31:0] tag;
        reg [63:0] before_requested;
    begin
        before_requested=items_requested;begin_request(address,tag);
        finish_request(0,1,1,0,before_requested);
    end endtask

    task local_bad;
        input [63:0] address;
        input [31:0] tag;
        reg [63:0] before_requested;
    begin
        begin_batch(16'ha5d3,16'h82a5,native_counts,native_addresses);
        before_requested=items_requested;begin_request(address,tag);
        finish_request(1,0,0,0,before_requested);end_batch;
    end endtask

    task cancel_context;
    begin
        if(f_tag!=0)begin old_f_valid=1;old_f_tag=f_tag;old_f_epoch=f_epoch;old_f_program=f_program;old_f_pc=f_pc;end
        if(c_tag!=0)begin old_c_valid=1;old_c_tag=c_tag;old_c_epoch=c_epoch;old_c_program=c_program;old_c_index=c_index;end
        cancel=1;batch_valid=0;batch_end=0;ds_req_valid=0;ds_rsp_ready=0;step;
        f_pending=0;c_pending=0;f_held=0;c_held=0;cancel=0;#1;
        if(batch_active||ds_rsp_valid||item_rsp_valid||fetch_valid||cache_req_valid||item_commit_valid||item_stage_valid)
            $fatal(1,"dataset_service cancel left abandoned traffic visible");
        cancellations=cancellations+1;
    end endtask

    task normal_checks;
    begin
        quiescent_reset;
        begin_batch(16'ha5d3,16'h82a5,native_counts,native_addresses);
        good_request(64'd0,32'ha5d3d173);
        stall_services=1;good_request(64'd64,32'ha5d38173);stall_services=0;
        // Third item must fail locally even though its address is valid.
        begin : excess
            reg [63:0] before_requested;
            before_requested=items_requested;begin_request(64'd128,32'ha5d3d173);
            finish_request(1,0,0,0,before_requested);
        end
        end_batch;
        begin_batch(16'h5aa6,16'h19c7,native_counts,native_addresses);
        good_request(LAST_ADDRESS,32'h5aa6d173);end_batch;
    end endtask

    task error_checks;
        integer d,k,service;
        reg [79:0] bad_counts;
        reg [63:0] bad_addresses,before_requested;
    begin
        quiescent_reset;
        local_bad(64'd1,32'ha5d3d173);
        local_bad(LAST_ADDRESS+1,32'ha5d3d173);
        local_bad(LAST_ADDRESS+64,32'ha5d3d173);
        local_bad(64'h0000000181ffff80,32'ha5d3d173);
        local_bad(64'h8000000000000000,32'ha5d3d173);
        local_bad(64'd0,32'h25d3d173);
        local_bad(64'd0,32'ha5d2d173);
        for(d=0;d<8;d=d+1)begin
            for(k=0;k<2;k=k+1)begin
                bad_counts=native_counts;bad_addresses=native_addresses;
                if(k==0)bad_counts[d*10+:10]=10'd513;
                else bad_addresses[d*8+:8]=8'd8;
                begin_batch(16'ha5d3,16'h82a5,bad_counts,bad_addresses);
                before_requested=items_requested;begin_request(0,32'ha5d3d173);
                finish_request(1,1,0,d,before_requested);
                if(commits||stages||fetch_accepts||cache_accepts||f_pending||c_pending)$fatal(1,"invalid descriptor performed work");
                end_batch;
            end
        end
        for(service=1;service<=2;service=service+1)begin
            for(k=1;k<=2;k=k+1)begin
                fault_service=service;fault_kind=k;
                begin_batch(16'ha5d3,16'h82a5,native_counts,native_addresses);
                before_requested=items_requested;begin_request(0,32'ha5d3d173);
                finish_request(1,1,0,0,before_requested);end_batch;
            end
        end
        fault_service=0;fault_kind=0;
    end endtask

    task cancel_checks;
        integer target,prior_commits;
    begin
        quiescent_reset;
        for(target=0;target<4;target=target+1)begin
            block_fetch=target==1;block_cache=target==0;
            begin_batch(16'h9321,16'h3100+target,native_counts,native_addresses);
            begin_request(target*64,32'h9321d173);
            case(target)
                0:while(!c_pending)step;
                1:while(!f_pending)step;
                2:begin
                    while(!multiply_delivered)step;
                    prior_commits=commits;repeat(2)step;
                    if(commits!=prior_commits||item_phase!=4)$fatal(1,"multiply cancel target already retired");
                end
                3:while(item_phase!=2)step;
            endcase
            cancel_context;
        end
        block_fetch=0;block_cache=0;inject_stale=1;
        repeat(3)step;
        begin_batch(16'h9321,16'h7e42,native_counts,native_addresses);
        // Same complete DS caller tag, different epoch and item, no reset.
        good_request(64'd320,32'h9321d173);end_batch;
        inject_stale=0;
        if(!old_f_valid||!old_c_valid||stale_packets==0)$fatal(1,"canceled service traffic was not replayed/drained");
    end endtask

    task budget_checks;
        integer b;
        reg [63:0] old_requested;
    begin
        quiescent_reset;
        for(b=0;b<4095;b=b+1)begin
            begin_batch(16'h40a5,16'h62c3,native_counts,native_addresses);
            old_requested=items_requested;cancel_context;
            if(items_requested!==old_requested)$fatal(1,"budget loop launched an item");
            budget_batches=budget_batches+1;
        end
        budget_remaining=items_remaining;
        if(items_reserved!=8190||items_remaining!=1||!generation_exhausted||batch_ready)
            $fatal(1,"public N2 reservation exhaustion reserved=%0d remaining=%0d",items_reserved,items_remaining);
        batch_valid=1;batch_generation=16'h7777;image_epoch=16'h8888;
        repeat(4)begin step;if(batch_ready||batch_active||items_reserved!=8190||items_remaining!=1)$fatal(1,"insufficient reservation admitted N2");end
        batch_valid=0;quiescent_reset;
        begin_batch(16'hc15e,16'hc20f,native_counts,native_addresses);
        good_request(64'd384,32'hc15ed173);end_batch;reset_recoveries=reset_recoveries+1;
    end endtask

    initial begin
        if(ITEMS_PER_BATCH!=2)$fatal(1,"this standalone ledger contract requires ITEMS_PER_BATCH=2");
        if(!$value$plusargs("asset_root=%s",asset_root))$fatal(1,"+asset_root=RX_PREPARED_CACHE_ROOT is required");
        if(!$value$plusargs("output=%s",output_directory))$fatal(1,"+output=fresh_unit_output_directory is required");
        if(!$value$plusargs("MODE=%s",mode))mode="all";
        if(mode!="normal"&&mode!="errors"&&mode!="cancel"&&mode!="budget"&&mode!="all")$fatal(1,"unknown dataset_service MODE");
        path=$sformatf("%s/cache-0-prepared-programs.mem",asset_root);$readmemh(path,programs);
        path=$sformatf("%s/cache-0-reciprocals.mem",asset_root);$readmemh(path,reciprocals);
        path=$sformatf("%s/cache-0.bin",asset_root);cache_fd=$fopen(path,"rb");
        if(!cache_fd)$fatal(1,"cannot open immutable cache-0.bin");
        native_counts=0;native_addresses=0;
        native_counts[0+:10]=447;native_counts[10+:10]=438;native_counts[20+:10]=449;native_counts[30+:10]=447;
        native_counts[40+:10]=444;native_counts[50+:10]=449;native_counts[60+:10]=452;native_counts[70+:10]=437;
        native_addresses[0+:8]=4;native_addresses[8+:8]=5;native_addresses[16+:8]=4;native_addresses[24+:8]=3;
        native_addresses[32+:8]=4;native_addresses[40+:8]=0;native_addresses[48+:8]=5;native_addresses[56+:8]=0;
        for(i=0;i<8;i=i+1)begin
            for(j=0;j<native_counts[i*10+:10];j=j+1)
                if(^programs[i*512+j]===1'bx)$fatal(1,"missing immutable prepared instruction stage=%0d pc=%0d",i,j);
        end
        for(i=0;i<239;i=i+1)
            if(^reciprocals[i]===1'bx)$fatal(1,"missing immutable reciprocal index=%0d",i);
        if(mode=="normal"||mode=="all")normal_checks;
        if(mode=="errors"||mode=="all")error_checks;
        if(mode=="cancel"||mode=="all")cancel_checks;
        if(mode=="budget"||mode=="all")budget_checks;
        $fclose(cache_fd);
        path=$sformatf("%s/provider-host-time.json",output_directory);
`ifdef VERILATOR
        rx_provider_stats(path);
`else
        $rx_provider_stats(path);
`endif
        $display("PASS dataset_service mode=%0s batch_accepts=%0d ds_accepts=%0d ds_returns=%0d native_assertions=%0d held_checks=%0d local_errors=%0d child_errors=%0d cancellations=%0d stale_packets=%0d budget_batches=%0d budget_remaining=%0d reset_recoveries=%0d commits=%0d stages=%0d service_stalls=%0d",
            mode,batches,requests,returns,native_assertions,held_checks,local_errors,child_errors,cancellations,
            stale_packets,budget_batches,budget_remaining,reset_recoveries,all_commits,all_stages,service_stalls);
        $finish;
    end
endmodule
