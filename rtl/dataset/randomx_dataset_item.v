// SPDX-License-Identifier: BSD-3-Clause
// One native dataset item over immutable externally prepared programs/table and
// cache. Reuses the accepted executor and multiplier without modifying either.
`default_nettype none
module randomx_dataset_item #(parameter integer MUL_RADIX4=1)(
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
    output wire [31:0] cache_req_tag,
    output wire [15:0] cache_req_epoch,
    output wire [2:0] cache_req_program,
    output wire [21:0] cache_req_index,
    input wire cache_rsp_valid,output wire cache_rsp_ready,
    input wire [31:0] cache_rsp_tag,
    input wire [15:0] cache_rsp_epoch,
    input wire [2:0] cache_rsp_program,
    input wire [21:0] cache_rsp_index,
    input wire [511:0] cache_rsp_data,
    input wire cache_rsp_error,
    output wire fetch_valid,input wire fetch_ready,
    output wire [31:0] fetch_tag,
    output wire [15:0] fetch_epoch,
    output wire [2:0] fetch_program,
    output wire [8:0] fetch_pc,
    input wire fetch_rsp_valid,output wire fetch_rsp_ready,
    input wire [31:0] fetch_rsp_tag,
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
    output wire [3:0] phase
);
    localparam [3:0] IDLE=0,SEED_REQ=1,SEED_WAIT=2,EXEC_REQ=3,
        EXEC_WAIT=4,CACHE_REQ=5,CACHE_WAIT=6,XOR_STAGE=7,RETURN=8;
    reg [3:0] state_q,completed_q;
    reg [15:0] generation_q,exec_accepted_q,tag_q,epoch_q;
    reg [31:0] service_tag_q,rcp_count_q;
    reg [63:0] item_q,cycles_q,exec_cycles_q,program_cycles_q;
    reg [79:0] counts_q;
    reg [63:0] address_regs_q;
    reg [511:0] r_q,exec_r_q,cache_data_q;
    reg [21:0] cache_index_q;
    reg [2:0] program_q,error_stage_q;
    reg [8:0] error_pc_q;
    reg [12:0] retired_q,muls_q;
    reg error_q,stage_q;
    reg [2:0] stage_program_q;
    reg [21:0] stage_cache_index_q;
    reg [63:0] stage_selected_q,stage_cycles_q;
    wire active=!rst&&!cancel;

    // Validate the complete captured descriptor, including later stages,
    // before launching either arithmetic or an external transaction.
    reg descriptor_error;
    reg [2:0] descriptor_error_stage;
    integer d;
    always @* begin
        descriptor_error=0;descriptor_error_stage=0;
        for(d=0;d<8;d=d+1)begin
            if(!descriptor_error&&(req_counts[d*10+:10]>10'd512||
               req_address_regs[d*8+:8]>=8'd8))begin
                descriptor_error=1;descriptor_error_stage=d;
            end
        end
    end

    wire exec_generation_exhausted;
    // Each accepted item reserves room for all eight executor requests. These
    // two ledgers survive cancel; only externally quiescent reset recycles IDs.
    assign generation_exhausted=!rst&&(generation_q==16'hffff||
        exec_accepted_q>16'hfff7||exec_generation_exhausted);
    assign req_ready=active&&state_q==IDLE&&!generation_exhausted;
    assign rsp_valid=active&&state_q==RETURN;
    assign rsp_tag=tag_q;assign rsp_epoch=epoch_q;assign rsp_data=r_q;
    assign rsp_error=error_q;assign rsp_error_stage=error_stage_q;assign rsp_error_pc=error_pc_q;
    assign rsp_completed_stages=completed_q;
    assign rsp_retired=retired_q;assign rsp_muls=muls_q;
    assign rsp_cycles=cycles_q;assign rsp_exec_cycles=exec_cycles_q;
    assign phase=state_q;

    assign cache_req_valid=active&&state_q==CACHE_REQ;
    assign cache_req_tag=service_tag_q;assign cache_req_epoch=epoch_q;
    assign cache_req_program=program_q;assign cache_req_index=cache_index_q;
    // Stale outer tags drain everywhere. A current-tag packet is held until
    // an accepted cache request; IDLE/RETURN may harmlessly drain duplicates.
    assign cache_rsp_ready=active&&(cache_rsp_tag!=service_tag_q||
        state_q==CACHE_WAIT||state_q==IDLE||state_q==RETURN);

    wire seed_req_ready,seed_rsp_valid;
    wire [15:0] seed_rsp_tag;
    wire [63:0] seed_result;
    randomx_mul64 #(.RADIX4(MUL_RADIX4)) seed_multiplier(
        .clk(clk),.rst(rst||cancel),
        .req_valid(active&&state_q==SEED_REQ),.req_ready(seed_req_ready),
        .req_tag(tag_q),.req_a(item_q+64'd1),.req_b(64'h5851f42d4c957f2d),
        .req_high(1'b0),.req_signed(1'b0),
        .rsp_valid(seed_rsp_valid),.rsp_ready(active&&state_q==SEED_WAIT),
        .rsp_tag(seed_rsp_tag),.rsp_result(seed_result)
    );
    wire [511:0] seeded_r={
        seed_result^64'h84853bf7b62ce54e,seed_result^64'h2f2a56746ce62d78,
        seed_result^64'h9237efb9ceaaec0c,seed_result^64'h494d2597179f8a62,
        seed_result^64'h8126b91cbf22495c,seed_result^64'ha77099df38c2d846,
        seed_result^64'h810a978a59f5a1fc,seed_result};

    wire exec_req_valid=active&&state_q==EXEC_REQ;
    wire exec_req_ready,exec_rsp_valid,exec_rsp_error;
    wire [15:0] exec_rsp_tag,exec_rsp_epoch;
    wire [511:0] exec_rsp_r;
    wire [8:0] exec_rsp_error_pc;
    wire [63:0] exec_rsp_cycles;
    wire [9:0] exec_rsp_retired,exec_rsp_muls;
    wire exec_fetch_valid,exec_fetch_rsp_ready,exec_commit_valid;
    wire [2:0] address_reg=address_regs_q[program_q*8+:3];
    assign fetch_valid=active&&exec_fetch_valid;
    assign fetch_program=program_q;
    assign fetch_rsp_ready=active&&exec_fetch_rsp_ready;
    assign commit_valid=active&&state_q==EXEC_WAIT&&exec_commit_valid;
    assign commit_program=program_q;
    randomx_superscalar_execute #(.MUL_RADIX4(MUL_RADIX4)) executor(
        .clk(clk),.rst(rst),.cancel(cancel),
        .req_valid(exec_req_valid),.req_ready(exec_req_ready),
        .req_tag(tag_q),.req_epoch(epoch_q),.req_r(r_q),
        .req_count(counts_q[program_q*10+:10]),
        .req_address_reg(address_regs_q[program_q*8+:8]),.req_rcp_count(rcp_count_q),
        .fetch_valid(exec_fetch_valid),.fetch_ready(active&&fetch_ready),
        .fetch_tag(fetch_tag),.fetch_epoch(fetch_epoch),.fetch_pc(fetch_pc),
        .fetch_rsp_valid(active&&fetch_rsp_valid),.fetch_rsp_ready(exec_fetch_rsp_ready),
        .fetch_rsp_tag(fetch_rsp_tag),.fetch_rsp_epoch(fetch_rsp_epoch),.fetch_rsp_pc(fetch_rsp_pc),
        .fetch_rsp_instruction(fetch_rsp_instruction),
        .fetch_rsp_error(fetch_rsp_error||fetch_rsp_program!=program_q),
        .fetch_rsp_rcp_valid(fetch_rsp_rcp_valid),.fetch_rsp_rcp_index(fetch_rsp_rcp_index),
        .fetch_rsp_rcp_value(fetch_rsp_rcp_value),
        .rsp_valid(exec_rsp_valid),.rsp_ready(active&&state_q==EXEC_WAIT),
        .rsp_tag(exec_rsp_tag),.rsp_epoch(exec_rsp_epoch),.rsp_r(exec_rsp_r),.rsp_selected(),
        .rsp_error(exec_rsp_error),.rsp_error_pc(exec_rsp_error_pc),.rsp_cycles(exec_rsp_cycles),
        .rsp_retired(exec_rsp_retired),.rsp_muls(exec_rsp_muls),
        .commit_valid(exec_commit_valid),.commit_tag(),.commit_epoch(),
        .commit_pc(commit_pc),.commit_opcode(commit_opcode),.commit_r(commit_r),
        .phase(),.generation_exhausted(exec_generation_exhausted)
    );

    wire [511:0] post_xor_r=exec_r_q^cache_data_q;
    wire [63:0] post_xor_selected=post_xor_r[address_reg*64+:64];
    assign stage_valid=active&&stage_q;
    assign stage_program=stage_program_q;assign stage_cache_index=stage_cache_index_q;
    assign stage_r=r_q;assign stage_selected=stage_selected_q;assign stage_program_cycles=stage_cycles_q;

    always @(posedge clk)begin
        if(rst)begin generation_q<=0;exec_accepted_q<=0;end
        else begin
            if(req_valid&&req_ready)generation_q<=generation_q+1'b1;
            if(exec_req_valid&&exec_req_ready)exec_accepted_q<=exec_accepted_q+1'b1;
        end
        if(rst||cancel)begin
            state_q<=IDLE;completed_q<=0;tag_q<=0;epoch_q<=0;service_tag_q<=0;rcp_count_q<=0;
            item_q<=0;cycles_q<=0;exec_cycles_q<=0;program_cycles_q<=0;
            counts_q<=0;address_regs_q<=0;r_q<=0;exec_r_q<=0;cache_data_q<=0;cache_index_q<=0;
            program_q<=0;error_stage_q<=0;error_pc_q<=0;retired_q<=0;muls_q<=0;
            error_q<=0;stage_q<=0;stage_program_q<=0;stage_cache_index_q<=0;
            stage_selected_q<=0;stage_cycles_q<=0;
        end else begin
            stage_q<=0;
            if(state_q!=IDLE&&state_q!=RETURN)cycles_q<=cycles_q+1'b1;
            case(state_q)
                IDLE:if(req_valid&&req_ready)begin
                    tag_q<=req_tag;epoch_q<=req_epoch;item_q<=req_item;
                    service_tag_q<={generation_q+16'd1,req_tag};
                    counts_q<=req_counts;address_regs_q<=req_address_regs;rcp_count_q<=req_rcp_count;
                    cache_index_q<=req_item[21:0];program_q<=0;r_q<=0;
                    completed_q<=0;retired_q<=0;muls_q<=0;cycles_q<=0;exec_cycles_q<=0;
                    error_q<=descriptor_error;error_stage_q<=descriptor_error?descriptor_error_stage:3'b0;
                    error_pc_q<=0;program_cycles_q<=0;
                    if(descriptor_error)state_q<=RETURN;else state_q<=SEED_REQ;
                end
                SEED_REQ:if(seed_req_ready)state_q<=SEED_WAIT;
                SEED_WAIT:if(seed_rsp_valid)begin
                    if(seed_rsp_tag!=tag_q)begin
                        error_q<=1;error_stage_q<=0;error_pc_q<=0;state_q<=RETURN;
                    end else begin r_q<=seeded_r;state_q<=EXEC_REQ;end
                end
                EXEC_REQ:if(exec_req_ready)state_q<=EXEC_WAIT;
                EXEC_WAIT:if(exec_rsp_valid)begin
                    retired_q<=retired_q+{3'b0,exec_rsp_retired};
                    muls_q<=muls_q+{3'b0,exec_rsp_muls};
                    exec_cycles_q<=exec_cycles_q+exec_rsp_cycles;program_cycles_q<=exec_rsp_cycles;
                    if(exec_rsp_error||exec_rsp_tag!=tag_q||exec_rsp_epoch!=epoch_q)begin
                        error_q<=1;error_stage_q<=program_q;
                        error_pc_q<=exec_rsp_error?exec_rsp_error_pc:9'b0;state_q<=RETURN;
                    end else begin exec_r_q<=exec_rsp_r;state_q<=CACHE_REQ;end
                end
                CACHE_REQ:if(cache_req_ready)state_q<=CACHE_WAIT;
                CACHE_WAIT:if(cache_rsp_valid&&cache_rsp_ready&&cache_rsp_tag==service_tag_q)begin
                    if(cache_rsp_error||cache_rsp_epoch!=epoch_q||cache_rsp_program!=program_q||
                       cache_rsp_index!=cache_index_q)begin
                        error_q<=1;error_stage_q<=program_q;error_pc_q<=0;state_q<=RETURN;
                    end else begin cache_data_q<=cache_rsp_data;state_q<=XOR_STAGE;end
                end
                XOR_STAGE:begin
                    r_q<=post_xor_r;completed_q<=completed_q+1'b1;
                    stage_q<=1;stage_program_q<=program_q;stage_cache_index_q<=cache_index_q;
                    stage_selected_q<=post_xor_selected;stage_cycles_q<=program_cycles_q;
                    if(program_q==7)state_q<=RETURN;
                    else begin
                        program_q<=program_q+1'b1;cache_index_q<=post_xor_selected[21:0];state_q<=EXEC_REQ;
                    end
                end
                RETURN:if(rsp_ready)state_q<=IDLE;
                default:state_q<=IDLE;
            endcase
        end
    end
endmodule
`default_nettype wire
