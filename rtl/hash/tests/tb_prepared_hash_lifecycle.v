// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_prepared_hash_lifecycle #(parameter integer PROGRAMS=8,ITERATIONS=2,PREPARED_RCP=1,STALL=0,CANCEL_PHASE=0,ERROR_PORT=0,CAPACITY_TEST=0,EVENT_TRACE=0,HARDWARE_FILL=0);
`ifdef VERILATOR
 import "DPI-C" function void rx_life_initial(input bit[639:0] value,input int length,input string filename,output bit[511:0] result);
 import "DPI-C" function void rx_life_input_hash(input bit[639:0] value,input int length,output bit[511:0] result);
 import "DPI-C" function void rx_generate(input bit[511:0] value,input string filename,output bit[1023:0] entropy);
 import "DPI-C" function void rx_next_seed(input bit[511:0] r,input bit[511:0] f,input bit[511:0] e,input bit[511:0] a,output bit[511:0] result);
 import "DPI-C" function void rx_dataset(input bit[63:0] address,output bit[511:0] result);
 import "DPI-C" function void rx_provider_stats(input string filename);
`define RX_INITIAL rx_life_initial
`define RX_INPUT_HASH rx_life_input_hash
`define RX_GENERATE rx_generate
`define RX_NEXT rx_next_seed
`define RX_DATASET rx_dataset
`define RX_STATS rx_provider_stats
`else
`define RX_INITIAL $rx_life_initial
`define RX_INPUT_HASH $rx_life_input_hash
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
 wire [1:0] init_fill_phase;
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
 always #5 clk=~clk;
 randomx_prepared_hash_lifecycle #(.PROGRAMS(PROGRAMS),.ITERATIONS(ITERATIONS),.PREPARED_RCP(PREPARED_RCP),.HARDWARE_FILL(HARDWARE_FILL)) dut(
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
 wire [31:0] done_mx=dut.chain_done_mx,done_ma=dut.chain_done_ma,done_spaddr0=dut.chain_done_spaddr0,done_spaddr1=dut.chain_done_spaddr1;
 wire [3:0] iteration_phase=dut.chain.iteration_chain.iteration.iteration.controller.phase_q;
 wire [4:0] execute_phase=dut.chain.iteration_chain.iteration.iteration.execute.state_q;
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
 integer ledger[0:9],iteration_detail[0:11],final_detail[0:5],exec_detail[0:17];
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
 integer seed_hashes=0;
 integer matching_fault_accepted=0;
 task check_capacity;begin
  req_valid=0;
  force dut.chain.iteration_chain.epoch_counter_q=65535-PROGRAMS;#1;
  if(generation_exhausted||!req_ready)$fatal(1,"exact remaining batch capacity was rejected");
  force dut.chain.iteration_chain.epoch_counter_q=65536-PROGRAMS;#1;
  if(!generation_exhausted||req_ready)$fatal(1,"insufficient batch capacity was accepted");
  req_valid=1;
  repeat(3)begin @(posedge clk);#1;
   if(init_req_valid||sp_wr_valid||meta_req_valid||dut.chain_start_valid)$fatal(1,"exhausted batch emitted work");
   @(negedge clk);
  end
  req_valid=0;release dut.chain.iteration_chain.epoch_counter_q;
  // No transports were admitted; a hard reset can now restart the namespaces.
  rst=1;@(posedge clk);#1;@(negedge clk);rst=0;#1;
  if(generation_exhausted||!req_ready)$fatal(1,"drained reset did not clear capacity exhaustion");
  force dut.generation_counter_q=16'hffff;#1;
  if(!generation_exhausted||req_ready)$fatal(1,"hash generation wrap was accepted");
  req_valid=1;
  repeat(3)begin @(posedge clk);#1;if(init_req_valid||sp_wr_valid||meta_req_valid)$fatal(1,"exhausted hash emitted work");@(negedge clk);end
  req_valid=0;release dut.generation_counter_q;
  rst=1;@(posedge clk);#1;@(negedge clk);rst=0;#1;
  if(generation_exhausted||!req_ready)$fatal(1,"drained reset did not clear hash exhaustion");
  req_valid=1;req_tag=16'h9001;req_input=input_value;req_input_bytes=input_bytes;
  @(posedge clk);#1;@(negedge clk);req_valid=0;
  if(!init_req_valid||init_req_tag!==16'd1)$fatal(1,"reset did not restart fresh initialization");
  $display("PASS lifecycle_capacity programs=%0d exact_capacity_allowed=1 insufficient_batch_refused=1 hash_wrap_refused=1 drained_reset_recovery=1",PROGRAMS);
  $finish;
 end endtask
 wire prep_rcp_fire;
 generate if(PREPARED_RCP)begin: observed_prepared
  assign prep_rcp_fire=dut.chain.iteration_chain.iteration.cache.prepared.reciprocal.req_valid&&dut.chain.iteration_chain.iteration.cache.prepared.reciprocal.req_ready;
 end else begin: observed_baseline
  assign prep_rcp_fire=0;
 end endgenerate
 integer preparation_reciprocals=0,runtime_reciprocals=0,final_native_completions=0;
 integer stall_sp_requests=0,stall_sp_writes=0,stall_dataset_requests=0,stall_program_loads=0;
 integer waiting_sp_replies=0,waiting_dataset_replies=0,waiting_program_replies=0;
 task cancel_and_restart;begin
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
   @(negedge clk);
  end
  meta_rsp_valid=0;sp_rsp_valid=0;prog_rsp_valid=0;ds_rsp_valid=0;
  for(i=0;i<131072;i=i+1)if(ram[i]!==cancel_ram[i])$fatal(1,"cancel rolled back accepted writes");
  restart_input=input_value^640'd1;restart_bytes=input_bytes?input_bytes:1;
  req_valid=1;req_tag=16'h9001;
  req_input=HARDWARE_FILL&&CANCEL_PHASE==1?restart_input:input_value;
  req_input_bytes=HARDWARE_FILL&&CANCEL_PHASE==1?restart_bytes:input_bytes;
  @(posedge clk);#1;@(negedge clk);req_valid=0;
  if(!init_req_valid||init_req_tag!==batch_tag+1||meta_req_valid||sp_wr_valid)$fatal(1,"fresh generation after cancel");
  if(HARDWARE_FILL&&CANCEL_PHASE==1)begin
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
   while(!meta_req_valid)begin
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
  if(!init_req_valid||init_req_tag!==batch_tag+1||meta_req_valid||sp_wr_valid)$fatal(1,"fresh generation after matching error");
  $display("PASS lifecycle_matching_error port=%0d selected_fault_accepted=1 expected_code_matched=1 held_error=1 late_replies_drained=1 accepted_writes_persist=1 fresh_initialization_required=1",ERROR_PORT);
  $finish;
 end endtask
 initial begin #2000000000;$fatal(1,"sequence simulation deadlock");end
 initial begin
  if(!$value$plusargs("directory=%s",directory)||!$value$plusargs("output=%s",output_directory)||
     !$value$plusargs("input=%h",input_value)||!$value$plusargs("input_bytes=%d",input_bytes))$fatal(1,"profile arguments missing");
  for(i=0;i<10;i=i+1)ledger[i]=0;for(i=0;i<12;i=i+1)iteration_detail[i]=0;
  for(i=0;i<6;i=i+1)final_detail[i]=0;for(i=0;i<18;i=i+1)exec_detail[i]=0;
  for(i=0;i<3;i=i+1)fill_detail[i]=0;
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
  if(CAPACITY_TEST)check_capacity();
  req_valid=1;req_tag=16'h4000;req_input=input_value;req_input_bytes=ERROR_PORT==7?7'd81:input_bytes;#1;
  if(!req_ready)$fatal(1,"hash not ready");@(posedge clk);
  if(ERROR_PORT==7&&req_valid&&req_ready&&req_input_bytes==81)matching_fault_accepted=1;
  #1;@(negedge clk);req_valid=0;
  while(!accepted_done)begin
   // Only actual provider/DUT state drives these inputs; gold is assertion-only.
   req_tag=~req_tag;req_input=~req_input;req_input_bytes=~req_input_bytes;
   init_req_ready=!initializing;
   if(HARDWARE_FILL&&init_req_valid&&init_req_ready)begin
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
   if(HARDWARE_FILL&&STALL&&phase==1&&init_input_hash_calls&& !init_request_seed_pending&&init_write_drops==0)begin init_wr_valid=1;init_wr_tag=batch_tag-1;init_wr_strb=0;end
   init_rsp_valid=HARDWARE_FILL?(initializing||init_request_seed_pending):(initializing&&initial_index==131072);
   init_rsp_tag=init_generation;init_rsp_seed=seed;
   init_rsp_error=ERROR_PORT==1;
   if(ERROR_PORT==1&&!HARDWARE_FILL&&initializing&&initial_index>=3)begin init_wr_valid=0;init_rsp_valid=1;end
   if(HARDWARE_FILL&&STALL&&phase==1&&init_input_hash_calls&&!init_request_seed_pending&&init_response_drops<2)begin
    init_rsp_valid=1;init_rsp_tag=batch_tag-1;init_rsp_seed=~seed;init_rsp_error=1;
   end
   meta_req_ready=!meta_pending&&(!STALL||meta_stalls>=2);
   if(meta_delay>0)meta_delay=meta_delay-1;
   meta_rsp_valid=meta_pending&&meta_delay==0;meta_rsp_tag=meta_tag;meta_rsp_program=meta_program;
   meta_rsp_entropy=native_entropy;meta_rsp_program_addr=64'h10000000+active_program*4096;meta_rsp_error=0;
   if(STALL&&meta_rsp_valid&&meta_injected<2)begin
    if(meta_injected==0)meta_rsp_tag=batch_tag-1;else meta_rsp_program=meta_program-1;
    meta_rsp_entropy=~native_entropy;meta_rsp_error=1;
   end
   if(ERROR_PORT==2&&meta_rsp_valid&&meta_injected>=2)meta_rsp_error=1;
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
   prog_rsp_valid=rom_pending&&rom_delay==0;prog_rsp_tag=rom_tag;prog_rsp_instruction=rom_data;prog_rsp_error=0;
   if(STALL&&prog_rsp_valid&&rom_injected<2)begin
    prog_rsp_tag=rom_injected==0?rom_tag^(41'b1<<25):rom_tag^(41'b1<<9);
    prog_rsp_instruction=~rom_data;prog_rsp_error=1;
   end
   if(ERROR_PORT==3&&prog_rsp_valid&&rom_injected>=2)prog_rsp_error=1;
   ds_req_ready=!ds_pending&&(!STALL||ds_stalls>=2);
   if(ds_delay>0)ds_delay=ds_delay-1;
   ds_rsp_valid=ds_pending&&ds_delay==0;ds_rsp_tag=ds_tag;ds_rsp_data=ds_data;ds_rsp_error=0;
   if(STALL&&ds_rsp_valid&&ds_injected<2)begin
    ds_rsp_tag=ds_injected==0?ds_tag^(32'b1<<16):ds_tag^32'b1;
    ds_rsp_data=~ds_data;ds_rsp_error=1;
   end
   if(ERROR_PORT==5&&ds_rsp_valid&&ds_injected>=2)ds_rsp_error=1;
   program_done_ready=!(CANCEL_PHASE==4)&&(!STALL||program_hold>=3);rsp_ready=!ERROR_PORT&&!(CANCEL_PHASE==6)&&(!STALL||done_hold>=3);
   @(posedge clk);
   if((ERROR_PORT==1&&phase==1&&init_rsp_valid&&init_rsp_ready&&init_rsp_tag==batch_tag&&init_rsp_error)||
      (ERROR_PORT==2&&meta_pending&&meta_rsp_valid&&meta_rsp_ready&&meta_rsp_tag==meta_tag&&meta_rsp_program==meta_program&&meta_rsp_error)||
      (ERROR_PORT==3&&rom_pending&&prog_rsp_valid&&prog_rsp_ready&&prog_rsp_tag==rom_tag&&prog_rsp_error)||
      (ERROR_PORT==4&&sp_pending&&sp_rsp_valid&&sp_rsp_ready&&sp_rsp_tag==sp_tag&&sp_tag[34:33]==1&&sp_rsp_error)||
      (ERROR_PORT==5&&ds_pending&&ds_rsp_valid&&ds_rsp_ready&&ds_rsp_tag==ds_tag&&ds_rsp_error)||
      (ERROR_PORT==6&&sp_pending&&sp_rsp_valid&&sp_rsp_ready&&sp_rsp_tag==sp_tag&&sp_tag[34:33]==2&&sp_rsp_error)||
      (ERROR_PORT==8&&phase==1&&init_wr_valid&&init_wr_ready&&init_wr_tag==batch_tag&&init_wr_strb!=16'hffff))
    matching_fault_accepted=matching_fault_accepted+1;
   if(phase<1||phase>9||(^phase)===1'bx)$fatal(1,"invalid outer ledger phase");
   ledger[phase]=ledger[phase]+1;
   if(HARDWARE_FILL&&phase==1)begin
    if(dut.state_q==9||dut.state_q==10)begin
     if(init_fill_phase>2||(^init_fill_phase)===1'bx)$fatal(1,"initial fill phase");
     fill_detail[init_fill_phase]=fill_detail[init_fill_phase]+1;
    end else init_provider_wait=init_provider_wait+1;
   end
   if(sp_rd_valid&&!sp_rd_ready)stall_sp_requests=stall_sp_requests+1;
   if(sp_wr_valid&&!sp_wr_ready)stall_sp_writes=stall_sp_writes+1;
   if(ds_req_valid&&!ds_req_ready)stall_dataset_requests=stall_dataset_requests+1;
   if(prog_valid&&!prog_ready)stall_program_loads=stall_program_loads+1;
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
   if(phase==6)begin final_phase_index=dut.finalizer.state_q;if(final_phase_index>5)$fatal(1,"finalizer phase");final_detail[final_phase_index]=final_detail[final_phase_index]+1;end
   if(prep_rcp_fire)preparation_reciprocals=preparation_reciprocals+1;
   if(dut.chain.iteration_chain.iteration.iteration.execute.reciprocal.req_valid&&dut.chain.iteration_chain.iteration.iteration.execute.reciprocal.req_ready)runtime_reciprocals=runtime_reciprocals+1;
   if(!EVENT_TRACE||phase!=last_trace_phase||iteration_phase!=last_trace_iteration||execute_phase!=last_trace_execute||commit_valid||sp_rd_valid&&sp_rd_ready||sp_wr_valid&&sp_wr_ready||ds_req_valid&&ds_req_ready||prep_commit_valid||program_done_valid||rsp_valid)
    $fdisplay(trace_file,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0h,%0d,%0h,%0h,%0d,%0h",cycle,phase,iteration_phase,execute_phase,commit_valid,commit_pc,sp_rd_valid&&sp_rd_ready,sp_rd_addr,sp_wr_valid&&sp_wr_ready,sp_wr_addr,sp_wr_strb,ds_req_valid&&ds_req_ready,ds_req_addr);
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
    if(HARDWARE_FILL&&init_wr_tag!=batch_tag)init_write_drops=init_write_drops+1;
    else if(!HARDWARE_FILL)initial_index=initial_index+1;
   end
   if(init_rsp_valid&&init_rsp_ready)begin
    if(HARDWARE_FILL&&init_rsp_tag!=batch_tag)init_response_drops=init_response_drops+1;
    else begin
     if(HARDWARE_FILL&&init_request_seed_pending)begin
      if(dut.state_q!=2||{init_rsp_tag,init_rsp_seed,init_rsp_error}!==held_init_response)$fatal(1,"held input seed changed before acceptance");
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
    if(ERROR_PORT)matching_error_and_restart();
    else $fatal(1,"sequence returned error program=%0d code=%0d pc=%0d opcode=%0d",error_program,error_code,error_pc,error_opcode);
   end
   if(held_read&&(!sp_rd_valid||now_read!==saved_read))$fatal(1,"held SRAM read changed");
   if(held_write&&(!sp_wr_valid||now_write!==saved_write))$fatal(1,"held SRAM write changed");
   if(held_rom&&(!prog_valid||now_rom!==saved_rom))$fatal(1,"held instruction request changed");
   if(held_meta&&(!meta_req_valid||now_meta!==saved_meta))$fatal(1,"held metadata request changed");
   if(held_ds&&(!ds_req_valid||now_ds!==saved_ds))$fatal(1,"held dataset request changed");
   if(held_program&&(!program_done_valid||now_program!==saved_program))$fatal(1,"held program result changed");
   if(held_done&&(!done_valid||now_done!==saved_done))$fatal(1,"held batch result changed");
   held_read=sp_rd_valid&&!sp_rd_ready;saved_read=now_read;
   held_write=sp_wr_valid&&!sp_wr_ready;saved_write=now_write;
   held_rom=prog_valid&&!prog_ready;saved_rom=now_rom;
   held_meta=meta_req_valid&&!meta_req_ready;saved_meta=now_meta;
   held_ds=ds_req_valid&&!ds_req_ready;saved_ds=now_ds;
   held_program=program_done_valid&&!program_done_ready;saved_program=now_program;
   held_done=done_valid&&!done_ready;saved_done=now_done;
   if(meta_req_valid&&!meta_req_ready)meta_stalls=meta_stalls+1;
   if(sp_rd_valid&&!sp_rd_ready)rd_stalls=rd_stalls+1;
   if(sp_wr_valid&&!sp_wr_ready)wr_stalls=wr_stalls+1;
   if(prog_valid&&!prog_ready)rom_stalls=rom_stalls+1;
   if(ds_req_valid&&!ds_req_ready)ds_stalls=ds_stalls+1;
   if(program_done_valid&&!program_done_ready)program_hold=program_hold+1;
   if(done_valid&&!done_ready)done_hold=done_hold+1;
   if(meta_rsp_valid&&meta_rsp_ready)begin
    if(meta_rsp_tag!=batch_tag||meta_rsp_program!=meta_program)begin meta_injected=meta_injected+1;meta_drops=meta_drops+1;end else meta_pending=0;
   end
   if(sp_rsp_valid&&sp_rsp_ready)begin
    if(sp_rsp_tag!=sp_tag)begin sp_injected=sp_injected+1;sp_drops=sp_drops+1;end else sp_pending=0;
   end
   if(prog_rsp_valid&&prog_rsp_ready)begin
    if(prog_rsp_tag!=rom_tag)begin rom_injected=rom_injected+1;rom_drops=rom_drops+1;end else rom_pending=0;
   end
   if(ds_rsp_valid&&ds_rsp_ready)begin
    if(ds_rsp_tag!=ds_tag)begin ds_injected=ds_injected+1;ds_drops=ds_drops+1;end else ds_pending=0;
   end
   if(meta_req_valid&&meta_req_ready)begin
    if(meta_req_tag!==batch_tag||meta_req_program!==programs_finished||meta_pending)$fatal(1,"program request order/tag");
    if(HARDWARE_FILL&&programs_finished==0&&(init_writes!=131072||meta_req_seed!==expected_seed))$fatal(1,"program0 escaped full hardware fill or postfill seed mismatch");
    active_program=meta_req_program;meta_tag=batch_tag;meta_program=meta_req_program;
    $sformat(path,"%0s/actual-program-%0d.mem",output_directory,active_program);`RX_GENERATE(meta_req_seed,path,native_entropy);$readmemh(path,rom);
    $sformat(path,"%0s/program-%0d.mem",directory,active_program);$readmemh(path,gold_rom);
    for(i=0;i<384;i=i+1)if(rom[i]!==gold_rom[i])$fatal(1,"actual generated instruction image mismatch");
    if(native_entropy!==gold_meta[active_program][1023:0])$fatal(1,"DUT-derived next-program entropy disagreement at program=%0d",active_program);
    meta_pending=1;meta_delay=STALL?3:1;meta_injected=0;meta_stalls=0;
   end
   if(prog_valid&&prog_ready)begin
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
   if(ds_req_valid&&ds_req_ready)begin
    if(ds_pending||dataset_taken||ds_req_tag!=={batch_tag,inner_tag}||ds_req_addr!==gold[global_iteration][2305:2242]||
      ds_prefetch_addr!==gold[global_iteration][2369:2306]||!ds_prefetch_valid)$fatal(1,"native dataset/control state");
    if(event_index!=gold[global_iteration][2497:2466]+gold[global_iteration][2529:2498])$fatal(1,"native bytecode event count");
    dataset_taken=1;`RX_DATASET(ds_req_addr,ds_data);ds_tag=ds_req_tag;ds_pending=1;ds_delay=STALL?3:1;ds_injected=0;ds_stalls=0;
   end
   if(sp_wr_valid&&sp_wr_ready)begin
    if(sp_wr_tag[50:35]!==batch_tag||sp_wr_addr[3:0]!=0)$fatal(1,"SRAM write generation/alignment");
    physical_write_bus_bytes=physical_write_bus_bytes+16;
    for(byte_index=0;byte_index<16;byte_index=byte_index+1)if(sp_wr_strb[byte_index])useful_write_bytes=useful_write_bytes+1;
    if(sp_wr_tag[34:33]==0)begin
     if(scratchpad_owner!==0||sp_wr_addr!==init_writes*16||sp_wr_strb!==16'hffff)$fatal(1,"exclusive initialization owner");
     if(HARDWARE_FILL&&(sp_wr_data!==gold_ram[init_writes]||sp_rd_valid||prog_valid||meta_req_valid||ds_req_valid))$fatal(1,"native hardware initial fill data or exclusive ownership");
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
    if(meta_req_valid||prog_valid||sp_rd_valid||sp_wr_valid||ds_req_valid)$fatal(1,"completed batch emitted requests");
    if(final_reads!=131072||init_writes!=131072||admissions!=PROGRAMS||loaded_words!=PROGRAMS*384)$fatal(1,"complete ownership/admission accounting");
    for(i=0;i<131072;i=i+1)if(ram[i]!==gold_ram[i])$fatal(1,"finalizer modified memory");
    $sformat(path,"%0s/actual-final-digest32.hex",output_directory);ledger_file=$fopen(path,"w");
    if(!ledger_file)$fatal(1,"actual digest output open");$fdisplay(ledger_file,"%064h",rsp_digest);$fclose(ledger_file);
    accepted_done=1;final_native_completions=final_native_completions+1;
   end
   if((CANCEL_PHASE==1&&init_writes==3)||(CANCEL_PHASE==2&&loaded_words==3)||
      (CANCEL_PHASE==3&&ds_pending)||(CANCEL_PHASE==4&&program_done_valid&&program_hold>=4)||
      (CANCEL_PHASE==5&&final_reads==3)||(CANCEL_PHASE==6&&rsp_valid))cancel_and_restart();
   #1;cycle=cycle+1;@(negedge clk);
  end
  if(seed_hashes!=PROGRAMS-1||event_index!=TOTAL_EVENTS||total_instructions!=TOTAL_INSTRUCTIONS||tail_writes!=8*TOTAL_ITERATIONS)$fatal(1,"sequence coverage accounting");
  for(i=0;i<10;i=i+1)stage_sum=stage_sum+ledger[i];
  if(stage_sum!=cycle)$fatal(1,"nonclosing outer cycle ledger");
  if(HARDWARE_FILL&&init_provider_wait+fill_detail[0]+fill_detail[1]+fill_detail[2]!=ledger[1])$fatal(1,"nonclosing initialization ledger");
  if(HARDWARE_FILL&&STALL&&(init_response_drops!=2||init_write_drops!=1))$fatal(1,"stale initialization coverage");
  if(HARDWARE_FILL&&(init_input_hash_calls!=1||init_same_cycle_offers!=1||init_same_cycle_accepts!=1||init_request_seed_pending))$fatal(1,"same-cycle initialization response coverage");
  stage_sum=0;for(i=0;i<12;i=i+1)stage_sum=stage_sum+iteration_detail[i];
  if(stage_sum!=ledger[4])$fatal(1,"nonclosing nested iteration ledger");
  stage_sum=0;for(i=0;i<6;i=i+1)stage_sum=stage_sum+final_detail[i];
  if(stage_sum!=ledger[6])$fatal(1,"nonclosing nested finalization ledger");
  stage_sum=0;for(i=0;i<18;i=i+1)stage_sum=stage_sum+exec_detail[i];
  if(stage_sum!=iteration_detail[7])$fatal(1,"nonclosing nested executor ledger");
  if(STALL&&(meta_drops!=2*PROGRAMS||rom_drops!=2*loaded_words||sp_drops!=2*reads||ds_drops!=2*TOTAL_ITERATIONS))$fatal(1,"stale error injection coverage");
  $fclose(trace_file);$sformat(path,"%0s/provider-host-time.json",output_directory);`RX_STATS(path);
  $sformat(path,"%0s/ledger.json",output_directory);ledger_file=$fopen(path,"w");if(!ledger_file)$fatal(1,"ledger write");
  if(HARDWARE_FILL)begin
   $fdisplay(ledger_file,"{\"cycles\":%0d,\"hardware_fill_enabled\":true,\"stage_cycles\":{\"initialization_hardware_fill\":%0d,\"control_and_metadata\":%0d,\"program_preparation\":%0d,\"execution\":%0d,\"interprogram_seed\":%0d,\"finalization\":%0d,\"held_return\":%0d},",cycle,ledger[1],ledger[2],ledger[3],ledger[4],ledger[5],ledger[6],ledger[8]);
   $fdisplay(ledger_file,"\"nested_initialization\":{\"provider_wait\":%0d,\"fill_phases\":[%0d,%0d,%0d]},",init_provider_wait,fill_detail[0],fill_detail[1],fill_detail[2]);
  end else $fdisplay(ledger_file,"{\"cycles\":%0d,\"hardware_fill_enabled\":false,\"stage_cycles\":{\"initialization_transport\":%0d,\"control_and_metadata\":%0d,\"program_preparation\":%0d,\"execution\":%0d,\"interprogram_seed\":%0d,\"finalization\":%0d,\"held_return\":%0d},",cycle,ledger[1],ledger[2],ledger[3],ledger[4],ledger[5],ledger[6],ledger[8]);
  $fdisplay(ledger_file,"\"nested_iteration_phases\":[%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d],\"nested_finalization_phases\":[%0d,%0d,%0d,%0d,%0d,%0d],",iteration_detail[0],iteration_detail[1],iteration_detail[2],iteration_detail[3],iteration_detail[4],iteration_detail[5],iteration_detail[6],iteration_detail[7],iteration_detail[8],iteration_detail[9],iteration_detail[10],iteration_detail[11],final_detail[0],final_detail[1],final_detail[2],final_detail[3],final_detail[4],final_detail[5]);
  $fdisplay(ledger_file,"\"nested_stalls\":{\"sp_request\":%0d,\"sp_write\":%0d,\"dataset_request\":%0d,\"program_load\":%0d},\"preparation_reciprocals\":%0d,\"runtime_reciprocals\":%0d,",stall_sp_requests,stall_sp_writes,stall_dataset_requests,stall_program_loads,preparation_reciprocals,runtime_reciprocals);
  $fdisplay(ledger_file,"\"nested_executor_phases\":[%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d],",exec_detail[0],exec_detail[1],exec_detail[2],exec_detail[3],exec_detail[4],exec_detail[5],exec_detail[6],exec_detail[7],exec_detail[8],exec_detail[9],exec_detail[10],exec_detail[11],exec_detail[12],exec_detail[13],exec_detail[14],exec_detail[15],exec_detail[16],exec_detail[17]);
  $fdisplay(ledger_file,"\"nested_reply_waits\":{\"scratchpad\":%0d,\"dataset\":%0d,\"program\":%0d},\"stale_error_replies_dropped\":{\"metadata\":%0d,\"program\":%0d,\"scratchpad\":%0d,\"dataset\":%0d},",waiting_sp_replies,waiting_dataset_replies,waiting_program_replies,meta_drops,rom_drops,sp_drops,ds_drops);
  $fdisplay(ledger_file,"\"scratchpad_bytes\":2097152,\"physical_port_read_bytes\":%0d,\"physical_port_write_bus_bytes\":%0d,\"strobed_write_bytes\":%0d,\"dataset_logical_bytes\":%0d,\"logical_bytecode_memory_bytes\":%0d,\"logical_entry_bytes\":%0d,\"logical_tail_bytes\":%0d,\"initialization_and_finalization_bytes_each\":2097152,\"program_image_load_bytes\":%0d,\"native_dataset_internal_physical_bytes\":null,\"untimed_provider_device_cycles\":null}",physical_read_bytes,physical_write_bus_bytes,useful_write_bytes,TOTAL_ITERATIONS*64,TOTAL_EVENTS*8,TOTAL_ITERATIONS*128,TOTAL_ITERATIONS*128,loaded_words*8);
  $fclose(ledger_file);
  $display("PASS prepared_hash_lifecycle prepared=%0d programs=%0d iterations_per_program=%0d stall=%0d total_iterations=%0d actual_instructions=%0d bytecode_events=%0d admissions=%0d loaded_words=%0d hardware_seeds=%0d initial_writes=%0d final_reads=%0d cycles=%0d native_digest32=1 native_actual_dataset=1 full_scratchpad_bytes=2097152 ledger_closes=1",PREPARED_RCP,PROGRAMS,ITERATIONS,STALL,global_iteration,total_instructions,event_index,admissions,loaded_words,seed_hashes,init_writes,final_reads,cycle);
  $finish;
 end
endmodule
