// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_program_hash_sequence #(parameter integer PROGRAMS=8,ITERATIONS=4,V2=1,STALL=0,RESET_PROGRAM=0,RESET_ITERATION=0);
 reg  clk=0;
 reg  rst=0;
 reg  start_valid=0;
 wire  start_ready;
 reg [15:0] start_tag=0;
 reg  start_v2=0;
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
 wire program_done_seed_valid;wire [511:0] program_done_seed;reg [511:0] native_expected_seed;integer seed_hashes=0;
 wire  done_valid;
 reg  done_ready=0;
 wire [15:0] done_tag;
 wire [511:0] done_r;
 wire [511:0] done_f;
 wire [511:0] done_e;
 wire [511:0] done_a;
 wire [1:0] done_round_mode;
 wire [31:0] done_mx;
 wire [31:0] done_ma;
 wire [31:0] done_spaddr0;
 wire [31:0] done_spaddr1;
 wire  error_valid;
 reg  error_ready=0;
 wire [15:0] error_tag;
 wire [2:0] error_program;
 wire [1:0] error_code;
 wire [8:0] error_pc;
 wire [7:0] error_opcode;
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
 wire [15:0] sp_rd_tag;
 reg  sp_rsp_valid=0;
 wire  sp_rsp_ready;
 reg [127:0] sp_rsp_data=0;
 reg [15:0] sp_rsp_tag=0;
 wire  sp_wr_valid;
 reg  sp_wr_ready=0;
 wire [20:0] sp_wr_addr;
 wire [127:0] sp_wr_data;
 wire [15:0] sp_wr_strb;
 wire [15:0] sp_wr_tag;
 wire  ds_req_valid;
 reg  ds_req_ready=0;
 wire [63:0] ds_req_addr;
 wire [63:0] ds_prefetch_addr;
 wire [15:0] ds_req_tag;
 wire  ds_prefetch_valid;
 reg  ds_rsp_valid=0;
 wire  ds_rsp_ready;
 reg [15:0] ds_rsp_tag=0;
 reg [511:0] ds_rsp_data=0;
 wire  prog_valid;
 reg  prog_ready=0;
 wire [63:0] prog_addr;
 wire [15:0] prog_tag;
 reg  prog_rsp_valid=0;
 wire  prog_rsp_ready;
 reg [15:0] prog_rsp_tag=0;
 reg [63:0] prog_rsp_instruction=0;
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
`ifdef PROGRAM_HASH_SEQUENCE_NETLIST
 randomx_program_hash_sequence dut(
`else
 randomx_program_hash_sequence #(.PROGRAMS(PROGRAMS),.ITERATIONS(ITERATIONS)) dut(
