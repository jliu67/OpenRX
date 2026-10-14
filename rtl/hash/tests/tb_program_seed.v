// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_program_seed;
 reg clk=0,rst=1,req_valid=0,rsp_ready=0;always #5 clk=~clk;
 reg [15:0] req_tag=0;reg [2:0] req_index=0;reg [11:0] req_iterations=2048;reg [1:0] req_round_mode=0;
 reg [2047:0] registers=0;wire req_ready,rsp_valid,rsp_error,rsp_seed_valid;
 wire [15:0] rsp_tag;wire [2:0] rsp_index;wire [11:0] rsp_iterations;wire [1:0] rsp_round_mode;
 wire [511:0] rsp_r,rsp_f,rsp_e,rsp_a,rsp_seed;
`ifdef PROGRAM_SEED_NETLIST
 randomx_program_seed dut(
`else
 randomx_program_seed #(.PROGRAMS(8)) dut(
`endif
  .clk(clk),.rst(rst),.req_valid(req_valid),.req_ready(req_ready),.req_tag(req_tag),.req_index(req_index),
  .req_iterations(req_iterations),.req_round_mode(req_round_mode),.req_r(registers[511:0]),.req_f(registers[1023:512]),
  .req_e(registers[1535:1024]),.req_a(registers[2047:1536]),.rsp_valid(rsp_valid),.rsp_ready(rsp_ready),
  .rsp_tag(rsp_tag),.rsp_index(rsp_index),.rsp_iterations(rsp_iterations),.rsp_round_mode(rsp_round_mode),
  .rsp_r(rsp_r),.rsp_f(rsp_f),.rsp_e(rsp_e),.rsp_a(rsp_a),.rsp_seed(rsp_seed),.rsp_seed_valid(rsp_seed_valid),.rsp_error(rsp_error)
 );
 reg [2047:0] message;reg [511:0] expected;reg [15:0] active_tag;reg [2:0] active_index;reg [1:0] active_round;
 integer f,got,count=0,hashes=0,bypasses=0,cycles=0,began,cost,hash_cost=-1,i,resets=0,errors=0;string path;
 task tick;begin @(posedge clk);#1;cycles=cycles+1;end endtask
 task launch;input [15:0] tag;input [2:0] index;input [11:0] iterations;begin
  if(!req_ready)$fatal(1,"seed request not ready");active_tag=tag;active_index=index;active_round=tag[1:0];
  req_tag=tag;req_index=index;req_iterations=iterations;req_round_mode=active_round;registers=message;req_valid=1;
  tick;req_valid=0;began=cycles;req_tag=~tag;req_index=~index;req_iterations=~iterations;req_round_mode=~active_round;registers=~message;
 end endtask
 task await_result;begin
  while(!rsp_valid)begin tick;if(req_ready||cycles-began>80)$fatal(1,"seed busy/timeout");end
 end endtask
 task check_good;begin
  if(!rsp_valid||rsp_error||rsp_tag!==active_tag||rsp_index!==active_index||rsp_iterations!==2048||rsp_round_mode!==active_round||
   {rsp_a,rsp_e,rsp_f,rsp_r}!==message)$fatal(1,"held native register result");
  if(active_index==7)begin if(rsp_seed_valid||rsp_seed!==0)$fatal(1,"final program was incorrectly hashed");end
  else if(!rsp_seed_valid||rsp_seed!==expected)$fatal(1,"interprogram native seed mismatch");
 end endtask
 task reset_stage;begin rst=1;#1;if(req_ready||rsp_valid)$fatal(1,"seed reset suppression");tick;tick;rst=0;tick;resets=resets+1;
  repeat(80)begin tick;if(!req_ready||rsp_valid)$fatal(1,"late cancelled seed");end end endtask
 initial begin
  if(!$value$plusargs("vectors=%s",path))$fatal(1,"vectors missing");f=$fopen(path,"r");if(!f)$fatal(1,"vectors open");tick;tick;rst=0;tick;
  while(!$feof(f))begin
   got=$fscanf(f,"%h %h",message,expected);
   if(got==2)begin
    launch(16'h5000+count,count%8,2048);await_result;cost=cycles-began;
    if(active_index==7)begin if(cost!=0)$fatal(1,"last-program bypass latency");bypasses=bypasses+1;end
    else begin if(hash_cost<0)hash_cost=cost;if(cost!=hash_cost)$fatal(1,"hash bridge latency");hashes=hashes+1;end
    repeat(4)begin check_good;tick;end
    rsp_ready=1;tick;rsp_ready=0;if(!req_ready||rsp_valid)$fatal(1,"seed result consume");count=count+1;
   end else if(!$feof(f))$fatal(1,"vector row");
  end
  $fclose(f);if(count!=524)$fatal(1,"seed corpus count");
  launch(16'he000,0,2048);repeat(5)tick;reset_stage;
  launch(16'he001,6,2048);repeat(36)tick;reset_stage;
  launch(16'he002,0,2048);await_result;check_good;reset_stage;
  launch(16'he003,7,2048);await_result;check_good;reset_stage;
  for(i=0;i<3;i=i+1)begin
   launch(16'hef00+i,0,i==0?0:i==1?2049:4095);await_result;
   repeat(4)begin if(!rsp_error||rsp_seed_valid||rsp_seed!==0||rsp_tag!==active_tag||req_ready)$fatal(1,"held seed descriptor error");tick;end
   rsp_ready=1;tick;rsp_ready=0;if(!req_ready||rsp_valid)$fatal(1,"seed error consume");errors=errors+1;
  end
  launch(16'hf100,0,2048);await_result;check_good;rsp_ready=1;tick;
  $display("PASS program_seed native_records=%0d hashes=%0d final_bypasses=%0d hash_latency=%0d bypass_latency=0 resets=%0d invalid_iterations=%0d register_round_tag_capture=1 held_inactive=1",count,hashes,bypasses,hash_cost,resets,errors);$finish;
 end
 initial begin #2000000;$fatal(1,"seed deadlock");end
endmodule
