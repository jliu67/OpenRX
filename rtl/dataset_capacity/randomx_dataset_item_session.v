// SPDX-License-Identifier: BSD-3-Clause
// Non-recycled outer identity permits safe private accepted-core resets between
// items. The licensed/native item arithmetic and inner executor stay unchanged.
`default_nettype none
module randomx_dataset_item_session #(parameter integer MUL_RADIX4=1,SESSION_BITS=32)(
    input wire clk,rst,cancel,
    input wire req_valid,output wire req_ready,
    input wire [15:0] req_tag,req_epoch,
    input wire [63:0] req_item,
    input wire [79:0] req_counts,
    input wire [63:0] req_address_regs,
    input wire [31:0] req_rcp_count,
    output wire rsp_valid,input wire rsp_ready,
    output wire [15:0] rsp_tag,rsp_epoch,
    output wire [511:0] rsp_data,
    output wire rsp_error,
    output wire [2:0] rsp_error_stage,
    output wire [8:0] rsp_error_pc,
    output wire [3:0] rsp_completed_stages,
    output wire [12:0] rsp_retired,rsp_muls,
    output wire [63:0] rsp_cycles,rsp_exec_cycles,
    output wire cache_req_valid,input wire cache_req_ready,
    output wire [63:0] cache_req_tag,
    output wire [15:0] cache_req_epoch,
    output wire [2:0] cache_req_program,
    output wire [21:0] cache_req_index,
    input wire cache_rsp_valid,output wire cache_rsp_ready,
    input wire [63:0] cache_rsp_tag,
    input wire [15:0] cache_rsp_epoch,
    input wire [2:0] cache_rsp_program,
    input wire [21:0] cache_rsp_index,
    input wire [511:0] cache_rsp_data,
    input wire cache_rsp_error,
    output wire fetch_valid,input wire fetch_ready,
    output wire [63:0] fetch_tag,
    output wire [15:0] fetch_epoch,
    output wire [2:0] fetch_program,
    output wire [8:0] fetch_pc,
    input wire fetch_rsp_valid,output wire fetch_rsp_ready,
    input wire [63:0] fetch_rsp_tag,
    input wire [15:0] fetch_rsp_epoch,
    input wire [2:0] fetch_rsp_program,
    input wire [8:0] fetch_rsp_pc,
    input wire [63:0] fetch_rsp_instruction,
    input wire fetch_rsp_error,fetch_rsp_rcp_valid,
    input wire [31:0] fetch_rsp_rcp_index,
    input wire [63:0] fetch_rsp_rcp_value,
    output wire commit_valid,
    output wire [2:0] commit_program,
    output wire [8:0] commit_pc,
    output wire [7:0] commit_opcode,
    output wire [511:0] commit_r,
    output wire stage_valid,
    output wire [2:0] stage_program,
    output wire [21:0] stage_cache_index,
    output wire [511:0] stage_r,
    output wire [63:0] stage_selected,stage_program_cycles,
    output wire generation_exhausted,
    output wire [3:0] phase,
    output wire [1:0] session_phase,
    output wire [31:0] session_namespace,sessions_used,
    output wire [63:0] rsp_core_cycles
);

    localparam [1:0] IDLE=0,LAUNCH=1,ACTIVE=2;
    localparam [63:0] SESSION_LIMIT=(SESSION_BITS>=1&&SESSION_BITS<=32)?
        ((64'd1<<SESSION_BITS)-64'd1):64'b0;
    localparam [31:0] SESSION_MAX=SESSION_LIMIT[31:0];
    reg [1:0] state_q;
    reg [31:0] namespace_counter_q,namespace_q;
    reg [15:0] tag_q,epoch_q;
    reg [63:0] item_q,address_regs_q,cycles_q;
    reg [79:0] counts_q;
    reg [31:0] rcp_count_q;
    wire active=!rst&&!cancel;
    // An accepted descriptor edge always samples a private reset. Only the
    // retained outer namespace may distinguish replies after this local reset.
    wire core_rst=rst||cancel||state_q==IDLE;
    wire forwarding=active&&state_q==ACTIVE;
    wire core_req_ready,core_rsp_valid,core_generation_exhausted;
    wire core_cache_req_valid,core_cache_rsp_ready,core_fetch_valid,core_fetch_rsp_ready;
    wire [31:0] core_cache_req_tag,core_fetch_tag;
    wire cache_current=cache_rsp_tag[63:32]==namespace_q;
    wire fetch_current=fetch_rsp_tag[63:32]==namespace_q;
    generate if(SESSION_BITS<1||SESSION_BITS>32)begin: invalid_session_width
        dataset_item_session_requires_SESSION_BITS_1_to_32 invalid();
    end endgenerate
    assign generation_exhausted=!rst&&namespace_counter_q==SESSION_MAX;
    assign req_ready=active&&state_q==IDLE&&!generation_exhausted;
    assign rsp_valid=forwarding&&core_rsp_valid;
    assign rsp_cycles=cycles_q;
    assign session_phase=state_q;
    assign session_namespace=namespace_q;assign sessions_used=namespace_counter_q;
    assign cache_req_valid=forwarding&&core_cache_req_valid;
    assign fetch_valid=forwarding&&core_fetch_valid;
    assign cache_req_tag={namespace_q,core_cache_req_tag};
    assign fetch_tag={namespace_q,core_fetch_tag};
    // Old namespaces drain before low-tag reconstruction. A matching early
    // response is held in LAUNCH; ACTIVE delegates low-tag/metadata checks.
    assign cache_rsp_ready=active&&(!cache_current||state_q==IDLE||
        (state_q==ACTIVE&&core_cache_rsp_ready));
    assign fetch_rsp_ready=active&&(!fetch_current||state_q==IDLE||
        (state_q==ACTIVE&&core_fetch_rsp_ready));

    randomx_dataset_item #(.MUL_RADIX4(MUL_RADIX4)) core(
        .clk(clk),
        .rst(core_rst),
        .cancel(cancel),
        .req_valid(active&&state_q==LAUNCH),
        .req_ready(core_req_ready),
        .req_tag(tag_q),
        .req_epoch(epoch_q),
        .req_item(item_q),
        .req_counts(counts_q),
        .req_address_regs(address_regs_q),
        .req_rcp_count(rcp_count_q),
        .rsp_valid(core_rsp_valid),
        .rsp_ready(forwarding&&rsp_ready),
        .rsp_tag(rsp_tag),
        .rsp_epoch(rsp_epoch),
        .rsp_data(rsp_data),
        .rsp_error(rsp_error),
        .rsp_error_stage(rsp_error_stage),
        .rsp_error_pc(rsp_error_pc),
        .rsp_completed_stages(rsp_completed_stages),
        .rsp_retired(rsp_retired),
        .rsp_muls(rsp_muls),
        .rsp_cycles(rsp_core_cycles),
        .rsp_exec_cycles(rsp_exec_cycles),
        .cache_req_valid(core_cache_req_valid),
        .cache_req_ready(forwarding&&cache_req_ready),
        .cache_req_tag(core_cache_req_tag),
        .cache_req_epoch(cache_req_epoch),
        .cache_req_program(cache_req_program),
        .cache_req_index(cache_req_index),
        .cache_rsp_valid(forwarding&&cache_current&&cache_rsp_valid),
        .cache_rsp_ready(core_cache_rsp_ready),
        .cache_rsp_tag(cache_rsp_tag[31:0]),
        .cache_rsp_epoch(cache_rsp_epoch),
        .cache_rsp_program(cache_rsp_program),
        .cache_rsp_index(cache_rsp_index),
        .cache_rsp_data(cache_rsp_data),
        .cache_rsp_error(cache_rsp_error),
        .fetch_valid(core_fetch_valid),
        .fetch_ready(forwarding&&fetch_ready),
        .fetch_tag(core_fetch_tag),
        .fetch_epoch(fetch_epoch),
        .fetch_program(fetch_program),
        .fetch_pc(fetch_pc),
        .fetch_rsp_valid(forwarding&&fetch_current&&fetch_rsp_valid),
        .fetch_rsp_ready(core_fetch_rsp_ready),
        .fetch_rsp_tag(fetch_rsp_tag[31:0]),
        .fetch_rsp_epoch(fetch_rsp_epoch),
        .fetch_rsp_program(fetch_rsp_program),
        .fetch_rsp_pc(fetch_rsp_pc),
        .fetch_rsp_instruction(fetch_rsp_instruction),
        .fetch_rsp_error(fetch_rsp_error),
        .fetch_rsp_rcp_valid(fetch_rsp_rcp_valid),
        .fetch_rsp_rcp_index(fetch_rsp_rcp_index),
        .fetch_rsp_rcp_value(fetch_rsp_rcp_value),
        .commit_valid(commit_valid),
        .commit_program(commit_program),
        .commit_pc(commit_pc),
        .commit_opcode(commit_opcode),
        .commit_r(commit_r),
        .stage_valid(stage_valid),
        .stage_program(stage_program),
        .stage_cache_index(stage_cache_index),
        .stage_r(stage_r),
        .stage_selected(stage_selected),
        .stage_program_cycles(stage_program_cycles),
        .generation_exhausted(core_generation_exhausted),
        .phase(phase)
    );

    // This counter measures actual session request-to-availability clocks.
    // It includes LAUNCH and freezes as soon as the child result is available;
    // response backpressure therefore cannot inflate the availability latency.
    always @(posedge clk)begin
        if(rst)namespace_counter_q<=0;
        else if(req_valid&&req_ready)namespace_counter_q<=namespace_counter_q+1'b1;
        if(rst||cancel)begin
            state_q<=IDLE;namespace_q<=0;tag_q<=0;epoch_q<=0;item_q<=0;
            counts_q<=0;address_regs_q<=0;rcp_count_q<=0;cycles_q<=0;
        end else begin
            if(state_q==LAUNCH||(state_q==ACTIVE&&!core_rsp_valid))cycles_q<=cycles_q+1'b1;
            case(state_q)
                IDLE:if(req_valid&&req_ready)begin
                    namespace_q<=namespace_counter_q+1'b1;tag_q<=req_tag;epoch_q<=req_epoch;
                    item_q<=req_item;counts_q<=req_counts;address_regs_q<=req_address_regs;
                    rcp_count_q<=req_rcp_count;cycles_q<=0;state_q<=LAUNCH;
                end
                LAUNCH:if(core_req_ready)state_q<=ACTIVE;
                ACTIVE:if(core_rsp_valid&&rsp_ready)state_q<=IDLE;
                default:state_q<=IDLE;
            endcase
        end
    end
endmodule
`default_nettype wire
