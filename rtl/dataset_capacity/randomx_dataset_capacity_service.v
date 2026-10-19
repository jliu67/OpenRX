// SPDX-License-Identifier: BSD-3-Clause
// Dataset-byte-address service over the unchanged prepared native item core.
// A whole hash attempt burns its item reservation before any dataset work.
`default_nettype none
module randomx_dataset_capacity_service #(parameter integer ITEMS_PER_BATCH=1,MUL_RADIX4=1,SESSION_BITS=32)(
    input wire clk,rst,cancel,
    input wire batch_valid,output wire batch_ready,input wire batch_end,
    input wire [15:0] batch_generation,image_epoch,
    input wire [79:0] counts,input wire [63:0] address_regs,
    input wire [31:0] rcp_count,
    input wire ds_req_valid,output wire ds_req_ready,
    input wire [63:0] ds_req_addr,input wire [31:0] ds_req_tag,
    output wire ds_rsp_valid,input wire ds_rsp_ready,
    output wire [31:0] ds_rsp_tag,output wire [511:0] ds_rsp_data,output wire ds_rsp_error,
    output wire cache_req_valid,input wire cache_req_ready,
    output wire [63:0] cache_req_tag,output wire [15:0] cache_req_epoch,
    output wire [2:0] cache_req_program,output wire [21:0] cache_req_index,
    input wire cache_rsp_valid,output wire cache_rsp_ready,
    input wire [63:0] cache_rsp_tag,input wire [15:0] cache_rsp_epoch,
    input wire [2:0] cache_rsp_program,input wire [21:0] cache_rsp_index,
    input wire [511:0] cache_rsp_data,input wire cache_rsp_error,
    output wire fetch_valid,input wire fetch_ready,
    output wire [63:0] fetch_tag,output wire [15:0] fetch_epoch,
    output wire [2:0] fetch_program,output wire [8:0] fetch_pc,
    input wire fetch_rsp_valid,output wire fetch_rsp_ready,
    input wire [63:0] fetch_rsp_tag,input wire [15:0] fetch_rsp_epoch,
    input wire [2:0] fetch_rsp_program,input wire [8:0] fetch_rsp_pc,
    input wire [63:0] fetch_rsp_instruction,input wire fetch_rsp_error,fetch_rsp_rcp_valid,
    input wire [31:0] fetch_rsp_rcp_index,input wire [63:0] fetch_rsp_rcp_value,
    output wire [1:0] phase,output wire [3:0] item_phase,
    output wire generation_exhausted,batch_active,
    output wire [31:0] items_reserved,items_remaining,
    output wire [63:0] items_requested,items_completed,ds_requests,ds_responses,
    output wire item_req_valid,item_req_ready,
    output wire [15:0] item_req_tag,item_req_epoch,output wire [63:0] item_req_item,
    output wire item_rsp_valid,item_rsp_ready,
    output wire [15:0] item_rsp_tag,item_rsp_epoch,output wire [511:0] item_rsp_data,
    output wire item_rsp_error,output wire [2:0] item_rsp_error_stage,
    output wire [8:0] item_rsp_error_pc,output wire [3:0] item_rsp_completed_stages,
    output wire [12:0] item_rsp_retired,item_rsp_muls,
    output wire [63:0] item_rsp_cycles,item_rsp_exec_cycles,item_rsp_core_cycles,
    output wire [1:0] item_session_phase,
    output wire [31:0] item_namespace,item_sessions_used,
    output wire item_commit_valid,output wire [2:0] item_commit_program,
    output wire [8:0] item_commit_pc,output wire [7:0] item_commit_opcode,
    output wire [511:0] item_commit_r,
    output wire item_stage_valid,output wire [2:0] item_stage_program,
    output wire [21:0] item_stage_cache_index,output wire [511:0] item_stage_r,
    output wire [63:0] item_stage_selected,item_stage_program_cycles
);
    localparam [1:0] IDLE=0,ITEM=1,ERROR=2;
    localparam [63:0] SESSION_LIMIT=(SESSION_BITS>=1&&SESSION_BITS<=32)?
        ((64'd1<<SESSION_BITS)-64'd1):64'b0;
    localparam [63:0] BATCH_ITEMS=ITEMS_PER_BATCH;
    localparam [31:0] SESSION_MAX=SESSION_LIMIT[31:0];
    reg [1:0] state_q;
    reg batch_active_q;
    reg [15:0] batch_generation_q,epoch_q;
    reg [79:0] counts_q;reg [63:0] address_regs_q;reg [31:0] rcp_count_q;
    reg [31:0] tag_q;
    reg [31:0] reserved_q,seen_q;
    reg [63:0] requested_q,completed_q,ds_requests_q,ds_responses_q;
    wire active=!rst&&!cancel;
    wire item_exhausted;
    wire [63:0] reservation_sum={32'b0,reserved_q}+BATCH_ITEMS;
    wire owned=active&&batch_active_q&&!batch_end;
    wire request_error=ds_req_addr[5:0]!=0||ds_req_addr>64'h0000000081ffff80||
        ds_req_tag[31:16]!=batch_generation_q||seen_q>=ITEMS_PER_BATCH;
    wire response_error=item_rsp_error||item_rsp_tag!=tag_q[15:0]||
        item_rsp_epoch!=epoch_q||item_rsp_completed_stages!=8;
    generate if(SESSION_BITS<1||SESSION_BITS>32)begin: invalid_session_width
        dataset_service_requires_SESSION_BITS_1_to_32 invalid();
    end
    if(ITEMS_PER_BATCH<1||ITEMS_PER_BATCH>65535||BATCH_ITEMS>SESSION_LIMIT)begin: invalid_batch_capacity
        dataset_service_requires_batch_1_to_min_65535_SESSION_MAX invalid();
    end endgenerate
    assign generation_exhausted=!rst&&(reservation_sum>SESSION_LIMIT||item_exhausted);
    assign batch_ready=active&&!batch_active_q&&state_q==IDLE&&!generation_exhausted;
    assign batch_active=batch_active_q;
    assign items_reserved=reserved_q;assign items_remaining=SESSION_MAX-reserved_q;
    assign items_requested=requested_q;assign items_completed=completed_q;
    assign ds_requests=ds_requests_q;assign ds_responses=ds_responses_q;
    assign phase=state_q;
    assign ds_req_ready=owned&&state_q==IDLE&&(request_error||item_req_ready);
    assign item_req_valid=owned&&state_q==IDLE&&ds_req_valid&&!request_error;
    assign item_req_tag=ds_req_tag[15:0];assign item_req_epoch=epoch_q;
    assign item_req_item={6'b0,ds_req_addr[63:6]};
    // The session adapter owns descriptor capture and measures its launch clock.
    // Direct response routing never XORs a line already mixed by the lifecycle.
    assign ds_rsp_valid=owned&&(state_q==ERROR||(state_q==ITEM&&item_rsp_valid));
    assign ds_rsp_tag=tag_q;
    assign ds_rsp_error=state_q==ERROR||response_error;
    assign ds_rsp_data=state_q==ITEM&&!response_error?item_rsp_data:512'b0;
    assign item_rsp_ready=owned&&state_q==ITEM&&ds_rsp_ready;

    randomx_dataset_item_session #(.MUL_RADIX4(MUL_RADIX4),.SESSION_BITS(SESSION_BITS)) item(
        .clk(clk),.rst(rst),.cancel(cancel),
        .req_valid(item_req_valid),.req_ready(item_req_ready),
        .req_tag(item_req_tag),.req_epoch(item_req_epoch),.req_item(item_req_item),
        .req_counts(counts_q),.req_address_regs(address_regs_q),.req_rcp_count(rcp_count_q),
        .rsp_valid(item_rsp_valid),.rsp_ready(item_rsp_ready),
        .rsp_tag(item_rsp_tag),.rsp_epoch(item_rsp_epoch),.rsp_data(item_rsp_data),
        .rsp_error(item_rsp_error),.rsp_error_stage(item_rsp_error_stage),.rsp_error_pc(item_rsp_error_pc),
        .rsp_completed_stages(item_rsp_completed_stages),.rsp_retired(item_rsp_retired),.rsp_muls(item_rsp_muls),
        .rsp_cycles(item_rsp_cycles),.rsp_exec_cycles(item_rsp_exec_cycles),
        .cache_req_valid(cache_req_valid),.cache_req_ready(cache_req_ready),
        .cache_req_tag(cache_req_tag),.cache_req_epoch(cache_req_epoch),
        .cache_req_program(cache_req_program),.cache_req_index(cache_req_index),
        .cache_rsp_valid(cache_rsp_valid),.cache_rsp_ready(cache_rsp_ready),
        .cache_rsp_tag(cache_rsp_tag),.cache_rsp_epoch(cache_rsp_epoch),
        .cache_rsp_program(cache_rsp_program),.cache_rsp_index(cache_rsp_index),
        .cache_rsp_data(cache_rsp_data),.cache_rsp_error(cache_rsp_error),
        .fetch_valid(fetch_valid),.fetch_ready(fetch_ready),.fetch_tag(fetch_tag),
        .fetch_epoch(fetch_epoch),.fetch_program(fetch_program),.fetch_pc(fetch_pc),
        .fetch_rsp_valid(fetch_rsp_valid),.fetch_rsp_ready(fetch_rsp_ready),
        .fetch_rsp_tag(fetch_rsp_tag),.fetch_rsp_epoch(fetch_rsp_epoch),
        .fetch_rsp_program(fetch_rsp_program),.fetch_rsp_pc(fetch_rsp_pc),
        .fetch_rsp_instruction(fetch_rsp_instruction),.fetch_rsp_error(fetch_rsp_error),
        .fetch_rsp_rcp_valid(fetch_rsp_rcp_valid),.fetch_rsp_rcp_index(fetch_rsp_rcp_index),
        .fetch_rsp_rcp_value(fetch_rsp_rcp_value),
        .commit_valid(item_commit_valid),.commit_program(item_commit_program),
        .commit_pc(item_commit_pc),.commit_opcode(item_commit_opcode),.commit_r(item_commit_r),
        .stage_valid(item_stage_valid),.stage_program(item_stage_program),
        .stage_cache_index(item_stage_cache_index),.stage_r(item_stage_r),
        .stage_selected(item_stage_selected),.stage_program_cycles(item_stage_program_cycles),
        .generation_exhausted(item_exhausted),.phase(item_phase),
        .session_phase(item_session_phase),.session_namespace(item_namespace),
        .sessions_used(item_sessions_used),.rsp_core_cycles(item_rsp_core_cycles)
    );

    // Full reservations and actual-transfer statistics are separate lifetime
    // ledgers. Neither cancellation nor ordinary completion refunds a budget.
    always @(posedge clk)begin
        if(rst)begin
            reserved_q<=0;requested_q<=0;completed_q<=0;ds_requests_q<=0;ds_responses_q<=0;
        end else begin
            if(batch_valid&&batch_ready)reserved_q<=reservation_sum[31:0];
            if(ds_req_valid&&ds_req_ready)ds_requests_q<=ds_requests_q+1'b1;
            if(ds_rsp_valid&&ds_rsp_ready)ds_responses_q<=ds_responses_q+1'b1;
            if(item_req_valid&&item_req_ready)requested_q<=requested_q+1'b1;
            if(item_rsp_valid&&item_rsp_ready&&!response_error)completed_q<=completed_q+1'b1;
        end
        if(rst||cancel)begin
            state_q<=IDLE;batch_active_q<=0;batch_generation_q<=0;epoch_q<=0;
            counts_q<=0;address_regs_q<=0;rcp_count_q<=0;tag_q<=0;seen_q<=0;
        end else if(batch_valid&&batch_ready)begin
            batch_active_q<=1;batch_generation_q<=batch_generation;epoch_q<=image_epoch;
            counts_q<=counts;address_regs_q<=address_regs;rcp_count_q<=rcp_count;seen_q<=0;
        end else if(batch_end&&state_q==IDLE)begin
            batch_active_q<=0;seen_q<=0;
        end else begin
            case(state_q)
                IDLE:if(ds_req_valid&&ds_req_ready)begin
                    tag_q<=ds_req_tag;
                    if(seen_q<ITEMS_PER_BATCH)seen_q<=seen_q+1'b1;
                    if(request_error)state_q<=ERROR;else state_q<=ITEM;
                end
                ITEM,ERROR:if(ds_rsp_valid&&ds_rsp_ready)state_q<=IDLE;
                default:state_q<=IDLE;
            endcase
        end
    end
endmodule
`default_nettype wire
