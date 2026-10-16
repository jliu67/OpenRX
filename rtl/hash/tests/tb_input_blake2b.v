// SPDX-License-Identifier: BSD-3-Clause
// Native expected digests are assertion-only. Test requests contain raw input.
`timescale 1ns/1ps
module tb_input_blake2b;
 reg clk=0,rst=1,cancel=0,req_valid=0,rsp_ready=0;
 always #5 clk=~clk;
 reg [15:0] req_tag=0;
 reg [639:0] req_input=0;
 reg [6:0] req_input_bytes=0;
 wire req_ready,rsp_valid,rsp_error;
 wire [15:0] rsp_tag;
 wire [511:0] rsp_seed;
 wire [1:0] phase;
 randomx_input_blake2b dut(
  .clk(clk),.rst(rst),.cancel(cancel),.req_valid(req_valid),.req_ready(req_ready),
  .req_tag(req_tag),.req_input(req_input),.req_input_bytes(req_input_bytes),
  .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_tag(rsp_tag),.rsp_seed(rsp_seed),.rsp_error(rsp_error),.phase(phase)
 );
 reg [639:0] queued_input=0;
 reg [6:0] queued_bytes=0;
 reg [511:0] queued_seed=0,active_seed=0;
 reg queued_error=0,active_error=0,active=0,held_response=0;
 reg [15:0] active_tag=0;
 reg [528:0] saved_response;
 wire [528:0] now_response={rsp_tag,rsp_seed,rsp_error};
 integer cycles=0,requests=0,completed=0,verified_digests=0,invalid_lengths=0;
 integer start_cycle=0,latency_min=1000,latency_max=0,valid_compute_cycles=0;
 integer held_response_cycles=0,held_request_cycles=0,aborts=0,target_age=-1;
 integer fd,scan,length0,length1,rows=0,count,i,old_requests,old_completed,errors_checked=0;
 reg [639:0] input0,input1;
 reg [511:0] digest0,digest1;
 string directory,vectors,path,mode="corpus";

 always @(posedge clk)begin
  cycles=cycles+1;
  if(rst||cancel)begin
   if(req_ready||rsp_valid||phase!==0)$fatal(1,"reset/cancel handshake gating");
   active=0;held_response=0;
  end else begin
   if(held_response&&(!rsp_valid||now_response!==saved_response))$fatal(1,"held digest/error changed");
   if(req_valid&&req_ready)begin
    if(active||phase!==0||req_input!==queued_input||req_input_bytes!==queued_bytes)$fatal(1,"request capture descriptor");
    requests=requests+1;active=1;active_tag=req_tag;active_seed=queued_seed;active_error=queued_error;start_cycle=cycles;
   end else if(req_valid&&!req_ready)held_request_cycles=held_request_cycles+1;
   if(phase==1&&(!active||active_error||req_ready||rsp_valid))$fatal(1,"core phase ownership");
   if(rsp_valid)begin
    if(!active||phase!==2||req_ready||rsp_tag!==active_tag||rsp_seed!==active_seed||rsp_error!==active_error)
     $fatal(1,"native seed/error/tag mismatch tag=%h expected=%h error=%b expected_error=%b",rsp_tag,active_tag,rsp_error,active_error);
    if(rsp_ready)begin completed=completed+1;active=0;end
    else held_response_cycles=held_response_cycles+1;
   end
   held_response=rsp_valid&&!rsp_ready;saved_response=now_response;
  end
 end

 task queue_descriptor;
  input integer bytes;
  input [639:0] value;
  input [511:0] expected;
  input error;
  begin queued_bytes=bytes;queued_input=value;queued_seed=expected;queued_error=error;end
 endtask

 task launch;
  input [15:0] tag;
  input integer bytes;
  input [639:0] value;
  input [511:0] expected;
  input error;
  begin
   @(negedge clk);queue_descriptor(bytes,value,expected,error);
   req_tag=tag;req_input=value;req_input_bytes=bytes;req_valid=1;rsp_ready=0;old_requests=requests;
   #1;if(!req_ready||rsp_valid||phase!==0)$fatal(1,"input hash not idle before request");
   @(posedge clk);#1;
   if(requests!=old_requests+1||req_ready)$fatal(1,"request capture count");
   req_valid=0;req_tag=~tag;req_input=~value;req_input_bytes=~bytes;
  end
 endtask

 task step;
  begin @(negedge clk);rsp_ready=0;@(posedge clk);#1;end
 endtask

 task await_result;
  integer began,latency;
  begin
   began=cycles;
   while(!rsp_valid)begin step();if(cycles-began>80)$fatal(1,"one-block hash timeout");end
   if(rsp_seed!==active_seed||rsp_error!==active_error||rsp_tag!==active_tag)$fatal(1,"completed result payload");
   latency=cycles-start_cycle;
   if(active_error)begin
    if(latency!=0||rsp_seed!==0)$fatal(1,"invalid input launched hash or nonzero result");
    invalid_lengths=invalid_lengths+1;
   end else begin
    if(latency<latency_min)latency_min=latency;
    if(latency>latency_max)latency_max=latency;
    valid_compute_cycles=valid_compute_cycles+latency;verified_digests=verified_digests+1;
   end
  end
 endtask

 task hold_result;
  integer age;
  begin
   for(age=0;age<5;age=age+1)begin step();if(!rsp_valid||req_ready)$fatal(1,"held result ownership");end
  end
 endtask

 task consume_result;
  begin
   @(negedge clk);rsp_ready=1;old_completed=completed;
   @(posedge clk);#1;
   if(completed!=old_completed+1||!req_ready||rsp_valid||phase!==0)$fatal(1,"result release");
   rsp_ready=0;
  end
 endtask

 task abort_and_release;
  input integer use_reset;
  begin
   old_requests=requests;old_completed=completed;
   @(negedge clk);rst=use_reset;cancel=!use_reset;req_valid=1;req_input=~input0;req_input_bytes=7'd127;rsp_ready=1;
   #1;if(req_ready||rsp_valid||phase!==0)$fatal(1,"abort combinational gating");
   @(posedge clk);#1;
   if(requests!=old_requests||completed!=old_completed||req_ready||rsp_valid)$fatal(1,"transfer accepted during abort");
   aborts=aborts+1;
   @(negedge clk);rst=0;cancel=0;req_valid=0;rsp_ready=0;
   @(posedge clk);#1;
   if(!req_ready||rsp_valid||phase!==0)$fatal(1,"abort restart idle");
   // A reset/cancelled core must not resurrect its old sticky digest.
   repeat(2)begin step();if(rsp_valid||!req_ready)$fatal(1,"stale core digest after abort");end
  end
 endtask

 initial begin
  if(!$value$plusargs("DIR=%s",directory))$fatal(1,"missing native fixture directory");
  i=$value$plusargs("MODE=%s",mode);
  if(!$value$plusargs("VECTORS=%s",vectors))vectors="vectors.hex";
  @(posedge clk);#1;@(negedge clk);rst=0;
  if(mode=="corpus")begin
   $sformat(path,"%0s/%0s",directory,vectors);fd=$fopen(path,"r");if(!fd)$fatal(1,"native vectors open");
   while(!$feof(fd))begin
    scan=$fscanf(fd,"%d %h %h\n",length0,input0,digest0);
    if(scan==3)begin
     if(length0<0||length0>80||^input0===1'bx||^digest0===1'bx)$fatal(1,"malformed native vector");
     launch(16'h8000+rows,length0,input0,digest0,0);await_result();consume_result();rows=rows+1;
    end else if(scan!=-1&&scan!=0)$fatal(1,"truncated native vector");
   end
   $fclose(fd);if(rows<1||verified_digests!=rows||requests!=rows||completed!=rows)$fatal(1,"native corpus count");
  end else begin
   $sformat(path,"%0s/control.hex",directory);fd=$fopen(path,"r");if(!fd)$fatal(1,"control vectors open");
   scan=$fscanf(fd,"%d %h %h\n",length0,input0,digest0);if(scan!=3)$fatal(1,"first native control vector");
   scan=$fscanf(fd,"%d %h %h\n",length1,input1,digest1);if(scan!=3)$fatal(1,"restart native control vector");$fclose(fd);
   if(length0!=80||length1!=0||input0===input1||digest0===digest1)$fatal(1,"changed-input control fixture");
   if(mode=="held_request")begin
    launch(16'h8101,length0,input0,digest0,0);
    @(negedge clk);queue_descriptor(length1,input1,digest1,0);req_valid=1;req_tag=16'h8102;req_input=input1;req_input_bytes=length1;
    await_result();hold_result();consume_result();
    if(requests!=1)$fatal(1,"held request admitted before result release");
    @(posedge clk);#1;if(requests!=2||req_ready)$fatal(1,"waiting request not captured once idle");
    req_valid=0;req_input=~input1;req_input_bytes=7'd127;
    await_result();hold_result();consume_result();
   end else if(mode=="held_response")begin
    launch(16'h8101,length0,input0,digest0,0);await_result();hold_result();consume_result();
    launch(16'h8102,length1,input1,digest1,0);await_result();hold_result();consume_result();
   end else if(mode=="invalid_all"||mode=="invalid_edges")begin
    // Follow real computation with errors, then a different valid message,
    // proving neither old core-valid nor invalid descriptors become a seed.
    launch(16'h8101,length0,input0,digest0,0);await_result();consume_result();
    for(count=81;count<=127;count=count+1)begin
     if(mode=="invalid_all"||count==81||count==127)begin
      launch(16'h8200+count,count,input0,512'b0,1);await_result();hold_result();consume_result();errors_checked=errors_checked+1;
     end
    end
    launch(16'h8102,length1,input1,digest1,0);await_result();consume_result();
   end else if(mode=="cancel_before"||mode=="reset_before")begin
    abort_and_release(mode=="reset_before");
    launch(16'h8102,length1,input1,digest1,0);await_result();hold_result();consume_result();
   end else if(mode=="cancel_return"||mode=="reset_return")begin
    launch(16'h8101,length0,input0,digest0,0);await_result();hold_result();
    abort_and_release(mode=="reset_return");
    launch(16'h8102,length1,input1,digest1,0);await_result();hold_result();consume_result();
   end else begin
    if(mode=="cancel_start"||mode=="reset_start")target_age=0;
    if(mode=="cancel_early"||mode=="reset_early")target_age=2;
    if(mode=="cancel_middle"||mode=="reset_middle")target_age=14;
    if(mode=="cancel_final"||mode=="reset_final")target_age=26;
    if(target_age<0)$fatal(1,"unknown mode %0s",mode);
    launch(16'h8101,length0,input0,digest0,0);
    repeat(target_age)step();
    if(rsp_valid||phase!==1)$fatal(1,"abort phase coverage");
    abort_and_release(mode=="reset_start"||mode=="reset_early"||mode=="reset_middle"||mode=="reset_final");
    launch(16'h8102,length1,input1,digest1,0);await_result();hold_result();consume_result();
   end
   if(mode=="held_request"&&(requests!=2||completed!=2||held_request_cycles<1))$fatal(1,"held request coverage");
   if(mode=="invalid_all"&&(invalid_lengths!=47||errors_checked!=47))$fatal(1,"unsupported length coverage");
   if(mode=="invalid_edges"&&(invalid_lengths!=2||errors_checked!=2))$fatal(1,"mapped unsupported length edges");
   if(held_response_cycles<5)$fatal(1,"held response/error coverage");
  end
  if(verified_digests<1||latency_min<1||latency_min!=latency_max)$fatal(1,"missing constant one-block native result");
  $display("PASS input_blake2b mode=%0s native_vectors=%0d requests=%0d completed=%0d latency_min=%0d latency_max=%0d native_vector_compute_cycles=%0d invalid_lengths=%0d held_request_cycles=%0d held_response_cycles=%0d aborts=%0d abort_age=%0d captured_input_tag=1 empty_tail_restart=1",mode,verified_digests,requests,completed,latency_min,latency_max,valid_compute_cycles,invalid_lengths,held_request_cycles,held_response_cycles,aborts,target_age);
  $finish;
 end
 initial begin #10000000;$fatal(1,"input hash test deadlock");end
endmodule
