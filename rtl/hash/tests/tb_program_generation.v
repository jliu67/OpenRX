// SPDX-License-Identifier: BSD-3-Clause
// Expected native bytes are assertion-only; only seed-in drives the generator.
`timescale 1ns/1ps
module tb_program_generation #(parameter integer OUTPUT_BYTES=3200);
 localparam integer BEATS=OUTPUT_BYTES/16;
 reg clk=0,rst=1,cancel=0,req_valid=0,out_ready=0,rsp_ready=0;
 always #5 clk=~clk;
 wire req_ready,out_valid,rsp_valid;
 reg [15:0] req_tag=0;
 reg [511:0] req_seed=0;
 wire [11:0] out_addr;
 wire [127:0] out_data;
 wire [15:0] out_tag,rsp_tag;
 wire [1:0] phase;
`ifdef PROGRAM_GENERATION_NETLIST
 randomx_program_generation dut(
`else
 randomx_program_generation #(.OUTPUT_BYTES(OUTPUT_BYTES)) dut(
`endif
  .clk(clk),.rst(rst),.cancel(cancel),.req_valid(req_valid),.req_ready(req_ready),
  .req_tag(req_tag),.req_seed(req_seed),.out_valid(out_valid),.out_ready(out_ready),
  .out_addr(out_addr),.out_data(out_data),.out_tag(out_tag),
  .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_tag(rsp_tag),.phase(phase)
 );
 reg [127:0] expected_image[0:BEATS-1],memory[0:BEATS-1];
 reg [511:0] initial_seed[0:0];
 reg [15:0] active_tag=0,saved_response=0;
 reg run_active=0,held_output=0,held_response=0;
 reg [155:0] saved_output;
 wire [155:0] now_output={out_tag,out_addr,out_data};
 string directory,path,mode="ideal";
 integer cycles=0,requests=0,completed=0,full_images=0,verified_outputs=0;
 integer run_outputs=0,run_start=0,run_compute=0,first_availability=0,primary_outputs=0;
 integer output_stalls=0,held_response_cycles=0,held_request_cycles=0,aborts=0,aborted_outputs=0;
 integer i,n,old_requests,old_completed,old_outputs,stalled=0,target_round=-1;

 function [127:0] sentinel;
  input integer index;
  begin sentinel=128'hd3adbeef9182736455aacc00fe12ba34^index;end
 endfunction

 always @(posedge clk)begin
  cycles=cycles+1;
  if(rst||cancel)begin
   if(req_ready||out_valid||rsp_valid)$fatal(1,"reset/cancel did not suppress handshakes");
   held_output=0;held_response=0;run_active=0;
  end else begin
   if(held_output&&(!out_valid||now_output!==saved_output))$fatal(1,"stalled output changed");
   if(held_response&&(!rsp_valid||rsp_tag!==saved_response))$fatal(1,"held response changed");
   if(req_valid&&req_ready)begin
    if(run_active||phase!==0||req_seed!==initial_seed[0])$fatal(1,"unexpected request admission");
    requests=requests+1;active_tag=req_tag;run_outputs=0;run_compute=0;run_start=cycles;run_active=1;
   end else if(req_valid&&!req_ready)held_request_cycles=held_request_cycles+1;
   if(phase==1)begin
    if(!run_active||req_ready||rsp_valid)$fatal(1,"round computation ownership/phase");
    if(!out_valid||out_ready)run_compute=run_compute+1;
   end
   if(out_valid)begin
    if(!run_active||phase!==1||rsp_valid||req_ready)$fatal(1,"output ownership/phase");
    if(out_tag!==active_tag||out_addr!==run_outputs*16)$fatal(1,"output descriptor index=%0d",run_outputs);
    if(run_outputs>=BEATS||out_data!==expected_image[run_outputs])$fatal(1,"native program byte mismatch index=%0d",run_outputs);
    if(out_ready)begin
     memory[run_outputs]=out_data;run_outputs=run_outputs+1;verified_outputs=verified_outputs+1;
    end else output_stalls=output_stalls+1;
   end
   if(rsp_valid)begin
    if(!run_active||run_outputs!=BEATS||run_compute!=4*BEATS||phase!==2||out_valid||req_ready)
     $fatal(1,"response before complete four-round stream");
    if(rsp_tag!==active_tag)$fatal(1,"response tag mismatch");
    if(rsp_ready)begin completed=completed+1;run_active=0;end
    else held_response_cycles=held_response_cycles+1;
   end
   held_output=out_valid&&!out_ready;saved_output=now_output;
   held_response=rsp_valid&&!rsp_ready;saved_response=rsp_tag;
  end
 end

 task check_memory;
  input integer count;
  integer index;
  begin
   for(index=0;index<BEATS;index=index+1)
    if(memory[index]!==(index<count?expected_image[index]:sentinel(index)))
     $fatal(1,"accepted output did not persist index=%0d accepted=%0d",index,count);
  end
 endtask

 task launch;
  input [15:0] tag;
  begin
   @(negedge clk);req_tag=tag;req_seed=initial_seed[0];req_valid=1;out_ready=0;rsp_ready=0;
   #1;if(!req_ready||out_valid||rsp_valid||phase!==0)$fatal(1,"generator not idle before request");
   old_requests=requests;
   @(posedge clk);#1;
   if(requests!=old_requests+1||req_ready||phase!==1)$fatal(1,"request capture");
   // Change all input bits immediately; recurrence must consume captured state.
   req_valid=0;req_tag=~tag;req_seed=~initial_seed[0];
  end
 endtask

 task step;
  input integer add_stalls;
  begin
   @(negedge clk);out_ready=!add_stalls||(cycles%5>=2);rsp_ready=0;
   @(posedge clk);#1;
  end
 endtask

 task await_result;
  input integer add_stalls;
  integer began;
  begin
   began=cycles;
   while(!rsp_valid)begin
    step(add_stalls);
    if(cycles-began>BEATS*8+64)$fatal(1,"program generation response timeout");
   end
   if(run_outputs!=BEATS||run_compute!=4*BEATS||rsp_tag!==active_tag)$fatal(1,"complete response payload/cost");
   if(!first_availability)begin first_availability=cycles-run_start;primary_outputs=run_outputs;end
   for(i=0;i<BEATS;i=i+1)if(memory[i]!==expected_image[i])$fatal(1,"full program image mismatch index=%0d",i);
   full_images=full_images+1;
  end
 endtask

 task hold_result;
  integer count;
  begin
   for(count=0;count<5;count=count+1)begin
    @(negedge clk);out_ready=1;rsp_ready=0;
    @(posedge clk);#1;
    if(!rsp_valid||rsp_tag!==active_tag||out_valid||req_ready)$fatal(1,"response backpressure stability");
   end
  end
 endtask

 task consume_result;
  begin
   @(negedge clk);rsp_ready=1;out_ready=1;old_completed=completed;
   @(posedge clk);#1;
   if(completed!=old_completed+1||!req_ready||out_valid||rsp_valid||phase!==0)$fatal(1,"response release");
   rsp_ready=0;
  end
 endtask

 task abort_and_release;
  input integer use_reset;
  input integer accepted;
  begin
   check_memory(accepted);old_requests=requests;old_outputs=verified_outputs;
   @(negedge clk);rst=use_reset;cancel=!use_reset;out_ready=1;rsp_ready=1;
   req_valid=1;req_tag=16'hdead;req_seed=~initial_seed[0];
   #1;if(req_ready||out_valid||rsp_valid||phase!==0)$fatal(1,"abort gating before edge");
   @(posedge clk);#1;
   if(req_ready||out_valid||rsp_valid||requests!=old_requests||verified_outputs!=old_outputs)
    $fatal(1,"abort accepted a transfer");
   check_memory(accepted);aborts=aborts+1;aborted_outputs=accepted;
   @(negedge clk);rst=0;cancel=0;req_valid=0;out_ready=0;rsp_ready=0;
   @(posedge clk);#1;
   if(!req_ready||out_valid||rsp_valid||phase!==0)$fatal(1,"abort did not restore idle");
   check_memory(accepted);
  end
 endtask

 initial begin
  if(!$value$plusargs("DIR=%s",directory))$fatal(1,"missing fixture directory");
  i=$value$plusargs("MODE=%s",mode);
  $sformat(path,"%0s/seed-in.hex",directory);$readmemh(path,initial_seed);
  $sformat(path,"%0s/image.hex",directory);$readmemh(path,expected_image);
  if(^initial_seed[0]===1'bx)$fatal(1,"unknown native input seed");
  for(i=0;i<BEATS;i=i+1)begin
   if(^expected_image[i]===1'bx)$fatal(1,"unknown native image index=%0d",i);
   memory[i]=sentinel(i);
  end
  @(posedge clk);#1;@(negedge clk);rst=0;
  if(mode=="cancel_before"||mode=="reset_before")begin
   abort_and_release(mode=="reset_before",0);
   launch(16'h7402);await_result(0);hold_result();consume_result();
  end else if(mode=="cancel_return"||mode=="reset_return")begin
   launch(16'h7401);await_result(0);hold_result();
   abort_and_release(mode=="reset_return",BEATS);
   launch(16'h7402);await_result(1);hold_result();consume_result();
  end else if(mode=="held_request")begin
   launch(16'h7401);
   @(negedge clk);req_valid=1;req_tag=16'h7402;req_seed=initial_seed[0];
   await_result(1);hold_result();consume_result();
   if(requests!=1)$fatal(1,"held request admitted before idle");
   @(posedge clk);#1;
   if(requests!=2||req_ready||phase!==1)$fatal(1,"held request not captured once idle");
   req_valid=0;req_tag=16'hffff;req_seed=~initial_seed[0];
   await_result(1);hold_result();consume_result();
  end else if(mode=="ideal"||mode=="stalled"||mode=="held_response")begin
   stalled=mode=="stalled";
   launch(16'h7401);await_result(stalled);hold_result();consume_result();
   if(!stalled&&first_availability!=4*BEATS)$fatal(1,"ideal four-round cost");
  end else begin
   if(mode=="cancel_round0"||mode=="reset_round0")target_round=0;
   if(mode=="cancel_round1"||mode=="reset_round1")target_round=1;
   if(mode=="cancel_round2"||mode=="reset_round2")target_round=2;
   if(mode=="cancel_round3"||mode=="reset_round3")target_round=3;
   if(target_round<0)$fatal(1,"unknown mode %0s",mode);
   launch(16'h7401);while(run_outputs<3)step(0);
   // After the third accepted output the next lane starts round0. Advance
   // exactly to the selected round using only interface clocks, not DUT internals.
   for(n=0;n<target_round;n=n+1)begin @(negedge clk);out_ready=0;@(posedge clk);#1;end
   if(phase!==1||out_valid!==(target_round==3))$fatal(1,"round-position coverage");
   if(target_round==3)repeat(3)begin @(negedge clk);out_ready=0;@(posedge clk);#1;end
   abort_and_release(mode=="reset_round0"||mode=="reset_round1"||mode=="reset_round2"||mode=="reset_round3",3);
   launch(16'h7402);await_result(1);hold_result();consume_result();
  end
  if(completed<1||full_images<1||!first_availability)$fatal(1,"missing native differential result");
  if(mode=="held_request"&&(requests!=2||completed!=2||held_request_cycles<1))$fatal(1,"held request coverage");
  if(mode=="stalled"&&output_stalls<1)$fatal(1,"output stall coverage");
  if(held_response_cycles<5)$fatal(1,"held response coverage");
  if(target_round>=0&&aborted_outputs!=3)$fatal(1,"partial output persistence coverage");
  $display("PASS program_generation bytes=%0d mode=%0s requests=%0d completed=%0d full_images=%0d verified_outputs=%0d primary_outputs=%0d availability_cycles=%0d compute_cycles=%0d output_stall_cycles=%0d held_request_cycles=%0d held_response_cycles=%0d aborts=%0d aborted_outputs=%0d round_position=%0d native_program_bytes=1 accepted_outputs_persist=1",OUTPUT_BYTES,mode,requests,completed,full_images,verified_outputs,primary_outputs,first_availability,4*BEATS,output_stalls,held_request_cycles,held_response_cycles,aborts,aborted_outputs,target_round);
  $finish;
 end
 initial begin #10000000;$fatal(1,"program generation test deadlock");end
endmodule
