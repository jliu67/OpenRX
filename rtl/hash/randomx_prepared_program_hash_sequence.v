// SPDX-License-Identifier: BSD-3-Clause
// Hardware interprogram seeds above admitted prepared program execution.
`default_nettype none
module randomx_prepared_program_hash_sequence #(parameter integer PROGRAMS=8,ITERATIONS=2048,PREPARED_RCP=1,
 LANES=4,SERIAL_CONVERT=0,COALESCE_LINES=1,SERIAL_IADD=0,MUL_RADIX4=0,FP_LANES=2,DIVSQRT_LANES=2)(
 input wire  clk,
 input wire  rst,
 input wire cancel,
 output wire [3:0] phase,
 output wire prep_commit_valid,
 output wire [15:0] prep_commit_epoch,
 output wire [2:0] prep_commit_program,
 input wire  start_valid,
 output wire  start_ready,
 input wire [15:0] start_tag,
 input wire  start_v2,
 output wire  meta_req_valid,
 input wire  meta_req_ready,
 output wire [15:0] meta_req_tag,
 output wire [2:0] meta_req_program,
 input wire  meta_rsp_valid,
 output wire  meta_rsp_ready,
 input wire [15:0] meta_rsp_tag,
 input wire [2:0] meta_rsp_program,
 input wire [1023:0] meta_rsp_entropy,
 input wire [63:0] meta_rsp_program_addr,
 output wire  program_done_valid,
 input wire  program_done_ready,
 output wire [15:0] program_done_tag,
 output wire [2:0] program_done_index,
 output wire [11:0] program_done_iterations,
 output wire [511:0] program_done_r,
 output wire [511:0] program_done_f,
 output wire [511:0] program_done_e,
 output wire [511:0] program_done_a,
 output wire [1:0] program_done_round_mode,
 output wire program_done_seed_valid,
 output wire [511:0] program_done_seed,
 output wire  done_valid,
 input wire  done_ready,
 output wire [15:0] done_tag,
 output wire [511:0] done_r,
 output wire [511:0] done_f,
 output wire [511:0] done_e,
 output wire [511:0] done_a,
 output wire [1:0] done_round_mode,
 output wire [31:0] done_mx,
 output wire [31:0] done_ma,
 output wire [31:0] done_spaddr0,
 output wire [31:0] done_spaddr1,
 output wire  error_valid,
 input wire  error_ready,
 output wire [15:0] error_tag,
 output wire [2:0] error_program,
 output wire [1:0] error_code,
 output wire [8:0] error_pc,
 output wire [7:0] error_opcode,
 output wire  iteration_commit_valid,
 output wire [15:0] iteration_commit_tag,
 output wire [15:0] iteration_commit_backend_tag,
 output wire [2:0] iteration_commit_program,
 output wire [10:0] iteration_commit_index,
 output wire [511:0] iteration_commit_r,
 output wire [511:0] iteration_commit_f,
 output wire [511:0] iteration_commit_e,
 output wire [511:0] iteration_commit_a,
 output wire [1:0] iteration_commit_round_mode,
 output wire [31:0] iteration_commit_mx,
 output wire [31:0] iteration_commit_ma,
 output wire [31:0] iteration_commit_spaddr0,
 output wire [31:0] iteration_commit_spaddr1,
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
 output wire  prog_valid,
 input wire  prog_ready,
 output wire [63:0] prog_addr,
 output wire [24:0] prog_tag,
 input wire  prog_rsp_valid,
 output wire  prog_rsp_ready,
 input wire [24:0] prog_rsp_tag,
 input wire [63:0] prog_rsp_instruction,
 input wire prog_rsp_error,
 output wire  commit_valid,
 output wire [15:0] commit_tag,
 output wire [8:0] commit_pc,
 output wire [7:0] commit_opcode,
 output wire [511:0] commit_r,
 output wire [8:0] commit_next_pc,
 output wire [8:0] commit_branch_target,
 output wire [511:0] commit_f,
 output wire [511:0] commit_e,
 output wire [1:0] commit_round_mode
);
 wire [3:0] sequence_phase;
 assign phase=!seed_req_ready?4'd5:sequence_phase;
 reg abort_q;wire core_rst=rst||cancel||abort_q;wire seed_req_ready,seed_rsp_valid,seed_rsp_error;
 wire  inner_meta_req_valid;
 wire  inner_meta_req_ready;
 wire  inner_program_done_valid;
 wire  inner_program_done_ready;
 wire [15:0] inner_program_done_tag;
 wire [2:0] inner_program_done_index;
 wire [11:0] inner_program_done_iterations;
 wire [511:0] inner_program_done_r;
 wire [511:0] inner_program_done_f;
 wire [511:0] inner_program_done_e;
 wire [511:0] inner_program_done_a;
 wire [1:0] inner_program_done_round_mode;
 wire  inner_done_valid;
 wire  inner_done_ready;
 wire  inner_error_valid;
 wire  inner_error_ready;
 wire [15:0] inner_error_tag;
 wire [2:0] inner_error_program;
 wire [1:0] inner_error_code;
 wire [8:0] inner_error_pc;
 wire [7:0] inner_error_opcode;
 assign inner_program_done_ready=seed_req_ready;
 assign meta_req_valid=!core_rst&&inner_meta_req_valid&&seed_req_ready;
 assign inner_meta_req_ready=meta_req_ready&&seed_req_ready;
 assign done_valid=!core_rst&&inner_done_valid&&seed_req_ready;
 assign inner_done_ready=done_ready&&seed_req_ready;
 assign program_done_valid=!core_rst&&seed_rsp_valid&&!seed_rsp_error;
 assign error_valid=!core_rst&&(inner_error_valid||seed_rsp_valid&&seed_rsp_error);
 assign error_tag=seed_rsp_error?program_done_tag:inner_error_tag;
 assign error_program=seed_rsp_error?program_done_index:inner_error_program;
 assign error_code=seed_rsp_error?2'd3:inner_error_code;
 assign error_pc=seed_rsp_error?9'b0:inner_error_pc;assign error_opcode=seed_rsp_error?8'b0:inner_error_opcode;
 assign inner_error_ready=error_ready&&!seed_rsp_error;
 always @(posedge clk)begin
  if(core_rst)abort_q<=0;else abort_q<=seed_rsp_valid&&seed_rsp_error&&error_ready;
 end
`ifdef PROGRAM_SEED_NETLIST
 randomx_program_seed seed_stage(
`else
 randomx_program_seed #(.PROGRAMS(PROGRAMS)) seed_stage(
`endif
  .clk(clk),.rst(core_rst),.req_valid(inner_program_done_valid),.req_ready(seed_req_ready),
  .req_tag(inner_program_done_tag),.req_index(inner_program_done_index),.req_iterations(inner_program_done_iterations),
  .req_round_mode(inner_program_done_round_mode),.req_r(inner_program_done_r),.req_f(inner_program_done_f),.req_e(inner_program_done_e),.req_a(inner_program_done_a),
  .rsp_valid(seed_rsp_valid),.rsp_ready(program_done_ready&&!seed_rsp_error),.rsp_tag(program_done_tag),.rsp_index(program_done_index),
  .rsp_iterations(program_done_iterations),.rsp_round_mode(program_done_round_mode),.rsp_r(program_done_r),.rsp_f(program_done_f),
  .rsp_e(program_done_e),.rsp_a(program_done_a),.rsp_seed(program_done_seed),.rsp_seed_valid(program_done_seed_valid),.rsp_error(seed_rsp_error)
 );
 randomx_prepared_program_sequence #(.PROGRAMS(PROGRAMS),.ITERATIONS(ITERATIONS),.PREPARED_RCP(PREPARED_RCP),.LANES(LANES),.SERIAL_CONVERT(SERIAL_CONVERT),
  .COALESCE_LINES(COALESCE_LINES),.SERIAL_IADD(SERIAL_IADD),.MUL_RADIX4(MUL_RADIX4),.FP_LANES(FP_LANES),.DIVSQRT_LANES(DIVSQRT_LANES)) iteration_chain(
  .clk(clk),
  .rst(rst),.cancel(cancel||abort_q),.phase(sequence_phase),
  .prep_commit_valid(prep_commit_valid),.prep_commit_epoch(prep_commit_epoch),.prep_commit_program(prep_commit_program),
  .start_valid(start_valid),
  .start_ready(start_ready),
  .start_tag(start_tag),
  .start_v2(start_v2),
  .meta_req_valid(inner_meta_req_valid),
  .meta_req_ready(inner_meta_req_ready),
  .meta_req_tag(meta_req_tag),
  .meta_req_program(meta_req_program),
  .meta_rsp_valid(meta_rsp_valid),
  .meta_rsp_ready(meta_rsp_ready),
  .meta_rsp_tag(meta_rsp_tag),
  .meta_rsp_program(meta_rsp_program),
  .meta_rsp_entropy(meta_rsp_entropy),
  .meta_rsp_program_addr(meta_rsp_program_addr),
  .program_done_valid(inner_program_done_valid),
  .program_done_ready(inner_program_done_ready),
  .program_done_tag(inner_program_done_tag),
  .program_done_index(inner_program_done_index),
  .program_done_iterations(inner_program_done_iterations),
  .program_done_r(inner_program_done_r),
  .program_done_f(inner_program_done_f),
  .program_done_e(inner_program_done_e),
  .program_done_a(inner_program_done_a),
  .program_done_round_mode(inner_program_done_round_mode),
  .done_valid(inner_done_valid),
  .done_ready(inner_done_ready),
  .done_tag(done_tag),
  .done_r(done_r),
  .done_f(done_f),
  .done_e(done_e),
  .done_a(done_a),
  .done_round_mode(done_round_mode),
  .done_mx(done_mx),
  .done_ma(done_ma),
  .done_spaddr0(done_spaddr0),
  .done_spaddr1(done_spaddr1),
  .error_valid(inner_error_valid),
  .error_ready(inner_error_ready),
  .error_tag(inner_error_tag),
  .error_program(inner_error_program),
  .error_code(inner_error_code),
  .error_pc(inner_error_pc),
  .error_opcode(inner_error_opcode),
  .iteration_commit_valid(iteration_commit_valid),
  .iteration_commit_tag(iteration_commit_tag),
  .iteration_commit_backend_tag(iteration_commit_backend_tag),
  .iteration_commit_program(iteration_commit_program),
  .iteration_commit_index(iteration_commit_index),
  .iteration_commit_r(iteration_commit_r),
  .iteration_commit_f(iteration_commit_f),
  .iteration_commit_e(iteration_commit_e),
  .iteration_commit_a(iteration_commit_a),
  .iteration_commit_round_mode(iteration_commit_round_mode),
  .iteration_commit_mx(iteration_commit_mx),
  .iteration_commit_ma(iteration_commit_ma),
  .iteration_commit_spaddr0(iteration_commit_spaddr0),
  .iteration_commit_spaddr1(iteration_commit_spaddr1),
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
  .prog_valid(prog_valid),
  .prog_ready(prog_ready),
  .prog_addr(prog_addr),
  .prog_tag(prog_tag),
  .prog_rsp_valid(prog_rsp_valid),
  .prog_rsp_ready(prog_rsp_ready),
  .prog_rsp_tag(prog_rsp_tag),
  .prog_rsp_instruction(prog_rsp_instruction),.prog_rsp_error(prog_rsp_error),
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
