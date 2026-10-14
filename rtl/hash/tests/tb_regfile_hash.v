// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_regfile_hash #(parameter integer DIGEST_BYTES=64);
 reg clk=0,rst=1,req_valid=0,rsp_ready=0;always #5 clk=~clk;
 reg [15:0] req_tag=0;reg [8:0] req_bytes=256;reg [2047:0] registers=0;
 wire req_ready,rsp_valid,rsp_error;wire [15:0] rsp_tag;wire [511:0] rsp_digest;
`ifdef REGFILE_BLAKE2B_NETLIST
 randomx_regfile_blake2b dut(
`else
 randomx_regfile_blake2b #(.DIGEST_BYTES(DIGEST_BYTES)) dut(
`endif
  .clk(clk),.rst(rst),.req_valid(req_valid),.req_ready(req_ready),.req_tag(req_tag),.req_bytes(req_bytes),
  .req_r(registers[511:0]),.req_f(registers[1023:512]),.req_e(registers[1535:1024]),.req_a(registers[2047:1536]),
  .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_tag(rsp_tag),.rsp_digest(rsp_digest),.rsp_error(rsp_error)
 );
 reg [2047:0] message;reg [511:0] expected;reg [15:0] active_tag;
 string path;integer f,got,count=0,cycle=0,began,latency,min_latency=1000,max_latency=0,total_latency=0,i,resets=0,errors=0;
 task tick;begin @(posedge clk);#1;cycle=cycle+1;end endtask
 task launch;input [15:0] tag;input [8:0] bytes;begin
  if(!req_ready)$fatal(1,"new request not ready");
  active_tag=tag;registers=message;req_tag=tag;req_bytes=bytes;req_valid=1;tick;req_valid=0;began=cycle;
  registers=~registers;req_tag=~tag;req_bytes=~bytes;
 end endtask
 task await_response;begin
  while(!rsp_valid)begin
   if(req_ready)$fatal(1,"busy stage accepted another descriptor");
   tick;if(cycle-began>80)$fatal(1,"hash timeout");
  end
 end endtask
 task check_good;begin
  if(rsp_error||rsp_tag!==active_tag||rsp_digest!==expected)$fatal(1,"native hash mismatch tag=%h digest_bytes=%0d got=%h expected=%h",active_tag,DIGEST_BYTES,rsp_digest,expected);
 end endtask
 task reset_stage;begin
  rst=1;#1;if(req_ready||rsp_valid)$fatal(1,"reset output suppression");tick;tick;rst=0;tick;resets=resets+1;
  repeat(80)begin tick;if(!req_ready||rsp_valid)$fatal(1,"cancelled hash returned");end
 end endtask
 initial begin
  if(!$value$plusargs("vectors=%s",path))$fatal(1,"vectors missing");
  f=$fopen(path,"r");if(!f)$fatal(1,"vectors open");tick;tick;rst=0;tick;
  while(!$feof(f))begin
   got=$fscanf(f,"%h %h",message,expected);
   if(got==2)begin
    launch(16'h4000+count,256);await_response;latency=cycle-began;
    if(latency<min_latency)min_latency=latency;if(latency>max_latency)max_latency=latency;total_latency=total_latency+latency;
    repeat(4)begin check_good;tick;registers=~registers;req_tag=~req_tag;req_bytes=~req_bytes;end
    check_good;rsp_ready=1;tick;rsp_ready=0;if(!req_ready||rsp_valid)$fatal(1,"response consume");count=count+1;
   end else if(!$feof(f))$fatal(1,"vector row");
  end
  $fclose(f);if(count!=524)$fatal(1,"balanced corpus count %0d",count);
  // Reuse the last native vector for cancellation at both compression blocks.
  launch(16'he000,256);repeat(5)tick;if(rsp_valid||req_ready)$fatal(1,"first-block cancellation setup");reset_stage;
  launch(16'he001,256);repeat(35)tick;if(rsp_valid||req_ready)$fatal(1,"second-block cancellation setup");reset_stage;
  launch(16'he002,256);await_response;check_good;reset_stage;
  for(i=0;i<6;i=i+1)begin
   case(i)0:req_bytes=0;1:req_bytes=1;2:req_bytes=128;3:req_bytes=255;4:req_bytes=257;5:req_bytes=511;endcase
   launch(16'hef00+i,req_bytes);await_response;
   repeat(4)begin
    if(!rsp_error||rsp_tag!==active_tag||rsp_digest!==0||req_ready)$fatal(1,"held invalid-length error");tick;
   end
   rsp_ready=1;tick;rsp_ready=0;if(!req_ready||rsp_valid)$fatal(1,"error consume restart");errors=errors+1;
  end
  launch(16'hf100,256);await_response;check_good;rsp_ready=1;tick;rsp_ready=0;
  if(min_latency!=max_latency)$fatal(1,"unexpected data-dependent control latency");
  $display("PASS regfile_hash digest_bytes=%0d native_vectors=%0d latency_min=%0d latency_max=%0d native_vector_compute_cycles=%0d resets=%0d invalid_lengths=%0d held_inactive=1 subsequent_hash_restart=1",DIGEST_BYTES,count,min_latency,max_latency,total_latency,resets,errors);$finish;
 end
 initial begin #2000000;$fatal(1,"test deadlock");end
endmodule
