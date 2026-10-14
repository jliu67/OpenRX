// SPDX-License-Identifier: BSD-3-Clause
// Native fixture values are assertion-only, except rf-in and the private input
// scratchpad. No expected AES state or digest drives a DUT request or response.
`timescale 1ns/1ps
module tb_scratchpad_finalization #(parameter integer SCRATCHPAD_BYTES=2097152);
 localparam integer BEATS=SCRATCHPAD_BYTES/16;
 localparam integer MAX_RUN_CYCLES=BEATS*30+256;
 reg clk=0,rst=1,req_valid=0,rsp_ready=0;
 always #5 clk=~clk;
 wire req_ready;
 reg [15:0] req_tag=0;
 reg [21:0] req_scratchpad_bytes=0;
 reg [1:0] req_round_mode=0;
 reg [511:0] req_r=0,req_f=0,req_e=0,req_a=0;
 wire sp_rd_valid;
 reg sp_rd_ready=0;
 wire [20:0] sp_rd_addr;
 wire [32:0] sp_rd_tag;
 reg sp_rsp_valid=0,sp_rsp_error=0;
 wire sp_rsp_ready;
 reg [127:0] sp_rsp_data=0;
 reg [32:0] sp_rsp_tag=0;
 wire rsp_valid,rsp_error;
 wire [15:0] rsp_tag;
 wire [1:0] rsp_round_mode;
 wire [511:0] rsp_r,rsp_f,rsp_e,rsp_a;
 wire [255:0] rsp_digest;
`ifdef SCRATCHPAD_FINALIZER_NETLIST
 randomx_scratchpad_finalizer dut(
`else
 randomx_scratchpad_finalizer #(.SCRATCHPAD_BYTES(SCRATCHPAD_BYTES)) dut(
`endif
  .clk(clk),.rst(rst),.req_valid(req_valid),.req_ready(req_ready),.req_tag(req_tag),
  .req_scratchpad_bytes(req_scratchpad_bytes),.req_round_mode(req_round_mode),
  .req_r(req_r),.req_f(req_f),.req_e(req_e),.req_a(req_a),
  .sp_rd_valid(sp_rd_valid),.sp_rd_ready(sp_rd_ready),.sp_rd_addr(sp_rd_addr),.sp_rd_tag(sp_rd_tag),
  .sp_rsp_valid(sp_rsp_valid),.sp_rsp_ready(sp_rsp_ready),.sp_rsp_data(sp_rsp_data),
  .sp_rsp_tag(sp_rsp_tag),.sp_rsp_error(sp_rsp_error),
  .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_tag(rsp_tag),.rsp_round_mode(rsp_round_mode),
  .rsp_r(rsp_r),.rsp_f(rsp_f),.rsp_e(rsp_e),.rsp_a(rsp_a),.rsp_digest(rsp_digest),.rsp_error(rsp_error)
 );

 reg [127:0] scratchpad[0:BEATS-1],original_scratchpad[0:BEATS-1];
 reg [2047:0] rf_input[0:0],rf_final[0:0];
 reg [511:0] expected_a[0:0],expected_digest64[0:0];
 reg [255:0] expected_digest32[0:0];
 string directory,path,mode="ideal";
 integer mode_id=0,round_argument=-1,restart_only=0;
 integer cycles=0,began=0,launches=0,completed=0,errors=0,resets=0;
 always @(posedge clk)cycles=cycles+1;
 integer run_reads=0,matched_reads=0,total_reads=0,total_matches=0;
 integer primary_reads=0,restart_reads=0,restarting=0,partial_restarts=0,native_success=0,verified_results=0;
 integer primary_response_latency=0,restart_response_latency=0;
 integer read_stalls=0,stall_cycles=0,stale_errors=0,held_reply_drops=0;
 integer pending=0,reply_delay=0,stale_phase=0,matching_error=0;
 integer transport_stall=0,inject_stale=0,inject_held_reply=0,error_index=-1;
 integer cancelled_reads=0,cancelled_matches=0,hash_wait_age=0;
 integer i,n;
 reg [15:0] active_tag=0,cancelled_generation=0;
 reg [1:0] active_round=0;
 reg [32:0] pending_tag=0,cancelled_reply_tag=0,last_read_tag=0;
 reg [127:0] pending_data=0;
 reg held_read=0,have_cancelled_generation=0;
 reg [53:0] saved_read;
 reg [2322:0] saved_result;
 wire [53:0] now_read={sp_rd_tag,sp_rd_addr};
 wire [2322:0] now_result={rsp_tag,rsp_round_mode,rsp_r,rsp_f,rsp_e,rsp_a,rsp_digest,rsp_error};

 task unchanged_memory;
  integer word_index;
  begin
   for(word_index=0;word_index<BEATS;word_index=word_index+1)
    if(scratchpad[word_index]!==original_scratchpad[word_index])
     $fatal(1,"private read-only scratchpad changed word=%0d",word_index);
  end
 endtask

 task launch;
  input [21:0] bytes;
  input [1:0] round_mode;
  begin
   @(negedge clk);
   if(!req_ready||rsp_valid||sp_rd_valid)$fatal(1,"new finalizer generation not idle");
   launches=launches+1;active_tag=16'h5100+launches;active_round=round_mode;
   if(have_cancelled_generation&&active_tag==cancelled_generation)$fatal(1,"cancelled generation reused");
   run_reads=0;matched_reads=0;pending=0;reply_delay=0;stale_phase=0;read_stalls=0;held_read=0;
   sp_rd_ready=0;sp_rsp_valid=0;sp_rsp_error=0;rsp_ready=0;inject_held_reply=0;
   req_tag=active_tag;req_scratchpad_bytes=bytes;req_round_mode=active_round;
   req_r=rf_input[0][511:0];req_f=rf_input[0][1023:512];
   req_e=rf_input[0][1535:1024];req_a=rf_input[0][2047:1536];req_valid=1;
   #1;if(!req_ready)$fatal(1,"request ready changed before capture");
   @(posedge clk);#1;began=cycles;req_valid=0;
   // Every descriptor field changes immediately after the capture edge.
   req_tag=~active_tag;req_scratchpad_bytes=~bytes;req_round_mode=~active_round;
   req_r=~req_r;req_f=~req_f;req_e=~req_e;req_a=~req_a;
   if(req_ready)$fatal(1,"accepted generation left descriptor ready");
  end
 endtask

 // One ordered read is outstanding. Request acceptance and a matching response
 // are separated by at least one clock even in ideal mode. Stalled mode adds
 // two held-request clocks and three-to-five clocks of memory latency per beat.
 // Wrong generation/index errors are deliberately delivered before real data.
 task step;
  reg read_taken,response_taken;
  begin
   @(negedge clk);
   sp_rd_ready=!pending&&(!transport_stall||read_stalls>=2);
   sp_rsp_valid=0;sp_rsp_error=0;
   if(pending)begin
    if(reply_delay>0)reply_delay=reply_delay-1;
    else begin
     sp_rsp_valid=1;sp_rsp_data=pending_data;sp_rsp_tag=pending_tag;
     sp_rsp_error=matching_error;
     if(stale_phase==1)begin
      sp_rsp_tag=have_cancelled_generation?cancelled_reply_tag:{active_tag^16'h8000,pending_tag[16:0]};
      sp_rsp_data=~pending_data;sp_rsp_error=1;
     end else if(stale_phase==2)begin
      sp_rsp_tag={active_tag,pending_tag[16:0]^17'h00001};
      sp_rsp_data=~pending_data;sp_rsp_error=1;
     end
    end
   end else if(inject_held_reply)begin
    sp_rsp_valid=1;sp_rsp_tag={active_tag^16'h8000,17'b0};sp_rsp_data=~128'b0;sp_rsp_error=1;
   end
   @(posedge clk);
   if(req_ready)$fatal(1,"busy/held finalizer accepted a second descriptor");
   if(held_read&&(!sp_rd_valid||now_read!==saved_read))$fatal(1,"held read address/tag changed");
   held_read=sp_rd_valid&&!sp_rd_ready;saved_read=now_read;
   if(sp_rd_valid&&!sp_rd_ready)begin read_stalls=read_stalls+1;stall_cycles=stall_cycles+1;end
   read_taken=sp_rd_valid&&sp_rd_ready;response_taken=sp_rsp_valid&&sp_rsp_ready;
   if(response_taken)begin
    if(!pending)begin
     if(!inject_held_reply)$fatal(1,"unexpected adapter response");
     held_reply_drops=held_reply_drops+1;
    end else if(stale_phase!=0)begin
     if(sp_rsp_tag===pending_tag)$fatal(1,"stale-error test reused matching identity");
     stale_errors=stale_errors+1;
     if(stale_phase==1)stale_phase=2;else stale_phase=0;
     reply_delay=1;
    end else begin
     if(sp_rsp_tag!==pending_tag)$fatal(1,"matching adapter response identity");
     pending=0;matched_reads=matched_reads+1;total_matches=total_matches+1;
    end
   end
   if(read_taken)begin
    if(pending||run_reads>=BEATS)$fatal(1,"overlapping/extra scratchpad read");
    if(sp_rd_addr!==run_reads*16||sp_rd_tag!=={active_tag,run_reads[16:0]})
     $fatal(1,"ordered address/tag disagreement beat=%0d addr=%h tag=%h",run_reads,sp_rd_addr,sp_rd_tag);
    if(sp_rd_addr[3:0]!==0)$fatal(1,"unaligned scratchpad beat");
    if(run_reads==BEATS-1&&sp_rd_addr!==(SCRATCHPAD_BYTES-16))$fatal(1,"last scratchpad beat");
    pending_data=scratchpad[run_reads];pending_tag=sp_rd_tag;last_read_tag=sp_rd_tag;pending=1;
    reply_delay=transport_stall?2+(run_reads%3):0;
    matching_error=run_reads==error_index;
    stale_phase=inject_stale?(run_reads==0?1:run_reads==BEATS-1?2:0):0;
    run_reads=run_reads+1;total_reads=total_reads+1;read_stalls=0;
    if(restarting)restart_reads=restart_reads+1;else primary_reads=primary_reads+1;
   end
   if(rsp_valid&&pending)$fatal(1,"response published with an unresolved memory read");
   #1;
   if(stale_phase!=0&&rsp_valid)$fatal(1,"stale read error committed a result");
   if(cycles-began>MAX_RUN_CYCLES)$fatal(1,"bounded finalizer timeout");
  end
 endtask

 task check_result;
  input expect_error;
  begin
   if(!rsp_valid||rsp_tag!==active_tag||rsp_round_mode!==active_round||rsp_error!==expect_error||
     {rsp_e,rsp_f,rsp_r}!==rf_input[0][1535:0])$fatal(1,"captured R/F/E/round/tag result");
   if(expect_error)begin
    if(rsp_a!==rf_input[0][2047:1536]||rsp_digest!==0)$fatal(1,"error committed A or digest");
   end else if({rsp_a,rsp_e,rsp_f,rsp_r}!==rf_final[0]||rsp_a!==expected_a[0]||
     rsp_digest!==expected_digest32[0]||rsp_digest===expected_digest64[0][255:0])
    $fatal(1,"native post-AES RegisterFile/digest32 mismatch");
  end
 endtask

 task wait_result;
  begin while(!rsp_valid)step;end
 endtask

 task hold_result;
  input expect_error;
  input integer expected_reads;
  begin
   wait_result;check_result(expect_error);verified_results=verified_results+1;
   if(restarting)restart_response_latency=cycles-began;
   else primary_response_latency=cycles-began;
   if(!expect_error)native_success=native_success+1;
   if(run_reads!=expected_reads||matched_reads!=expected_reads||pending)$fatal(1,"result read count");
   saved_result=now_result;
   // held mode adds an adversarial descriptor and old read-error traffic. All
   // modes hold the full atomic result for eight clocks before acknowledging it.
   if(mode_id==2)begin req_valid=1;inject_held_reply=1;end
   repeat(8)begin
    if(sp_rd_valid||req_ready)$fatal(1,"held result emitted another request");
    check_result(expect_error);if(now_result!==saved_result)$fatal(1,"held result changed");
    step;
   end
   check_result(expect_error);if(now_result!==saved_result)$fatal(1,"held result changed after eight clocks");
   unchanged_memory;
  end
 endtask

 task consume;
  begin
   @(negedge clk);req_valid=0;inject_held_reply=0;sp_rsp_valid=0;rsp_ready=1;
   @(posedge clk);if(!rsp_valid)$fatal(1,"result disappeared before consume");#1;rsp_ready=0;
   if(!req_ready||rsp_valid||sp_rd_valid)$fatal(1,"result consume did not restore idle");
   completed=completed+1;
   repeat(4)begin
    @(posedge clk);#1;
    if(!req_ready||rsp_valid||sp_rd_valid)$fatal(1,"late result after consume");
   end
  end
 endtask

 task cancel;
  begin
   cancelled_generation=active_tag;have_cancelled_generation=1;
   if(resets==0)begin cancelled_reads=run_reads;cancelled_matches=matched_reads;end
   if(pending)cancelled_reply_tag=pending_tag;
   else if(run_reads>0)cancelled_reply_tag=last_read_tag;
   else cancelled_reply_tag={active_tag,17'b0};
   @(negedge clk);rst=1;req_valid=0;rsp_ready=0;sp_rd_ready=0;
   sp_rsp_valid=1;sp_rsp_tag=cancelled_reply_tag;sp_rsp_data=~128'b0;sp_rsp_error=1;
   #1;if(req_ready||sp_rd_valid||rsp_valid)$fatal(1,"reset output suppression");
   repeat(2)begin @(posedge clk);#1;if(req_ready||sp_rd_valid||rsp_valid)$fatal(1,"held reset suppression");end
   @(negedge clk);rst=0;pending=0;held_read=0;inject_held_reply=0;
   // Keep the old response visible beyond either BLAKE2 compression interval.
   // A fresh generation below also receives this exact cancelled identity while
   // its first read is pending, followed by a wrong-index error and real data.
   repeat(80)begin
    @(posedge clk);#1;
    if(!req_ready||sp_rd_valid||rsp_valid)$fatal(1,"cancelled generation returned late");
   end
   @(negedge clk);sp_rsp_valid=0;sp_rsp_error=0;resets=resets+1;unchanged_memory;
  end
 endtask

 task good_restart;
  begin
   error_index=-1;inject_stale=1;restarting=1;
   launch(SCRATCHPAD_BYTES,(active_round+1)&2'b11);
   if(restart_only)begin
    // Explicit bounded default-gate contract: verify the new generation and
    // its first real matching beat after stale errors, then cancel it. This is
    // not a native AES/digest pass or a complete default mapped memory scan.
    while(matched_reads==0)step;
    if(run_reads!=1||matched_reads!=1||pending||rsp_valid||req_ready)$fatal(1,"partial fresh-generation restart");
    partial_restarts=partial_restarts+1;unchanged_memory;cancel;
   end else begin hold_result(0,BEATS);consume;end
  end
 endtask

 initial begin
  if(SCRATCHPAD_BYTES<64||SCRATCHPAD_BYTES>2097152||SCRATCHPAD_BYTES%64!=0)$fatal(1,"bench scratchpad parameter");
  if(!$value$plusargs("DIR=%s",directory))$fatal(1,"DIR fixture argument missing");
  if($value$plusargs("MODE=%s",mode))begin end
  if(mode=="ideal")mode_id=0;
  else if(mode=="stalled")mode_id=1;
  else if(mode=="held")mode_id=2;
  else if(mode=="invalid")mode_id=3;
  else if(mode=="error_first")mode_id=4;
  else if(mode=="error_last")mode_id=5;
  else if(mode=="reset_req")mode_id=6;
  else if(mode=="reset_read")mode_id=7;
  else if(mode=="reset_aes")mode_id=8;
  else if(mode=="reset_hash")mode_id=9;
  else if(mode=="reset_return")mode_id=10;
  else $fatal(1,"unknown finalization MODE=%s",mode);
  if($value$plusargs("RESTART_ONLY=%d",restart_only))begin
   if(restart_only!=0&&restart_only!=1)$fatal(1,"RESTART_ONLY must be 0 or 1");
   if(restart_only&&mode_id!=3&&mode_id!=4&&mode_id!=6&&mode_id!=7)$fatal(1,"partial restart mode not permitted");
  end
  if($value$plusargs("ROUND_MODE=%d",round_argument))begin
   if(round_argument<0||round_argument>3)$fatal(1,"ROUND_MODE must be 0..3");
  end else round_argument=mode_id%4;
  $sformat(path,"%0s/scratchpad.hex",directory);$readmemh(path,scratchpad);
  $sformat(path,"%0s/rf-in.hex",directory);$readmemh(path,rf_input);
  $sformat(path,"%0s/rf-final.hex",directory);$readmemh(path,rf_final);
  $sformat(path,"%0s/aes-hash.hex",directory);$readmemh(path,expected_a);
  $sformat(path,"%0s/digest32.hex",directory);$readmemh(path,expected_digest32);
  $sformat(path,"%0s/digest64.hex",directory);$readmemh(path,expected_digest64);
  if($isunknown({rf_input[0],rf_final[0],expected_a[0],expected_digest32[0],expected_digest64[0]}))$fatal(1,"incomplete native fixture");
  if(rf_final[0][1535:0]!==rf_input[0][1535:0]||rf_final[0][2047:1536]!==expected_a[0]||
    expected_digest32[0]===expected_digest64[0][255:0])$fatal(1,"native fixture contract");
  for(i=0;i<BEATS;i=i+1)begin
   if($isunknown(scratchpad[i]))$fatal(1,"incomplete scratchpad fixture word=%0d",i);
   original_scratchpad[i]=scratchpad[i];
  end
  repeat(2)begin @(posedge clk);#1;end
  @(negedge clk);rst=0;#1;if(!req_ready||rsp_valid||sp_rd_valid)$fatal(1,"initial idle");
  transport_stall=mode_id==1||mode_id==7;
  inject_stale=mode_id!=0;
  if(mode_id==3)begin
   // Each runtime length error is held with the original RegisterFile, then a
   // full valid request proves that the error descriptor cannot contaminate it.
   for(n=0;n<6;n=n+1)begin
    case(n)
     0:req_scratchpad_bytes=0;1:req_scratchpad_bytes=1;2:req_scratchpad_bytes=16;
     3:req_scratchpad_bytes=SCRATCHPAD_BYTES-64;4:req_scratchpad_bytes=SCRATCHPAD_BYTES+64;
     5:req_scratchpad_bytes=22'h3fffff;
    endcase
    launch(req_scratchpad_bytes,(round_argument+n)&2'b11);hold_result(1,0);consume;errors=errors+1;
   end
   good_restart;
  end else begin
   if(mode_id==4)error_index=0;else if(mode_id==5)error_index=BEATS-1;
   launch(SCRATCHPAD_BYTES,round_argument);
   if(mode_id==4||mode_id==5)begin
    hold_result(1,mode_id==4?1:BEATS);consume;errors=errors+1;good_restart;
   end else if(mode_id>=6)begin
    case(mode_id)
     6:begin end // accepted descriptor, before the scanner's first request
     7:begin while(run_reads==0)step;if(!pending||matched_reads!=0)$fatal(1,"pending-read reset setup");end
     8:begin while(matched_reads<4)step;if(rsp_valid)$fatal(1,"AES reset setup");end
     9:begin
      while(matched_reads<BEATS)step;
      // One final ROUND, four XKEY0 lanes, four XKEY1 lanes, return/capture
      // and hash request stages finish before this offset; native hash latency
      // is 56 clocks. No internal names or forced state enter mapped coverage.
      repeat(24)begin step;hash_wait_age=hash_wait_age+1;end
      if(rsp_valid||sp_rd_valid||pending)$fatal(1,"running-hash reset setup");
     end
     10:hold_result(0,BEATS);
    endcase
    cancel;good_restart;
   end else begin hold_result(0,BEATS);consume;end
  end
  unchanged_memory;
  if(restart_only)begin
   if(run_reads!=1||matched_reads!=1||partial_restarts!=1||native_success!=0)$fatal(1,"partial restart scope/count");
  end else if(run_reads!=BEATS||matched_reads!=BEATS||native_success==0)$fatal(1,"final successful run did not scan all memory");
  if(mode_id==0&&stale_errors!=0)$fatal(1,"ideal profile had injected stale traffic");
  if(mode_id!=0&&stale_errors<2)$fatal(1,"wrong generation/index stale errors not exercised");
  if(transport_stall&&stall_cycles<2)$fatal(1,"held read request not exercised");
  if(mode_id>=6&&resets!=1+partial_restarts)$fatal(1,"reset coverage count");
  if(mode_id==3&&errors!=6)$fatal(1,"runtime-length coverage count");
  if((mode_id==4||mode_id==5)&&errors!=1)$fatal(1,"matching memory-error coverage count");
  if(mode_id==0&&primary_response_latency!=3*BEATS+68)$fatal(1,"ideal component latency");
  $display("PASS scratchpad_finalization mode=%0s bytes=%0d reads=%0d primary_reads=%0d restart_reads=%0d native_success=%0d restart_only=%0d matched_beats=%0d total_matches=%0d completed=%0d errors=%0d resets=%0d cancelled_reads=%0d cancelled_matches=%0d hash_cancel_offset=%0d stale_errors=%0d request_stall_clocks=%0d held_reply_drops=%0d elapsed_cycles=%0d primary_response_latency=%0d restart_response_latency=%0d held_result_clocks=8 exact_addresses_tags=1 read_only_memory=1 native_RFE_round_preserved=%0d native_AES_A=%0d native_digest32_not_truncated64=%0d fresh_generation_restart=%0d",mode,SCRATCHPAD_BYTES,total_reads,primary_reads,restart_reads,native_success,restart_only,matched_reads,total_matches,completed,errors,resets,cancelled_reads,cancelled_matches,hash_wait_age,stale_errors,stall_cycles,held_reply_drops,cycles,primary_response_latency,restart_response_latency,verified_results!=0,native_success!=0,native_success!=0,restarting);
  $finish;
 end
 initial begin #2000000000;$fatal(1,"finalization bench deadlock");end
endmodule
