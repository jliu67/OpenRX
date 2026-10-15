// SPDX-License-Identifier: BSD-3-Clause
// One immutable program admission can serve repeated exact native iterations.
// Baseline and prepared configurations use the same instruction image/fetch path.
`default_nettype none
module randomx_prepared_integer_iteration #(
    parameter integer PREPARED_RCP=1,LANES=4,SERIAL_CONVERT=0,COALESCE_LINES=1,
    SERIAL_IADD=0,MUL_RADIX4=0,FP_LANES=2,DIVSQRT_LANES=2
)(
    input wire clk,
    input wire rst,
    input wire req_valid,
    output wire req_ready,
    input wire [15:0] req_tag,
    input wire req_v2,
    input wire [1:0] req_round_mode,
    input wire [511:0] req_r,
    input wire [511:0] req_a,
    input wire [31:0] req_spaddr0,
    input wire [31:0] req_spaddr1,
    input wire [31:0] req_mx,
    input wire [31:0] req_ma,
    input wire [2:0] req_read0,
    input wire [2:0] req_read1,
    input wire [2:0] req_read2,
    input wire [2:0] req_read3,
    input wire [63:0] req_emask0,
    input wire [63:0] req_emask1,
    input wire [63:0] req_dataset_offset,
    input wire [63:0] req_program_addr,
    output wire sp_rd_valid,
    input wire sp_rd_ready,
    output wire [20:0] sp_rd_addr,
    output wire [15:0] sp_rd_tag,
    input wire sp_rsp_valid,
    output wire sp_rsp_ready,
    input wire [127:0] sp_rsp_data,
    input wire [15:0] sp_rsp_tag,
    output wire sp_wr_valid,
    input wire sp_wr_ready,
    output wire [20:0] sp_wr_addr,
    output wire [127:0] sp_wr_data,
    output wire [15:0] sp_wr_strb,
    output wire [15:0] sp_wr_tag,
    output wire ds_req_valid,
    input wire ds_req_ready,
    output wire [63:0] ds_req_addr,
    output wire [63:0] ds_prefetch_addr,
    output wire [15:0] ds_req_tag,
    output wire ds_prefetch_valid,
    input wire ds_rsp_valid,
    output wire ds_rsp_ready,
    input wire [15:0] ds_rsp_tag,
    input wire [511:0] ds_rsp_data,
    output wire done_valid,
    input wire done_ready,
    output wire [15:0] done_tag,
    output wire [1:0] done_round_mode,
    output wire [511:0] done_r,
    output wire [511:0] done_f,
    output wire [511:0] done_e,
    output wire [31:0] done_mx,
    output wire [31:0] done_ma,
    output wire [31:0] done_spaddr0,
    output wire [31:0] done_spaddr1,
    input wire [15:0] req_program_epoch,
    output wire error_valid,
    input wire error_ready,
    output wire [15:0] error_tag,
    output wire [8:0] error_pc,
    output wire [7:0] error_opcode,
    output wire commit_valid,
    output wire [15:0] commit_tag,
    output wire [8:0] commit_pc,
    output wire [7:0] commit_opcode,
    output wire [511:0] commit_r,
    output wire [8:0] commit_next_pc,
    output wire [8:0] commit_branch_target,
    output wire [511:0] commit_f,
    output wire [511:0] commit_e,
    output wire [1:0] commit_round_mode,
    input wire cancel,exec_cancel,
    input wire prep_valid,output wire prep_ready,
    input wire [15:0] prep_epoch,input wire prep_v2,input wire [63:0] prep_program_addr,
    output wire load_req_valid,input wire load_req_ready,
    output wire [63:0] load_req_addr,output wire [24:0] load_req_tag,
    input wire load_rsp_valid,output wire load_rsp_ready,input wire [24:0] load_rsp_tag,
    input wire [63:0] load_rsp_instruction,input wire load_rsp_error,
    output wire prep_rsp_valid,input wire prep_rsp_ready,
    output wire [15:0] prep_rsp_epoch,output wire prep_rsp_error,
    output wire image_valid,output wire [15:0] image_epoch,
    output wire image_v2,output wire [63:0] image_program_addr,
    output wire [1:0] error_reason
);
    reg active_q,local_error_q;
    reg [15:0] local_error_tag_q;
    wire internal_rst=rst|cancel|exec_cancel;
    wire iter_req_ready,iter_error_valid,cache_prep_ready;
    wire [15:0] iter_error_tag;wire [8:0] iter_error_pc;wire [7:0] iter_error_opcode;
    wire prog_valid,prog_ready,prog_rsp_valid,prog_rsp_ready;
    wire [63:0] prog_addr,prog_rsp_instruction,prog_rsp_rcp_value;
    wire [15:0] prog_tag,prog_rsp_tag,prog_rsp_prepared_epoch;
    wire [8:0] prog_rsp_prepared_pc;
    wire prog_rsp_prepared_error,prog_rsp_rcp_valid,prog_rsp_rcp_nop;
    wire [31:0] prog_rsp_rcp_divisor;
    wire [63:0] fetch_offset=prog_addr-image_program_addr;
    wire slot_match=image_valid&&req_program_epoch==image_epoch&&req_v2==image_v2&&
                    req_program_addr==image_program_addr;
    assign prep_ready=!internal_rst&&!active_q&&!local_error_q&&cache_prep_ready;
    assign req_ready=!internal_rst&&!active_q&&!local_error_q&&cache_prep_ready&&!prep_valid&&iter_req_ready;
    assign error_valid=!internal_rst&&(local_error_q||iter_error_valid);
    assign error_tag=local_error_q?local_error_tag_q:iter_error_tag;
    assign error_pc=local_error_q?9'b0:iter_error_pc;
    assign error_opcode=local_error_q?8'b0:iter_error_opcode;
    assign error_reason=local_error_q?2'd1:iter_error_valid?2'd2:2'd0;
    always @(posedge clk)begin
        if(internal_rst)begin active_q<=0;local_error_q<=0;local_error_tag_q<=0;end
        else begin
            if(req_valid&&req_ready)begin
                if(slot_match)active_q<=1;
                else begin local_error_q<=1;local_error_tag_q<=req_tag;end
            end
            if(done_valid&&done_ready)active_q<=0;
            if(error_valid&&error_ready)begin active_q<=0;local_error_q<=0;end
        end
    end
    randomx_program_reciprocals #(.PREPARE_RCP(PREPARED_RCP)) cache(
        .clk(clk),.rst(rst),.cancel(cancel),
        .prep_valid(prep_valid&&!active_q&&!local_error_q&&!internal_rst),.prep_ready(cache_prep_ready),
        .prep_epoch(prep_epoch),.prep_v2(prep_v2),.prep_program_addr(prep_program_addr),
        .load_req_valid(load_req_valid),.load_req_ready(load_req_ready),
        .load_req_addr(load_req_addr),.load_req_tag(load_req_tag),
        .load_rsp_valid(load_rsp_valid),.load_rsp_ready(load_rsp_ready),
        .load_rsp_tag(load_rsp_tag),.load_rsp_instruction(load_rsp_instruction),.load_rsp_error(load_rsp_error),
        .prep_rsp_valid(prep_rsp_valid),.prep_rsp_ready(prep_rsp_ready),
        .prep_rsp_epoch(prep_rsp_epoch),.prep_rsp_error(prep_rsp_error),
        .image_valid(image_valid),.image_epoch(image_epoch),.image_v2(image_v2),.image_program_addr(image_program_addr),
        .fetch_req_valid(prog_valid&&active_q&&!internal_rst),.fetch_req_ready(prog_ready),
        .fetch_req_pc(fetch_offset[11:3]),.fetch_req_tag(prog_tag),.fetch_req_epoch(image_epoch),
        .fetch_rsp_valid(prog_rsp_valid),.fetch_rsp_ready(prog_rsp_ready||exec_cancel),
        .fetch_rsp_tag(prog_rsp_tag),.fetch_rsp_instruction(prog_rsp_instruction),
        .fetch_rsp_epoch(prog_rsp_prepared_epoch),.fetch_rsp_pc(prog_rsp_prepared_pc),
        .fetch_rsp_rcp_valid(prog_rsp_rcp_valid),.fetch_rsp_rcp_nop(prog_rsp_rcp_nop),
        .fetch_rsp_rcp_divisor(prog_rsp_rcp_divisor),.fetch_rsp_rcp_value(prog_rsp_rcp_value),
        .fetch_rsp_error(prog_rsp_prepared_error));
    randomx_integer_iteration #(.PREPARED_RCP(PREPARED_RCP),.LANES(LANES),
        .SERIAL_CONVERT(SERIAL_CONVERT),.COALESCE_LINES(COALESCE_LINES),.SERIAL_IADD(SERIAL_IADD),
        .MUL_RADIX4(MUL_RADIX4),.FP_LANES(FP_LANES),.DIVSQRT_LANES(DIVSQRT_LANES)) iteration(
        .clk(clk),
        .rst(internal_rst),
        .req_valid(req_valid&&req_ready&&slot_match),
        .req_ready(iter_req_ready),
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
        .req_program_epoch(req_program_epoch),
        .prog_rsp_prepared_epoch(prog_rsp_prepared_epoch),
        .prog_rsp_prepared_pc(prog_rsp_prepared_pc),
        .prog_rsp_prepared_error(prog_rsp_prepared_error),
        .prog_rsp_rcp_valid(prog_rsp_rcp_valid),
        .prog_rsp_rcp_nop(prog_rsp_rcp_nop),
        .prog_rsp_rcp_divisor(prog_rsp_rcp_divisor),
        .prog_rsp_rcp_value(prog_rsp_rcp_value),
        .error_valid(iter_error_valid),
        .error_ready(error_ready&&!local_error_q),
        .error_tag(iter_error_tag),
        .error_pc(iter_error_pc),
        .error_opcode(iter_error_opcode),
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
endmodule
`default_nettype wire
