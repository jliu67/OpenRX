// SPDX-License-Identifier: BSD-3-Clause
// Integer hardware execution connected to the accepted iteration controller.
`default_nettype none
module randomx_integer_iteration #(parameter integer LANES=4,SERIAL_CONVERT=0,COALESCE_LINES=1,SERIAL_IADD=0)(
    input wire  clk,
    input wire  rst,
    input wire  req_valid,
    output wire  req_ready,
    input wire [15:0] req_tag,
    input wire  req_v2,
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
    output wire  sp_rd_valid,
    input wire  sp_rd_ready,
    output wire [20:0] sp_rd_addr,
    output wire [15:0] sp_rd_tag,
    input wire  sp_rsp_valid,
    output wire  sp_rsp_ready,
    input wire [127:0] sp_rsp_data,
    input wire [15:0] sp_rsp_tag,
    output wire  sp_wr_valid,
    input wire  sp_wr_ready,
    output wire [20:0] sp_wr_addr,
    output wire [127:0] sp_wr_data,
    output wire [15:0] sp_wr_strb,
    output wire [15:0] sp_wr_tag,
    output wire  ds_req_valid,
    input wire  ds_req_ready,
    output wire [63:0] ds_req_addr,
    output wire [63:0] ds_prefetch_addr,
    output wire [15:0] ds_req_tag,
    output wire  ds_prefetch_valid,
    input wire  ds_rsp_valid,
    output wire  ds_rsp_ready,
    input wire [15:0] ds_rsp_tag,
    input wire [511:0] ds_rsp_data,
    output wire  done_valid,
    input wire  done_ready,
    output wire [15:0] done_tag,
    output wire [1:0] done_round_mode,
    output wire [511:0] done_r,
    output wire [511:0] done_f,
    output wire [511:0] done_e,
    output wire [31:0] done_mx,
    output wire [31:0] done_ma,
    output wire [31:0] done_spaddr0,
    output wire [31:0] done_spaddr1,
    output wire  prog_valid,
    input wire  prog_ready,
    output wire [63:0] prog_addr,
    output wire [15:0] prog_tag,
    input wire  prog_rsp_valid,
    output wire  prog_rsp_ready,
    input wire [15:0] prog_rsp_tag,
    input wire [63:0] prog_rsp_instruction,
    output wire  error_valid,
    input wire  error_ready,
    output wire [15:0] error_tag,
    output wire [8:0] error_pc,
    output wire [7:0] error_opcode,
    output wire  commit_valid,
    output wire [15:0] commit_tag,
    output wire [8:0] commit_pc,
    output wire [7:0] commit_opcode,
    output wire [511:0] commit_r
);
    reg abort_q;
    wire internal_rst=rst|abort_q;
    always @(posedge clk)begin
        if(rst)abort_q<=0;else abort_q<=error_valid && error_ready;
    end
    wire  ex_req_valid;
    wire  ex_req_ready;
    wire [15:0] ex_req_tag;
    wire  ex_req_v2;
    wire [1:0] ex_req_round_mode;
    wire [511:0] ex_req_r;
    wire [511:0] ex_req_f;
    wire [511:0] ex_req_e;
    wire [511:0] ex_req_a;
    wire [63:0] ex_req_emask0;
    wire [63:0] ex_req_emask1;
    wire [63:0] ex_req_program_addr;
    wire  ex_ret_valid;
    wire  ex_ret_ready;
    wire [15:0] ex_ret_tag;
    wire [511:0] ex_ret_r;
    wire [511:0] ex_ret_f;
    wire [511:0] ex_ret_e;
    wire [1:0] ex_ret_round_mode;
    wire [15:0] ex_mem_tag;
    wire  ex_rd_valid;
    wire  ex_rd_ready;
    wire [20:0] ex_rd_addr;
    wire  ex_rsp_valid;
    wire  ex_rsp_ready;
    wire [127:0] ex_rsp_data;
    wire [15:0] ex_rsp_tag;
    wire  ex_wr_valid;
    wire  ex_wr_ready;
    wire [20:0] ex_wr_addr;
    wire [127:0] ex_wr_data;
    wire [15:0] ex_wr_strb;
    randomx_iteration_engine #(.LANES(LANES),.SERIAL_CONVERT(SERIAL_CONVERT),.COALESCE_LINES(COALESCE_LINES)) controller(
        .clk(clk),
        .rst(internal_rst),
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
        .ex_req_valid(ex_req_valid),
        .ex_req_ready(ex_req_ready),
        .ex_req_tag(ex_req_tag),
        .ex_req_v2(ex_req_v2),
        .ex_req_round_mode(ex_req_round_mode),
        .ex_req_r(ex_req_r),
        .ex_req_f(ex_req_f),
        .ex_req_e(ex_req_e),
        .ex_req_a(ex_req_a),
        .ex_req_emask0(ex_req_emask0),
        .ex_req_emask1(ex_req_emask1),
        .ex_req_program_addr(ex_req_program_addr),
        .ex_ret_valid(ex_ret_valid),
        .ex_ret_ready(ex_ret_ready),
        .ex_ret_tag(ex_ret_tag),
        .ex_ret_r(ex_ret_r),
        .ex_ret_f(ex_ret_f),
        .ex_ret_e(ex_ret_e),
        .ex_ret_round_mode(ex_ret_round_mode),
        .ex_mem_tag(ex_mem_tag),
        .ex_rd_valid(ex_rd_valid),
        .ex_rd_ready(ex_rd_ready),
        .ex_rd_addr(ex_rd_addr),
        .ex_rsp_valid(ex_rsp_valid),
        .ex_rsp_ready(ex_rsp_ready),
        .ex_rsp_data(ex_rsp_data),
        .ex_rsp_tag(ex_rsp_tag),
        .ex_wr_valid(ex_wr_valid),
        .ex_wr_ready(ex_wr_ready),
        .ex_wr_addr(ex_wr_addr),
        .ex_wr_data(ex_wr_data),
        .ex_wr_strb(ex_wr_strb),
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
        .done_spaddr1(done_spaddr1)
    );
`ifdef INTEGER_EXECUTE_NETLIST
    randomx_integer_execute execute (
`else
    randomx_integer_execute #(.SERIAL_IADD(SERIAL_IADD)) execute(
`endif
        .clk(clk),
        .rst(internal_rst),
        .req_valid(ex_req_valid),
        .req_ready(ex_req_ready),
        .req_tag(ex_req_tag),
        .req_v2(ex_req_v2),
        .req_round_mode(ex_req_round_mode),
        .req_r(ex_req_r),
        .req_f(ex_req_f),
        .req_e(ex_req_e),
        .req_a(ex_req_a),
        .req_emask0(ex_req_emask0),
        .req_emask1(ex_req_emask1),
        .req_program_addr(ex_req_program_addr),
        .mem_tag(ex_mem_tag),
        .rd_valid(ex_rd_valid),
        .rd_ready(ex_rd_ready),
        .rd_addr(ex_rd_addr),
        .rsp_valid(ex_rsp_valid),
        .rsp_ready(ex_rsp_ready),
        .rsp_tag(ex_rsp_tag),
        .rsp_data(ex_rsp_data),
        .wr_valid(ex_wr_valid),
        .wr_ready(ex_wr_ready),
        .wr_addr(ex_wr_addr),
        .wr_data(ex_wr_data),
        .wr_strb(ex_wr_strb),
        .ret_valid(ex_ret_valid),
        .ret_ready(ex_ret_ready),
        .ret_tag(ex_ret_tag),
        .ret_r(ex_ret_r),
        .ret_f(ex_ret_f),
        .ret_e(ex_ret_e),
        .ret_round_mode(ex_ret_round_mode),
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
endmodule
`default_nettype wire
