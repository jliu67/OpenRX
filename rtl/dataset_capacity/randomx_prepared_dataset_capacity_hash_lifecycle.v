// SPDX-License-Identifier: BSD-3-Clause
// Optional prepared native dataset service around the unchanged hash lifecycle.
// All legacy ports and their disabled-mode behavior are preserved.
`default_nettype none
module randomx_prepared_dataset_capacity_hash_lifecycle #(
 parameter integer PROGRAMS=8,ITERATIONS=2048,PREPARED_RCP=1,SCRATCHPAD_BYTES=2097152,HARDWARE_FILL=0,HARDWARE_PROGRAM=0,HARDWARE_INPUT_HASH=0,
 parameter integer HARDWARE_DATASET=0,DATASET_MUL_RADIX4=1,DATASET_SESSION_BITS=32
)(
 input wire clk,rst,cancel,
 input wire req_valid,output wire req_ready,input wire [15:0] req_tag,
 input wire [639:0] req_input,input wire [6:0] req_input_bytes,
 output wire init_req_valid,input wire init_req_ready,output wire [15:0] init_req_tag,
 output wire [639:0] init_req_input,output wire [6:0] init_req_input_bytes,
 input wire init_wr_valid,output wire init_wr_ready,input wire [15:0] init_wr_tag,
 input wire [20:0] init_wr_addr,input wire [127:0] init_wr_data,input wire [15:0] init_wr_strb,
 input wire init_rsp_valid,output wire init_rsp_ready,input wire [15:0] init_rsp_tag,
 input wire [511:0] init_rsp_seed,input wire init_rsp_error,
 output wire [511:0] meta_req_seed,input wire meta_rsp_error,
 input wire sp_rsp_error,input wire ds_rsp_error,
 output wire rsp_valid,input wire rsp_ready,output wire [15:0] rsp_tag,
 output wire [511:0] rsp_r,rsp_f,rsp_e,rsp_a,output wire [1:0] rsp_round_mode,
 output wire [255:0] rsp_digest,output wire rsp_error,
 output wire error_valid,output wire [15:0] error_tag,output wire [2:0] error_program,
 output wire [1:0] error_code,output wire [8:0] error_pc,output wire [7:0] error_opcode,
 output wire [3:0] phase,output wire [1:0] init_fill_phase,output wire [1:0] program_gen_phase,output wire [1:0] input_hash_phase,output wire [1:0] scratchpad_owner,output wire generation_exhausted,
 output wire  prep_commit_valid,
 output wire [15:0] prep_commit_epoch,
 output wire [2:0] prep_commit_program,
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
 output wire  program_done_seed_valid,
 output wire [511:0] program_done_seed,
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
 output wire [50:0] sp_rd_tag,
 input wire  sp_rsp_valid,
 output wire  sp_rsp_ready,
 input wire [127:0] sp_rsp_data,
 input wire [50:0] sp_rsp_tag,
 output wire  sp_wr_valid,
 input wire  sp_wr_ready,
 output wire [20:0] sp_wr_addr,
 output wire [127:0] sp_wr_data,
 output wire [15:0] sp_wr_strb,
 output wire [50:0] sp_wr_tag,
 output wire  ds_req_valid,
 input wire  ds_req_ready,
 output wire [63:0] ds_req_addr,
 output wire [63:0] ds_prefetch_addr,
 output wire [31:0] ds_req_tag,
 output wire  ds_prefetch_valid,
 input wire  ds_rsp_valid,
 output wire  ds_rsp_ready,
 input wire [31:0] ds_rsp_tag,
 input wire [511:0] ds_rsp_data,
 output wire  prog_valid,
 input wire  prog_ready,
 output wire [63:0] prog_addr,
 output wire [40:0] prog_tag,
 input wire  prog_rsp_valid,
 output wire  prog_rsp_ready,
 input wire [40:0] prog_rsp_tag,
 input wire [63:0] prog_rsp_instruction,
 input wire  prog_rsp_error,
 output wire  commit_valid,
 output wire [15:0] commit_tag,
 output wire [8:0] commit_pc,
 output wire [7:0] commit_opcode,
 output wire [511:0] commit_r,
 output wire [8:0] commit_next_pc,
 output wire [8:0] commit_branch_target,
 output wire [511:0] commit_f,
 output wire [511:0] commit_e,
 output wire [1:0] commit_round_mode,
 input wire [15:0] req_dataset_epoch,
 input wire [79:0] req_dataset_counts,
 input wire [63:0] req_dataset_address_regs,
 input wire [31:0] req_dataset_rcp_count,
 output wire dataset_cache_req_valid,
 input wire dataset_cache_req_ready,
 output wire [63:0] dataset_cache_req_tag,
 output wire [15:0] dataset_cache_req_epoch,
 output wire [2:0] dataset_cache_req_program,
 output wire [21:0] dataset_cache_req_index,
 input wire dataset_cache_rsp_valid,
 output wire dataset_cache_rsp_ready,
 input wire [63:0] dataset_cache_rsp_tag,
 input wire [15:0] dataset_cache_rsp_epoch,
 input wire [2:0] dataset_cache_rsp_program,
 input wire [21:0] dataset_cache_rsp_index,
 input wire [511:0] dataset_cache_rsp_data,
 input wire dataset_cache_rsp_error,
 output wire dataset_fetch_valid,
 input wire dataset_fetch_ready,
 output wire [63:0] dataset_fetch_tag,
 output wire [15:0] dataset_fetch_epoch,
 output wire [2:0] dataset_fetch_program,
 output wire [8:0] dataset_fetch_pc,
 input wire dataset_fetch_rsp_valid,
 output wire dataset_fetch_rsp_ready,
 input wire [63:0] dataset_fetch_rsp_tag,
 input wire [15:0] dataset_fetch_rsp_epoch,
 input wire [2:0] dataset_fetch_rsp_program,
 input wire [8:0] dataset_fetch_rsp_pc,
 input wire [63:0] dataset_fetch_rsp_instruction,
 input wire dataset_fetch_rsp_error,
 input wire dataset_fetch_rsp_rcp_valid,
 input wire [31:0] dataset_fetch_rsp_rcp_index,
 input wire [63:0] dataset_fetch_rsp_rcp_value,
 output wire [1:0] dataset_service_phase,
 output wire [3:0] dataset_item_phase,
 output wire dataset_generation_exhausted,
 output wire dataset_batch_active,
 output wire [31:0] dataset_items_reserved,
 output wire [31:0] dataset_items_remaining,
 output wire [63:0] dataset_items_requested,
 output wire [63:0] dataset_items_completed,
 output wire [63:0] dataset_ds_requests,
 output wire [63:0] dataset_ds_responses,
 output wire dataset_item_req_valid,
 output wire dataset_item_req_ready,
 output wire [15:0] dataset_item_req_tag,
 output wire [15:0] dataset_item_req_epoch,
 output wire [63:0] dataset_item_req_item,
 output wire dataset_item_rsp_valid,
 output wire dataset_item_rsp_ready,
 output wire [15:0] dataset_item_rsp_tag,
 output wire [15:0] dataset_item_rsp_epoch,
 output wire [511:0] dataset_item_rsp_data,
 output wire dataset_item_rsp_error,
 output wire [2:0] dataset_item_rsp_error_stage,
 output wire [8:0] dataset_item_rsp_error_pc,
 output wire [3:0] dataset_item_rsp_completed_stages,
 output wire [12:0] dataset_item_rsp_retired,
 output wire [12:0] dataset_item_rsp_muls,
 output wire [63:0] dataset_item_rsp_cycles,
 output wire [63:0] dataset_item_rsp_core_cycles,
 output wire [1:0] dataset_item_session_phase,
 output wire [31:0] dataset_item_namespace,dataset_item_sessions_used,
 output wire [63:0] dataset_item_rsp_exec_cycles,
 output wire dataset_item_commit_valid,
 output wire [2:0] dataset_item_commit_program,
 output wire [8:0] dataset_item_commit_pc,
 output wire [7:0] dataset_item_commit_opcode,
 output wire [511:0] dataset_item_commit_r,
 output wire dataset_item_stage_valid,
 output wire [2:0] dataset_item_stage_program,
 output wire [21:0] dataset_item_stage_cache_index,
 output wire [511:0] dataset_item_stage_r,
 output wire [63:0] dataset_item_stage_selected,
 output wire [63:0] dataset_item_stage_program_cycles,
 output wire dataset_req_ready,
 output wire dataset_rsp_valid,
 output wire dataset_rsp_ready,
 output wire [31:0] dataset_rsp_tag,
 output wire [511:0] dataset_rsp_data,
 output wire dataset_rsp_error
);

 localparam integer ITEMS_PER_BATCH=PROGRAMS*ITERATIONS;
 wire active=!rst&&!cancel;
 wire core_req_ready,core_generation_exhausted,core_rsp_valid,core_error_valid;
 wire core_ds_req_valid,core_ds_req_ready,core_ds_prefetch_valid,core_ds_rsp_ready;
 wire [63:0] core_ds_req_addr,core_ds_prefetch_addr;
 wire [31:0] core_ds_req_tag;
 wire service_batch_ready,service_ds_req_ready,service_ds_rsp_valid,service_ds_rsp_error;
 wire [31:0] service_ds_rsp_tag;
 wire [511:0] service_ds_rsp_data;
 wire core_req_valid=req_valid&&(!HARDWARE_DATASET||service_batch_ready);
 wire service_batch_valid=HARDWARE_DATASET&&req_valid&&core_req_ready;
 wire selected_ds_rsp_valid=HARDWARE_DATASET?service_ds_rsp_valid:ds_rsp_valid;
 wire [31:0] selected_ds_rsp_tag=HARDWARE_DATASET?service_ds_rsp_tag:ds_rsp_tag;
 wire [511:0] selected_ds_rsp_data=HARDWARE_DATASET?service_ds_rsp_data:ds_rsp_data;
 wire selected_ds_rsp_error=HARDWARE_DATASET?service_ds_rsp_error:ds_rsp_error;
 // Mirror precisely the primary's cancel-retained acceptance counter. Its
 // per-request generation_q is not suitable: that context clears on cancel.
 reg [15:0] hash_generation_counter_q;
 always @(posedge clk)begin
     if(rst)hash_generation_counter_q<=0;
     else if(req_valid&&req_ready)hash_generation_counter_q<=hash_generation_counter_q+16'd1;
 end
 assign req_ready=core_req_ready&&(!HARDWARE_DATASET||service_batch_ready);
 assign generation_exhausted=core_generation_exhausted||(HARDWARE_DATASET&&dataset_generation_exhausted);
 assign rsp_valid=core_rsp_valid;assign error_valid=core_error_valid;
 assign core_ds_req_ready=HARDWARE_DATASET?service_ds_req_ready:ds_req_ready;
 assign ds_req_valid=core_ds_req_valid;assign ds_req_addr=core_ds_req_addr;
 assign ds_req_tag=core_ds_req_tag;assign ds_prefetch_addr=core_ds_prefetch_addr;
 assign ds_prefetch_valid=core_ds_prefetch_valid;
 // Legacy requests are observations only in hardware mode. Removed software
 // replies drain without contributing any data, identity or error to the core.
 assign ds_rsp_ready=HARDWARE_DATASET?active:core_ds_rsp_ready;
 assign dataset_req_ready=core_ds_req_ready;
 assign dataset_rsp_valid=selected_ds_rsp_valid;
 assign dataset_rsp_ready=core_ds_rsp_ready;
 assign dataset_rsp_tag=selected_ds_rsp_tag;assign dataset_rsp_data=selected_ds_rsp_data;
 assign dataset_rsp_error=selected_ds_rsp_error;
 generate if(HARDWARE_DATASET!=0&&HARDWARE_DATASET!=1)begin: invalid_dataset_mode
     prepared_dataset_lifecycle_requires_HARDWARE_DATASET_0_or_1 invalid();
 end endgenerate

 randomx_prepared_hash_lifecycle #(
     .PROGRAMS(PROGRAMS),
     .ITERATIONS(ITERATIONS),
     .PREPARED_RCP(PREPARED_RCP),
     .SCRATCHPAD_BYTES(SCRATCHPAD_BYTES),
     .HARDWARE_FILL(HARDWARE_FILL),
     .HARDWARE_PROGRAM(HARDWARE_PROGRAM),
     .HARDWARE_INPUT_HASH(HARDWARE_INPUT_HASH)
 ) lifecycle(
     .clk(clk),
     .rst(rst),
     .cancel(cancel),
     .req_valid(core_req_valid),
     .req_ready(core_req_ready),
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
     .ds_rsp_error(selected_ds_rsp_error),
     .rsp_valid(core_rsp_valid),
     .rsp_ready(rsp_ready),
     .rsp_tag(rsp_tag),
     .rsp_r(rsp_r),
     .rsp_f(rsp_f),
     .rsp_e(rsp_e),
     .rsp_a(rsp_a),
     .rsp_round_mode(rsp_round_mode),
     .rsp_digest(rsp_digest),
     .rsp_error(rsp_error),
     .error_valid(core_error_valid),
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
     .generation_exhausted(core_generation_exhausted),
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
     .ds_req_valid(core_ds_req_valid),
     .ds_req_ready(core_ds_req_ready),
     .ds_req_addr(core_ds_req_addr),
     .ds_prefetch_addr(core_ds_prefetch_addr),
     .ds_req_tag(core_ds_req_tag),
     .ds_prefetch_valid(core_ds_prefetch_valid),
     .ds_rsp_valid(selected_ds_rsp_valid),
     .ds_rsp_ready(core_ds_rsp_ready),
     .ds_rsp_tag(selected_ds_rsp_tag),
     .ds_rsp_data(selected_ds_rsp_data),
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

 generate if(HARDWARE_DATASET)begin: hardware_dataset
     randomx_dataset_capacity_service #(.ITEMS_PER_BATCH(ITEMS_PER_BATCH),.MUL_RADIX4(DATASET_MUL_RADIX4),.SESSION_BITS(DATASET_SESSION_BITS)) service(
         .clk(clk),
         .rst(rst),
         .cancel(cancel||core_error_valid),
         .batch_valid(service_batch_valid),
         .batch_ready(service_batch_ready),
         .batch_end(core_rsp_valid&&rsp_ready&&!core_error_valid),
         .batch_generation(hash_generation_counter_q+16'd1),
         .image_epoch(req_dataset_epoch),
         .counts(req_dataset_counts),
         .address_regs(req_dataset_address_regs),
         .rcp_count(req_dataset_rcp_count),
         .ds_req_valid(core_ds_req_valid),
         .ds_req_ready(service_ds_req_ready),
         .ds_req_addr(core_ds_req_addr),
         .ds_req_tag(core_ds_req_tag),
         .ds_rsp_valid(service_ds_rsp_valid),
         .ds_rsp_ready(core_ds_rsp_ready),
         .ds_rsp_tag(service_ds_rsp_tag),
         .ds_rsp_data(service_ds_rsp_data),
         .ds_rsp_error(service_ds_rsp_error),
         .cache_req_valid(dataset_cache_req_valid),
         .cache_req_ready(dataset_cache_req_ready),
         .cache_req_tag(dataset_cache_req_tag),
         .cache_req_epoch(dataset_cache_req_epoch),
         .cache_req_program(dataset_cache_req_program),
         .cache_req_index(dataset_cache_req_index),
         .cache_rsp_valid(dataset_cache_rsp_valid),
         .cache_rsp_ready(dataset_cache_rsp_ready),
         .cache_rsp_tag(dataset_cache_rsp_tag),
         .cache_rsp_epoch(dataset_cache_rsp_epoch),
         .cache_rsp_program(dataset_cache_rsp_program),
         .cache_rsp_index(dataset_cache_rsp_index),
         .cache_rsp_data(dataset_cache_rsp_data),
         .cache_rsp_error(dataset_cache_rsp_error),
         .fetch_valid(dataset_fetch_valid),
         .fetch_ready(dataset_fetch_ready),
         .fetch_tag(dataset_fetch_tag),
         .fetch_epoch(dataset_fetch_epoch),
         .fetch_program(dataset_fetch_program),
         .fetch_pc(dataset_fetch_pc),
         .fetch_rsp_valid(dataset_fetch_rsp_valid),
         .fetch_rsp_ready(dataset_fetch_rsp_ready),
         .fetch_rsp_tag(dataset_fetch_rsp_tag),
         .fetch_rsp_epoch(dataset_fetch_rsp_epoch),
         .fetch_rsp_program(dataset_fetch_rsp_program),
         .fetch_rsp_pc(dataset_fetch_rsp_pc),
         .fetch_rsp_instruction(dataset_fetch_rsp_instruction),
         .fetch_rsp_error(dataset_fetch_rsp_error),
         .fetch_rsp_rcp_valid(dataset_fetch_rsp_rcp_valid),
         .fetch_rsp_rcp_index(dataset_fetch_rsp_rcp_index),
         .fetch_rsp_rcp_value(dataset_fetch_rsp_rcp_value),
         .phase(dataset_service_phase),
         .item_phase(dataset_item_phase),
         .generation_exhausted(dataset_generation_exhausted),
         .batch_active(dataset_batch_active),
         .items_reserved(dataset_items_reserved),
         .items_remaining(dataset_items_remaining),
         .items_requested(dataset_items_requested),
         .items_completed(dataset_items_completed),
         .ds_requests(dataset_ds_requests),
         .ds_responses(dataset_ds_responses),
         .item_req_valid(dataset_item_req_valid),
         .item_req_ready(dataset_item_req_ready),
         .item_req_tag(dataset_item_req_tag),
         .item_req_epoch(dataset_item_req_epoch),
         .item_req_item(dataset_item_req_item),
         .item_rsp_valid(dataset_item_rsp_valid),
         .item_rsp_ready(dataset_item_rsp_ready),
         .item_rsp_tag(dataset_item_rsp_tag),
         .item_rsp_epoch(dataset_item_rsp_epoch),
         .item_rsp_data(dataset_item_rsp_data),
         .item_rsp_error(dataset_item_rsp_error),
         .item_rsp_error_stage(dataset_item_rsp_error_stage),
         .item_rsp_error_pc(dataset_item_rsp_error_pc),
         .item_rsp_completed_stages(dataset_item_rsp_completed_stages),
         .item_rsp_retired(dataset_item_rsp_retired),
         .item_rsp_muls(dataset_item_rsp_muls),
         .item_rsp_cycles(dataset_item_rsp_cycles),
         .item_rsp_core_cycles(dataset_item_rsp_core_cycles),
         .item_session_phase(dataset_item_session_phase),
         .item_namespace(dataset_item_namespace),
         .item_sessions_used(dataset_item_sessions_used),
         .item_rsp_exec_cycles(dataset_item_rsp_exec_cycles),
         .item_commit_valid(dataset_item_commit_valid),
         .item_commit_program(dataset_item_commit_program),
         .item_commit_pc(dataset_item_commit_pc),
         .item_commit_opcode(dataset_item_commit_opcode),
         .item_commit_r(dataset_item_commit_r),
         .item_stage_valid(dataset_item_stage_valid),
         .item_stage_program(dataset_item_stage_program),
         .item_stage_cache_index(dataset_item_stage_cache_index),
         .item_stage_r(dataset_item_stage_r),
         .item_stage_selected(dataset_item_stage_selected),
         .item_stage_program_cycles(dataset_item_stage_program_cycles)
     );
 end else begin: legacy_dataset
     assign service_batch_ready=1'b1;
     assign service_ds_req_ready=1'b0;
     assign service_ds_rsp_valid=1'b0;assign service_ds_rsp_error=1'b0;
     assign service_ds_rsp_tag=32'b0;assign service_ds_rsp_data=512'b0;
     assign dataset_cache_req_valid='d0;
     assign dataset_cache_req_tag='d0;
     assign dataset_cache_req_epoch='d0;
     assign dataset_cache_req_program='d0;
     assign dataset_cache_req_index='d0;
     assign dataset_cache_rsp_ready='d0;
     assign dataset_fetch_valid='d0;
     assign dataset_fetch_tag='d0;
     assign dataset_fetch_epoch='d0;
     assign dataset_fetch_program='d0;
     assign dataset_fetch_pc='d0;
     assign dataset_fetch_rsp_ready='d0;
     assign dataset_service_phase='d0;
     assign dataset_item_phase='d0;
     assign dataset_generation_exhausted='d0;
     assign dataset_batch_active='d0;
     assign dataset_items_reserved='d0;
     assign dataset_items_remaining='d0;
     assign dataset_items_requested='d0;
     assign dataset_items_completed='d0;
     assign dataset_ds_requests='d0;
     assign dataset_ds_responses='d0;
     assign dataset_item_req_valid='d0;
     assign dataset_item_req_ready='d0;
     assign dataset_item_req_tag='d0;
     assign dataset_item_req_epoch='d0;
     assign dataset_item_req_item='d0;
     assign dataset_item_rsp_valid='d0;
     assign dataset_item_rsp_ready='d0;
     assign dataset_item_rsp_tag='d0;
     assign dataset_item_rsp_epoch='d0;
     assign dataset_item_rsp_data='d0;
     assign dataset_item_rsp_error='d0;
     assign dataset_item_rsp_error_stage='d0;
     assign dataset_item_rsp_error_pc='d0;
     assign dataset_item_rsp_completed_stages='d0;
     assign dataset_item_rsp_retired='d0;
     assign dataset_item_rsp_muls='d0;
     assign dataset_item_rsp_cycles='d0;
     assign dataset_item_rsp_core_cycles='d0;
     assign dataset_item_session_phase='d0;
     assign dataset_item_namespace='d0;
     assign dataset_item_sessions_used='d0;
     assign dataset_item_rsp_exec_cycles='d0;
     assign dataset_item_commit_valid='d0;
     assign dataset_item_commit_program='d0;
     assign dataset_item_commit_pc='d0;
     assign dataset_item_commit_opcode='d0;
     assign dataset_item_commit_r='d0;
     assign dataset_item_stage_valid='d0;
     assign dataset_item_stage_program='d0;
     assign dataset_item_stage_cache_index='d0;
     assign dataset_item_stage_r='d0;
     assign dataset_item_stage_selected='d0;
     assign dataset_item_stage_program_cycles='d0;
 end endgenerate
endmodule
`default_nettype wire