`endif
  .clk(clk),
  .rst(rst),
  .start_valid(start_valid),
  .start_ready(start_ready),
  .start_tag(start_tag),
  .start_v2(start_v2),
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
  .error_valid(error_valid),
  .error_ready(error_ready),
  .error_tag(error_tag),
  .error_program(error_program),
  .error_code(error_code),
  .error_pc(error_pc),
  .error_opcode(error_opcode),
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
`include "sequence_sizes.vh"
 reg [127:0] ram[0:131071],gold_ram[0:131071];
 reg [63:0] rom[0:383];reg [2529:0] gold[0:TOTAL_ITERATIONS-1];
 reg [1803:0] gold_meta[0:PROGRAMS-1];reg [85:0] events[0:TOTAL_EVENTS-1];
 reg [4095:0] directory,path;reg [511:0] seed;reg [1023:0] native_entropy;
 integer cycle=0,global_iteration=0,programs_finished=0,event_index=0,total_instructions=0;
 integer reads=0,writes=0,tail_writes=0,meta_drops=0,rom_drops=0,sp_drops=0,ds_drops=0;
 integer meta_pending=0,meta_delay=0,meta_injected=0,meta_stalls=0,active_program=0;
 integer sp_pending=0,sp_delay=0,sp_injected=0,rd_stalls=0,wr_stalls=0;
 integer rom_pending=0,rom_delay=0,rom_injected=0,rom_stalls=0;
 integer ds_pending=0,ds_delay=0,ds_injected=0,ds_stalls=0;
 integer kernel_started=0,dataset_taken=0,tail_index=0,steps=0,program_hold=0,done_hold=0;
 integer accepted_done=0,i,b,pc,entry_reads=0;
 reg [15:0] meta_tag,sp_tag,rom_tag,ds_tag,batch_tag,inner_tag;
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
 wire [4095:0] now_done={done_tag,done_round_mode,done_r,done_f,done_e,done_a,done_mx,done_ma,done_spaddr0,done_spaddr1};
 function [511:0] dataset_line;input [63:0] address;reg [63:0] x;integer n;begin
  x=address^64'hdabacafe13456789;
  for(n=0;n<8;n=n+1)begin x=x^(x<<13);x=x^(x>>7);x=x^(x<<17);dataset_line[64*n+:64]=x;end
 end endfunction
 task finish_cancel;input program_boundary;begin
    $sformat(path,"%0s/final-0.hex",directory);$readmemh(path,gold_ram);
    for(i=0;i<131072;i=i+1)if(ram[i]!==gold_ram[i])$fatal(1,"committed native memory before reset");
    #1;@(negedge clk);rst=1;#1;
    if(meta_req_valid||program_done_valid||done_valid||error_valid||iteration_commit_valid||commit_valid||
     sp_rd_valid||sp_wr_valid||prog_valid||ds_req_valid)$fatal(1,"held program reset suppression");
    @(posedge clk);#1;@(negedge clk);rst=0;
    meta_rsp_valid=1;meta_rsp_tag=batch_tag;meta_rsp_program=0;meta_rsp_entropy=~native_entropy;
    sp_rsp_valid=1;sp_rsp_tag=batch_tag;sp_rsp_data=~sp_data;
    prog_rsp_valid=1;prog_rsp_tag=batch_tag;prog_rsp_instruction=~rom_data;
    ds_rsp_valid=1;ds_rsp_tag=batch_tag;ds_rsp_data=~ds_data;
    repeat(3)begin
     @(posedge clk);#1;
     if(!start_ready||!meta_rsp_ready||!sp_rsp_ready||!prog_rsp_ready||!ds_rsp_ready||
      meta_req_valid||program_done_valid||iteration_commit_valid||commit_valid||sp_wr_valid||error_valid||done_valid)
      $fatal(1,"late responses after held program reset");
     @(negedge clk);
    end
    meta_rsp_valid=0;sp_rsp_valid=0;prog_rsp_valid=0;ds_rsp_valid=0;
    for(i=0;i<131072;i=i+1)if(ram[i]!==gold_ram[i])$fatal(1,"committed program memory after reset");
    start_valid=1;start_tag=16'hc000;start_v2=!V2;
    @(posedge clk);#1;@(negedge clk);start_valid=0;
    if(!meta_req_valid||meta_req_tag!==16'hc000||meta_req_program!==0)$fatal(1,"reset version/program restart");
    if(program_boundary)
     $display("PASS program_sequence_cancel v2=%0d native_iterations=%0d held_program_reset=1 late_meta_rom_sp_ds_drop=1 all_memory_bytes_preserved=2097152 version_restart=1",V2,global_iteration);
    else
     $display("PASS program_sequence_first_iteration v2=%0d native_iterations=1 full_register_round_memory_control=1 late_meta_rom_sp_ds_drop=1 all_memory_bytes_preserved=2097152 version_restart=1",V2);
    $finish;
  end endtask
 initial begin #2000000000;$fatal(1,"sequence simulation deadlock");end
 initial begin
  if(!$value$plusargs("directory=%s",directory))$fatal(1,"output directory missing");
  $sformat(path,"%0s/iterations.mem",directory);$readmemh(path,gold);
  $sformat(path,"%0s/metadata.mem",directory);$readmemh(path,gold_meta);
  $sformat(path,"%0s/events.mem",directory);$readmemh(path,events);
  // Preparation is performed independently by the native external provider.
  $sformat(path,"%0s/actual-initial.hex",directory);$rx_initial(path,seed);$readmemh(path,ram);
  $sformat(path,"%0s/initial.hex",directory);$readmemh(path,gold_ram);
  for(i=0;i<131072;i=i+1)if(ram[i]!==gold_ram[i])$fatal(1,"external initial memory disagreement");
  batch_tag=V2?16'h4000:16'h8000;inner_tag=batch_tag;
  rst=1;@(posedge clk);#1;@(negedge clk);rst=0;start_valid=1;start_tag=batch_tag;start_v2=V2;#1;
  if(!start_ready)$fatal(1,"batch not ready");@(posedge clk);#1;@(negedge clk);start_valid=0;
  while(!accepted_done)begin
   // Only actual provider/DUT state drives these inputs; gold is assertion-only.
   start_tag=~start_tag;start_v2=~start_v2;
   meta_req_ready=!meta_pending&&(!STALL||meta_stalls>=2);
   if(meta_delay>0)meta_delay=meta_delay-1;
   meta_rsp_valid=meta_pending&&meta_delay==0;meta_rsp_tag=meta_tag;meta_rsp_program=meta_program;
   meta_rsp_entropy=native_entropy;meta_rsp_program_addr=64'h10000000+active_program*4096;
   if(STALL&&meta_rsp_valid&&!meta_injected)begin meta_rsp_tag=batch_tag-1;meta_rsp_entropy=~native_entropy;end
   sp_rd_ready=!sp_pending&&(!STALL||rd_stalls>=2);sp_wr_ready=!STALL||wr_stalls>=2;
   if(sp_delay>0)sp_delay=sp_delay-1;
   sp_rsp_valid=sp_pending&&sp_delay==0;sp_rsp_tag=sp_tag;sp_rsp_data=sp_data;
   if(STALL&&sp_rsp_valid&&!sp_injected)begin sp_rsp_tag=sp_tag-1;sp_rsp_data=~sp_data;end
   prog_ready=!rom_pending&&(!STALL||rom_stalls>=2);
   if(rom_delay>0)rom_delay=rom_delay-1;
   prog_rsp_valid=rom_pending&&rom_delay==0;prog_rsp_tag=rom_tag;prog_rsp_instruction=rom_data;
   if(STALL&&prog_rsp_valid&&!rom_injected)begin prog_rsp_tag=rom_tag-1;prog_rsp_instruction=~rom_data;end
   ds_req_ready=!ds_pending&&(!STALL||ds_stalls>=2);
   if(ds_delay>0)ds_delay=ds_delay-1;
   ds_rsp_valid=ds_pending&&ds_delay==0;ds_rsp_tag=ds_tag;ds_rsp_data=ds_data;
   if(STALL&&ds_rsp_valid&&!ds_injected)begin ds_rsp_tag=ds_tag-1;ds_rsp_data=~ds_data;end
   program_done_ready=!RESET_PROGRAM&&(!STALL||program_hold>=3);done_ready=!STALL||done_hold>=3;
   @(posedge clk);
   if(error_valid)$fatal(1,"sequence returned error program=%0d code=%0d pc=%0d opcode=%0d",error_program,error_code,error_pc,error_opcode);
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
    if(meta_rsp_tag!=batch_tag)begin meta_injected=1;meta_drops=meta_drops+1;end else meta_pending=0;
   end
   if(sp_rsp_valid&&sp_rsp_ready)begin
    if(sp_rsp_tag!=inner_tag)begin sp_injected=1;sp_drops=sp_drops+1;end else sp_pending=0;
   end
   if(prog_rsp_valid&&prog_rsp_ready)begin
    if(prog_rsp_tag!=inner_tag)begin rom_injected=1;rom_drops=rom_drops+1;end else rom_pending=0;
   end
   if(ds_rsp_valid&&ds_rsp_ready)begin
    if(ds_rsp_tag!=inner_tag)begin ds_injected=1;ds_drops=ds_drops+1;end else ds_pending=0;
   end
   if(meta_req_valid&&meta_req_ready)begin
    if(meta_req_tag!==batch_tag||meta_req_program!==programs_finished||meta_pending)$fatal(1,"program request order/tag");
    active_program=meta_req_program;meta_tag=batch_tag;meta_program=meta_req_program;
    $sformat(path,"%0s/actual-program-%0d.mem",directory,active_program);$rx_generate(seed,path,native_entropy);$readmemh(path,rom);
    if(native_entropy!==gold_meta[active_program][1023:0])$fatal(1,"DUT-derived next-program entropy disagreement at program=%0d",active_program);
    meta_pending=1;meta_delay=STALL?3:1;meta_injected=0;meta_stalls=0;
   end
   if(prog_valid&&prog_ready)begin
    pc=(prog_addr-(64'h10000000+active_program*4096))>>3;
    if(rom_pending||prog_tag!==inner_tag||prog_addr[2:0]!=0||pc<0||pc>=(V2?384:256))$fatal(1,"instruction fetch/identity");
    if(!kernel_started)begin kernel_started=1;route=64'hcbf29ce484222325;steps=0;end
    rom_data=rom[pc];rom_tag=prog_tag;rom_pending=1;rom_delay=STALL?3:1;rom_injected=0;rom_stalls=0;
   end
   if(commit_valid)begin
    if(!kernel_started||commit_tag!==inner_tag)$fatal(1,"instruction retirement generation");
    word=({55'b0,commit_pc}<<17)|({56'b0,commit_opcode}<<9)|{55'b0,commit_next_pc};
    route=(route^word)*64'h100000001b3;steps=steps+1;total_instructions=total_instructions+1;
   end
   if(sp_rd_valid&&sp_rd_ready)begin
    if(sp_pending||sp_rd_tag!==inner_tag||sp_rd_addr[3:0]!=0)$fatal(1,"SRAM read protocol");
    sp_data=ram[sp_rd_addr>>4];sp_tag=sp_rd_tag;sp_pending=1;sp_delay=STALL?3:1;sp_injected=0;rd_stalls=0;reads=reads+1;
    if(kernel_started&&!dataset_taken)begin
     if(event_index>=gold[global_iteration][2497:2466]+gold[global_iteration][2529:2498]||events[event_index][85]||
      {events[event_index][84:68],4'b0}!==sp_rd_addr)$fatal(1,"native bytecode read address/order");
     expected_data=sp_data;if((events[event_index][67]?sp_data[127:64]:sp_data[63:0])!==events[event_index][63:0])$fatal(1,"native bytecode read data");
     event_index=event_index+1;
    end else entry_reads=entry_reads+1;
   end
   if(ds_req_valid&&ds_req_ready)begin
    if(ds_pending||dataset_taken||ds_req_tag!==inner_tag||ds_req_addr!==gold[global_iteration][2305:2242]||
      ds_prefetch_addr!==gold[global_iteration][2369:2306]||!ds_prefetch_valid)$fatal(1,"native dataset/control state");
    if(event_index!=gold[global_iteration][2497:2466]+gold[global_iteration][2529:2498])$fatal(1,"native bytecode event count");
    dataset_taken=1;ds_data=dataset_line(ds_req_addr);ds_tag=ds_req_tag;ds_pending=1;ds_delay=STALL?3:1;ds_injected=0;ds_stalls=0;
   end
   if(sp_wr_valid&&sp_wr_ready)begin
    if(sp_wr_tag!==inner_tag||sp_wr_addr[3:0]!=0)$fatal(1,"SRAM write generation/alignment");
    if(!dataset_taken)begin
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
   if(RESET_ITERATION&&global_iteration==1)finish_cancel(0);
   if(RESET_PROGRAM&&program_done_valid&&program_hold>=4)begin
    if(global_iteration!=ITERATIONS||program_done_index!==0||program_done_tag!==batch_tag||
     {program_done_a,program_done_e,program_done_f,program_done_r}!==gold[ITERATIONS-1][2047:0]||
     program_done_round_mode!==gold[ITERATIONS-1][2049:2048])$fatal(1,"native held program before reset");
    finish_cancel(1);
   end
   if(program_done_valid&&program_done_ready)begin
    i=program_done_index*ITERATIONS+ITERATIONS-1;
    if(program_done_tag!==batch_tag||program_done_index!==programs_finished||program_done_iterations!=ITERATIONS||
      {program_done_a,program_done_e,program_done_f,program_done_r}!==gold[i][2047:0]||program_done_round_mode!==gold[i][2049:2048])$fatal(1,"native program transition/state");
    $sformat(path,"%0s/final-%0d.hex",directory,programs_finished);$readmemh(path,gold_ram);
    for(i=0;i<131072;i=i+1)if(ram[i]!==gold_ram[i])$fatal(1,"native full scratchpad disagreement at program=%0d line=%0d",programs_finished,i);
    // Actual DUT output supplies the next seed; no oracle register ever feeds it.
    $rx_next_seed(program_done_r,program_done_f,program_done_e,program_done_a,native_expected_seed);
    if(program_done_index<PROGRAMS-1)begin
     if(!program_done_seed_valid||program_done_seed!==native_expected_seed)$fatal(1,"hardware/native register digest mismatch");
     seed=program_done_seed;seed_hashes=seed_hashes+1;
    end else if(program_done_seed_valid||program_done_seed!==0)$fatal(1,"eighth program incorrectly interprogram-hashed");
    programs_finished=programs_finished+1;program_hold=0;
   end
   if(done_valid&&done_ready)begin
    if(global_iteration!=TOTAL_ITERATIONS||programs_finished!=PROGRAMS||done_tag!==batch_tag||
      {done_a,done_e,done_f,done_r}!==gold[TOTAL_ITERATIONS-1][2047:0]||
      {done_spaddr1,done_spaddr0,done_ma,done_mx,done_round_mode}!==gold[TOTAL_ITERATIONS-1][2177:2048])$fatal(1,"batch completion/state");
    if(meta_req_valid||prog_valid||sp_rd_valid||sp_wr_valid||ds_req_valid)$fatal(1,"completed batch emitted requests");
    accepted_done=1;
   end
   #1;cycle=cycle+1;@(negedge clk);
  end
  if(seed_hashes!=PROGRAMS-1||event_index!=TOTAL_EVENTS||total_instructions!=TOTAL_INSTRUCTIONS||tail_writes!=8*TOTAL_ITERATIONS)$fatal(1,"sequence coverage accounting");
  $display("PASS program_hash_sequence hardware_seed_hashes=7 programs=%0d iterations_per_program=%0d v2=%0d stall=%0d total_iterations=%0d actual_instructions=%0d bytecode_events=%0d tail_writes=%0d full_memory_bytes=2097152 elapsed_cycles=%0d source_DUT_derived=1 native_register_round_memory_control=1 held_inactive=1 meta_stale=%0d rom_stale=%0d sp_stale=%0d ds_stale=%0d",PROGRAMS,ITERATIONS,V2,STALL,global_iteration,total_instructions,event_index,tail_writes,cycle,meta_drops,rom_drops,sp_drops,ds_drops);
  $finish;
 end
endmodule
