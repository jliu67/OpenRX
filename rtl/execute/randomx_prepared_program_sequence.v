// SPDX-License-Identifier: BSD-3-Clause
// Program-loop control with immutable per-program admission and charged reciprocal preparation.
`default_nettype none
module randomx_prepared_program_sequence #(parameter integer PROGRAMS=8,ITERATIONS=2048,PREPARED_RCP=1,
 LANES=4,SERIAL_CONVERT=0,COALESCE_LINES=1,SERIAL_IADD=0,MUL_RADIX4=0,FP_LANES=2,DIVSQRT_LANES=2)(
 input wire  clk,
 input wire  rst,
 input wire cancel,
 output wire [3:0] phase,
 output reg prep_commit_valid,
 output wire [15:0] prep_commit_epoch,
 output wire [2:0] prep_commit_program,
 output wire epoch_capacity_exhausted,
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
 wire  iter_req_valid;
 wire  iter_req_ready;
 wire [15:0] iter_req_tag;
 wire  iter_req_v2;
 wire [1:0] iter_req_round_mode;
 wire [511:0] iter_req_r;
 wire [511:0] iter_req_a;
 wire [31:0] iter_req_spaddr0;
 wire [31:0] iter_req_spaddr1;
 wire [31:0] iter_req_mx;
 wire [31:0] iter_req_ma;
 wire [2:0] iter_req_read0;
 wire [2:0] iter_req_read1;
 wire [2:0] iter_req_read2;
 wire [2:0] iter_req_read3;
 wire [63:0] iter_req_emask0;
 wire [63:0] iter_req_emask1;
 wire [63:0] iter_req_dataset_offset;
 wire [63:0] iter_req_program_addr;
 wire  iter_done_valid;
 wire  iter_done_ready;
 wire [15:0] iter_done_tag;
 wire [511:0] iter_done_r;
 wire [511:0] iter_done_f;
 wire [511:0] iter_done_e;
 wire [1:0] iter_done_round_mode;
 wire [31:0] iter_done_mx;
 wire [31:0] iter_done_ma;
 wire [31:0] iter_done_spaddr0;
 wire [31:0] iter_done_spaddr1;
 wire  iter_error_valid;
 wire  iter_error_ready;
 wire [15:0] iter_error_tag;
 wire [8:0] iter_error_pc;
 wire [7:0] iter_error_opcode;
 // Admission epochs never wrap or reset on cancellation. A hard reset requires
 // the external fabric to drain old replies before identifiers can be reused.
 localparam [2:0] M_IDLE=0,M_START=1,M_WAIT=2,M_DELIVER=3,M_FAULT=4;
 reg [2:0] meta_state_q;reg pending_q,v2_q,abort_q,iteration_active_q;
 reg [15:0] epoch_counter_q,image_epoch_q,meta_tag_q;
 reg [2:0] meta_program_q;reg [1023:0] entropy_q;reg [63:0] address_q;
 wire core_rst=rst||cancel||abort_q;
 wire control_start_ready,control_meta_rsp_ready,control_error_valid;
 wire [15:0] control_error_tag;wire [2:0] control_error_program;
 wire [1:0] control_error_code;wire [8:0] control_error_pc;wire [7:0] control_error_opcode;
 wire prep_ready,prep_rsp_valid,prep_rsp_error;wire [15:0] prep_rsp_epoch;
 wire image_valid,image_v2;wire [15:0] image_epoch;wire [63:0] image_program_addr;
 wire [1:0] iteration_error_reason;
 wire stale_meta=meta_rsp_tag!=meta_req_tag||meta_rsp_program!=meta_req_program;
 // Reserve enough unique admission epochs for the entire batch before taking
 // its start. Refuse an unfinishable batch rather than hanging after init.
 assign epoch_capacity_exhausted=epoch_counter_q>(65535-PROGRAMS);
 assign start_ready=!core_rst&&control_start_ready&&!epoch_capacity_exhausted;
 assign meta_rsp_ready=!core_rst&&(stale_meta||(pending_q&&meta_state_q==M_IDLE));
 assign error_valid=!core_rst&&(meta_state_q==M_FAULT||control_error_valid);
 assign error_tag=meta_state_q==M_FAULT?meta_tag_q:control_error_tag;
 assign error_program=meta_state_q==M_FAULT?meta_program_q:control_error_program;
 assign error_code=meta_state_q==M_FAULT?2'd3:control_error_code;
 assign error_pc=meta_state_q==M_FAULT?9'b0:control_error_pc;
 assign error_opcode=meta_state_q==M_FAULT?8'b0:control_error_opcode;
 assign phase=(meta_state_q==M_START||meta_state_q==M_WAIT)?4'd3:
              (iteration_active_q||iter_req_valid)?4'd4:4'd2;
 assign prep_commit_epoch=image_epoch_q;assign prep_commit_program=meta_program_q;
 always @(posedge clk)begin
  if(rst)epoch_counter_q<=0;
  else if(!core_rst&&meta_rsp_valid&&meta_rsp_ready&&!stale_meta&&epoch_counter_q!=16'hffff)
   epoch_counter_q<=epoch_counter_q+16'd1;
  if(core_rst)begin
   meta_state_q<=M_IDLE;pending_q<=0;v2_q<=0;abort_q<=0;iteration_active_q<=0;
   image_epoch_q<=0;meta_tag_q<=0;meta_program_q<=0;entropy_q<=0;address_q<=0;prep_commit_valid<=0;
  end else begin
   prep_commit_valid<=0;abort_q<=0;
   if(start_valid&&start_ready)v2_q<=start_v2;
   if(meta_req_valid&&meta_req_ready)pending_q<=1;
   if(iter_req_valid&&iter_req_ready)iteration_active_q<=1;
   if((iter_done_valid&&iter_done_ready)||(iter_error_valid&&iter_error_ready))iteration_active_q<=0;
   case(meta_state_q)
    M_IDLE:if(meta_rsp_valid&&meta_rsp_ready&&!stale_meta)begin
     pending_q<=0;meta_tag_q<=meta_rsp_tag;meta_program_q<=meta_rsp_program;
     entropy_q<=meta_rsp_entropy;address_q<=meta_rsp_program_addr;
     image_epoch_q<=epoch_counter_q+16'd1;
     if(epoch_counter_q==16'hffff||meta_rsp_program_addr[2:0]!=0)meta_state_q<=M_FAULT;
     else meta_state_q<=M_START;
    end
    M_START:if(prep_ready)meta_state_q<=M_WAIT;
    M_WAIT:if(prep_rsp_valid)begin
     if(prep_rsp_error||prep_rsp_epoch!=image_epoch_q||!image_valid||image_epoch!=image_epoch_q||
        image_v2!=v2_q||image_program_addr!=address_q)meta_state_q<=M_FAULT;
     else begin prep_commit_valid<=1;meta_state_q<=M_DELIVER;end
    end
    M_DELIVER:if(control_meta_rsp_ready)meta_state_q<=M_IDLE;
    M_FAULT:if(error_ready)abort_q<=1;
    default:meta_state_q<=M_FAULT;
   endcase
  end
 end
`ifdef PROGRAM_CONTROL_NETLIST
 randomx_program_control control(
`else
 randomx_program_control #(.PROGRAMS(PROGRAMS),.ITERATIONS(ITERATIONS)) control(
`endif
  .clk(clk),
  .rst(core_rst),
  .start_valid(start_valid&&!epoch_capacity_exhausted),
  .start_ready(control_start_ready),
  .start_tag(start_tag),
  .start_v2(start_v2),
  .meta_req_valid(meta_req_valid),
  .meta_req_ready(meta_req_ready),
  .meta_req_tag(meta_req_tag),
  .meta_req_program(meta_req_program),
  .meta_rsp_valid(meta_state_q==M_DELIVER),
  .meta_rsp_ready(control_meta_rsp_ready),
  .meta_rsp_tag(meta_tag_q),
  .meta_rsp_program(meta_program_q),
  .meta_rsp_entropy(entropy_q),
  .meta_rsp_program_addr(address_q),
  .program_done_valid(program_done_valid),
  .program_done_ready(program_done_ready),
  .program_done_tag(program_done_tag),
  .program_done_index(program_done_index),
  .program_done_iterations(program_done_iterations),
  .program_done_r(program_done_r),
  .program_done_f(program_done_f),
  .program_done_e(program_done_e),
  .program_done_a(program_done_a),
  .program_done_round_mode(program_done_round_mode),
  .done_valid(done_valid),
  .done_ready(done_ready),
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
  .error_valid(control_error_valid),
  .error_ready(error_ready&&meta_state_q!=M_FAULT),
  .error_tag(control_error_tag),
  .error_program(control_error_program),
  .error_code(control_error_code),
  .error_pc(control_error_pc),
  .error_opcode(control_error_opcode),
  .iter_req_valid(iter_req_valid),
  .iter_req_ready(iter_req_ready),
  .iter_req_tag(iter_req_tag),
  .iter_req_v2(iter_req_v2),
  .iter_req_round_mode(iter_req_round_mode),
  .iter_req_r(iter_req_r),
  .iter_req_a(iter_req_a),
  .iter_req_spaddr0(iter_req_spaddr0),
  .iter_req_spaddr1(iter_req_spaddr1),
  .iter_req_mx(iter_req_mx),
  .iter_req_ma(iter_req_ma),
  .iter_req_read0(iter_req_read0),
  .iter_req_read1(iter_req_read1),
  .iter_req_read2(iter_req_read2),
  .iter_req_read3(iter_req_read3),
  .iter_req_emask0(iter_req_emask0),
  .iter_req_emask1(iter_req_emask1),
  .iter_req_dataset_offset(iter_req_dataset_offset),
  .iter_req_program_addr(iter_req_program_addr),
  .iter_done_valid(iter_done_valid),
  .iter_done_ready(iter_done_ready),
  .iter_done_tag(iter_done_tag),
  .iter_done_r(iter_done_r),
  .iter_done_f(iter_done_f),
  .iter_done_e(iter_done_e),
  .iter_done_round_mode(iter_done_round_mode),
  .iter_done_mx(iter_done_mx),
  .iter_done_ma(iter_done_ma),
  .iter_done_spaddr0(iter_done_spaddr0),
  .iter_done_spaddr1(iter_done_spaddr1),
  .iter_error_valid(iter_error_valid),
  .iter_error_ready(iter_error_ready),
  .iter_error_tag(iter_error_tag),
  .iter_error_pc(iter_error_pc),
  .iter_error_opcode(iter_error_opcode),
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
  .iteration_commit_spaddr1(iteration_commit_spaddr1)
 );
 randomx_prepared_integer_iteration #(.PREPARED_RCP(PREPARED_RCP),.LANES(LANES),.SERIAL_CONVERT(SERIAL_CONVERT),.COALESCE_LINES(COALESCE_LINES),
  .SERIAL_IADD(SERIAL_IADD),.MUL_RADIX4(MUL_RADIX4),.FP_LANES(FP_LANES),.DIVSQRT_LANES(DIVSQRT_LANES)) iteration(
  .clk(clk),
  .rst(core_rst),
  .req_valid(iter_req_valid),
  .req_ready(iter_req_ready),
  .req_tag(iter_req_tag),
  .req_v2(iter_req_v2),
  .req_round_mode(iter_req_round_mode),
  .req_r(iter_req_r),
  .req_a(iter_req_a),
  .req_spaddr0(iter_req_spaddr0),
  .req_spaddr1(iter_req_spaddr1),
  .req_mx(iter_req_mx),
  .req_ma(iter_req_ma),
  .req_read0(iter_req_read0),
  .req_read1(iter_req_read1),
  .req_read2(iter_req_read2),
  .req_read3(iter_req_read3),
  .req_emask0(iter_req_emask0),
  .req_emask1(iter_req_emask1),
  .req_dataset_offset(iter_req_dataset_offset),
  .req_program_addr(iter_req_program_addr),
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
  .done_valid(iter_done_valid),
  .done_ready(iter_done_ready),
  .done_tag(iter_done_tag),
  .done_round_mode(iter_done_round_mode),
  .done_r(iter_done_r),
  .done_f(iter_done_f),
  .done_e(iter_done_e),
  .done_mx(iter_done_mx),
  .done_ma(iter_done_ma),
  .done_spaddr0(iter_done_spaddr0),
  .done_spaddr1(iter_done_spaddr1),
  .load_req_valid(prog_valid),
  .load_req_ready(prog_ready),
  .load_req_addr(prog_addr),
  .load_req_tag(prog_tag),
  .load_rsp_valid(prog_rsp_valid),
  .load_rsp_ready(prog_rsp_ready),
  .load_rsp_tag(prog_rsp_tag),
  .load_rsp_instruction(prog_rsp_instruction),
  .cancel(cancel||abort_q),.exec_cancel(1'b0),.req_program_epoch(image_epoch_q),
  .prep_valid(meta_state_q==M_START),.prep_ready(prep_ready),.prep_epoch(image_epoch_q),
  .prep_v2(v2_q),.prep_program_addr(address_q),.load_rsp_error(prog_rsp_error),
  .prep_rsp_valid(prep_rsp_valid),.prep_rsp_ready(meta_state_q==M_WAIT),
  .prep_rsp_epoch(prep_rsp_epoch),.prep_rsp_error(prep_rsp_error),
  .image_valid(image_valid),.image_epoch(image_epoch),.image_v2(image_v2),
  .image_program_addr(image_program_addr),.error_reason(iteration_error_reason),
  .error_valid(iter_error_valid),
  .error_ready(iter_error_ready),
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
