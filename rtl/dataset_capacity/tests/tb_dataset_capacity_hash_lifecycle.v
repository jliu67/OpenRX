// SPDX-License-Identifier: BSD-3-Clause
// Capacity-connected derivative of the unchanged accepted dataset lifecycle TB.
// Reuses retained native 2x1 assertion gold; it never regenerates that gold.
`timescale 1ns/1ps
module tb_dataset_capacity_hash_lifecycle #(parameter integer PROGRAMS=2,ITERATIONS=1,PREPARED_RCP=1,STALL=0,CANCEL_PHASE=0,ERROR_PORT=0,CAPACITY_TEST=0,EVENT_TRACE=0,HARDWARE_FILL=1,HARDWARE_PROGRAM=1,HARDWARE_INPUT_HASH=1,INPUT_HASH_BOUNDARY_TEST=0,HARDWARE_DATASET=1,DATASET_MUL_RADIX4=1,DATASET_CANCEL=0,DATASET_ERROR=0,DATASET_SESSION_BITS=32);
`ifdef VERILATOR
 import "DPI-C" function void rx_life_initial(input bit[639:0] value,input int length,input string filename,output bit[511:0] result);
 import "DPI-C" function void rx_life_input_hash(input bit[639:0] value,input int length,output bit[511:0] result);
 import "DPI-C" function void rx_life_input_hash_assertion(input bit[639:0] value,input int length,output bit[511:0] result);
 import "DPI-C" function void rx_generate_assertion(input bit[511:0] value,input string filename,output bit[1023:0] entropy);
 import "DPI-C" function void rx_generate(input bit[511:0] value,input string filename,output bit[1023:0] entropy);
 import "DPI-C" function void rx_next_seed(input bit[511:0] r,input bit[511:0] f,input bit[511:0] e,input bit[511:0] a,output bit[511:0] result);
 import "DPI-C" function void rx_dataset(input bit[63:0] address,output bit[511:0] result);
 import "DPI-C" function void rx_provider_stats(input string filename);
