// SPDX-License-Identifier: BSD-3-Clause
// Raw immutable program words are DUT inputs. Native reciprocal plans are
// assertions for the cache and native input packets for the combinational guard.
`timescale 1ns/1ps
module tb_prepared_reciprocals #(parameter integer PREPARE_RCP=1,STALL=1);
 reg clk=0,rst=1,cancel=0;always #5 clk=~clk;
 reg prep_valid=0,prep_v2=0,prep_rsp_ready=0;
 wire prep_ready,prep_rsp_valid,prep_rsp_error,image_valid,image_v2;
 reg [15:0] prep_epoch=0;
 reg [63:0] prep_program_addr=0;
 wire [15:0] prep_rsp_epoch,image_epoch;
 wire [63:0] image_program_addr;
 wire load_req_valid,load_rsp_ready;reg load_req_ready=0,load_rsp_valid=0,load_rsp_error=0;
 wire [63:0] load_req_addr;wire [24:0] load_req_tag;
 reg [24:0] load_rsp_tag=0;reg [63:0] load_rsp_instruction=0;
 reg fetch_req_valid=0,fetch_rsp_ready=0;
 wire fetch_req_ready,fetch_rsp_valid,fetch_rsp_error,fetch_rsp_rcp_valid,fetch_rsp_rcp_nop;
 reg [8:0] fetch_req_pc=0;reg [15:0] fetch_req_tag=0,fetch_req_epoch=0;
 wire [8:0] fetch_rsp_pc;wire [15:0] fetch_rsp_tag,fetch_rsp_epoch;
 wire [63:0] fetch_rsp_instruction,fetch_rsp_rcp_value;wire [31:0] fetch_rsp_rcp_divisor;
`ifdef PROGRAM_RECIPROCALS_NETLIST
 randomx_program_reciprocals dut(
`else
 randomx_program_reciprocals #(.PREPARE_RCP(PREPARE_RCP)) dut(
`endif
  .clk(clk),.rst(rst),.cancel(cancel),.prep_valid(prep_valid),.prep_ready(prep_ready),
  .prep_epoch(prep_epoch),.prep_v2(prep_v2),.prep_program_addr(prep_program_addr),
  .load_req_valid(load_req_valid),.load_req_ready(load_req_ready),.load_req_addr(load_req_addr),.load_req_tag(load_req_tag),
  .load_rsp_valid(load_rsp_valid),.load_rsp_ready(load_rsp_ready),.load_rsp_tag(load_rsp_tag),
  .load_rsp_instruction(load_rsp_instruction),.load_rsp_error(load_rsp_error),
  .prep_rsp_valid(prep_rsp_valid),.prep_rsp_ready(prep_rsp_ready),.prep_rsp_epoch(prep_rsp_epoch),.prep_rsp_error(prep_rsp_error),
  .image_valid(image_valid),.image_epoch(image_epoch),.image_v2(image_v2),.image_program_addr(image_program_addr),
  .fetch_req_valid(fetch_req_valid),.fetch_req_ready(fetch_req_ready),.fetch_req_pc(fetch_req_pc),
  .fetch_req_tag(fetch_req_tag),.fetch_req_epoch(fetch_req_epoch),.fetch_rsp_valid(fetch_rsp_valid),.fetch_rsp_ready(fetch_rsp_ready),
  .fetch_rsp_tag(fetch_rsp_tag),.fetch_rsp_instruction(fetch_rsp_instruction),.fetch_rsp_epoch(fetch_rsp_epoch),.fetch_rsp_pc(fetch_rsp_pc),
  .fetch_rsp_rcp_valid(fetch_rsp_rcp_valid),.fetch_rsp_rcp_nop(fetch_rsp_rcp_nop),
  .fetch_rsp_rcp_divisor(fetch_rsp_rcp_divisor),.fetch_rsp_rcp_value(fetch_rsp_rcp_value),.fetch_rsp_error(fetch_rsp_error)
 );
 reg [15:0] guard_expected_epoch=0,guard_packet_epoch=0;
 reg [8:0] guard_expected_pc=0,guard_packet_pc=0;
 reg [63:0] guard_instruction=0,guard_packet_value=0;
 reg guard_packet_error=0,guard_packet_rcp_valid=0,guard_packet_nop=0;
 reg [31:0] guard_packet_divisor=0;wire guard_valid;wire [63:0] guard_value;
 randomx_prepared_rcp_guard guard(
  .expected_epoch(guard_expected_epoch),.packet_epoch(guard_packet_epoch),
  .expected_pc(guard_expected_pc),.packet_pc(guard_packet_pc),.instruction(guard_instruction),
  .packet_value(guard_packet_value),.packet_error(guard_packet_error),.packet_rcp_valid(guard_packet_rcp_valid),
  .packet_nop(guard_packet_nop),.packet_divisor(guard_packet_divisor),.valid(guard_valid),.value(guard_value)
 );
 reg [63:0] programs[0:1023];reg [97:0] native_plan[0:1023];string directory,path;
 integer cycles=0,serial=0,active_version=0,expected_words=0,run_reads=0,matched_reads=0;
 integer pending=0,delay=0,stale_phase=0,req_stalls=0,fail_pc=-1,began=0;
 integer total_loads=0,stale_errors=0,fetches=0,fetch_errors=0,preparations=0,prep_errors=0;
 integer resets=0,cancels=0,prep_cycles=0,native_packets=0,guard_rejections=0,cache_rcp=0,cache_nop=0;
 integer pc,version,word_index,first_active=-1,probe,n;
 reg [15:0] active_epoch=0,old_epoch=0;reg [63:0] active_addr=0,pending_word=0;
 reg [24:0] pending_tag=0,old_reply_tag=0,last_load_tag=0;
 reg held_load=0;reg [88:0] saved_load;
 reg [203:0] saved_fetch;
 wire [88:0] now_load={load_req_tag,load_req_addr};
 wire [203:0] now_fetch={fetch_rsp_tag,fetch_rsp_epoch,fetch_rsp_pc,fetch_rsp_instruction,
  fetch_rsp_rcp_valid,fetch_rsp_rcp_nop,fetch_rsp_rcp_divisor,fetch_rsp_rcp_value,fetch_rsp_error};
 always @(posedge clk)cycles=cycles+1;

 task begin_prep;input v2;begin
  @(negedge clk);if(!prep_ready||fetch_rsp_valid)$fatal(1,"prep reservation not idle");
  serial=serial+1;active_epoch=16'h6100+serial;active_version=v2;expected_words=v2?384:256;
  active_addr=64'h10000000+(v2?64'h2000:64'b0);
  run_reads=0;matched_reads=0;pending=0;delay=0;stale_phase=0;req_stalls=0;held_load=0;
  prep_epoch=active_epoch;prep_v2=v2;prep_program_addr=active_addr;prep_valid=1;
  prep_rsp_ready=0;load_req_ready=0;load_rsp_valid=0;fetch_req_valid=0;
  @(posedge clk);#1;began=cycles;prep_valid=0;
  prep_epoch=~active_epoch;prep_v2=~v2;prep_program_addr=~active_addr;
  if(image_valid||prep_ready||fetch_req_ready)$fatal(1,"prep capture did not invalidate old image/reserve fetch");
 end endtask

 task step;begin
  @(negedge clk);
  load_req_ready=!pending&&(!STALL||req_stalls>=2);load_rsp_valid=0;load_rsp_error=0;
  if(pending)begin
   if(delay>0)delay=delay-1;
   else begin
    load_rsp_valid=1;load_rsp_tag=pending_tag;load_rsp_instruction=pending_word;load_rsp_error=pending_tag[8:0]==fail_pc;
    if(stale_phase==1)begin load_rsp_tag=old_epoch!=0?old_reply_tag:{active_epoch^16'h8000,pending_tag[8:0]};load_rsp_instruction=~pending_word;load_rsp_error=1;end
    else if(stale_phase==2)begin load_rsp_tag={active_epoch,pending_tag[8:0]^9'd1};load_rsp_instruction=~pending_word;load_rsp_error=1;end
   end
  end
  @(posedge clk);
  if(held_load&&(!load_req_valid||now_load!==saved_load))$fatal(1,"held immutable load request changed");
  held_load=load_req_valid&&!load_req_ready;saved_load=now_load;
  if(load_req_valid&&!load_req_ready)req_stalls=req_stalls+1;
  if(load_rsp_valid&&load_rsp_ready)begin
   if(!pending)$fatal(1,"untracked load response");
   if(stale_phase!=0)begin
    if(load_rsp_tag===pending_tag)$fatal(1,"stale loader used matching identity");
    stale_errors=stale_errors+1;stale_phase=stale_phase==1?2:0;delay=1;
   end else begin pending=0;matched_reads=matched_reads+1;end
  end
  if(load_req_valid&&load_req_ready)begin
   if(pending||run_reads>=expected_words||load_req_addr!==active_addr+run_reads*8||load_req_tag!=={active_epoch,run_reads[8:0]})$fatal(1,"ordered immutable program load identity");
   pending=1;pending_tag=load_req_tag;last_load_tag=load_req_tag;
   pending_word=programs[active_version*512+run_reads];delay=STALL?2+(run_reads%2):0;
   stale_phase=run_reads==0?1:run_reads==expected_words-1?2:0;
   run_reads=run_reads+1;total_loads=total_loads+1;req_stalls=0;
  end
  #1;
  if(image_valid&&(run_reads!=expected_words||matched_reads!=expected_words||pending))$fatal(1,"partial program image became visible");
  if(!prep_rsp_valid&&fetch_req_ready)$fatal(1,"fetch accepted during preparation");
  if(cycles-began>100000)$fatal(1,"bounded preparation timeout");
 end endtask

 task finish_prep;input expect_error;begin
  while(!prep_rsp_valid)step;
  prep_cycles=prep_cycles+cycles-began;
  if(prep_rsp_epoch!==active_epoch||prep_rsp_error!==expect_error||image_valid===expect_error)$fatal(1,"held preparation result/image");
  if(!expect_error&&(run_reads!=expected_words||matched_reads!=expected_words||image_epoch!==active_epoch||image_v2!==active_version[0]||image_program_addr!==active_addr))$fatal(1,"complete immutable image metadata");
  if(expect_error&&(run_reads!=fail_pc+1||matched_reads!=fail_pc+1))$fatal(1,"load error count");
  repeat(4)begin
   @(negedge clk);fetch_req_valid=1;fetch_req_epoch=active_epoch;fetch_req_pc=0;
   #1;if(fetch_req_ready||prep_ready||load_req_valid||!prep_rsp_valid||prep_rsp_epoch!==active_epoch||prep_rsp_error!==expect_error)$fatal(1,"held prep result serialization");
   @(posedge clk);#1;
  end
  @(negedge clk);fetch_req_valid=0;load_rsp_valid=0;prep_rsp_ready=1;
  @(posedge clk);#1;prep_rsp_ready=0;
  if(!prep_ready||prep_rsp_valid)$fatal(1,"preparation result consume");
  preparations=preparations+1;if(expect_error)prep_errors=prep_errors+1;
 end endtask

 task fetch;input [15:0] epoch;input [8:0] index;input expect_error;input drop;reg [15:0] expected_epoch,tag;reg [97:0] expected;begin
  @(negedge clk);expected_epoch=image_epoch;tag=16'h9000+fetches;
  if(!fetch_req_ready)$fatal(1,"immutable lookup not ready");
  fetch_req_epoch=epoch;fetch_req_pc=index;fetch_req_tag=tag;fetch_req_valid=1;fetch_rsp_ready=0;
  @(posedge clk);#1;fetch_req_valid=0;fetch_req_epoch=~epoch;fetch_req_pc=~index;fetch_req_tag=~tag;
  if(!fetch_rsp_valid||fetch_rsp_tag!==tag||fetch_rsp_epoch!==expected_epoch||fetch_rsp_pc!==index||fetch_rsp_error!==expect_error)$fatal(1,"captured synchronous lookup response");
  expected=PREPARE_RCP?native_plan[active_version*512+index]:98'b0;
  if(expect_error)begin
   if(fetch_rsp_instruction!==0||{fetch_rsp_rcp_valid,fetch_rsp_rcp_nop,fetch_rsp_rcp_divisor,fetch_rsp_rcp_value}!==0)$fatal(1,"lookup error leaked image/metadata");
  end else begin
   if(fetch_rsp_instruction!==programs[active_version*512+index]||{fetch_rsp_rcp_valid,fetch_rsp_rcp_nop,fetch_rsp_rcp_divisor,fetch_rsp_rcp_value}!==expected)$fatal(1,"native immutable word/reciprocal plan mismatch pc=%0d",index);
   cache_rcp=cache_rcp+expected[97];cache_nop=cache_nop+expected[96];
  end
  saved_fetch=now_fetch;
  repeat(4)begin
   @(negedge clk);prep_valid=1;prep_epoch=16'hffff;prep_v2=~active_version[0];prep_program_addr=3;
   #1;if(prep_ready||!fetch_rsp_valid||now_fetch!==saved_fetch)$fatal(1,"held fetch changed or admitted replacement");
   @(posedge clk);#1;
  end
  @(negedge clk);prep_valid=0;
  if(drop)begin cancel=1;#1;if(fetch_rsp_valid||image_valid||prep_ready)$fatal(1,"cancel held fetch suppression");@(posedge clk);#1;@(negedge clk);cancel=0;cancels=cancels+1;end
  else begin fetch_rsp_ready=1;@(posedge clk);#1;fetch_rsp_ready=0;if(fetch_rsp_valid||!prep_ready)$fatal(1,"held lookup consume");end
  fetches=fetches+1;if(expect_error)fetch_errors=fetch_errors+1;
 end endtask

 task cancel_prep;input use_reset;begin
  old_epoch=active_epoch;old_reply_tag=pending?pending_tag:last_load_tag;
  if(run_reads==0)old_reply_tag={active_epoch,9'b0};
  @(negedge clk);if(use_reset)rst=1;else cancel=1;
  load_req_ready=0;load_rsp_valid=1;load_rsp_tag=old_reply_tag;load_rsp_instruction=~64'b0;load_rsp_error=1;
  #1;if(image_valid||load_req_valid||prep_rsp_valid||fetch_rsp_valid||prep_ready||fetch_req_ready)$fatal(1,"reset/cancel logical invalidation");
  repeat(2)begin @(posedge clk);#1;end
  @(negedge clk);rst=0;cancel=0;pending=0;held_load=0;
  repeat(80)begin @(posedge clk);#1;if(!prep_ready||image_valid||load_req_valid||prep_rsp_valid||fetch_rsp_valid||!load_rsp_ready)$fatal(1,"late canceled load/reciprocal result");end
  @(negedge clk);load_rsp_valid=0;if(use_reset)resets=resets+1;else cancels=cancels+1;
 end endtask

 task guard_native;input integer offset;input integer index;reg [97:0] packet;begin
  packet=native_plan[offset+index];guard_expected_epoch=16'h7123;guard_packet_epoch=guard_expected_epoch;
  guard_expected_pc=index;guard_packet_pc=index;guard_instruction=programs[offset+index];
  guard_packet_error=0;guard_packet_rcp_valid=packet[97];guard_packet_nop=packet[96];
  guard_packet_divisor=packet[95:64];guard_packet_value=packet[63:0];
  #1;if(guard_valid!==1'b1||guard_value!==packet[63:0])$fatal(1,"native guard packet");native_packets=native_packets+1;
  guard_packet_epoch=guard_packet_epoch^16'd1;#1;if(guard_valid!==1'b0)$fatal(1,"guard accepted wrong epoch");guard_rejections=guard_rejections+1;guard_packet_epoch=guard_expected_epoch;
  guard_packet_pc=guard_packet_pc^9'd1;#1;if(guard_valid!==1'b0)$fatal(1,"guard accepted wrong PC");guard_rejections=guard_rejections+1;guard_packet_pc=guard_expected_pc;
  guard_packet_error=1;#1;if(guard_valid!==1'b0)$fatal(1,"guard accepted packet error");guard_rejections=guard_rejections+1;guard_packet_error=0;
  guard_packet_rcp_valid=~packet[97];#1;if(guard_valid!==1'b0)$fatal(1,"guard accepted wrong opcode kind");guard_rejections=guard_rejections+1;guard_packet_rcp_valid=packet[97];
  guard_packet_divisor=packet[95:64]^32'd1;#1;if(guard_valid!==1'b0)$fatal(1,"guard accepted wrong unsigned divisor");guard_rejections=guard_rejections+1;guard_packet_divisor=packet[95:64];
  guard_packet_nop=~packet[96];#1;if(guard_valid!==1'b0)$fatal(1,"guard accepted wrong NOP flag");guard_rejections=guard_rejections+1;guard_packet_nop=packet[96];
  if(!packet[97]||packet[96])begin guard_packet_value=64'd1;#1;if(guard_valid!==1'b0)$fatal(1,"guard accepted forbidden NOP/non-RCP constant");guard_rejections=guard_rejections+1;guard_packet_value=packet[63:0];end
  #1;if(guard_valid!==1'b1)$fatal(1,"guard did not recover to native packet");
 end endtask

 initial begin
  if(!$value$plusargs("DIR=%s",directory))$fatal(1,"DIR missing");
  $sformat(path,"%0s/primitive-programs.mem",directory);$readmemh(path,programs);
  $sformat(path,"%0s/primitive-metadata.mem",directory);$readmemh(path,native_plan);
  for(version=0;version<2;version=version+1)for(pc=0;pc<(version?384:256);pc=pc+1)begin
   if((^programs[version*512+pc])===1'bx||(^native_plan[version*512+pc])===1'bx)$fatal(1,"missing primitive word/native metadata");
   guard_native(version*512,pc);
  end
  repeat(2)begin @(posedge clk);#1;end @(negedge clk);rst=0;#1;
  fetch(16'h1234,0,1,0);
  for(version=1;version>=0;version=version-1)begin
   fail_pc=-1;begin_prep(version);finish_prep(0);
   for(pc=0;pc<expected_words;pc=pc+1)fetch(active_epoch,pc,0,0);
   fetch(active_epoch^16'd1,0,1,0);fetch(active_epoch,expected_words,1,0);fetch(active_epoch,511,1,0);
  end
  // v1 replacement must make the former v2 tail inaccessible.
  fetch(active_epoch,300,1,0);
  fail_pc=0;begin_prep(1);finish_prep(1);fetch(active_epoch,0,1,0);
  fail_pc=255;begin_prep(0);finish_prep(1);fetch(active_epoch,0,1,0);fail_pc=-1;
  begin_prep(1);while(run_reads==0)step;cancel_prep(0);
  fetch(active_epoch,0,1,0);
  begin_prep(0);while(matched_reads==0)step;cancel_prep(1);
  // Identify the first active reciprocal by native assertion-only classification.
  first_active=-1;for(pc=0;pc<384;pc=pc+1)if(first_active<0&&native_plan[512+pc][97]&&!native_plan[512+pc][96])first_active=pc;
  if(first_active<0)$fatal(1,"primitive active reciprocal coverage missing");
  begin_prep(1);while(matched_reads<=first_active)step;
  if(PREPARE_RCP)begin repeat(8)step;if(load_req_valid||prep_rsp_valid)$fatal(1,"running reciprocal cancellation setup");end
  cancel_prep(0);
  begin_prep(1);finish_prep(0);fetch(active_epoch,first_active,0,1);
  fetch(active_epoch,first_active,1,0);
  begin_prep(0);while(!prep_rsp_valid)step;cancel_prep(0);
  fetch(active_epoch,0,1,0);
  begin_prep(1);finish_prep(0);
  for(pc=0;pc<384;pc=pc+1)fetch(active_epoch,pc,0,0);
  if(native_packets!=640||stale_errors<6||resets!=1||cancels!=4||prep_errors!=2)$fatal(1,"primitive control accounting");
  $display("PASS prepared_reciprocals prepare_rcp=%0d stall=%0d native_guard_packets=%0d guard_rejections=%0d preparations=%0d preparation_clocks=%0d load_reads=%0d fetches=%0d fetch_errors=%0d native_rcp_metadata=%0d native_nop_metadata=%0d stale_load_errors=%0d resets=%0d cancels=%0d held_load_fetch_prep=1 logical_image_invalidation=1 v2_to_v1_tail_invalid=1 unsigned_native_values=1",PREPARE_RCP,STALL,native_packets,guard_rejections,preparations,prep_cycles,total_loads,fetches,fetch_errors,cache_rcp,cache_nop,stale_errors,resets,cancels);
  $finish;
 end
 initial begin #20000000;$fatal(1,"prepared primitive deadlock");end
endmodule

// Real execute-core guard closure. Only a raw RCP NOP with zero metadata value
// is allowed to retire. The following malformed current-tag packet must reach
// held ERROR before any arithmetic or memory side effect. Poisoned active-RCP
// values below are invalid traffic; no expected active reciprocal drives a
// successful DUT execution.
module tb_prepared_rcp_core_guard;
 reg clk=0,rst=1,req_valid=0,prog_ready=0,prog_rsp_valid=0,error_ready=0;
 always #5 clk=~clk;
 wire req_ready,prog_valid,prog_rsp_ready,rd_valid,wr_valid,rsp_ready,ret_valid,error_valid,commit_valid;
 reg [15:0] req_tag=0,req_program_epoch=0,prog_rsp_tag=0,packet_epoch=0;
 reg [1:0] req_round_mode=0;reg [63:0] req_program_addr=0,prog_rsp_instruction=0;
 reg [511:0] req_r=0,req_f=0,req_e=0;
 reg [8:0] packet_pc=0;reg packet_error=0,packet_rcp_valid=0,packet_nop=0;
 reg [31:0] packet_divisor=0;reg [63:0] packet_value=0;
 wire [63:0] prog_addr;wire [15:0] prog_tag,mem_tag,ret_tag,error_tag,commit_tag;
 wire [20:0] rd_addr,wr_addr;wire [127:0] wr_data;wire [15:0] wr_strb;
 wire [511:0] ret_r,ret_f,ret_e,commit_r,commit_f,commit_e;
 wire [1:0] ret_round_mode,commit_round_mode;
 wire [8:0] error_pc,commit_pc,commit_next_pc,commit_branch_target;
 wire [7:0] error_opcode,commit_opcode;
 randomx_integer_execute #(.PREPARED_RCP(1)) dut(
  .clk(clk),.rst(rst),.req_valid(req_valid),.req_ready(req_ready),.req_tag(req_tag),.req_v2(1'b0),
  .req_round_mode(req_round_mode),.req_r(req_r),.req_f(req_f),.req_e(req_e),.req_a(512'b0),
  .req_emask0(64'b0),.req_emask1(64'b0),.req_program_addr(req_program_addr),.req_program_epoch(req_program_epoch),
  .prog_valid(prog_valid),.prog_ready(prog_ready),.prog_addr(prog_addr),.prog_tag(prog_tag),
  .prog_rsp_valid(prog_rsp_valid),.prog_rsp_ready(prog_rsp_ready),.prog_rsp_tag(prog_rsp_tag),.prog_rsp_instruction(prog_rsp_instruction),
  .prog_rsp_prepared_epoch(packet_epoch),.prog_rsp_prepared_pc(packet_pc),.prog_rsp_prepared_error(packet_error),
  .prog_rsp_rcp_valid(packet_rcp_valid),.prog_rsp_rcp_nop(packet_nop),.prog_rsp_rcp_divisor(packet_divisor),.prog_rsp_rcp_value(packet_value),
  .mem_tag(mem_tag),.rd_valid(rd_valid),.rd_ready(1'b0),.rd_addr(rd_addr),.rsp_valid(1'b0),.rsp_ready(rsp_ready),
  .rsp_tag(16'b0),.rsp_data(128'b0),.wr_valid(wr_valid),.wr_ready(1'b0),.wr_addr(wr_addr),.wr_data(wr_data),.wr_strb(wr_strb),
  .ret_valid(ret_valid),.ret_ready(1'b0),.ret_tag(ret_tag),.ret_r(ret_r),.ret_f(ret_f),.ret_e(ret_e),.ret_round_mode(ret_round_mode),
  .error_valid(error_valid),.error_ready(error_ready),.error_tag(error_tag),.error_pc(error_pc),.error_opcode(error_opcode),
  .commit_valid(commit_valid),.commit_tag(commit_tag),.commit_pc(commit_pc),.commit_opcode(commit_opcode),
  .commit_r(commit_r),.commit_f(commit_f),.commit_e(commit_e),.commit_round_mode(commit_round_mode),
  .commit_next_pc(commit_next_pc),.commit_branch_target(commit_branch_target)
 );
 integer cycles=0,test_index,commits=0,case_commits=0,stale_packets=0,held_errors=0,fetches=0,timeout=0;
 reg [15:0] active_tag,active_epoch;reg [63:0] active_program;
 reg [511:0] captured_r,captured_f,captured_e;reg [1:0] captured_mode;reg [7:0] rejected_opcode;
 always @(posedge clk)cycles=cycles+1;
 task observe;begin
  if(rd_valid||wr_valid||ret_valid||dut.reciprocal.req_valid||dut.multiplier.req_valid)$fatal(1,"rejected prepared packet reached execution/memory");
  if(commit_valid)begin
   if(case_commits!=0||commit_tag!==active_tag||commit_pc!==0||commit_opcode!==8'd76||commit_next_pc!==1||
      commit_branch_target!==9'h1ff||{commit_round_mode,commit_e,commit_f,commit_r}!=={captured_mode,captured_e,captured_f,captured_r})
     $fatal(1,"guard prefix must retire exact raw native RCP NOP");
   case_commits=case_commits+1;commits=commits+1;
  end
 end endtask
 task send_packet;input [8:0] pc;input malformed;begin
  timeout=0;
  while(!prog_valid)begin @(posedge clk);observe;#1;@(negedge clk);timeout=timeout+1;if(timeout>50)$fatal(1,"guard fetch timeout");end
  repeat(2)begin
   if(prog_addr!==active_program+pc*8||prog_tag!==active_tag||prog_ready||error_valid||req_ready)$fatal(1,"held guard fetch identity");
   @(posedge clk);observe;#1;@(negedge clk);
  end
  prog_ready=1;@(posedge clk);observe;fetches=fetches+1;#1;prog_ready=0;@(negedge clk);
  // Old transport identity must drain even when its metadata is poisoned.
  prog_rsp_valid=1;prog_rsp_tag=active_tag^16'h8000;prog_rsp_instruction=~64'b0;
  packet_epoch=~active_epoch;packet_pc=~pc;packet_error=1;packet_rcp_valid=0;packet_nop=0;packet_divisor=1;packet_value=1;
  #1;if(!prog_rsp_ready)$fatal(1,"old-tag guard packet not drainable");
  @(posedge clk);observe;stale_packets=stale_packets+1;#1;if(error_valid||prog_valid)$fatal(1,"old tag entered semantic guard");@(negedge clk);
  prog_rsp_tag=active_tag;packet_epoch=active_epoch;packet_pc=pc;packet_error=0;
  packet_rcp_valid=1;packet_nop=!malformed;packet_divisor=malformed?32'd3:32'b0;
  packet_value=malformed?64'hbad00feed00dcafe:64'b0;
  prog_rsp_instruction={packet_divisor,8'b0,8'hf8,8'hf8,8'd76};
  if(malformed)begin
   case(test_index)
    0:packet_epoch=active_epoch^16'd1;
    1:packet_pc=pc^9'd1;
    2:packet_divisor=32'h80000003;
    3:packet_nop=1;
    4:packet_rcp_valid=0;
    5:packet_error=1;
    6:begin prog_rsp_instruction={32'b0,8'b0,8'hf8,8'hf8,8'd76};packet_nop=1;packet_divisor=0;packet_value=1;end
    7:begin prog_rsp_instruction={32'b0,8'b0,8'hf8,8'hf8,8'd84};packet_nop=0;packet_divisor=0;packet_value=0;end
   endcase
   rejected_opcode=prog_rsp_instruction[7:0];
   if(case_commits!=1)$fatal(1,"guard packet did not follow a committed prefix");
  end
  #1;if(!prog_rsp_ready)$fatal(1,"current guard packet not accepted");
  @(posedge clk);observe;#1;prog_rsp_valid=0;
  if(malformed&&(!error_valid||commit_valid))$fatal(1,"malformed current packet did not fail before retirement");
  @(negedge clk);
 end endtask
 initial begin
  repeat(2)begin @(posedge clk);#1;end @(negedge clk);rst=0;
  for(test_index=0;test_index<8;test_index=test_index+1)begin
   active_tag=16'ha100+test_index;active_epoch=16'hb100+test_index;active_program=64'h20000000+test_index*4096;
   captured_r={8{64'h8000000000000001^test_index}};
   captured_f={64'h7ff0000000000000,64'hfff0000000000000,64'h8000000000000000,64'h0000000000000000,
               64'h7ff800000000cafe,64'h7ff0000000000001,64'h0000000000000001,64'hffffffffffffffff};
   captured_e=~captured_f;captured_mode=test_index%4;case_commits=0;
   req_tag=active_tag;req_program_epoch=active_epoch;req_program_addr=active_program;req_round_mode=captured_mode;
   req_r=captured_r;req_f=captured_f;req_e=captured_e;req_valid=1;
   if(!req_ready)$fatal(1,"guard core did not release previous held error");
   @(posedge clk);observe;#1;req_valid=0;req_tag=~active_tag;req_program_epoch=~active_epoch;req_program_addr=~active_program;
   req_round_mode=~captured_mode;req_r=~captured_r;req_f=~captured_f;req_e=~captured_e;@(negedge clk);
   send_packet(0,0);send_packet(1,1);
   repeat(4)begin
    if(!error_valid||error_tag!==active_tag||error_pc!==1||error_opcode!==rejected_opcode||req_ready||prog_valid||
       {ret_round_mode,ret_e,ret_f,ret_r}!=={captured_mode,captured_e,captured_f,captured_r})$fatal(1,"held metadata error changed committed register state");
    @(posedge clk);observe;held_errors=held_errors+1;#1;@(negedge clk);
   end
   if(case_commits!=1)$fatal(1,"rejected packet committed");
   error_ready=1;@(posedge clk);observe;#1;error_ready=0;
   if(error_valid||!req_ready)$fatal(1,"held metadata error consume");@(negedge clk);
  end
  if(commits!=8||fetches!=16||stale_packets!=16||held_errors!=32)$fatal(1,"core metadata guard coverage");
  $display("PASS prepared_rcp_core_guard contexts=8 prefix_native_nops=8 rejected_current_packets=8 wrong_epoch=1 wrong_pc=1 wrong_unsigned_divisor=1 wrong_nop=1 wrong_kind=2 packet_error=1 forbidden_nop_value=1 stale_transport_packets=16 held_error_clocks=32 no_rejected_commit_memory_or_reciprocal=1 raw_RFE_round_preserved=1 elapsed_cycles=%0d",cycles);
  $finish;
 end
 initial begin #1000000;$fatal(1,"prepared core guard deadlock");end
endmodule