`define RX_INITIAL rx_life_initial
`define RX_INPUT_HASH rx_life_input_hash
`define RX_INPUT_HASH_ASSERTION rx_life_input_hash_assertion
`define RX_GENERATE_ASSERTION rx_generate_assertion
`define RX_GENERATE rx_generate
`define RX_NEXT rx_next_seed
`define RX_DATASET rx_dataset
`define RX_STATS rx_provider_stats
`else
`define RX_INITIAL $rx_life_initial
`define RX_INPUT_HASH $rx_life_input_hash
`define RX_INPUT_HASH_ASSERTION $rx_life_input_hash_assertion
`define RX_GENERATE_ASSERTION $rx_generate_assertion
`define RX_GENERATE $rx_generate
`define RX_NEXT $rx_next_seed
`define RX_DATASET $rx_dataset
`define RX_STATS $rx_provider_stats
`endif
 reg  clk=0;
 reg  rst=0;
 reg  cancel=0;
 reg  req_valid=0;
 wire  req_ready;
 reg [15:0] req_tag=0;
 reg [639:0] req_input=0;
 reg [6:0] req_input_bytes=0;
 wire  init_req_valid;
 reg  init_req_ready=0;
 wire [15:0] init_req_tag;
 wire [639:0] init_req_input;
 wire [6:0] init_req_input_bytes;
 reg  init_wr_valid=0;
 wire  init_wr_ready;
 reg [15:0] init_wr_tag=0;
 reg [20:0] init_wr_addr=0;
 reg [127:0] init_wr_data=0;
 reg [15:0] init_wr_strb=0;
 reg  init_rsp_valid=0;
 wire  init_rsp_ready;
 reg [15:0] init_rsp_tag=0;
 reg [511:0] init_rsp_seed=0;
 reg  init_rsp_error=0;
 wire [511:0] meta_req_seed;
 reg  meta_rsp_error=0;
 reg  sp_rsp_error=0;
 reg  ds_rsp_error=0;
 wire  rsp_valid;
 reg  rsp_ready=0;
 wire [15:0] rsp_tag;
 wire [511:0] rsp_r;
 wire [511:0] rsp_f;
 wire [511:0] rsp_e;
 wire [511:0] rsp_a;
 wire [1:0] rsp_round_mode;
 wire [255:0] rsp_digest;
 wire  rsp_error;
 wire  error_valid;
 wire [15:0] error_tag;
 wire [2:0] error_program;
 wire [1:0] error_code;
 wire [8:0] error_pc;
 wire [7:0] error_opcode;
 wire [3:0] phase;
 wire [1:0] init_fill_phase,program_gen_phase,input_hash_phase;
 wire [1:0] scratchpad_owner;
 wire  generation_exhausted;
 wire  prep_commit_valid;
 wire [15:0] prep_commit_epoch;
 wire [2:0] prep_commit_program;
 wire  meta_req_valid;
 reg  meta_req_ready=0;
 wire [15:0] meta_req_tag;
 wire [2:0] meta_req_program;
 reg  meta_rsp_valid=0;
 wire  meta_rsp_ready;
 reg [15:0] meta_rsp_tag=0;
 reg [2:0] meta_rsp_program=0;
 reg [1023:0] meta_rsp_entropy=0;
 reg [63:0] meta_rsp_program_addr=0;
 wire  program_done_valid;
 reg  program_done_ready=0;
 wire [15:0] program_done_tag;
 wire [2:0] program_done_index;
 wire [11:0] program_done_iterations;
 wire [511:0] program_done_r;
 wire [511:0] program_done_f;
 wire [511:0] program_done_e;
 wire [511:0] program_done_a;
 wire [1:0] program_done_round_mode;
 wire  program_done_seed_valid;
 wire [511:0] program_done_seed;
 wire  iteration_commit_valid;
 wire [15:0] iteration_commit_tag;
 wire [15:0] iteration_commit_backend_tag;
 wire [2:0] iteration_commit_program;
 wire [10:0] iteration_commit_index;
 wire [511:0] iteration_commit_r;
 wire [511:0] iteration_commit_f;
 wire [511:0] iteration_commit_e;
 wire [511:0] iteration_commit_a;
 wire [1:0] iteration_commit_round_mode;
 wire [31:0] iteration_commit_mx;
 wire [31:0] iteration_commit_ma;
 wire [31:0] iteration_commit_spaddr0;
 wire [31:0] iteration_commit_spaddr1;
 wire  sp_rd_valid;
 reg  sp_rd_ready=0;
 wire [20:0] sp_rd_addr;
 wire [50:0] sp_rd_tag;
 reg  sp_rsp_valid=0;
 wire  sp_rsp_ready;
 reg [127:0] sp_rsp_data=0;
 reg [50:0] sp_rsp_tag=0;
 wire  sp_wr_valid;
 reg  sp_wr_ready=0;
 wire [20:0] sp_wr_addr;
 wire [127:0] sp_wr_data;
 wire [15:0] sp_wr_strb;
 wire [50:0] sp_wr_tag;
 wire  ds_req_valid;
 reg  ds_req_ready=0;
 wire [63:0] ds_req_addr;
 wire [63:0] ds_prefetch_addr;
 wire [31:0] ds_req_tag;
 wire  ds_prefetch_valid;
 reg  ds_rsp_valid=0;
 wire  ds_rsp_ready;
 reg [31:0] ds_rsp_tag=0;
 reg [511:0] ds_rsp_data=0;
 wire  prog_valid;
 reg  prog_ready=0;
 wire [63:0] prog_addr;
 wire [40:0] prog_tag;
 reg  prog_rsp_valid=0;
 wire  prog_rsp_ready;
 reg [40:0] prog_rsp_tag=0;
 reg [63:0] prog_rsp_instruction=0;
 reg  prog_rsp_error=0;
 wire  commit_valid;
 wire [15:0] commit_tag;
 wire [8:0] commit_pc;
 wire [7:0] commit_opcode;
 wire [511:0] commit_r;
 wire [8:0] commit_next_pc;
 wire [8:0] commit_branch_target;
 wire [511:0] commit_f;
 wire [511:0] commit_e;
 wire [1:0] commit_round_mode;

 // New prepared dataset ports; original lifecycle interfaces stay intact.
 reg [15:0] req_dataset_epoch=0;
 reg [79:0] req_dataset_counts=0;
 reg [63:0] req_dataset_address_regs=0;
 reg [31:0] req_dataset_rcp_count=0;
 wire dataset_cache_req_valid;
 reg dataset_cache_req_ready=0;
 wire [63:0] dataset_cache_req_tag;
 wire [15:0] dataset_cache_req_epoch;
 wire [2:0] dataset_cache_req_program;
 wire [21:0] dataset_cache_req_index;
 reg dataset_cache_rsp_valid=0;
 wire dataset_cache_rsp_ready;
 reg [63:0] dataset_cache_rsp_tag=0;
 reg [15:0] dataset_cache_rsp_epoch=0;
 reg [2:0] dataset_cache_rsp_program=0;
 reg [21:0] dataset_cache_rsp_index=0;
 reg [511:0] dataset_cache_rsp_data=0;
 reg dataset_cache_rsp_error=0;
 wire dataset_fetch_valid;
 reg dataset_fetch_ready=0;
 wire [63:0] dataset_fetch_tag;
 wire [15:0] dataset_fetch_epoch;
 wire [2:0] dataset_fetch_program;
 wire [8:0] dataset_fetch_pc;
 reg dataset_fetch_rsp_valid=0;
 wire dataset_fetch_rsp_ready;
 reg [63:0] dataset_fetch_rsp_tag=0;
 reg [15:0] dataset_fetch_rsp_epoch=0;
 reg [2:0] dataset_fetch_rsp_program=0;
 reg [8:0] dataset_fetch_rsp_pc=0;
 reg [63:0] dataset_fetch_rsp_instruction=0;
 reg dataset_fetch_rsp_error=0;
 reg dataset_fetch_rsp_rcp_valid=0;
 reg [31:0] dataset_fetch_rsp_rcp_index=0;
 reg [63:0] dataset_fetch_rsp_rcp_value=0;
 wire dataset_req_ready;
 wire dataset_rsp_valid;
 wire dataset_rsp_ready;
 wire [31:0] dataset_rsp_tag;
 wire [511:0] dataset_rsp_data;
 wire dataset_rsp_error;
 wire [1:0] dataset_service_phase;
 wire [3:0] dataset_item_phase;
 wire dataset_generation_exhausted;
 wire dataset_batch_active;
 wire [31:0] dataset_items_reserved;
 wire [31:0] dataset_items_remaining;
 wire [63:0] dataset_items_requested;
 wire [63:0] dataset_items_completed;
 wire [63:0] dataset_ds_requests;
 wire [63:0] dataset_ds_responses;
 wire dataset_item_req_valid;
 wire dataset_item_req_ready;
 wire [15:0] dataset_item_req_tag;
 wire [15:0] dataset_item_req_epoch;
 wire [63:0] dataset_item_req_item;
 wire dataset_item_rsp_valid;
 wire dataset_item_rsp_ready;
 wire [15:0] dataset_item_rsp_tag;
 wire [15:0] dataset_item_rsp_epoch;
 wire [511:0] dataset_item_rsp_data;
 wire dataset_item_rsp_error;
 wire [2:0] dataset_item_rsp_error_stage;
 wire [8:0] dataset_item_rsp_error_pc;
 wire [3:0] dataset_item_rsp_completed_stages;
 wire [12:0] dataset_item_rsp_retired;
 wire [12:0] dataset_item_rsp_muls;
 wire [63:0] dataset_item_rsp_cycles;
 wire [63:0] dataset_item_rsp_exec_cycles;
 wire [63:0] dataset_item_rsp_core_cycles;
 wire [1:0] dataset_item_session_phase;
 wire [31:0] dataset_item_namespace,dataset_item_sessions_used;
 localparam [63:0] DATASET_SESSION_LIMIT=(64'd1<<DATASET_SESSION_BITS)-1;
 wire dataset_item_commit_valid;
 wire [2:0] dataset_item_commit_program;
 wire [8:0] dataset_item_commit_pc;
 wire [7:0] dataset_item_commit_opcode;
 wire [511:0] dataset_item_commit_r;
 wire dataset_item_stage_valid;
 wire [2:0] dataset_item_stage_program;
 wire [21:0] dataset_item_stage_cache_index;
 wire [511:0] dataset_item_stage_r;
 wire [63:0] dataset_item_stage_selected;
 wire [63:0] dataset_item_stage_program_cycles;
 always #5 clk=~clk;
 randomx_prepared_dataset_capacity_hash_lifecycle #(.PROGRAMS(PROGRAMS),.ITERATIONS(ITERATIONS),.PREPARED_RCP(PREPARED_RCP),.HARDWARE_FILL(HARDWARE_FILL),.HARDWARE_PROGRAM(HARDWARE_PROGRAM),.HARDWARE_INPUT_HASH(HARDWARE_INPUT_HASH),.HARDWARE_DATASET(HARDWARE_DATASET),.DATASET_MUL_RADIX4(DATASET_MUL_RADIX4),.DATASET_SESSION_BITS(DATASET_SESSION_BITS)) dut(
  .req_dataset_epoch(req_dataset_epoch),
  .req_dataset_counts(req_dataset_counts),
  .req_dataset_address_regs(req_dataset_address_regs),
  .req_dataset_rcp_count(req_dataset_rcp_count),
  .dataset_cache_req_valid(dataset_cache_req_valid),
  .dataset_cache_req_ready(dataset_cache_req_ready),
  .dataset_cache_req_tag(dataset_cache_req_tag),
  .dataset_cache_req_epoch(dataset_cache_req_epoch),
  .dataset_cache_req_program(dataset_cache_req_program),
  .dataset_cache_req_index(dataset_cache_req_index),
  .dataset_cache_rsp_valid(dataset_cache_rsp_valid),
  .dataset_cache_rsp_ready(dataset_cache_rsp_ready),
  .dataset_cache_rsp_tag(dataset_cache_rsp_tag),
  .dataset_cache_rsp_epoch(dataset_cache_rsp_epoch),
  .dataset_cache_rsp_program(dataset_cache_rsp_program),
  .dataset_cache_rsp_index(dataset_cache_rsp_index),
  .dataset_cache_rsp_data(dataset_cache_rsp_data),
  .dataset_cache_rsp_error(dataset_cache_rsp_error),
  .dataset_fetch_valid(dataset_fetch_valid),
  .dataset_fetch_ready(dataset_fetch_ready),
  .dataset_fetch_tag(dataset_fetch_tag),
  .dataset_fetch_epoch(dataset_fetch_epoch),
  .dataset_fetch_program(dataset_fetch_program),
  .dataset_fetch_pc(dataset_fetch_pc),
  .dataset_fetch_rsp_valid(dataset_fetch_rsp_valid),
  .dataset_fetch_rsp_ready(dataset_fetch_rsp_ready),
  .dataset_fetch_rsp_tag(dataset_fetch_rsp_tag),
  .dataset_fetch_rsp_epoch(dataset_fetch_rsp_epoch),
  .dataset_fetch_rsp_program(dataset_fetch_rsp_program),
  .dataset_fetch_rsp_pc(dataset_fetch_rsp_pc),
  .dataset_fetch_rsp_instruction(dataset_fetch_rsp_instruction),
  .dataset_fetch_rsp_error(dataset_fetch_rsp_error),
  .dataset_fetch_rsp_rcp_valid(dataset_fetch_rsp_rcp_valid),
  .dataset_fetch_rsp_rcp_index(dataset_fetch_rsp_rcp_index),
  .dataset_fetch_rsp_rcp_value(dataset_fetch_rsp_rcp_value),
  .dataset_req_ready(dataset_req_ready),
  .dataset_rsp_valid(dataset_rsp_valid),
  .dataset_rsp_ready(dataset_rsp_ready),
  .dataset_rsp_tag(dataset_rsp_tag),
  .dataset_rsp_data(dataset_rsp_data),
  .dataset_rsp_error(dataset_rsp_error),
  .dataset_service_phase(dataset_service_phase),
  .dataset_item_phase(dataset_item_phase),
  .dataset_generation_exhausted(dataset_generation_exhausted),
  .dataset_batch_active(dataset_batch_active),
  .dataset_items_reserved(dataset_items_reserved),
  .dataset_items_remaining(dataset_items_remaining),
  .dataset_items_requested(dataset_items_requested),
  .dataset_items_completed(dataset_items_completed),
  .dataset_ds_requests(dataset_ds_requests),
  .dataset_ds_responses(dataset_ds_responses),
  .dataset_item_req_valid(dataset_item_req_valid),
  .dataset_item_req_ready(dataset_item_req_ready),
  .dataset_item_req_tag(dataset_item_req_tag),
  .dataset_item_req_epoch(dataset_item_req_epoch),
  .dataset_item_req_item(dataset_item_req_item),
  .dataset_item_rsp_valid(dataset_item_rsp_valid),
  .dataset_item_rsp_ready(dataset_item_rsp_ready),
  .dataset_item_rsp_tag(dataset_item_rsp_tag),
  .dataset_item_rsp_epoch(dataset_item_rsp_epoch),
  .dataset_item_rsp_data(dataset_item_rsp_data),
  .dataset_item_rsp_error(dataset_item_rsp_error),
  .dataset_item_rsp_error_stage(dataset_item_rsp_error_stage),
  .dataset_item_rsp_error_pc(dataset_item_rsp_error_pc),
  .dataset_item_rsp_completed_stages(dataset_item_rsp_completed_stages),
  .dataset_item_rsp_retired(dataset_item_rsp_retired),
  .dataset_item_rsp_muls(dataset_item_rsp_muls),
  .dataset_item_rsp_cycles(dataset_item_rsp_cycles),
  .dataset_item_rsp_exec_cycles(dataset_item_rsp_exec_cycles),
  .dataset_item_rsp_core_cycles(dataset_item_rsp_core_cycles),
  .dataset_item_session_phase(dataset_item_session_phase),
  .dataset_item_namespace(dataset_item_namespace),
  .dataset_item_sessions_used(dataset_item_sessions_used),
  .dataset_item_commit_valid(dataset_item_commit_valid),
  .dataset_item_commit_program(dataset_item_commit_program),
  .dataset_item_commit_pc(dataset_item_commit_pc),
  .dataset_item_commit_opcode(dataset_item_commit_opcode),
  .dataset_item_commit_r(dataset_item_commit_r),
  .dataset_item_stage_valid(dataset_item_stage_valid),
  .dataset_item_stage_program(dataset_item_stage_program),
  .dataset_item_stage_cache_index(dataset_item_stage_cache_index),
  .dataset_item_stage_r(dataset_item_stage_r),
  .dataset_item_stage_selected(dataset_item_stage_selected),
  .dataset_item_stage_program_cycles(dataset_item_stage_program_cycles),
  .clk(clk),
  .rst(rst),
  .cancel(cancel),
  .req_valid(req_valid),
  .req_ready(req_ready),
  .req_tag(req_tag),
  .req_input(req_input),
  .req_input_bytes(req_input_bytes),
  .init_req_valid(init_req_valid),
  .init_req_ready(init_req_ready),
  .init_req_tag(init_req_tag),
  .init_req_input(init_req_input),
  .init_req_input_bytes(init_req_input_bytes),
  .init_wr_valid(init_wr_valid),
  .init_wr_ready(init_wr_ready),
  .init_wr_tag(init_wr_tag),
  .init_wr_addr(init_wr_addr),
  .init_wr_data(init_wr_data),
  .init_wr_strb(init_wr_strb),
  .init_rsp_valid(init_rsp_valid),
  .init_rsp_ready(init_rsp_ready),
  .init_rsp_tag(init_rsp_tag),
  .init_rsp_seed(init_rsp_seed),
  .init_rsp_error(init_rsp_error),
  .meta_req_seed(meta_req_seed),
  .meta_rsp_error(meta_rsp_error),
  .sp_rsp_error(sp_rsp_error),
  .ds_rsp_error(ds_rsp_error),
  .rsp_valid(rsp_valid),
  .rsp_ready(rsp_ready),
  .rsp_tag(rsp_tag),
  .rsp_r(rsp_r),
  .rsp_f(rsp_f),
  .rsp_e(rsp_e),
  .rsp_a(rsp_a),
  .rsp_round_mode(rsp_round_mode),
  .rsp_digest(rsp_digest),
  .rsp_error(rsp_error),
  .error_valid(error_valid),
  .error_tag(error_tag),
  .error_program(error_program),
  .error_code(error_code),
  .error_pc(error_pc),
  .error_opcode(error_opcode),
  .phase(phase),
  .init_fill_phase(init_fill_phase),
  .program_gen_phase(program_gen_phase),
  .input_hash_phase(input_hash_phase),
  .scratchpad_owner(scratchpad_owner),
  .generation_exhausted(generation_exhausted),
  .prep_commit_valid(prep_commit_valid),
  .prep_commit_epoch(prep_commit_epoch),
  .prep_commit_program(prep_commit_program),
  .meta_req_valid(meta_req_valid),
  .meta_req_ready(meta_req_ready),
  .meta_req_tag(meta_req_tag),
  .meta_req_program(meta_req_program),
  .meta_rsp_valid(meta_rsp_valid),
  .meta_rsp_ready(meta_rsp_ready),
  .meta_rsp_tag(meta_rsp_tag),
  .meta_rsp_program(meta_rsp_program),
  .meta_rsp_entropy(meta_rsp_entropy),
  .meta_rsp_program_addr(meta_rsp_program_addr),
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
  .program_done_seed_valid(program_done_seed_valid),
  .program_done_seed(program_done_seed),
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
  .prog_rsp_instruction(prog_rsp_instruction),
  .prog_rsp_error(prog_rsp_error),
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
 wire done_valid=rsp_valid,done_ready=rsp_ready;wire [15:0] done_tag=rsp_tag;
 wire [511:0] done_r=rsp_r,done_f=rsp_f,done_e=rsp_e,done_a=rsp_a;
 wire [1:0] done_round_mode=rsp_round_mode;
 wire [31:0] done_mx=dut.lifecycle.chain_done_mx,done_ma=dut.lifecycle.chain_done_ma,done_spaddr0=dut.lifecycle.chain_done_spaddr0,done_spaddr1=dut.lifecycle.chain_done_spaddr1;
 wire [3:0] iteration_phase=dut.lifecycle.chain.iteration_chain.iteration.iteration.controller.phase_q;
 wire [4:0] execute_phase=dut.lifecycle.chain.iteration_chain.iteration.iteration.execute.state_q;
 wire observed_init_request=HARDWARE_INPUT_HASH?dut.lifecycle.ih_req_valid:init_req_valid;
// Assertion monitors select the actual internal preparation transfers in hardware
 // mode. External provider pins remain suppressed and cannot supply image data.
 wire observed_meta_req_valid=HARDWARE_PROGRAM?(dut.lifecycle.active&&dut.lifecycle.state_q==4&&dut.lifecycle.chain_meta_req_valid):meta_req_valid;
 wire observed_meta_req_ready=HARDWARE_PROGRAM?dut.lifecycle.chain_meta_req_ready:meta_req_ready;
 wire observed_meta_rsp_valid=HARDWARE_PROGRAM?dut.lifecycle.chain_meta_rsp_valid:meta_rsp_valid;
 wire observed_meta_rsp_ready=HARDWARE_PROGRAM?dut.lifecycle.chain_meta_rsp_ready:meta_rsp_ready;
 wire [15:0] observed_meta_rsp_tag=HARDWARE_PROGRAM?dut.lifecycle.chain_meta_rsp_tag:meta_rsp_tag;
 wire [2:0] observed_meta_rsp_program=HARDWARE_PROGRAM?dut.lifecycle.chain_meta_rsp_program:meta_rsp_program;
 wire observed_prog_valid=HARDWARE_PROGRAM?(dut.lifecycle.active&&dut.lifecycle.state_q==4&&dut.lifecycle.chain_prog_valid):prog_valid;
 wire observed_prog_ready=HARDWARE_PROGRAM?dut.lifecycle.chain_prog_ready:prog_ready;
 wire observed_prog_rsp_valid=HARDWARE_PROGRAM?dut.lifecycle.chain_prog_rsp_valid:prog_rsp_valid;
 wire observed_prog_rsp_ready=HARDWARE_PROGRAM?dut.lifecycle.chain_prog_rsp_ready:prog_rsp_ready;
 wire [40:0] observed_prog_rsp_tag=HARDWARE_PROGRAM?{dut.lifecycle.generation_q,dut.lifecycle.chain_prog_rsp_tag}:prog_rsp_tag;
 wire [63:0] observed_prog_rsp_instruction=HARDWARE_PROGRAM?dut.lifecycle.chain_prog_rsp_instruction:prog_rsp_instruction;
 `include "sequence_sizes.vh"
 reg [127:0] ram[0:131071],gold_ram[0:131071],initial_ram[0:131071],cancel_ram[0:131071];
 reg [63:0] gold_rom[0:383];reg [511:0] gold_final_a[0:0];reg [2047:0] gold_final_rf[0:0];reg [255:0] gold_digest[0:0];
 reg [63:0] rom[0:383];reg [2529:0] gold[0:TOTAL_ITERATIONS-1];
 reg [1803:0] gold_meta[0:PROGRAMS-1];reg [85:0] events[0:TOTAL_EVENTS-1];
 reg [4095:0] directory,path,output_directory;reg [511:0] seed;reg [1023:0] native_entropy;
 integer cycle=0,global_iteration=0,programs_finished=0,event_index=0,total_instructions=0;
 integer reads=0,writes=0,tail_writes=0,meta_drops=0,rom_drops=0,sp_drops=0,ds_drops=0;
 integer meta_pending=0,meta_delay=0,meta_injected=0,meta_stalls=0,active_program=0;
 integer sp_pending=0,sp_delay=0,sp_injected=0,rd_stalls=0,wr_stalls=0;
 integer rom_pending=0,rom_delay=0,rom_injected=0,rom_stalls=0;
 integer ds_pending=0,ds_delay=0,ds_injected=0,ds_stalls=0;
 integer kernel_started=0,dataset_taken=0,tail_index=0,steps=0,program_hold=0,done_hold=0;
 integer accepted_done=0,i,b,pc,entry_reads=0;
 reg [15:0] meta_tag,batch_tag,inner_tag;reg [50:0] sp_tag;reg [40:0] rom_tag;reg [31:0] ds_tag;
 reg [2:0] meta_program;
 reg [127:0] sp_data;reg [63:0] rom_data;reg [511:0] ds_data;
 reg [63:0] route,word;reg [31:0] expected_addr;reg [127:0] expected_data;
 reg held_read=0,held_write=0,held_rom=0,held_meta=0,held_ds=0,held_program=0,held_done=0;
 reg [255:0] saved_read,saved_write,saved_rom,saved_meta;
 reg [255:0] saved_ds;reg [4095:0] saved_program,saved_done;
 wire [255:0] now_read={sp_rd_tag,sp_rd_addr};
 wire [255:0] now_write={sp_wr_tag,sp_wr_addr,sp_wr_strb,sp_wr_data};
 wire [255:0] now_rom={prog_tag,prog_addr};wire [255:0] now_meta={meta_req_tag,meta_req_program};
 wire [255:0] now_ds={ds_req_tag,ds_req_addr,ds_prefetch_addr};
 wire [4095:0] now_program={program_done_tag,program_done_index,program_done_iterations,program_done_round_mode,
  program_done_r,program_done_f,program_done_e,program_done_a,program_done_seed_valid,program_done_seed};
 wire [4095:0] now_done={done_tag,done_round_mode,done_r,done_f,done_e,done_a,done_mx,done_ma,done_spaddr0,done_spaddr1,rsp_digest,rsp_error,error_program,error_code,error_pc,error_opcode};
 wire [4095:0] now_response={rsp_tag,rsp_round_mode,rsp_r,rsp_f,rsp_e,rsp_a,rsp_digest,rsp_error,error_tag,error_program,error_code,error_pc,error_opcode};
 integer initializing=0,initial_index=0,init_writes=0,final_reads=0,admissions=0,loaded_words=0;
 integer ledger[0:10],iteration_detail[0:11],final_detail[0:5],exec_detail[0:17];
 integer input_hash_detail[0:2],input_hash_requests=0,input_hash_completions=0,input_stage_clocks=0;
 integer removed_initial_replies=0,removed_initial_writes=0;
 reg [511:0] expected_input_seed;
 integer program_gen_detail[0:2],generated_beats=0,program_gen_images=0,generation_image_beats=0;
 integer external_meta_drops=0,external_program_drops=0;
 integer init_provider_wait=0,fill_detail[0:2],init_response_drops=0,init_write_drops=0;
 integer init_input_hash_calls=0,init_same_cycle_offers=0,init_same_cycle_accepts=0;
 reg init_request_seed_pending=0;reg [528:0] held_init_response;
 integer trace_file,ledger_file,stage_sum=0,phase_index=0,final_phase_index=0,byte_index=0;
 integer last_trace_phase=-1,last_trace_iteration=-1,last_trace_execute=-1;
 integer logical_sp_bytes=0,physical_read_bytes=0,physical_write_bus_bytes=0,useful_write_bytes=0;
 integer final_wait=0,held_response=0;reg [15:0] init_generation=0;reg [639:0] input_value=0;integer input_bytes=0;
 reg [511:0] expected_seed,native_expected_seed;reg [15:0] last_epoch=0;reg [24:0] current_load=0;
 reg [639:0] restart_input;reg [511:0] restart_seed,restart_expected_seed;integer restart_bytes=0,restart_writes=0,restart_cycles=0,restart_saw_hold=0;
 reg restart_held=0;reg [255:0] restart_saved_write;
 integer restart_image_beats=0,restart_metadata_accepted=0;
 integer seed_hashes=0;
 integer matching_fault_accepted=0;
 integer boundary_valid=0,boundary_invalid=0,boundary_canceled=0;
 reg [639:0] boundary_max_input;reg [511:0] boundary_cancel_seed;
 // Dataset observations are nested inside the existing iteration ledger.
 // They are never added to the outer total a second time.
 wire selected_ds_req_ready=HARDWARE_DATASET?dataset_req_ready:ds_req_ready;
 wire selected_ds_rsp_valid=HARDWARE_DATASET?dataset_rsp_valid:ds_rsp_valid;
 wire selected_ds_rsp_ready=HARDWARE_DATASET?dataset_rsp_ready:ds_rsp_ready;
 wire [31:0] selected_ds_rsp_tag=HARDWARE_DATASET?dataset_rsp_tag:ds_rsp_tag;
 wire [511:0] selected_ds_rsp_data=HARDWARE_DATASET?dataset_rsp_data:ds_rsp_data;
 wire selected_ds_rsp_error=HARDWARE_DATASET?dataset_rsp_error:ds_rsp_error;
 reg [4095:0] dataset_asset_root,dataset_path;
 reg [79:0] dataset_asset_counts;reg [63:0] dataset_asset_addresses;
 reg [31:0] dataset_asset_rcp_count;reg [15:0] dataset_asset_epoch=16'h4ca3;
 reg [63:0] dataset_programs[0:4095],dataset_reciprocals[0:4095];
 reg [7:0] dataset_cache_bytes[0:63];
 integer dataset_cache_fd,dataset_gold_fd,dataset_rows_fd,dataset_asset_fd;
 integer dataset_requests_seen=0,dataset_responses_seen=0,dataset_live_calls=0;
 integer dataset_items_seen=0,dataset_item_returns_seen=0,dataset_stage_pulses=0,dataset_commit_pulses=0;
 integer dataset_cache_requests=0,dataset_cache_responses=0,dataset_fetch_requests=0,dataset_fetch_responses=0;
 integer dataset_stale_packets=0,dataset_matching_faults=0;
 integer dataset_f_pending=0,dataset_f_delay=0,dataset_f_stale=0,dataset_f_wait=0;
 integer dataset_c_pending=0,dataset_c_delay=0,dataset_c_stale=0,dataset_c_wait=0;
 integer dataset_f_program=0,dataset_f_pc=0,dataset_c_program=0;
 reg [63:0] dataset_f_tag=0,dataset_c_tag=0;
 reg [31:0] dataset_owned_tag=0,dataset_owned_namespace=0,dataset_previous_namespace=0;
 reg [63:0] dataset_item_cache_tag=0,dataset_previous_cache_tag=0,dataset_previous_fetch_tag=0;
 reg [63:0] dataset_stage_fetch_tag[0:7];
 reg [15:0] dataset_f_epoch=0,dataset_c_epoch=0;
 reg [21:0] dataset_c_index=0,dataset_expected_index=0;
 reg [511:0] dataset_c_data=0,dataset_expected_data=0,dataset_program_result=0,dataset_last_commit=0,dataset_accepted_cache=0;
 reg [63:0] dataset_gold_address=0,dataset_owned_address=0;
 reg [63:0] dataset_replay_fetch_tag=0,dataset_replay_cache_tag=0;
 reg dataset_fetch_held=0,dataset_cache_held=0;
 reg [91:0] dataset_saved_fetch;reg [104:0] dataset_saved_cache;
 wire [91:0] dataset_now_fetch={dataset_fetch_tag,dataset_fetch_epoch,dataset_fetch_program,dataset_fetch_pc};
 wire [104:0] dataset_now_cache={dataset_cache_req_tag,dataset_cache_req_epoch,dataset_cache_req_program,dataset_cache_req_index};
 integer dataset_item_stage_count=0,dataset_item_commits=0,dataset_item_muls=0;
 integer dataset_stage_commits[0:7],dataset_stage_fetches[0:7],dataset_stage_muls[0:7];
 integer dataset_counts[0:7],dataset_mul_counts[0:7];
 integer dataset_service_detail[0:2],dataset_item_detail[0:8],dataset_session_detail[0:2];
 integer dataset_service_clocks=0,dataset_item_clocks=0,dataset_request_stalls=0;
 integer dataset_cache_request_stalls=0,dataset_fetch_request_stalls=0;
 reg [63:0] dataset_item_executor_sum=0,dataset_ideal_executor=0;
 reg [63:0] dataset_available_clocks=0,dataset_core_clocks=0,dataset_launch_clocks=0,dataset_executor_clocks=0,dataset_program_service_extra=0,dataset_cache_service_extra=0;
 reg [63:0] dataset_current_wait=0,dataset_response_wait_sum=0;
 reg dataset_wait_active=0,dataset_first_response_seen=0;
 integer dataset_multiply_wait=0,dataset_multiply_wait_clocks=0;
 function integer dataset_is_mul;
  input [7:0] op;
  begin dataset_is_mul=op==3||op==11||op==12||op==13;end
 endfunction
 task dataset_assets_load;
  integer status,n,j,asset_case,asset_cache;
  reg [63:0] unused_item;reg [511:0] unused_final;
 begin
  if(!$value$plusargs("asset_root=%s",dataset_asset_root))$fatal(1,"missing asset_root actual prepared cache inputs");
  $sformat(dataset_path,"%0s/cases-real.hex",dataset_asset_root);dataset_asset_fd=$fopen(dataset_path,"r");
  if(!dataset_asset_fd)$fatal(1,"prepared descriptor source missing");
  status=$fscanf(dataset_asset_fd,"%d %d %h %h %h %h %h\n",asset_case,asset_cache,unused_item,dataset_asset_rcp_count,dataset_asset_counts,dataset_asset_addresses,unused_final);
  $fclose(dataset_asset_fd);
  if(status!=7||asset_case!=0||asset_cache!=0||dataset_asset_rcp_count==0||dataset_asset_rcp_count>4096)
   $fatal(1,"prepared native cache0 descriptor context invalid");
  $sformat(dataset_path,"%0s/cache-0-prepared-programs.mem",dataset_asset_root);$readmemh(dataset_path,dataset_programs);
  $sformat(dataset_path,"%0s/cache-0-reciprocals.mem",dataset_asset_root);$readmemh(dataset_path,dataset_reciprocals,0,dataset_asset_rcp_count-1);
  $sformat(dataset_path,"%0s/cache-0.bin",dataset_asset_root);dataset_cache_fd=$fopen(dataset_path,"rb");
  if(!dataset_cache_fd)$fatal(1,"actual prepared native cache missing");
  $sformat(dataset_path,"%0s/dataset-items.hex",directory);dataset_gold_fd=$fopen(dataset_path,"r");
  if(!dataset_gold_fd)$fatal(1,"retained native dataset assertion rows missing");
  $sformat(dataset_path,"%0s/dataset-items-ledger.csv",output_directory);dataset_rows_fd=$fopen(dataset_path,"w");
  if(!dataset_rows_fd)$fatal(1,"dataset item ledger open");
  $fdisplay(dataset_rows_fd,"tag,address,image_epoch,item_namespace,item_cycles,core_cycles,executor_cycles,session_launch_extra,stages,retired,muls,instruction_service_extra,cache_service_extra,request_to_first_response");
  for(n=0;n<8;n=n+1)begin
   dataset_counts[n]=dataset_asset_counts[n*10+:10];dataset_mul_counts[n]=0;
   if(dataset_counts[n]==0||dataset_counts[n]>512||dataset_asset_addresses[n*8+:8]>7)
    $fatal(1,"integration requires the declared nonempty native cache0 program descriptors");
   for(j=0;j<dataset_counts[n];j=j+1)begin
    if(^dataset_programs[n*512+j]===1'bx)$fatal(1,"missing actual prepared instruction stage=%0d pc=%0d",n,j);
    dataset_mul_counts[n]=dataset_mul_counts[n]+dataset_is_mul(dataset_programs[n*512+j][7:0]);
   end
   dataset_ideal_executor=dataset_ideal_executor+3*dataset_counts[n]+(DATASET_MUL_RADIX4?34:2)*dataset_mul_counts[n];
  end
  for(n=0;n<dataset_asset_rcp_count;n=n+1)if(^dataset_reciprocals[n]===1'bx)$fatal(1,"missing actual prepared reciprocal index=%0d",n);
  if(DATASET_MUL_RADIX4&&dataset_ideal_executor!==64'd53325)$fatal(1,"declared native cache0 ideal executor baseline differs from 53325");
  for(n=0;n<3;n=n+1)begin dataset_service_detail[n]=0;dataset_session_detail[n]=0;end
  for(n=0;n<9;n=n+1)dataset_item_detail[n]=0;
  req_dataset_epoch=dataset_asset_epoch;req_dataset_counts=dataset_asset_counts;
  req_dataset_address_regs=dataset_asset_addresses;req_dataset_rcp_count=dataset_asset_rcp_count;
  if((DATASET_CANCEL||DATASET_ERROR)&&!HARDWARE_DATASET)$fatal(1,"dataset control profile requires hardware path");
  if(DATASET_CANCEL==3&&!DATASET_MUL_RADIX4)$fatal(1,"multiply-midpoint cancellation uses the declared iterative dataset profile");
  if(!HARDWARE_FILL||!HARDWARE_PROGRAM||!HARDWARE_INPUT_HASH)$fatal(1,"new dataset integration requires hardware preparation flags");
 end endtask
 task dataset_read_native_assertion;
  integer status;
 begin
  status=$fscanf(dataset_gold_fd,"%h %h\n",dataset_gold_address,dataset_expected_data);
  if(status!=2||dataset_gold_address!==ds_req_addr)$fatal(1,"actual dataset full64 address differs from retained native gold");
  dataset_requests_seen=dataset_requests_seen+1;
 end endtask
 task dataset_read_cache;
  input [21:0] index;output [511:0] data;
  integer status,n;
 begin
  status=$fseek(dataset_cache_fd,index*64,0);if(status)$fatal(1,"actual cache seek failed");
  status=$fread(dataset_cache_bytes,dataset_cache_fd,0,64);if(status!=64)$fatal(1,"actual cache short read");
  for(n=0;n<64;n=n+1)data[n*8+:8]=dataset_cache_bytes[n];
 end endtask
 task dataset_provider_drive;
  integer slot;reg [31:0] index;
 begin
  // Poison every caller asset field after outer acceptance. Only the captured
  // descriptor and epoch may reach the actual instruction/cache requests.
  req_dataset_epoch=~dataset_asset_epoch;req_dataset_counts=~dataset_asset_counts;
  req_dataset_address_regs=~dataset_asset_addresses;req_dataset_rcp_count=0;
  dataset_cache_req_ready=HARDWARE_DATASET&&!dataset_c_pending&&(!STALL||dataset_c_wait>=2);
  dataset_fetch_ready=HARDWARE_DATASET&&!dataset_f_pending&&(!STALL||dataset_f_wait>=2);
  dataset_cache_rsp_valid=0;dataset_cache_rsp_error=0;dataset_fetch_rsp_valid=0;dataset_fetch_rsp_error=0;dataset_fetch_rsp_rcp_valid=0;
  if(HARDWARE_DATASET&&STALL&&!dataset_c_pending)begin
   dataset_cache_rsp_valid=1;dataset_cache_rsp_tag=dataset_cache_req_tag^64'h8000000000000000;
   dataset_cache_rsp_data=~512'b0;dataset_cache_rsp_error=1;
  end
  if(HARDWARE_DATASET&&STALL&&!dataset_f_pending)begin
   dataset_fetch_rsp_valid=1;dataset_fetch_rsp_tag=dataset_fetch_tag^64'h8000000000000000;
   dataset_fetch_rsp_instruction=~64'b0;dataset_fetch_rsp_error=1;
  end
  if(dataset_f_pending)begin
   if(dataset_f_delay>0)dataset_f_delay=dataset_f_delay-1;
   else begin
    slot=dataset_f_program*512+dataset_f_pc;index=dataset_programs[slot][63:32];
    dataset_fetch_rsp_valid=1;dataset_fetch_rsp_tag=dataset_f_tag;dataset_fetch_rsp_epoch=dataset_f_epoch;
    dataset_fetch_rsp_program=dataset_f_program;dataset_fetch_rsp_pc=dataset_f_pc;
    dataset_fetch_rsp_instruction=dataset_programs[slot];dataset_fetch_rsp_rcp_valid=dataset_programs[slot][7:0]==13;
    dataset_fetch_rsp_rcp_index=index;dataset_fetch_rsp_rcp_value=index<dataset_asset_rcp_count?dataset_reciprocals[index]:0;
    if(dataset_f_stale)begin
     dataset_fetch_rsp_tag=dataset_f_tag^(dataset_f_stale==2?64'h8000000000000000:64'h0000000000000001);
     dataset_fetch_rsp_error=1;dataset_fetch_rsp_instruction=~64'b0;
    end else if(DATASET_ERROR==2&&dataset_f_program==0&&dataset_f_pc==0)dataset_fetch_rsp_error=1;
   end
  end
  if(dataset_c_pending)begin
   if(dataset_c_delay>0)dataset_c_delay=dataset_c_delay-1;
   else begin
    dataset_cache_rsp_valid=1;dataset_cache_rsp_tag=dataset_c_tag;dataset_cache_rsp_epoch=dataset_c_epoch;
    dataset_cache_rsp_program=dataset_c_program;dataset_cache_rsp_index=dataset_c_index;dataset_cache_rsp_data=dataset_c_data;
    if(dataset_c_stale)begin
     dataset_cache_rsp_tag=dataset_c_tag^(dataset_c_stale==2?64'h8000000000000000:64'h0000000000000001);
     dataset_cache_rsp_data=~512'b0;dataset_cache_rsp_error=1;
    end else if(DATASET_ERROR==1&&dataset_c_program==0)dataset_cache_rsp_error=1;
   end
  end
 end endtask
 task dataset_provider_observe;
  integer n,slot;reg [63:0] ideal_stage,outer_base;
 begin
  if(HARDWARE_DATASET)begin
   if(dataset_service_phase>2||dataset_item_phase>8||dataset_item_session_phase>2)$fatal(1,"invalid dataset nested phase");
   if(phase==4)begin dataset_service_detail[dataset_service_phase]=dataset_service_detail[dataset_service_phase]+1;dataset_service_clocks=dataset_service_clocks+1;dataset_session_detail[dataset_item_session_phase]=dataset_session_detail[dataset_item_session_phase]+1;end
   if(dataset_item_phase!=0)begin dataset_item_detail[dataset_item_phase]=dataset_item_detail[dataset_item_phase]+1;dataset_item_clocks=dataset_item_clocks+1;end
   if(dataset_wait_active&&!dataset_first_response_seen&&!dataset_rsp_valid)dataset_current_wait=dataset_current_wait+1;
   if(dataset_wait_active&&!dataset_first_response_seen&&dataset_rsp_valid)dataset_first_response_seen=1;
   if(dataset_multiply_wait)dataset_multiply_wait_clocks=dataset_multiply_wait_clocks+1;
   if(dataset_fetch_held&&(!dataset_fetch_valid||dataset_now_fetch!==dataset_saved_fetch))$fatal(1,"held prepared fetch changed");
   if(dataset_cache_held&&(!dataset_cache_req_valid||dataset_now_cache!==dataset_saved_cache))$fatal(1,"held actual cache request changed");
   dataset_fetch_held=dataset_fetch_valid&&!dataset_fetch_ready;dataset_saved_fetch=dataset_now_fetch;
   dataset_cache_held=dataset_cache_req_valid&&!dataset_cache_req_ready;dataset_saved_cache=dataset_now_cache;
   if(dataset_fetch_valid&&!dataset_fetch_ready)begin dataset_f_wait=dataset_f_wait+1;dataset_fetch_request_stalls=dataset_fetch_request_stalls+1;end
   if(dataset_cache_req_valid&&!dataset_cache_req_ready)begin dataset_c_wait=dataset_c_wait+1;dataset_cache_request_stalls=dataset_cache_request_stalls+1;end
   if(dataset_fetch_rsp_valid&&dataset_fetch_rsp_ready)begin
    if(!dataset_f_pending||dataset_fetch_rsp_tag!=dataset_f_tag)begin
     dataset_stale_packets=dataset_stale_packets+1;
     if(dataset_f_pending&&dataset_f_stale)begin dataset_f_stale=dataset_f_stale-1;dataset_f_delay=STALL?1:0;end
    end else begin
     dataset_f_pending=0;dataset_fetch_responses=dataset_fetch_responses+1;
     if(dataset_fetch_rsp_error)dataset_matching_faults=dataset_matching_faults+1;
     if(!dataset_fetch_rsp_error&&dataset_is_mul(dataset_fetch_rsp_instruction[7:0]))begin dataset_multiply_wait=1;dataset_multiply_wait_clocks=0;end
    end
   end
   if(dataset_cache_rsp_valid&&dataset_cache_rsp_ready)begin
    if(!dataset_c_pending||dataset_cache_rsp_tag!=dataset_c_tag)begin
     dataset_stale_packets=dataset_stale_packets+1;
     if(dataset_c_pending&&dataset_c_stale)begin dataset_c_stale=dataset_c_stale-1;dataset_c_delay=STALL?1:0;end
    end else begin
     dataset_c_pending=0;dataset_cache_responses=dataset_cache_responses+1;
     if(dataset_cache_rsp_error)dataset_matching_faults=dataset_matching_faults+1;
     else dataset_accepted_cache=dataset_cache_rsp_data;
    end
   end
   if(dataset_item_req_valid&&dataset_item_req_ready)begin
    if(!ds_req_valid||!selected_ds_req_ready||dataset_wait_active||dataset_item_req_tag!==ds_req_tag[15:0]||
       dataset_item_req_epoch!==dataset_asset_epoch||dataset_item_req_item!==(ds_req_addr>>6))
     $fatal(1,"dataset item launched without exact full-tag addressed demand");
    dataset_owned_tag=ds_req_tag;dataset_owned_address=ds_req_addr;
    dataset_owned_namespace=dataset_item_sessions_used+1;
    if(dataset_owned_namespace==0||dataset_owned_namespace<=dataset_previous_namespace)$fatal(1,"new full-width item namespace was reused or wrapped");
    dataset_previous_namespace=dataset_owned_namespace;dataset_expected_index=dataset_item_req_item[21:0];
    dataset_items_seen=dataset_items_seen+1;dataset_item_stage_count=0;dataset_item_commits=0;dataset_item_muls=0;dataset_item_executor_sum=0;
    dataset_wait_active=1;dataset_first_response_seen=0;dataset_current_wait=0;
    for(n=0;n<8;n=n+1)begin dataset_stage_commits[n]=0;dataset_stage_fetches[n]=0;dataset_stage_muls[n]=0;dataset_stage_fetch_tag[n]=0;end
   end
   if(dataset_item_commit_valid)begin
    slot=dataset_item_commit_program*512+dataset_stage_commits[dataset_item_commit_program];
    if(dataset_item_commit_program!==dataset_item_stage_count[2:0]||dataset_item_commit_pc!==dataset_stage_commits[dataset_item_commit_program][8:0]||
       dataset_item_commit_opcode!==dataset_programs[slot][7:0]||dataset_stage_commits[dataset_item_commit_program]>=dataset_counts[dataset_item_commit_program])
     $fatal(1,"nested dataset actual retirement identity/order");
    dataset_stage_commits[dataset_item_commit_program]=dataset_stage_commits[dataset_item_commit_program]+1;
    dataset_item_commits=dataset_item_commits+1;dataset_item_muls=dataset_item_muls+dataset_is_mul(dataset_item_commit_opcode);
    dataset_stage_muls[dataset_item_commit_program]=dataset_stage_muls[dataset_item_commit_program]+dataset_is_mul(dataset_item_commit_opcode);
    dataset_last_commit=dataset_item_commit_r;dataset_commit_pulses=dataset_commit_pulses+1;
    if(dataset_is_mul(dataset_item_commit_opcode))dataset_multiply_wait=0;
   end
   if(dataset_fetch_valid&&dataset_fetch_ready)begin
    if(dataset_f_pending||dataset_fetch_epoch!==dataset_asset_epoch||dataset_fetch_program!==dataset_item_stage_count[2:0]||
       dataset_fetch_pc!==dataset_stage_fetches[dataset_fetch_program][8:0]||dataset_fetch_pc>=dataset_counts[dataset_fetch_program])
     $fatal(1,"captured prepared image fetch association/count");
    if(dataset_fetch_tag[15:0]!==dataset_owned_tag[15:0]||dataset_fetch_tag[31:16]==0||dataset_fetch_tag[63:32]!==dataset_owned_namespace||dataset_item_namespace!==dataset_owned_namespace)$fatal(1,"full prepared fetch caller/generation identity");
    if(dataset_stage_fetches[dataset_fetch_program]==0)begin
     if(dataset_fetch_tag==dataset_previous_fetch_tag)$fatal(1,"prepared fetch generation reused");
     dataset_stage_fetch_tag[dataset_fetch_program]=dataset_fetch_tag;dataset_previous_fetch_tag=dataset_fetch_tag;
    end else if(dataset_fetch_tag!==dataset_stage_fetch_tag[dataset_fetch_program])$fatal(1,"full prepared fetch tag changed midprogram");
    dataset_f_pending=1;dataset_f_tag=dataset_fetch_tag;dataset_f_epoch=dataset_fetch_epoch;dataset_f_program=dataset_fetch_program;dataset_f_pc=dataset_fetch_pc;
    dataset_f_wait=0;dataset_f_delay=STALL?2+(dataset_fetch_pc%3):0;dataset_f_stale=STALL?2:0;
    dataset_stage_fetches[dataset_fetch_program]=dataset_stage_fetches[dataset_fetch_program]+1;dataset_fetch_requests=dataset_fetch_requests+1;
   end
   if(dataset_cache_req_valid&&dataset_cache_req_ready)begin
    if(dataset_c_pending||dataset_cache_req_epoch!==dataset_asset_epoch||dataset_cache_req_program!==dataset_item_stage_count[2:0]||
       dataset_cache_req_index!==dataset_expected_index||dataset_stage_commits[dataset_cache_req_program]!=dataset_counts[dataset_cache_req_program])
     $fatal(1,"actual cache request did not follow captured image and post-XOR recurrence");
    if(dataset_cache_req_tag[15:0]!==dataset_owned_tag[15:0]||dataset_cache_req_tag[31:16]==0||dataset_cache_req_tag[63:32]!==dataset_owned_namespace||dataset_item_namespace!==dataset_owned_namespace)$fatal(1,"full cache caller/generation identity");
    if(dataset_cache_req_program==0)begin
     if(dataset_cache_req_tag==dataset_previous_cache_tag)$fatal(1,"cache item generation reused");
     dataset_item_cache_tag=dataset_cache_req_tag;dataset_previous_cache_tag=dataset_cache_req_tag;
    end else if(dataset_cache_req_tag!==dataset_item_cache_tag)$fatal(1,"full cache tag changed within item");
    dataset_c_pending=1;dataset_c_tag=dataset_cache_req_tag;dataset_c_epoch=dataset_cache_req_epoch;
    dataset_c_program=dataset_cache_req_program;dataset_c_index=dataset_cache_req_index;
    dataset_read_cache(dataset_cache_req_index,dataset_c_data);dataset_program_result=dataset_last_commit;
    dataset_c_wait=0;dataset_c_delay=STALL?3+(dataset_cache_req_program%3):0;dataset_c_stale=STALL?2:0;
    dataset_cache_requests=dataset_cache_requests+1;
   end
   if(dataset_item_stage_valid)begin
    ideal_stage=3*dataset_counts[dataset_item_stage_count]+(DATASET_MUL_RADIX4?34:2)*dataset_mul_counts[dataset_item_stage_count];
    if(dataset_item_stage_count>=8||dataset_item_stage_program!==dataset_item_stage_count[2:0]||
       dataset_item_stage_cache_index!==dataset_expected_index||dataset_item_stage_r!==(dataset_program_result^dataset_accepted_cache)||
       dataset_item_stage_selected!==dataset_item_stage_r[dataset_asset_addresses[dataset_item_stage_count*8+:8]*64+:64]||
       dataset_item_stage_program_cycles<ideal_stage)$fatal(1,"nested dataset XOR/selected address/clock observation");
    if(!STALL&&dataset_item_stage_program_cycles!==ideal_stage)$fatal(1,"ideal nested dataset program clocks");
    dataset_expected_index=dataset_item_stage_selected[21:0];dataset_item_executor_sum=dataset_item_executor_sum+dataset_item_stage_program_cycles;
    dataset_item_stage_count=dataset_item_stage_count+1;dataset_stage_pulses=dataset_stage_pulses+1;
   end
   if(dataset_item_rsp_valid&&dataset_item_rsp_ready)begin
    if(dataset_item_rsp_tag!==dataset_owned_tag[15:0]||dataset_item_rsp_epoch!==dataset_asset_epoch||
       !dataset_rsp_valid||dataset_rsp_tag!==dataset_owned_tag||dataset_item_rsp_retired!==dataset_item_commits[12:0]||dataset_item_rsp_muls!==dataset_item_muls[12:0])
     $fatal(1,"nested dataset terminal tag/epoch/counter binding");
    if(!dataset_item_rsp_error)begin
     outer_base=DATASET_MUL_RADIX4?74:42;
     if(dataset_item_rsp_data!==dataset_expected_data||dataset_rsp_data!==dataset_expected_data||dataset_item_stage_count!=8||
        dataset_item_rsp_completed_stages!=8||dataset_item_rsp_exec_cycles!==dataset_item_executor_sum||
        dataset_current_wait!==dataset_item_rsp_cycles||dataset_item_rsp_cycles!==dataset_item_rsp_core_cycles+1||
        dataset_item_rsp_core_cycles<dataset_item_rsp_exec_cycles+outer_base)
      $fatal(1,"native nested item result or nonclosing availability ledger");
     if(!STALL&&dataset_item_rsp_core_cycles!==dataset_item_rsp_exec_cycles+outer_base)$fatal(1,"ideal nested dataset outer clocks");
     dataset_available_clocks=dataset_available_clocks+dataset_item_rsp_cycles;
     dataset_core_clocks=dataset_core_clocks+dataset_item_rsp_core_cycles;
     dataset_launch_clocks=dataset_launch_clocks+dataset_item_rsp_cycles-dataset_item_rsp_core_cycles;
     dataset_executor_clocks=dataset_executor_clocks+dataset_item_rsp_exec_cycles;
     dataset_program_service_extra=dataset_program_service_extra+dataset_item_rsp_exec_cycles-dataset_ideal_executor;
     dataset_cache_service_extra=dataset_cache_service_extra+dataset_item_rsp_core_cycles-dataset_item_rsp_exec_cycles-outer_base;
     dataset_response_wait_sum=dataset_response_wait_sum+dataset_current_wait;
     $fdisplay(dataset_rows_fd,"%h,%h,%h,%h,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",dataset_owned_tag,dataset_owned_address,dataset_asset_epoch,dataset_owned_namespace,dataset_item_rsp_cycles,dataset_item_rsp_core_cycles,dataset_item_rsp_exec_cycles,dataset_item_rsp_cycles-dataset_item_rsp_core_cycles,dataset_item_rsp_completed_stages,dataset_item_rsp_retired,dataset_item_rsp_muls,dataset_item_rsp_exec_cycles-dataset_ideal_executor,dataset_item_rsp_core_cycles-dataset_item_rsp_exec_cycles-outer_base,dataset_current_wait);
    end else if(!DATASET_ERROR||dataset_rsp_data!==0||!dataset_rsp_error||dataset_item_stage_count!=0||
       dataset_item_rsp_error_stage!==3'b0||dataset_item_rsp_error_pc!==9'b0||dataset_item_rsp_completed_stages!==4'b0)
     $fatal(1,"matching dataset error was not contained at the first-stage fault before XOR");
    dataset_wait_active=0;dataset_item_returns_seen=dataset_item_returns_seen+1;
   end
  end else if(dataset_item_req_valid||dataset_fetch_valid||dataset_cache_req_valid||dataset_item_commit_valid||dataset_item_stage_valid)
   $fatal(1,"software dataset baseline emitted hardware dataset work");
 end endtask
 task dataset_stale_drive;begin
  dataset_fetch_rsp_valid=1;dataset_fetch_rsp_tag=dataset_replay_fetch_tag;dataset_fetch_rsp_error=1;dataset_fetch_rsp_instruction=~64'b0;
  dataset_cache_rsp_valid=1;dataset_cache_rsp_tag=dataset_replay_cache_tag;dataset_cache_rsp_error=1;dataset_cache_rsp_data=~512'b0;
 end endtask
 task dataset_clear_provider;begin
  dataset_fetch_rsp_valid=0;dataset_cache_rsp_valid=0;dataset_fetch_rsp_error=0;dataset_cache_rsp_error=0;
  dataset_fetch_ready=0;dataset_cache_req_ready=0;dataset_f_pending=0;dataset_c_pending=0;
  dataset_fetch_held=0;dataset_cache_held=0;dataset_wait_active=0;dataset_multiply_wait=0;
 end endtask
 task dataset_restart_prefix;
  integer clocks;
  reg [511:0] changed_seed;
 begin
  dataset_asset_epoch=dataset_asset_epoch+16'b1;
  req_dataset_epoch=dataset_asset_epoch;req_dataset_counts=dataset_asset_counts;
  req_dataset_address_regs=dataset_asset_addresses;req_dataset_rcp_count=dataset_asset_rcp_count;
  restart_input=input_value^640'd1;restart_bytes=input_bytes?input_bytes:1;
  @(negedge clk);req_valid=1;req_tag=16'h9001;req_input=restart_input;req_input_bytes=restart_bytes;
  @(posedge clk);#1;@(negedge clk);req_valid=0;
  if(!observed_init_request||init_req_tag!==batch_tag+1||meta_req_valid||sp_wr_valid)$fatal(1,"dataset recovery did not use fresh outer generation");
  `RX_INPUT_HASH_ASSERTION(dut.lifecycle.input_q,dut.lifecycle.input_bytes_q,changed_seed);
  clocks=0;
  while(!dut.lifecycle.ih_rsp_valid)begin
   dataset_stale_drive();
   @(posedge clk);
   if(!dataset_fetch_rsp_ready||!dataset_cache_rsp_ready||dataset_item_req_valid||dataset_item_commit_valid||dataset_item_stage_valid||sp_wr_valid||rsp_valid)
    $fatal(1,"old dataset reply crossed changed generation seed prefix");
   #1;clocks=clocks+1;if(clocks>1000)$fatal(1,"changed seed prefix deadlock");@(negedge clk);
  end
  if(dut.lifecycle.ih_rsp_tag!==batch_tag+1||dut.lifecycle.ih_rsp_error||dut.lifecycle.ih_rsp_seed!==changed_seed||changed_seed===expected_input_seed)
   $fatal(1,"changed-input recovery seed mismatch");
  @(posedge clk);if(!dut.lifecycle.ih_rsp_ready)$fatal(1,"fresh recovery seed not accepted");
  #1;if(dut.lifecycle.state_q!=9||dut.lifecycle.seed_q!==changed_seed||!dut.lifecycle.fill_start_valid||sp_wr_valid)$fatal(1,"recovery fill preceded native seed");
  @(negedge clk);cancel=1;#1;
  if(sp_wr_valid||dataset_fetch_valid||dataset_cache_req_valid||dataset_item_rsp_valid)$fatal(1,"recovery prefix cancel suppression");
  @(posedge clk);#1;@(negedge clk);cancel=0;dataset_clear_provider();
  $sformat(path,"%0s/provider-host-time.json",output_directory);`RX_STATS(path);
 end endtask
 task dataset_cancel_and_restart;
  integer n;
 begin
  if(!HARDWARE_DATASET||!ds_pending||dataset_items_seen!=1)$fatal(1,"dataset cancel target coverage");
  dataset_replay_fetch_tag=dataset_f_tag;dataset_replay_cache_tag=dataset_c_tag;
  for(n=0;n<131072;n=n+1)cancel_ram[n]=ram[n];
  @(negedge clk);cancel=1;#1;
  if(req_ready||rsp_valid||sp_rd_valid||sp_wr_valid||ds_req_valid||dataset_cache_req_valid||dataset_fetch_valid||dataset_item_commit_valid||dataset_item_stage_valid)
   $fatal(1,"dataset cancellation transfer suppression");
  @(posedge clk);#1;@(negedge clk);cancel=0;dataset_clear_provider();
  repeat(3)begin
   dataset_stale_drive();@(posedge clk);#1;
   if(!req_ready||!dataset_fetch_rsp_ready||!dataset_cache_rsp_ready||dataset_item_req_valid||dataset_item_commit_valid||dataset_item_stage_valid||rsp_valid||sp_wr_valid)
    $fatal(1,"canceled dataset reply survived");
   @(negedge clk);
  end
  for(n=0;n<131072;n=n+1)if(ram[n]!==cancel_ram[n])$fatal(1,"dataset cancellation rolled back accepted SRAM writes");
  dataset_restart_prefix();
  $display("PASS dataset_capacity_lifecycle_cancel target=%0d changed_generation=1 changed_input=1 stale_replies_drained=1 accepted_writes_persist=1 prefix_only=1",DATASET_CANCEL);
  $finish;
 end endtask
 task dataset_error_and_restart;
  integer n;reg [4095:0] response;
 begin
  if(!HARDWARE_DATASET||!rsp_valid||!rsp_error||rsp_tag!==16'h4000||error_tag!==16'h4000||error_code!==3||rsp_digest!==0||
     req_ready||dataset_matching_faults!=1||dataset_item_stage_count!=0||global_iteration!=0||final_reads)
   $fatal(1,"matching prepared-service error was not held before wrong XOR/hash work");
  response=now_response;dataset_replay_fetch_tag=dataset_f_tag;dataset_replay_cache_tag=dataset_c_tag;
  for(n=0;n<131072;n=n+1)cancel_ram[n]=ram[n];
  repeat(3)begin
   @(negedge clk);rsp_ready=0;@(posedge clk);#1;
   if(!rsp_valid||!error_valid||now_response!==response||sp_rd_valid||sp_wr_valid||ds_req_valid||dataset_fetch_valid||dataset_cache_req_valid||dataset_item_commit_valid||dataset_item_stage_valid)
    $fatal(1,"held prepared-service hash error changed");
  end
  @(negedge clk);rsp_ready=1;@(posedge clk);#1;@(negedge clk);rsp_ready=0;dataset_clear_provider();
  repeat(3)begin
   dataset_stale_drive();@(posedge clk);#1;
   if(!req_ready||!dataset_cache_rsp_ready||!dataset_fetch_rsp_ready||dataset_item_req_valid||dataset_item_commit_valid||dataset_item_stage_valid||sp_wr_valid||rsp_valid)
    $fatal(1,"old failed dataset reply survived");
   @(negedge clk);
  end
  for(n=0;n<131072;n=n+1)if(ram[n]!==cancel_ram[n])$fatal(1,"failed dataset context rolled back accepted SRAM writes");
  dataset_restart_prefix();
  $display("PASS dataset_capacity_lifecycle_error service=%0d matching_faults=1 held_error=1 no_wrong_xor=1 changed_generation=1 changed_input=1 prefix_only=1",DATASET_ERROR);
  $finish;
 end endtask
 task dataset_write_ledger;
  integer fd,n,sum,status;
 begin
  if(dataset_requests_seen!=TOTAL_ITERATIONS||dataset_responses_seen!=TOTAL_ITERATIONS||ds_pending)$fatal(1,"full dataset demand/response accounting");
  if(HARDWARE_DATASET)begin
   if(dataset_live_calls||dataset_items_seen!=TOTAL_ITERATIONS||dataset_item_returns_seen!=TOTAL_ITERATIONS||dataset_stage_pulses!=8*TOTAL_ITERATIONS||
      dataset_items_requested!==dataset_items_seen||dataset_items_completed!==dataset_items_seen||dataset_ds_requests!==dataset_requests_seen||dataset_ds_responses!==dataset_responses_seen||
      dataset_f_pending||dataset_c_pending||dataset_wait_active||dataset_response_wait_sum!==dataset_available_clocks)
    $fatal(1,"dataset prefetch/child/stage/lifetime/availability ledgers do not close");
   if(dataset_items_reserved!==TOTAL_ITERATIONS||dataset_items_remaining!==DATASET_SESSION_LIMIT-TOTAL_ITERATIONS)$fatal(1,"dataset whole-batch reservation mismatch");
   sum=0;for(n=0;n<3;n=n+1)sum=sum+dataset_service_detail[n];
   if(sum!=dataset_service_clocks||dataset_service_clocks!=ledger[4])$fatal(1,"dataset bridge ledger not nested exactly within execution");
   sum=0;for(n=0;n<3;n=n+1)sum=sum+dataset_session_detail[n];
   if(sum!=dataset_service_clocks)$fatal(1,"session phase ledger is not nested in execution");
   if(dataset_item_sessions_used!==TOTAL_ITERATIONS)$fatal(1,"private accepted item-session counter mismatch");
   sum=0;for(n=0;n<9;n=n+1)sum=sum+dataset_item_detail[n];
   if(sum!=dataset_item_clocks||dataset_item_clocks>dataset_service_clocks)$fatal(1,"nonclosing nested dataset item phase ledger");
   if(dataset_available_clocks!==dataset_core_clocks+dataset_launch_clocks||dataset_launch_clocks!==TOTAL_ITERATIONS||
      dataset_core_clocks!==dataset_executor_clocks+(DATASET_MUL_RADIX4?74:42)*TOTAL_ITERATIONS+dataset_cache_service_extra||
      dataset_executor_clocks!==dataset_ideal_executor*TOTAL_ITERATIONS+dataset_program_service_extra)
    $fatal(1,"nonclosing disjoint dataset child program/cache service costs");
  end else if(dataset_live_calls!=TOTAL_ITERATIONS||dataset_items_seen||dataset_item_returns_seen||dataset_stage_pulses||dataset_cache_requests||dataset_fetch_requests)
   $fatal(1,"software baseline/hardware dataset boundary mismatch");
  status=$fscanf(dataset_gold_fd,"%h %h\n",dataset_gold_address,dataset_expected_data);
  if(status!=-1)$fatal(1,"retained native dataset gold contains extra or malformed demand rows");
  $fclose(dataset_gold_fd);$fclose(dataset_cache_fd);$fclose(dataset_rows_fd);
  $sformat(dataset_path,"%0s/dataset-ledger.json",output_directory);fd=$fopen(dataset_path,"w");if(!fd)$fatal(1,"dataset ledger open");
  $fdisplay(fd,"{\"schema\":\"openrx.dataset-capacity.nested-ledger.v1\",\"hardware_dataset\":%0d,\"outer_cycles\":%0d,\"dataset_costs_are_nested_not_added_to_outer_total\":true,",HARDWARE_DATASET,cycle);
  $fdisplay(fd,"\"demands\":%0d,\"responses\":%0d,\"live_native_dataset_calls\":%0d,\"items\":%0d,\"item_returns\":%0d,\"stages\":%0d,\"retirements\":%0d,",dataset_requests_seen,dataset_responses_seen,dataset_live_calls,dataset_items_seen,dataset_item_returns_seen,dataset_stage_pulses,dataset_commit_pulses);
  $fdisplay(fd,"\"item_availability_clocks\":%0d,\"executor_clocks\":%0d,\"ideal_executor_clocks_each\":%0d,\"program_service_extra_clocks\":%0d,\"cache_service_extra_clocks\":%0d,",dataset_available_clocks,dataset_executor_clocks,dataset_ideal_executor,dataset_program_service_extra,dataset_cache_service_extra);
  $fdisplay(fd,"\"session_namespace_bits\":%0d,\"external_tag_bits\":64,\"sessions_used\":%0d,\"core_item_availability_clocks\":%0d,\"session_launch_extra_clocks\":%0d,\"session_phase_cycles\":[%0d,%0d,%0d],",DATASET_SESSION_BITS,dataset_item_sessions_used,dataset_core_clocks,dataset_launch_clocks,dataset_session_detail[0],dataset_session_detail[1],dataset_session_detail[2]);
  $fdisplay(fd,"\"cache_requests\":%0d,\"cache_responses\":%0d,\"instruction_requests\":%0d,\"instruction_responses\":%0d,\"stale_packets_drained\":%0d,\"cache_request_stalls\":%0d,\"instruction_request_stalls\":%0d,",dataset_cache_requests,dataset_cache_responses,dataset_fetch_requests,dataset_fetch_responses,dataset_stale_packets,dataset_cache_request_stalls,dataset_fetch_request_stalls);
  $fdisplay(fd,"\"service_phase_cycles\":[%0d,%0d,%0d],\"item_phase_cycles\":[%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d],\"captured_asset_epoch\":%0d,\"all_descriptors_captured\":true,\"full_native_digest_registers_scratchpad\":true,\"physical_cache_service\":null}",dataset_service_detail[0],dataset_service_detail[1],dataset_service_detail[2],dataset_item_detail[0],dataset_item_detail[1],dataset_item_detail[2],dataset_item_detail[3],dataset_item_detail[4],dataset_item_detail[5],dataset_item_detail[6],dataset_item_detail[7],dataset_item_detail[8],dataset_asset_epoch);
  $fclose(fd);
  $display("PASS dataset_capacity_hash_lifecycle hardware_dataset=%0d programs=%0d iterations=%0d ds_requests=%0d items=%0d stages=%0d live_dataset_calls=%0d nested_clocks=1 full_native_digest_registers_scratchpad=1",HARDWARE_DATASET,PROGRAMS,ITERATIONS,dataset_requests_seen,dataset_items_seen,dataset_stage_pulses,dataset_live_calls);
 end endtask
 // New dataset capacity is tested through real public batch transfers in
 // tb_dataset_service_capacity; no hierarchical force/deposit is used in this TB.

 wire prep_rcp_fire;
 generate if(PREPARED_RCP)begin: observed_prepared
  assign prep_rcp_fire=dut.lifecycle.chain.iteration_chain.iteration.cache.prepared.reciprocal.req_valid&&dut.lifecycle.chain.iteration_chain.iteration.cache.prepared.reciprocal.req_ready;
 end else begin: observed_baseline
  assign prep_rcp_fire=0;
 end endgenerate
 integer preparation_reciprocals=0,runtime_reciprocals=0,final_native_completions=0;
 integer stall_sp_requests=0,stall_sp_writes=0,stall_dataset_requests=0,stall_program_loads=0;
 integer waiting_sp_replies=0,waiting_dataset_replies=0,waiting_program_replies=0;
 task cancel_and_restart;begin
  if(CANCEL_PHASE==8&&(!HARDWARE_INPUT_HASH||input_stage_clocks<3||input_hash_completions||init_writes))$fatal(1,"input hash cancellation coverage");
  if(CANCEL_PHASE==7&&(!HARDWARE_PROGRAM||generation_image_beats!=3||dut.lifecycle.pg_state_q!=2))$fatal(1,"hardware image cancellation coverage");
  for(i=0;i<131072;i=i+1)cancel_ram[i]=ram[i];
  @(negedge clk);cancel=1;#1;
  if(sp_wr_valid||sp_rd_valid||ds_req_valid||prog_valid||meta_req_valid||program_done_valid||rsp_valid)$fatal(1,"cancel suppression");
  @(posedge clk);#1;@(negedge clk);cancel=0;init_wr_valid=0;init_rsp_valid=0;
  meta_rsp_valid=1;meta_rsp_tag=batch_tag;meta_rsp_program=0;meta_rsp_entropy=~native_entropy;
  sp_rsp_valid=1;sp_rsp_tag={batch_tag,2'd1,17'b0,inner_tag};sp_rsp_data=~sp_data;
  prog_rsp_valid=1;prog_rsp_tag={batch_tag,current_load};prog_rsp_instruction=~rom_data;
  ds_rsp_valid=1;ds_rsp_tag={batch_tag,inner_tag};ds_rsp_data=~ds_data;
  repeat(3)begin @(posedge clk);#1;
   if(!req_ready||!meta_rsp_ready||!sp_rsp_ready||!prog_rsp_ready||!ds_rsp_ready||sp_wr_valid||iteration_commit_valid||commit_valid||rsp_valid)$fatal(1,"canceled late reply suppression");
   if(HARDWARE_PROGRAM&&(dut.lifecycle.pg_state_q!=0||dut.lifecycle.pg_fetch_pending_q||dut.lifecycle.pg_out_valid||dut.lifecycle.chain_meta_rsp_valid||dut.lifecycle.chain_prog_rsp_valid))$fatal(1,"cancel retained partial generated-image ownership");
   @(negedge clk);
  end
  meta_rsp_valid=0;sp_rsp_valid=0;prog_rsp_valid=0;ds_rsp_valid=0;
  for(i=0;i<131072;i=i+1)if(ram[i]!==cancel_ram[i])$fatal(1,"cancel rolled back accepted writes");
  restart_input=input_value^640'd1;restart_bytes=input_bytes?input_bytes:1;
  req_valid=1;req_tag=16'h9001;
  req_input=HARDWARE_INPUT_HASH||HARDWARE_FILL&&(CANCEL_PHASE==1||CANCEL_PHASE==7)?restart_input:input_value;
  req_input_bytes=HARDWARE_INPUT_HASH||HARDWARE_FILL&&(CANCEL_PHASE==1||CANCEL_PHASE==7)?restart_bytes:input_bytes;
  @(posedge clk);#1;@(negedge clk);req_valid=0;
  if(!observed_init_request||init_req_tag!==batch_tag+1||meta_req_valid||sp_wr_valid)$fatal(1,"fresh generation after cancel");
  if(HARDWARE_INPUT_HASH)begin
   `RX_INPUT_HASH_ASSERTION(dut.lifecycle.input_q,dut.lifecycle.input_bytes_q,restart_seed);
   while(!dut.lifecycle.ih_rsp_valid)begin
    init_rsp_valid=1;init_rsp_tag=batch_tag;init_rsp_seed=0;init_rsp_error=1;
    init_wr_valid=1;init_wr_tag=batch_tag+1;init_wr_addr=0;init_wr_data=0;init_wr_strb=0;
    @(posedge clk);
    if(init_req_valid||!init_rsp_ready||!init_wr_ready||sp_wr_valid||sp_rd_valid||prog_valid||meta_req_valid||rsp_valid)$fatal(1,"successor input hash/provider ownership");
    #1;restart_cycles=restart_cycles+1;if(restart_cycles>1000)$fatal(1,"successor input hash deadlock");@(negedge clk);
   end
   if(dut.lifecycle.ih_rsp_tag!==batch_tag+1||dut.lifecycle.ih_rsp_error||dut.lifecycle.ih_rsp_seed!==restart_seed||restart_seed===expected_input_seed)$fatal(1,"changed-input successor seed mismatch");
   @(posedge clk);if(!dut.lifecycle.ih_rsp_ready)$fatal(1,"successor input seed not accepted");
   #1;if(dut.lifecycle.seed_q!==restart_seed||dut.lifecycle.state_q!=9||!dut.lifecycle.fill_start_valid||!dut.lifecycle.fill_req_ready||sp_wr_valid)$fatal(1,"successor fill began before completed native seed");
   @(negedge clk);cancel=1;#1;if(sp_wr_valid||dut.lifecycle.ih_rsp_valid)$fatal(1,"successor prefix cancel suppression");
   @(posedge clk);#1;@(negedge clk);cancel=0;init_rsp_valid=0;init_wr_valid=0;
   $display("DETAIL lifecycle_hardware_input_cancel_prefix changed_input=1 native_seed=1 removed_provider_drained=1 seed_before_fill=1 prefix_only=1");
  end
  if(!HARDWARE_INPUT_HASH&&HARDWARE_FILL&&(CANCEL_PHASE==1||CANCEL_PHASE==7))begin
   if(init_req_input!==restart_input||init_req_input_bytes!==restart_bytes)$fatal(1,"successor did not capture fresh input");
   // The live provider computes only the actual input hash. This separate
   // software fill is an assertion oracle for the cancelled test's successor.
   `RX_INPUT_HASH(init_req_input,init_req_input_bytes,restart_seed);
   $sformat(path,"%0s/restart-assertion-only-initial.hex",output_directory);
   `RX_INITIAL(init_req_input,init_req_input_bytes,path,restart_expected_seed);$readmemh(path,initial_ram);
   if(restart_seed===seed)$fatal(1,"successor input hash was not fresh");
   meta_req_ready=0;sp_wr_ready=0;init_req_ready=1;
   @(posedge clk);#1;@(negedge clk);init_req_ready=0;
   init_rsp_valid=1;init_rsp_tag=batch_tag;init_rsp_seed=seed;init_rsp_error=0;
   init_wr_valid=1;init_wr_tag=batch_tag;init_wr_addr=0;init_wr_data=0;init_wr_strb=0;
   @(posedge clk);
   if(!init_rsp_ready||!init_wr_ready||sp_wr_valid||meta_req_valid)$fatal(1,"stale initialization crossed cancelled generation");
   #1;@(negedge clk);init_wr_valid=0;init_rsp_tag=batch_tag+1;init_rsp_seed=restart_seed;
   @(posedge clk);if(!init_rsp_ready)$fatal(1,"fresh input hash not accepted");
   #1;@(negedge clk);init_rsp_valid=0;
   while(!observed_meta_req_valid)begin
    // Several held cycles recur on each write; accepted SRAM bytes persist.
    sp_wr_ready=restart_cycles%7>=3;
    @(posedge clk);
    if(sp_rd_valid||prog_valid||ds_req_valid||rsp_valid||error_valid)$fatal(1,"successor escaped initial hardware fill");
    if(restart_held&&(!sp_wr_valid||now_write!==restart_saved_write))$fatal(1,"successor held initial write changed");
    restart_held=sp_wr_valid&&!sp_wr_ready;restart_saved_write=now_write;
    if(restart_held)restart_saw_hold=1;
    if(sp_wr_valid&&sp_wr_ready)begin
     if(restart_writes>=131072||scratchpad_owner!==0||sp_wr_tag[50:35]!==batch_tag+1||sp_wr_tag[34:33]!==0||
        sp_wr_addr!==restart_writes*16||sp_wr_strb!==16'hffff||sp_wr_data!==initial_ram[restart_writes])$fatal(1,"successor native initial image mismatch");
     ram[restart_writes]=sp_wr_data;restart_writes=restart_writes+1;
    end
    if(restart_cycles>2000000)$fatal(1,"successor fill deadlock");
    #1;restart_cycles=restart_cycles+1;@(negedge clk);
   end
   if(restart_writes!=131072||!restart_saw_hold||meta_req_tag!==batch_tag+1||meta_req_program!==0||
      meta_req_seed!==restart_expected_seed)$fatal(1,"successor full fill/postfill seed mismatch");
   $display("DETAIL lifecycle_hardware_fill_cancel_fresh_seed changed_input=1 successor_full_scratchpad_bytes=2097152 held_writes=1 stale_initialization_drained=1 postfill_seed=1");
   if(CANCEL_PHASE==7)begin
    // The new input's actual post-fill seed drives a fresh complete image.
    // These native bytes are assertion-only and never reach the DUT.
    $sformat(path,"%0s/restart-assertion-only-program.mem",output_directory);
    `RX_GENERATE_ASSERTION(meta_req_seed,path,native_entropy);$readmemh(path,rom);
    while(dut.lifecycle.pg_state_q!=4)begin
     @(posedge clk);
     if(meta_req_valid||prog_valid||sp_wr_valid||sp_rd_valid||ds_req_valid||rsp_valid||error_valid)$fatal(1,"successor generated-image ownership escaped");
     if(dut.lifecycle.pg_state_q==1&&dut.lifecycle.pg_seed_q!==restart_expected_seed)$fatal(1,"successor generator did not capture actual new seed");
     if(dut.lifecycle.pg_out_valid&&dut.lifecycle.pg_out_ready)begin
      if(restart_image_beats>=200||dut.lifecycle.pg_out_tag!==batch_tag+1||dut.lifecycle.pg_out_addr!==restart_image_beats*16)$fatal(1,"successor generated-image tag/order");
      if(restart_image_beats<8)expected_data=native_entropy[128*restart_image_beats+:128];
      else expected_data={rom[2*(restart_image_beats-8)+1],rom[2*(restart_image_beats-8)]};
      if(dut.lifecycle.pg_out_data!==expected_data)$fatal(1,"successor native program image mismatch");
      restart_image_beats=restart_image_beats+1;
     end
     if(dut.lifecycle.chain_meta_rsp_valid&&dut.lifecycle.chain_meta_rsp_ready)begin
      if(restart_image_beats!=200||dut.lifecycle.chain_meta_rsp_tag!==batch_tag+1||dut.lifecycle.chain_meta_rsp_program!==0||dut.lifecycle.chain_meta_rsp_entropy!==native_entropy)$fatal(1,"successor generated metadata mismatch");
      restart_metadata_accepted=restart_metadata_accepted+1;
     end
     #1;restart_cycles=restart_cycles+1;if(restart_cycles>2100000)$fatal(1,"successor generation deadlock");@(negedge clk);
    end
    if(restart_image_beats!=200||restart_metadata_accepted!=1)$fatal(1,"successor reused partial generated image");
    $display("DETAIL lifecycle_hardware_program_cancel_fresh_image changed_input=1 partial_image_invalidated=1 successor_native_image_bytes=3200 fresh_metadata=1");
   end
  end
  $display("PASS lifecycle_cancel phase=%0d completed_iterations=%0d accepted_writes_persist=1 stale_generation_dropped=1 fresh_initialization_required=1",CANCEL_PHASE,global_iteration);
  $finish;
 end endtask
 task matching_error_and_restart;begin
  if(!ERROR_PORT||!rsp_valid||!rsp_error||rsp_tag!==16'h4000||error_tag!==16'h4000||error_code==0||rsp_digest!==0||req_ready)
   $fatal(1,"matching provider error was not returned");
  if(matching_fault_accepted!=1||error_code!==((ERROR_PORT==1||ERROR_PORT==7||ERROR_PORT==8)?2'd1:2'd3))
   $fatal(1,"selected matching fault was not accepted or returned the wrong error code");
  if((ERROR_PORT==8||ERROR_PORT==1&&!HARDWARE_FILL)&&init_writes!=3)$fatal(1,"initializer fault coverage");
  if(ERROR_PORT==1&&HARDWARE_FILL&&init_writes!=0)$fatal(1,"input hash fault emitted hardware fill");
  if(ERROR_PORT==7&&(init_writes||loaded_words||admissions))$fatal(1,"invalid input emitted work");
  if(ERROR_PORT==5&&(!dataset_taken||global_iteration!=0||final_reads))$fatal(1,"dataset fault stage coverage");
  if(ERROR_PORT==6&&(programs_finished!=PROGRAMS||global_iteration!=TOTAL_ITERATIONS||final_reads==0))$fatal(1,"finalizer fault stage coverage");
  for(i=0;i<131072;i=i+1)cancel_ram[i]=ram[i];
  saved_done=now_response;
  repeat(3)begin
   @(negedge clk);rsp_ready=0;
   @(posedge clk);#1;
   if(!rsp_valid||!error_valid||now_response!==saved_done||init_req_valid||sp_wr_valid||sp_rd_valid||ds_req_valid||prog_valid||meta_req_valid||program_done_valid||iteration_commit_valid||commit_valid)
    $fatal(1,"held matching error changed or issued work");
  end
  @(negedge clk);rsp_ready=1;@(posedge clk);#1;@(negedge clk);rsp_ready=0;
  if(!req_ready||rsp_valid||error_valid)$fatal(1,"matching error did not retire");
  // A retired failed generation cannot mutate SRAM or seed its successor.
  init_wr_valid=1;init_wr_tag=batch_tag;init_wr_addr=0;init_wr_data=0;init_wr_strb=16'hffff;
  init_rsp_valid=1;init_rsp_tag=batch_tag;init_rsp_seed=0;init_rsp_error=1;
  meta_rsp_valid=1;meta_rsp_tag=batch_tag;meta_rsp_program=0;meta_rsp_error=1;
  sp_rsp_valid=1;sp_rsp_tag=sp_tag;sp_rsp_error=1;
  prog_rsp_valid=1;prog_rsp_tag=rom_tag;prog_rsp_error=1;
  ds_rsp_valid=1;ds_rsp_tag=ds_tag;ds_rsp_error=1;
  repeat(3)begin @(posedge clk);#1;
   if(!req_ready||!init_wr_ready||!init_rsp_ready||!meta_rsp_ready||!sp_rsp_ready||!prog_rsp_ready||!ds_rsp_ready||init_req_valid||sp_wr_valid||sp_rd_valid||rsp_valid||error_valid||program_done_valid||commit_valid||iteration_commit_valid)
    $fatal(1,"late failed generation was not drained");
   @(negedge clk);
  end
  init_wr_valid=0;init_rsp_valid=0;meta_rsp_valid=0;sp_rsp_valid=0;prog_rsp_valid=0;ds_rsp_valid=0;
  for(i=0;i<131072;i=i+1)if(ram[i]!==cancel_ram[i])$fatal(1,"matching error rolled back accepted writes");
  req_valid=1;req_tag=16'h9001;req_input=input_value;req_input_bytes=input_bytes;
  @(posedge clk);#1;@(negedge clk);req_valid=0;
  if(!observed_init_request||init_req_tag!==batch_tag+1||meta_req_valid||sp_wr_valid)$fatal(1,"fresh generation after matching error");
  $display("PASS lifecycle_matching_error port=%0d selected_fault_accepted=1 expected_code_matched=1 held_error=1 late_replies_drained=1 accepted_writes_persist=1 fresh_initialization_required=1",ERROR_PORT);
  $finish;
 end endtask
 // These are lifecycle prefixes, ending at the validated hardware-fill request.
 // No SRAM beat is accepted and no complete hash is claimed for these cases.
 task input_boundary_case(input [639:0] value,input integer length,input integer kill,input integer changed);
  reg [15:0] boundary_generation,boundary_caller;
  reg [511:0] boundary_seed;
  integer boundary_clocks,boundary_requests;
  begin: boundary_case
   boundary_generation=dut.lifecycle.generation_counter_q+16'd1;boundary_caller=16'h5000+boundary_generation;
   boundary_clocks=0;boundary_requests=0;
   req_valid=1;req_tag=boundary_caller;req_input=value;req_input_bytes=length;
   init_req_ready=1;sp_wr_ready=1;rsp_ready=0;
   #1;if(!req_ready)$fatal(1,"input boundary request not ready");
   @(posedge clk);if(sp_wr_valid||sp_rd_valid)$fatal(1,"input boundary admission emitted SRAM traffic");
   #1;@(negedge clk);req_valid=0;req_input=~value;req_input_bytes=127;req_tag=~boundary_caller;
   if(length>80)begin
    if(!rsp_valid||!rsp_error||rsp_tag!==boundary_caller||error_code!==1||rsp_digest!==0||dut.lifecycle.ih_req_valid||sp_wr_valid)$fatal(1,"invalid input boundary was not rejected before work");
    saved_done=now_response;
    repeat(3)begin
     @(posedge clk);#1;
     if(!rsp_valid||now_response!==saved_done||dut.lifecycle.ih_req_valid||dut.lifecycle.ih_rsp_valid||init_req_valid||sp_wr_valid||sp_rd_valid||meta_req_valid||prog_valid||ds_req_valid)$fatal(1,"held invalid input boundary emitted work");
     @(negedge clk);
    end
    rsp_ready=1;@(posedge clk);#1;@(negedge clk);rsp_ready=0;
    if(!req_ready)$fatal(1,"invalid input boundary did not retire");
    boundary_invalid=boundary_invalid+1;disable boundary_case;
   end
   // Only the actual captured input reaches this assertion-only oracle.
   if(dut.lifecycle.input_q!==value||dut.lifecycle.input_bytes_q!==length)$fatal(1,"input boundary capture changed");
   `RX_INPUT_HASH_ASSERTION(dut.lifecycle.input_q,dut.lifecycle.input_bytes_q,boundary_seed);
   while(!dut.lifecycle.ih_rsp_valid)begin
    // Both stale and matching removed-provider errors/writes must drain.
    init_rsp_valid=1;init_rsp_tag=boundary_clocks[0]?boundary_generation:boundary_generation-16'd1;
    init_rsp_seed=~boundary_seed;init_rsp_error=1;
    init_wr_valid=1;init_wr_tag=init_rsp_tag;init_wr_addr=0;init_wr_data=0;init_wr_strb=0;
    @(posedge clk);
    if(init_req_valid||!init_rsp_ready||!init_wr_ready||sp_wr_valid||sp_rd_valid||dut.lifecycle.fill_wr_valid||meta_req_valid||prog_valid||ds_req_valid||rsp_valid)$fatal(1,"input boundary ownership before seed completion");
    if(dut.lifecycle.ih_req_valid&&dut.lifecycle.ih_req_ready)boundary_requests=boundary_requests+1;
    #1;boundary_clocks=boundary_clocks+1;@(negedge clk);
    if(kill&&boundary_clocks==3)begin
     if(boundary_requests!=1||dut.lifecycle.ih_rsp_valid)$fatal(1,"input boundary cancel did not hit active hash");
     cancel=1;#1;if(sp_wr_valid||dut.lifecycle.ih_req_valid||dut.lifecycle.ih_rsp_valid)$fatal(1,"input boundary cancel suppression");
     @(posedge clk);#1;@(negedge clk);cancel=0;init_rsp_valid=0;init_wr_valid=0;#1;
     if(!req_ready||dut.lifecycle.ih_rsp_valid||dut.lifecycle.fill_wr_valid)$fatal(1,"input boundary cancel retained ownership");
     boundary_cancel_seed=boundary_seed;boundary_canceled=boundary_canceled+1;disable boundary_case;
    end
    if(boundary_clocks>1000)$fatal(1,"input boundary hash deadlock");
   end
   if(boundary_requests!=1||dut.lifecycle.ih_rsp_tag!==boundary_generation||dut.lifecycle.ih_rsp_error||dut.lifecycle.ih_rsp_seed!==boundary_seed)$fatal(1,"input boundary native seed mismatch");
   if(changed&&boundary_seed===boundary_cancel_seed)$fatal(1,"changed boundary input reused old seed");
   @(posedge clk);if(!dut.lifecycle.ih_rsp_ready||sp_wr_valid)$fatal(1,"input boundary seed handshake");
   #1;if(dut.lifecycle.state_q!=9||dut.lifecycle.seed_q!==boundary_seed||!dut.lifecycle.fill_start_valid||!dut.lifecycle.fill_req_ready||sp_wr_valid)$fatal(1,"input boundary fill did not receive completed seed");
   // Cancel before the filler can accept its request: prefix checks stay cheap.
   @(negedge clk);cancel=1;#1;if(sp_wr_valid||dut.lifecycle.ih_rsp_valid)$fatal(1,"input boundary prefix cancel suppression");
   @(posedge clk);#1;@(negedge clk);cancel=0;init_rsp_valid=0;init_wr_valid=0;#1;
   if(!req_ready||dut.lifecycle.ih_rsp_valid||dut.lifecycle.fill_wr_valid)$fatal(1,"input boundary prefix retained ownership");
   boundary_valid=boundary_valid+1;
  end
 endtask
 task check_input_boundaries;begin
  if(!HARDWARE_INPUT_HASH||!HARDWARE_FILL)$fatal(1,"input boundaries require hardware input hash/fill");
  input_boundary_case({640{1'b1}},0,0,0);
  for(i=0;i<80;i=i+1)boundary_max_input[8*i+:8]=i*37+11;
  input_boundary_case(boundary_max_input,80,0,0);
  input_boundary_case(boundary_max_input,80,1,0);
  input_boundary_case(boundary_max_input^640'd1,80,0,1);
  input_boundary_case(boundary_max_input,81,0,0);
  input_boundary_case(boundary_max_input,127,0,0);
  if(boundary_valid!=3||boundary_canceled!=1||boundary_invalid!=2||dut.lifecycle.generation_counter_q!=6)$fatal(1,"input boundary coverage");
  $sformat(path,"%0s/provider-host-time.json",output_directory);`RX_STATS(path);
  $sformat(path,"%0s/input-boundary-checks.json",output_directory);ledger_file=$fopen(path,"w");if(!ledger_file)$fatal(1,"input boundary report open");
  $fdisplay(ledger_file,"{\"prefix_only\":true,\"valid_seed_prefixes\":3,\"canceled_input_hashes\":1,\"invalid_lengths\":[81,127],\"valid_lengths\":[0,80],\"changed_input_successor\":true,\"native_seed_equal\":true,\"removed_provider_drained\":true,\"accepted_sram_writes\":0}");$fclose(ledger_file);
  $display("PASS lifecycle_input_hash_boundaries valid_prefixes=3 cancel=1 invalid_lengths=81,127 empty_and_max80=1 changed_input_successor=1 native_seed=1 accepted_sram_writes=0 prefix_only=1");
  $finish;
 end endtask
 initial begin #2000000000;$fatal(1,"sequence simulation deadlock");end
 initial begin
  if(!$value$plusargs("directory=%s",directory)||!$value$plusargs("output=%s",output_directory)||
     !$value$plusargs("input=%h",input_value)||!$value$plusargs("input_bytes=%d",input_bytes))$fatal(1,"profile arguments missing");
  for(i=0;i<11;i=i+1)ledger[i]=0;for(i=0;i<12;i=i+1)iteration_detail[i]=0;
  for(i=0;i<6;i=i+1)final_detail[i]=0;for(i=0;i<18;i=i+1)exec_detail[i]=0;
  for(i=0;i<3;i=i+1)begin fill_detail[i]=0;program_gen_detail[i]=0;input_hash_detail[i]=0;end
  $sformat(path,"%0s/trace.csv",output_directory);trace_file=$fopen(path,"w");if(!trace_file)$fatal(1,"trace open");
  $fdisplay(trace_file,"cycle,outer_phase,iteration_phase,execute_phase,commit,pc,sp_read,sp_addr,sp_write,write_addr,write_strb,dataset,dataset_addr");
  $sformat(path,"%0s/final-a.hex",directory);$readmemh(path,gold_final_a);
  $sformat(path,"%0s/final-rf.hex",directory);$readmemh(path,gold_final_rf);
  $sformat(path,"%0s/final-digest32.hex",directory);$readmemh(path,gold_digest);
  $sformat(path,"%0s/iterations.mem",directory);$readmemh(path,gold);
  $sformat(path,"%0s/metadata.mem",directory);$readmemh(path,gold_meta);
  $sformat(path,"%0s/events.mem",directory);$readmemh(path,events);
  $sformat(path,"%0s/initial.hex",directory);$readmemh(path,gold_ram);
  expected_seed={gold_ram[131071],gold_ram[131070],gold_ram[131069],gold_ram[131068]};
  batch_tag=16'd1;inner_tag=batch_tag;
  rst=1;@(posedge clk);#1;@(negedge clk);rst=0;
  if(INPUT_HASH_BOUNDARY_TEST)check_input_boundaries();
  if(CAPACITY_TEST)$fatal(1,"use public dataset-service budget mode instead");
  dataset_assets_load();
  req_valid=1;req_tag=16'h4000;req_input=input_value;req_input_bytes=ERROR_PORT==7?7'd81:input_bytes;#1;
  if(!req_ready)$fatal(1,"hash not ready");@(posedge clk);
  if(ERROR_PORT==7&&req_valid&&req_ready&&req_input_bytes==81)matching_fault_accepted=1;
  #1;@(negedge clk);req_valid=0;
  while(!accepted_done)begin
   // Only actual provider/DUT state drives these inputs; gold is assertion-only.
   req_tag=~req_tag;req_input=~req_input;req_input_bytes=~req_input_bytes;
   dataset_provider_drive();
   init_req_ready=!initializing;
   if(!HARDWARE_INPUT_HASH&&HARDWARE_FILL&&init_req_valid&&init_req_ready)begin
    if(init_input_hash_calls!=0)$fatal(1,"hardware input hash callback repeated");
    if(init_req_input!==input_value||init_req_input_bytes!==input_bytes)$fatal(1,"captured hash input changed");
    // Offer the live seed before the request-accepting edge. It must be held
    // until the following INIT_STREAM edge, without a duplicate native call.
    init_generation=init_req_tag;`RX_INPUT_HASH(init_req_input,init_req_input_bytes,seed);
    init_input_hash_calls=init_input_hash_calls+1;init_request_seed_pending=1;
   end
   init_wr_valid=!HARDWARE_FILL&&initializing&&initial_index<131072;init_wr_tag=init_generation;
   init_wr_addr=initial_index*16;init_wr_data=initial_ram[initial_index<131072?initial_index:0];init_wr_strb=16'hffff;
   if(ERROR_PORT==8&&!HARDWARE_FILL&&initializing&&initial_index>=3)init_wr_strb=16'h00ff;
   if(ERROR_PORT==8&&HARDWARE_FILL&&init_writes>=3)begin init_wr_valid=1;init_wr_tag=batch_tag;init_wr_strb=16'h00ff;end
   // Stale writes and stale error responses must drain without affecting fill.
   if(!HARDWARE_INPUT_HASH&&HARDWARE_FILL&&STALL&&phase==1&&init_input_hash_calls&& !init_request_seed_pending&&init_write_drops==0)begin init_wr_valid=1;init_wr_tag=batch_tag-1;init_wr_strb=0;end
   init_rsp_valid=!HARDWARE_INPUT_HASH&&(HARDWARE_FILL?(initializing||init_request_seed_pending):(initializing&&initial_index==131072));
   init_rsp_tag=init_generation;init_rsp_seed=seed;
   init_rsp_error=ERROR_PORT==1;
   if(ERROR_PORT==1&&!HARDWARE_FILL&&initializing&&initial_index>=3)begin init_wr_valid=0;init_rsp_valid=1;end
   if(!HARDWARE_INPUT_HASH&&HARDWARE_FILL&&STALL&&phase==1&&init_input_hash_calls&&!init_request_seed_pending&&init_response_drops<2)begin
    init_rsp_valid=1;init_rsp_tag=batch_tag-1;init_rsp_seed=~seed;init_rsp_error=1;
   end
   if(HARDWARE_INPUT_HASH&&STALL&&phase==10)begin
    if(removed_initial_replies<2)begin init_rsp_valid=1;init_rsp_tag=removed_initial_replies==0?batch_tag-16'd1:batch_tag;init_rsp_seed=0;init_rsp_error=1;end
    if(removed_initial_writes<2)begin init_wr_valid=1;init_wr_tag=removed_initial_writes==0?batch_tag-16'd1:batch_tag;init_wr_addr=0;init_wr_data=0;init_wr_strb=0;end
   end
   meta_req_ready=!meta_pending&&(!STALL||meta_stalls>=2);
   if(meta_delay>0)meta_delay=meta_delay-1;
   meta_rsp_valid=!HARDWARE_PROGRAM&&meta_pending&&meta_delay==0;meta_rsp_tag=meta_tag;meta_rsp_program=meta_program;
   meta_rsp_entropy=native_entropy;meta_rsp_program_addr=64'h10000000+active_program*4096;meta_rsp_error=0;
   if(!HARDWARE_PROGRAM&&STALL&&meta_rsp_valid&&meta_injected<2)begin
    if(meta_injected==0)meta_rsp_tag=batch_tag-1;else meta_rsp_program=meta_program-1;
    meta_rsp_entropy=~native_entropy;meta_rsp_error=1;
   end
   if(!HARDWARE_PROGRAM&&ERROR_PORT==2&&meta_rsp_valid&&meta_injected>=2)meta_rsp_error=1;
   sp_rd_ready=!sp_pending&&(!STALL||rd_stalls>=2);sp_wr_ready=!STALL||wr_stalls>=2;
   if(sp_delay>0)sp_delay=sp_delay-1;
   sp_rsp_valid=sp_pending&&sp_delay==0;sp_rsp_tag=sp_tag;sp_rsp_data=sp_data;sp_rsp_error=0;
   if(STALL&&sp_rsp_valid&&sp_injected<2)begin
    sp_rsp_tag=sp_injected==0?sp_tag^(51'b1<<35):sp_tag^51'b1;
    sp_rsp_data=~sp_data;sp_rsp_error=1;
   end
   if(sp_rsp_valid&&sp_injected>=2&&((ERROR_PORT==4&&sp_tag[34:33]==1)||(ERROR_PORT==6&&sp_tag[34:33]==2)))sp_rsp_error=1;
   prog_ready=!rom_pending&&(!STALL||rom_stalls>=2);
   if(rom_delay>0)rom_delay=rom_delay-1;
   prog_rsp_valid=!HARDWARE_PROGRAM&&rom_pending&&rom_delay==0;prog_rsp_tag=rom_tag;prog_rsp_instruction=rom_data;prog_rsp_error=0;
   if(!HARDWARE_PROGRAM&&STALL&&prog_rsp_valid&&rom_injected<2)begin
    prog_rsp_tag=rom_injected==0?rom_tag^(41'b1<<25):rom_tag^(41'b1<<9);
    prog_rsp_instruction=~rom_data;prog_rsp_error=1;
   end
   if(!HARDWARE_PROGRAM&&ERROR_PORT==3&&prog_rsp_valid&&rom_injected>=2)prog_rsp_error=1;
   ds_req_ready=!ds_pending&&(!STALL||ds_stalls>=2);
   if(ds_delay>0)ds_delay=ds_delay-1;
   ds_rsp_valid=!HARDWARE_DATASET&&ds_pending&&ds_delay==0;ds_rsp_tag=ds_tag;ds_rsp_data=ds_data;ds_rsp_error=0;
   if(STALL&&ds_rsp_valid&&ds_injected<2)begin
    ds_rsp_tag=ds_injected==0?ds_tag^(32'b1<<16):ds_tag^32'b1;
    ds_rsp_data=~ds_data;ds_rsp_error=1;
   end
   if(ERROR_PORT==5&&ds_rsp_valid&&ds_injected>=2)ds_rsp_error=1;
   if(HARDWARE_PROGRAM&&STALL&&dut.lifecycle.pg_state_q==2)begin
    if(external_meta_drops<2)begin meta_rsp_valid=1;meta_rsp_tag=external_meta_drops==0?batch_tag-1:batch_tag;meta_rsp_program=0;meta_rsp_error=1;end
    if(external_program_drops<2)begin prog_rsp_valid=1;prog_rsp_tag={external_program_drops==0?batch_tag-16'd1:batch_tag,25'd0};prog_rsp_instruction=0;prog_rsp_error=1;end
   end
   program_done_ready=!(CANCEL_PHASE==4)&&(!STALL||program_hold>=3);rsp_ready=!ERROR_PORT&&!DATASET_ERROR&&!(CANCEL_PHASE==6)&&(!STALL||done_hold>=3);
   @(posedge clk);
   dataset_provider_observe();
   if((ERROR_PORT==1&&phase==1&&init_rsp_valid&&init_rsp_ready&&init_rsp_tag==batch_tag&&init_rsp_error)||
      (ERROR_PORT==2&&meta_pending&&observed_meta_rsp_valid&&observed_meta_rsp_ready&&observed_meta_rsp_tag==meta_tag&&observed_meta_rsp_program==meta_program&&meta_rsp_error)||
      (ERROR_PORT==3&&rom_pending&&observed_prog_rsp_valid&&observed_prog_rsp_ready&&observed_prog_rsp_tag==rom_tag&&prog_rsp_error)||
      (ERROR_PORT==4&&sp_pending&&sp_rsp_valid&&sp_rsp_ready&&sp_rsp_tag==sp_tag&&sp_tag[34:33]==1&&sp_rsp_error)||
      (ERROR_PORT==5&&ds_pending&&ds_rsp_valid&&ds_rsp_ready&&ds_rsp_tag==ds_tag&&ds_rsp_error)||
      (ERROR_PORT==6&&sp_pending&&sp_rsp_valid&&sp_rsp_ready&&sp_rsp_tag==sp_tag&&sp_tag[34:33]==2&&sp_rsp_error)||
      (ERROR_PORT==8&&phase==1&&init_wr_valid&&init_wr_ready&&init_wr_tag==batch_tag&&init_wr_strb!=16'hffff))
    matching_fault_accepted=matching_fault_accepted+1;
   if(phase<1||phase>10||(^phase)===1'bx)$fatal(1,"invalid outer ledger phase");
   ledger[phase]=ledger[phase]+1;
   if(HARDWARE_INPUT_HASH)begin
    if(init_req_valid||initializing||init_request_seed_pending)$fatal(1,"hardware input hash emitted live host initialization");
    if(phase==10)begin
     if(input_hash_phase>2||(^input_hash_phase)===1'bx||sp_wr_valid||sp_rd_valid||dut.lifecycle.fill_wr_valid)$fatal(1,"input seed/fill ownership or phase");
     input_hash_detail[input_hash_phase]=input_hash_detail[input_hash_phase]+1;input_stage_clocks=input_stage_clocks+1;
    end
    if(dut.lifecycle.ih_req_valid&&dut.lifecycle.ih_req_ready)begin
     if(dut.lifecycle.input_q!==input_value||dut.lifecycle.input_bytes_q!==input_bytes||input_hash_requests)$fatal(1,"captured hardware input hash request changed");
     `RX_INPUT_HASH_ASSERTION(dut.lifecycle.input_q,dut.lifecycle.input_bytes_q,expected_input_seed);input_hash_requests=input_hash_requests+1;
    end
    if(dut.lifecycle.ih_rsp_valid&&dut.lifecycle.ih_rsp_ready)begin
     if(input_hash_requests!=1||input_hash_completions||dut.lifecycle.ih_rsp_tag!==batch_tag||dut.lifecycle.ih_rsp_error||dut.lifecycle.ih_rsp_seed!==expected_input_seed||sp_wr_valid)$fatal(1,"native hardware input hash seed mismatch");
     input_hash_completions=input_hash_completions+1;
    end
    if(sp_wr_valid&&input_hash_completions!=1)$fatal(1,"scratchpad write before completed input seed");
   end
   if(HARDWARE_PROGRAM&&(meta_req_valid||prog_valid))$fatal(1,"hardware program mode emitted a host provider request");
   if(HARDWARE_PROGRAM&&meta_rsp_valid&&meta_rsp_ready)external_meta_drops=external_meta_drops+1;
   if(HARDWARE_PROGRAM&&prog_rsp_valid&&prog_rsp_ready)external_program_drops=external_program_drops+1;
   if(HARDWARE_PROGRAM&&phase==7)begin
    if(program_gen_phase>2||(^program_gen_phase)===1'bx)$fatal(1,"program generation phase");
    program_gen_detail[program_gen_phase]=program_gen_detail[program_gen_phase]+1;
   end
   if(HARDWARE_PROGRAM&&dut.lifecycle.pg_out_valid&&dut.lifecycle.pg_out_ready)begin
    if(generation_image_beats>=200||dut.lifecycle.pg_out_tag!==batch_tag||dut.lifecycle.pg_out_addr!==generation_image_beats*16||
       observed_prog_valid||sp_wr_valid||sp_rd_valid||ds_req_valid)$fatal(1,"hardware program generation ownership/order");
    if(generation_image_beats<8)expected_data=native_entropy[128*generation_image_beats+:128];
    else expected_data={rom[2*(generation_image_beats-8)+1],rom[2*(generation_image_beats-8)]};
    if(dut.lifecycle.pg_out_data!==expected_data)$fatal(1,"native hardware program image mismatch program=%0d beat=%0d",active_program,generation_image_beats);
    generation_image_beats=generation_image_beats+1;generated_beats=generated_beats+1;
   end
   if(HARDWARE_FILL&&phase==1)begin
    if(dut.lifecycle.state_q==9||dut.lifecycle.state_q==10)begin
     if(init_fill_phase>2||(^init_fill_phase)===1'bx)$fatal(1,"initial fill phase");
     fill_detail[init_fill_phase]=fill_detail[init_fill_phase]+1;
    end else init_provider_wait=init_provider_wait+1;
   end
   if(sp_rd_valid&&!sp_rd_ready)stall_sp_requests=stall_sp_requests+1;
   if(sp_wr_valid&&!sp_wr_ready)stall_sp_writes=stall_sp_writes+1;
   if(ds_req_valid&&!selected_ds_req_ready)stall_dataset_requests=stall_dataset_requests+1;
   if(observed_prog_valid&&!observed_prog_ready)stall_program_loads=stall_program_loads+1;
   if(sp_pending)waiting_sp_replies=waiting_sp_replies+1;
   if(ds_pending)waiting_dataset_replies=waiting_dataset_replies+1;
   if(rom_pending)waiting_program_replies=waiting_program_replies+1;
   if(phase==4)begin
    if(iteration_phase>11||(^iteration_phase)===1'bx)$fatal(1,"iteration ledger phase");
    iteration_detail[iteration_phase]=iteration_detail[iteration_phase]+1;
    if(iteration_phase==7)begin
     if(execute_phase>17||(^execute_phase)===1'bx)$fatal(1,"executor phase");
     exec_detail[execute_phase]=exec_detail[execute_phase]+1;
    end
   end
   if(phase==6)begin final_phase_index=dut.lifecycle.finalizer.state_q;if(final_phase_index>5)$fatal(1,"finalizer phase");final_detail[final_phase_index]=final_detail[final_phase_index]+1;end
   if(prep_rcp_fire)preparation_reciprocals=preparation_reciprocals+1;
   if(dut.lifecycle.chain.iteration_chain.iteration.iteration.execute.reciprocal.req_valid&&dut.lifecycle.chain.iteration_chain.iteration.iteration.execute.reciprocal.req_ready)runtime_reciprocals=runtime_reciprocals+1;
   if(!EVENT_TRACE||phase!=last_trace_phase||iteration_phase!=last_trace_iteration||execute_phase!=last_trace_execute||commit_valid||sp_rd_valid&&sp_rd_ready||sp_wr_valid&&sp_wr_ready||ds_req_valid&&selected_ds_req_ready||prep_commit_valid||program_done_valid||rsp_valid)
    $fdisplay(trace_file,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0h,%0d,%0h,%0h,%0d,%0h",cycle,phase,iteration_phase,execute_phase,commit_valid,commit_pc,sp_rd_valid&&sp_rd_ready,sp_rd_addr,sp_wr_valid&&sp_wr_ready,sp_wr_addr,sp_wr_strb,ds_req_valid&&selected_ds_req_ready,ds_req_addr);
   last_trace_phase=phase;
   last_trace_iteration=iteration_phase;last_trace_execute=execute_phase;
   if(phase==4&&iteration_phase==7&&!kernel_started)begin kernel_started=1;route=64'hcbf29ce484222325;steps=0;end
   if(init_req_valid&&init_req_ready)begin
    init_generation=init_req_tag;initializing=1;initial_index=0;
    if(init_req_input!==input_value||init_req_input_bytes!==input_bytes)$fatal(1,"captured hash input changed");
    if(HARDWARE_FILL)begin
     if(!init_rsp_valid||init_rsp_tag!==init_req_tag||init_rsp_seed!==seed||init_rsp_ready||!init_request_seed_pending)$fatal(1,"same-cycle input seed was lost or accepted too early");
     held_init_response={init_rsp_tag,init_rsp_seed,init_rsp_error};init_same_cycle_offers=init_same_cycle_offers+1;
    end
    else begin
     $sformat(path,"%0s/actual-initial.hex",output_directory);`RX_INITIAL(init_req_input,init_req_input_bytes,path,seed);$readmemh(path,initial_ram);
     for(i=0;i<131072;i=i+1)if(initial_ram[i]!==gold_ram[i])$fatal(1,"native initial scratchpad disagreement");
    end
   end
   if(init_wr_valid&&init_wr_ready)begin
    if(HARDWARE_INPUT_HASH)removed_initial_writes=removed_initial_writes+1;
    else if(HARDWARE_FILL&&init_wr_tag!=batch_tag)init_write_drops=init_write_drops+1;
    else if(!HARDWARE_FILL)initial_index=initial_index+1;
   end
   if(init_rsp_valid&&init_rsp_ready)begin
    if(HARDWARE_INPUT_HASH)removed_initial_replies=removed_initial_replies+1;
    else if(HARDWARE_FILL&&init_rsp_tag!=batch_tag)init_response_drops=init_response_drops+1;
    else begin
     if(HARDWARE_FILL&&init_request_seed_pending)begin
      if(dut.lifecycle.state_q!=2||{init_rsp_tag,init_rsp_seed,init_rsp_error}!==held_init_response)$fatal(1,"held input seed changed before acceptance");
      init_request_seed_pending=0;init_same_cycle_accepts=init_same_cycle_accepts+1;
     end
     initializing=0;
    end
   end
   if(prep_commit_valid)begin
    if(prep_commit_program!==active_program||prep_commit_epoch<=last_epoch)$fatal(1,"admission ownership/epoch");
    last_epoch=prep_commit_epoch;admissions=admissions+1;
   end
   if(error_valid)begin
    if(DATASET_ERROR)dataset_error_and_restart();
    else if(ERROR_PORT)matching_error_and_restart();
    else $fatal(1,"sequence returned error program=%0d code=%0d pc=%0d opcode=%0d",error_program,error_code,error_pc,error_opcode);
   end
   if(held_read&&(!sp_rd_valid||now_read!==saved_read))$fatal(1,"held SRAM read changed");
   if(held_write&&(!sp_wr_valid||now_write!==saved_write))$fatal(1,"held SRAM write changed");
   if(held_rom&&(!observed_prog_valid||now_rom!==saved_rom))$fatal(1,"held instruction request changed");
   if(held_meta&&(!observed_meta_req_valid||now_meta!==saved_meta))$fatal(1,"held metadata request changed");
   if(held_ds&&(!ds_req_valid||now_ds!==saved_ds))$fatal(1,"held dataset request changed");
   if(held_program&&(!program_done_valid||now_program!==saved_program))$fatal(1,"held program result changed");
   if(held_done&&(!done_valid||now_done!==saved_done))$fatal(1,"held batch result changed");
   held_read=sp_rd_valid&&!sp_rd_ready;saved_read=now_read;
   held_write=sp_wr_valid&&!sp_wr_ready;saved_write=now_write;
   held_rom=observed_prog_valid&&!observed_prog_ready;saved_rom=now_rom;
   held_meta=observed_meta_req_valid&&!observed_meta_req_ready;saved_meta=now_meta;
   held_ds=ds_req_valid&&!selected_ds_req_ready;saved_ds=now_ds;
   held_program=program_done_valid&&!program_done_ready;saved_program=now_program;
   held_done=done_valid&&!done_ready;saved_done=now_done;
   if(observed_meta_req_valid&&!observed_meta_req_ready)meta_stalls=meta_stalls+1;
   if(sp_rd_valid&&!sp_rd_ready)rd_stalls=rd_stalls+1;
   if(sp_wr_valid&&!sp_wr_ready)wr_stalls=wr_stalls+1;
   if(observed_prog_valid&&!observed_prog_ready)rom_stalls=rom_stalls+1;
   if(ds_req_valid&&!selected_ds_req_ready)ds_stalls=ds_stalls+1;
   if(program_done_valid&&!program_done_ready)program_hold=program_hold+1;
   if(done_valid&&!done_ready)done_hold=done_hold+1;
   if(observed_meta_rsp_valid&&observed_meta_rsp_ready)begin
    if(HARDWARE_PROGRAM&&(generation_image_beats!=200||dut.lifecycle.chain_meta_rsp_entropy!==native_entropy))$fatal(1,"metadata escaped incomplete hardware image");
    if(observed_meta_rsp_tag!=batch_tag||observed_meta_rsp_program!=meta_program)begin meta_injected=meta_injected+1;meta_drops=meta_drops+1;end else meta_pending=0;
   end
   if(sp_rsp_valid&&sp_rsp_ready)begin
    if(sp_rsp_tag!=sp_tag)begin sp_injected=sp_injected+1;sp_drops=sp_drops+1;end else sp_pending=0;
   end
   if(observed_prog_rsp_valid&&observed_prog_rsp_ready)begin
    if(HARDWARE_PROGRAM&&observed_prog_rsp_instruction!==rom_data)$fatal(1,"native generated buffer fetch mismatch");
    if(observed_prog_rsp_tag!=rom_tag)begin rom_injected=rom_injected+1;rom_drops=rom_drops+1;end else rom_pending=0;
   end
   if(selected_ds_rsp_valid&&selected_ds_rsp_ready)begin
    if(selected_ds_rsp_tag!=ds_tag)begin ds_injected=ds_injected+1;ds_drops=ds_drops+1;end
    else begin
     if(!selected_ds_rsp_error&&selected_ds_rsp_data!==dataset_expected_data)$fatal(1,"native dataset response mismatch at actual full64 address");
     ds_pending=0;dataset_responses_seen=dataset_responses_seen+1;
    end
   end
   if(observed_meta_req_valid&&observed_meta_req_ready)begin
    if(meta_req_tag!==batch_tag||meta_req_program!==programs_finished||meta_pending)$fatal(1,"program request order/tag");
    if(HARDWARE_FILL&&programs_finished==0&&(init_writes!=131072||meta_req_seed!==expected_seed))$fatal(1,"program0 escaped full hardware fill or postfill seed mismatch");
    active_program=meta_req_program;meta_tag=batch_tag;meta_program=meta_req_program;
    $sformat(path,"%0s/actual-program-%0d.mem",output_directory,active_program);
    if(HARDWARE_PROGRAM)begin
     // Native generation is an assertion oracle; its image never drives a DUT pin.
     `RX_GENERATE_ASSERTION(meta_req_seed,path,native_entropy);
     generation_image_beats=0;program_gen_images=program_gen_images+1;
    end else `RX_GENERATE(meta_req_seed,path,native_entropy);
    $readmemh(path,rom);
    $sformat(path,"%0s/program-%0d.mem",directory,active_program);$readmemh(path,gold_rom);
    for(i=0;i<384;i=i+1)if(rom[i]!==gold_rom[i])$fatal(1,"actual generated instruction image mismatch");
    if(native_entropy!==gold_meta[active_program][1023:0])$fatal(1,"DUT-derived next-program entropy disagreement at program=%0d",active_program);
    meta_pending=1;meta_delay=STALL?3:1;meta_injected=0;meta_stalls=0;
   end
   if(observed_prog_valid&&observed_prog_ready)begin
    pc=(prog_addr-(64'h10000000+active_program*4096))>>3;
    if(rom_pending||prog_tag[40:25]!==batch_tag||prog_tag[8:0]!==pc||prog_addr[2:0]!=0||pc<0||pc>=384)$fatal(1,"instruction fetch/identity");
    current_load=prog_tag[24:0];loaded_words=loaded_words+1;
    rom_data=rom[pc];rom_tag=prog_tag;rom_pending=1;rom_delay=STALL?3:1;rom_injected=0;rom_stalls=0;
   end
   if(commit_valid)begin
    if(!kernel_started||commit_tag!==inner_tag)$fatal(1,"instruction retirement generation");
    word=({55'b0,commit_pc}<<17)|({56'b0,commit_opcode}<<9)|{55'b0,commit_next_pc};
    route=(route^word)*64'h100000001b3;steps=steps+1;total_instructions=total_instructions+1;
   end
   if(sp_rd_valid&&sp_rd_ready)begin
    if(sp_pending||sp_rd_tag[50:35]!==batch_tag||sp_rd_addr[3:0]!=0)$fatal(1,"SRAM read protocol");
    sp_data=ram[sp_rd_addr>>4];sp_tag=sp_rd_tag;sp_pending=1;sp_delay=STALL?3:1;sp_injected=0;rd_stalls=0;reads=reads+1;
    physical_read_bytes=physical_read_bytes+16;
    if(sp_rd_tag[34:33]==2)begin
     if(scratchpad_owner!==2||sp_rd_addr!==final_reads*16||sp_wr_valid)$fatal(1,"exclusive finalizer scan ownership");
     final_reads=final_reads+1;
    end else if(sp_rd_tag[34:33]!=1||sp_rd_tag[15:0]!==inner_tag)$fatal(1,"execution read owner/tag");
    else if(kernel_started&&!dataset_taken)begin
     if(event_index>=gold[global_iteration][2497:2466]+gold[global_iteration][2529:2498]||events[event_index][85]||
      {events[event_index][84:68],4'b0}!==sp_rd_addr)$fatal(1,"native bytecode read address/order");
     expected_data=sp_data;if((events[event_index][67]?sp_data[127:64]:sp_data[63:0])!==events[event_index][63:0])$fatal(1,"native bytecode read data");
     event_index=event_index+1;
    end else entry_reads=entry_reads+1;
   end
   if(ds_req_valid&&selected_ds_req_ready)begin
    if(ds_pending||dataset_taken||ds_req_tag!=={batch_tag,inner_tag}||ds_req_addr!==gold[global_iteration][2305:2242]||
      ds_prefetch_addr!==gold[global_iteration][2369:2306]||!ds_prefetch_valid)$fatal(1,"native dataset/control state");
    if(event_index!=gold[global_iteration][2497:2466]+gold[global_iteration][2529:2498])$fatal(1,"native bytecode event count");
    dataset_read_native_assertion();
    dataset_taken=1;
    if(!HARDWARE_DATASET)begin
     `RX_DATASET(ds_req_addr,ds_data);dataset_live_calls=dataset_live_calls+1;
     if(ds_data!==dataset_expected_data)$fatal(1,"software dataset provider differs from same native gold");
    end
    ds_tag=ds_req_tag;ds_pending=1;ds_delay=STALL?3:1;ds_injected=0;ds_stalls=0;
   end
   if(sp_wr_valid&&sp_wr_ready)begin
    if(sp_wr_tag[50:35]!==batch_tag||sp_wr_addr[3:0]!=0)$fatal(1,"SRAM write generation/alignment");
    physical_write_bus_bytes=physical_write_bus_bytes+16;
    for(byte_index=0;byte_index<16;byte_index=byte_index+1)if(sp_wr_strb[byte_index])useful_write_bytes=useful_write_bytes+1;
    if(sp_wr_tag[34:33]==0)begin
     if(scratchpad_owner!==0||sp_wr_addr!==init_writes*16||sp_wr_strb!==16'hffff)$fatal(1,"exclusive initialization owner");
     if(HARDWARE_FILL&&(sp_wr_data!==gold_ram[init_writes]||sp_rd_valid||observed_prog_valid||observed_meta_req_valid||ds_req_valid))$fatal(1,"native hardware initial fill data or exclusive ownership");
     init_writes=init_writes+1;
    end else if(sp_wr_tag[34:33]!=1||sp_wr_tag[15:0]!==inner_tag)$fatal(1,"execution write owner/tag");
    else if(!dataset_taken)begin
     if(event_index>=gold[global_iteration][2497:2466]+gold[global_iteration][2529:2498]||!events[event_index][85]||
      {events[event_index][84:68],4'b0}!==sp_wr_addr||sp_wr_strb!==(events[event_index][67]?16'hff00:16'h00ff)||
      (events[event_index][67]?sp_wr_data[127:64]:sp_wr_data[63:0])!==events[event_index][63:0])$fatal(1,"native bytecode write address/data/order");
     event_index=event_index+1;
    end else begin
     if(tail_index>=8)$fatal(1,"extra tail write");
     expected_addr=(tail_index<4?gold[global_iteration][2241:2210]:gold[global_iteration][2209:2178])+(tail_index%4)*16;
     expected_data=tail_index<4?gold[global_iteration][128*(tail_index%4)+:128]:gold[global_iteration][512+128*(tail_index%4)+:128];
     if(sp_wr_addr!==expected_addr[20:0]||sp_wr_strb!==16'hffff||sp_wr_data!==expected_data)$fatal(1,"native tail write/control");
     tail_index=tail_index+1;tail_writes=tail_writes+1;
    end
    for(b=0;b<16;b=b+1)if(sp_wr_strb[b])ram[sp_wr_addr>>4][8*b+:8]=sp_wr_data[8*b+:8];
    writes=writes+1;wr_stalls=0;
   end
   if(iteration_commit_valid)begin
    if(global_iteration>=TOTAL_ITERATIONS||iteration_commit_tag!==batch_tag||iteration_commit_backend_tag!==inner_tag||
     iteration_commit_program!==global_iteration/ITERATIONS||iteration_commit_index!==global_iteration%ITERATIONS||
     {iteration_commit_a,iteration_commit_e,iteration_commit_f,iteration_commit_r}!==gold[global_iteration][2047:0]||
     {iteration_commit_spaddr1,iteration_commit_spaddr0,iteration_commit_ma,iteration_commit_mx,iteration_commit_round_mode}!==gold[global_iteration][2177:2048]||
     steps!=gold[global_iteration][2465:2434]||route!==gold[global_iteration][2433:2370]||tail_index!=8||!dataset_taken)
      $fatal(1,"native full iteration state disagreement program=%0d iteration=%0d global=%0d steps=%0d",active_program,iteration_commit_index,global_iteration,steps);
    global_iteration=global_iteration+1;inner_tag=inner_tag+1;kernel_started=0;dataset_taken=0;tail_index=0;steps=0;
   end
   if(program_done_valid&&program_done_ready)begin
    i=program_done_index*ITERATIONS+ITERATIONS-1;
    if(program_done_tag!==batch_tag||program_done_index!==programs_finished||program_done_iterations!=ITERATIONS||
      {program_done_a,program_done_e,program_done_f,program_done_r}!==gold[i][2047:0]||program_done_round_mode!==gold[i][2049:2048])$fatal(1,"native program transition/state");
    $sformat(path,"%0s/final-%0d.hex",directory,programs_finished);$readmemh(path,gold_ram);
    for(i=0;i<131072;i=i+1)if(ram[i]!==gold_ram[i])$fatal(1,"native full scratchpad disagreement at program=%0d line=%0d",programs_finished,i);
    // Actual DUT output supplies the next seed; no oracle register ever feeds it.
    `RX_NEXT(program_done_r,program_done_f,program_done_e,program_done_a,native_expected_seed);
    if(program_done_index<PROGRAMS-1)begin
     if(!program_done_seed_valid||program_done_seed!==native_expected_seed)$fatal(1,"hardware/native register digest mismatch");
     seed_hashes=seed_hashes+1;
    end else if(program_done_seed_valid||program_done_seed!==0)$fatal(1,"eighth program incorrectly interprogram-hashed");
    programs_finished=programs_finished+1;program_hold=0;
   end
   if(done_valid&&done_ready)begin
    if(global_iteration!=TOTAL_ITERATIONS||programs_finished!=PROGRAMS||done_tag!==16'h4000||
      {done_a,done_e,done_f,done_r}!==gold_final_rf[0]||rsp_digest!==gold_digest[0]||rsp_error||
      {done_spaddr1,done_spaddr0,done_ma,done_mx,done_round_mode}!==gold[TOTAL_ITERATIONS-1][2177:2048])$fatal(1,"batch completion/state");
    if(observed_meta_req_valid||observed_prog_valid||sp_rd_valid||sp_wr_valid||ds_req_valid)$fatal(1,"completed batch emitted requests");
    if(final_reads!=131072||init_writes!=131072||admissions!=PROGRAMS||loaded_words!=PROGRAMS*384)$fatal(1,"complete ownership/admission accounting");
    for(i=0;i<131072;i=i+1)if(ram[i]!==gold_ram[i])$fatal(1,"finalizer modified memory");
    $sformat(path,"%0s/actual-final-digest32.hex",output_directory);ledger_file=$fopen(path,"w");
    if(!ledger_file)$fatal(1,"actual digest output open");$fdisplay(ledger_file,"%064h",rsp_digest);$fclose(ledger_file);
    accepted_done=1;final_native_completions=final_native_completions+1;
   end
   if(DATASET_CANCEL&&((DATASET_CANCEL==1&&dataset_c_pending)||(DATASET_CANCEL==2&&dataset_f_pending)||
      (DATASET_CANCEL==3&&dataset_multiply_wait&&dataset_multiply_wait_clocks>=16)))dataset_cancel_and_restart();
   if((CANCEL_PHASE==1&&init_writes==3)||(CANCEL_PHASE==2&&loaded_words==3)||
      (CANCEL_PHASE==3&&ds_pending)||(CANCEL_PHASE==4&&program_done_valid&&program_hold>=4)||
      (CANCEL_PHASE==5&&final_reads==3)||(CANCEL_PHASE==6&&rsp_valid)||(CANCEL_PHASE==7&&generation_image_beats==3)||
      (CANCEL_PHASE==8&&input_stage_clocks==3))cancel_and_restart();
   #1;cycle=cycle+1;@(negedge clk);
  end
  if(seed_hashes!=PROGRAMS-1||event_index!=TOTAL_EVENTS||total_instructions!=TOTAL_INSTRUCTIONS||tail_writes!=8*TOTAL_ITERATIONS)$fatal(1,"sequence coverage accounting");
  for(i=0;i<11;i=i+1)stage_sum=stage_sum+ledger[i];
  if(stage_sum!=cycle)$fatal(1,"nonclosing outer cycle ledger");
  if(HARDWARE_FILL&&init_provider_wait+fill_detail[0]+fill_detail[1]+fill_detail[2]!=ledger[1])$fatal(1,"nonclosing initialization ledger");
  if(!HARDWARE_INPUT_HASH&&HARDWARE_FILL&&STALL&&(init_response_drops!=2||init_write_drops!=1))$fatal(1,"stale initialization coverage");
  if(!HARDWARE_INPUT_HASH&&HARDWARE_FILL&&(init_input_hash_calls!=1||init_same_cycle_offers!=1||init_same_cycle_accepts!=1||init_request_seed_pending))$fatal(1,"same-cycle initialization response coverage");
  if(HARDWARE_INPUT_HASH&&(input_hash_requests!=1||input_hash_completions!=1||init_provider_wait||input_hash_detail[0]+input_hash_detail[1]+input_hash_detail[2]!=ledger[10]))$fatal(1,"input hash coverage/partition");
  if(HARDWARE_INPUT_HASH&&STALL&&(removed_initial_replies!=2||removed_initial_writes!=2))$fatal(1,"removed initialization provider drain coverage");
  stage_sum=0;for(i=0;i<12;i=i+1)stage_sum=stage_sum+iteration_detail[i];
  if(stage_sum!=ledger[4])$fatal(1,"nonclosing nested iteration ledger");
  stage_sum=0;for(i=0;i<6;i=i+1)stage_sum=stage_sum+final_detail[i];
  if(stage_sum!=ledger[6])$fatal(1,"nonclosing nested finalization ledger");
  stage_sum=0;for(i=0;i<18;i=i+1)stage_sum=stage_sum+exec_detail[i];
  if(stage_sum!=iteration_detail[7])$fatal(1,"nonclosing nested executor ledger");
  if(HARDWARE_PROGRAM&&(generated_beats!=PROGRAMS*200||program_gen_images!=PROGRAMS||program_gen_detail[0]+program_gen_detail[1]+program_gen_detail[2]!=ledger[7]))$fatal(1,"program generation coverage/ledger");
  if(HARDWARE_PROGRAM&&STALL&&(external_meta_drops!=2||external_program_drops!=2))$fatal(1,"external removed-provider response drain coverage");
  if(STALL&&(meta_drops!=(HARDWARE_PROGRAM?0:2*PROGRAMS)||rom_drops!=(HARDWARE_PROGRAM?0:2*loaded_words)||sp_drops!=2*reads||ds_drops!=(HARDWARE_DATASET?0:2*TOTAL_ITERATIONS)))$fatal(1,"stale error injection coverage");
  $fclose(trace_file);$sformat(path,"%0s/provider-host-time.json",output_directory);`RX_STATS(path);
  $sformat(path,"%0s/ledger.json",output_directory);ledger_file=$fopen(path,"w");if(!ledger_file)$fatal(1,"ledger write");
  $fwrite(ledger_file,"{\"cycles\":%0d,",cycle);
  if(HARDWARE_FILL)$fwrite(ledger_file,"\"hardware_fill_enabled\":true,");else $fwrite(ledger_file,"\"hardware_fill_enabled\":false,");
  if(HARDWARE_PROGRAM)$fwrite(ledger_file,"\"hardware_program_enabled\":true,");else $fwrite(ledger_file,"\"hardware_program_enabled\":false,");
  if(HARDWARE_INPUT_HASH)$fwrite(ledger_file,"\"hardware_input_hash_enabled\":true,");else $fwrite(ledger_file,"\"hardware_input_hash_enabled\":false,");
  $fwrite(ledger_file,"\"stage_cycles\":{");
  if(HARDWARE_FILL)$fwrite(ledger_file,"\"initialization_hardware_fill\":%0d,",ledger[1]);
  else $fwrite(ledger_file,"\"initialization_transport\":%0d,",ledger[1]);
  if(HARDWARE_PROGRAM)$fwrite(ledger_file,"\"program_generation\":%0d,",ledger[7]);
  if(HARDWARE_INPUT_HASH)$fwrite(ledger_file,"\"input_hash\":%0d,",ledger[10]);
  $fdisplay(ledger_file,"\"control_and_metadata\":%0d,\"program_preparation\":%0d,\"execution\":%0d,\"interprogram_seed\":%0d,\"finalization\":%0d,\"held_return\":%0d},",ledger[2],ledger[3],ledger[4],ledger[5],ledger[6],ledger[8]);
  if(HARDWARE_FILL)$fdisplay(ledger_file,"\"nested_initialization\":{\"provider_wait\":%0d,\"fill_phases\":[%0d,%0d,%0d]},",init_provider_wait,fill_detail[0],fill_detail[1],fill_detail[2]);
  if(HARDWARE_INPUT_HASH)$fdisplay(ledger_file,"\"nested_input_hash_phases\":[%0d,%0d,%0d],\"input_hash_bytes\":%0d,\"removed_initialization_replies_drained\":%0d,\"removed_initialization_writes_drained\":%0d,",input_hash_detail[0],input_hash_detail[1],input_hash_detail[2],input_bytes,removed_initial_replies,removed_initial_writes);
  if(HARDWARE_PROGRAM)$fdisplay(ledger_file,"\"nested_program_generation_phases\":[%0d,%0d,%0d],\"program_generation_output_bytes\":%0d,\"program_image_storage_bytes\":3200,\"program_image_transport\":\"internal_generated_buffer\",\"removed_provider_replies_drained\":{\"metadata\":%0d,\"program\":%0d},",program_gen_detail[0],program_gen_detail[1],program_gen_detail[2],generated_beats*16,external_meta_drops,external_program_drops);
  $fdisplay(ledger_file,"\"nested_iteration_phases\":[%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d],\"nested_finalization_phases\":[%0d,%0d,%0d,%0d,%0d,%0d],",iteration_detail[0],iteration_detail[1],iteration_detail[2],iteration_detail[3],iteration_detail[4],iteration_detail[5],iteration_detail[6],iteration_detail[7],iteration_detail[8],iteration_detail[9],iteration_detail[10],iteration_detail[11],final_detail[0],final_detail[1],final_detail[2],final_detail[3],final_detail[4],final_detail[5]);
  $fdisplay(ledger_file,"\"nested_stalls\":{\"sp_request\":%0d,\"sp_write\":%0d,\"dataset_request\":%0d,\"program_load\":%0d},\"preparation_reciprocals\":%0d,\"runtime_reciprocals\":%0d,",stall_sp_requests,stall_sp_writes,stall_dataset_requests,stall_program_loads,preparation_reciprocals,runtime_reciprocals);
  $fdisplay(ledger_file,"\"nested_executor_phases\":[%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d],",exec_detail[0],exec_detail[1],exec_detail[2],exec_detail[3],exec_detail[4],exec_detail[5],exec_detail[6],exec_detail[7],exec_detail[8],exec_detail[9],exec_detail[10],exec_detail[11],exec_detail[12],exec_detail[13],exec_detail[14],exec_detail[15],exec_detail[16],exec_detail[17]);
  $fdisplay(ledger_file,"\"nested_reply_waits\":{\"scratchpad\":%0d,\"dataset\":%0d,\"program\":%0d},\"stale_error_replies_dropped\":{\"metadata\":%0d,\"program\":%0d,\"scratchpad\":%0d,\"dataset\":%0d},",waiting_sp_replies,waiting_dataset_replies,waiting_program_replies,meta_drops,rom_drops,sp_drops,ds_drops);
  $fdisplay(ledger_file,"\"scratchpad_bytes\":2097152,\"physical_port_read_bytes\":%0d,\"physical_port_write_bus_bytes\":%0d,\"strobed_write_bytes\":%0d,\"dataset_logical_bytes\":%0d,\"logical_bytecode_memory_bytes\":%0d,\"logical_entry_bytes\":%0d,\"logical_tail_bytes\":%0d,\"initialization_and_finalization_bytes_each\":2097152,\"program_image_load_bytes\":%0d,\"native_dataset_internal_physical_bytes\":null,\"untimed_provider_device_cycles\":null}",physical_read_bytes,physical_write_bus_bytes,useful_write_bytes,TOTAL_ITERATIONS*64,TOTAL_EVENTS*8,TOTAL_ITERATIONS*128,TOTAL_ITERATIONS*128,loaded_words*8);
  $fclose(ledger_file);
  dataset_write_ledger();
  $display("PASS prepared_hash_lifecycle prepared=%0d programs=%0d iterations_per_program=%0d stall=%0d total_iterations=%0d actual_instructions=%0d bytecode_events=%0d admissions=%0d loaded_words=%0d hardware_seeds=%0d initial_writes=%0d final_reads=%0d cycles=%0d native_digest32=1 native_actual_dataset=1 full_scratchpad_bytes=2097152 ledger_closes=1",PREPARED_RCP,PROGRAMS,ITERATIONS,STALL,global_iteration,total_instructions,event_index,admissions,loaded_words,seed_hashes,init_writes,final_reads,cycle);
  $finish;
 end
endmodule
