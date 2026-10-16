// SPDX-License-Identifier: BSD-3-Clause
// Native images and post-fill seeds are assertion-only. Only seed-in drives DUT.
`timescale 1ns/1ps
module tb_initial_scratchpad_fill #(parameter integer SCRATCHPAD_BYTES=2097152);
 localparam integer BEATS=SCRATCHPAD_BYTES/16;
 reg clk=0,rst=1,cancel=0,req_valid=0,sp_wr_ready=0,rsp_ready=0;
 always #5 clk=~clk;
 wire req_ready,sp_wr_valid,rsp_valid;
 reg [15:0] req_tag=0;
 reg [511:0] req_seed=0;
 wire [20:0] sp_wr_addr;
 wire [127:0] sp_wr_data;
 wire [15:0] sp_wr_strb,sp_wr_tag,rsp_tag;
 wire [511:0] rsp_seed;
 wire [1:0] phase;
`ifdef INITIAL_SCRATCHPAD_FILL_NETLIST
 randomx_initial_scratchpad_fill dut(
`else
 randomx_initial_scratchpad_fill #(.SCRATCHPAD_BYTES(SCRATCHPAD_BYTES)) dut(
`endif
  .clk(clk),.rst(rst),.cancel(cancel),.req_valid(req_valid),.req_ready(req_ready),
  .req_tag(req_tag),.req_seed(req_seed),.sp_wr_valid(sp_wr_valid),.sp_wr_ready(sp_wr_ready),
  .sp_wr_addr(sp_wr_addr),.sp_wr_data(sp_wr_data),.sp_wr_strb(sp_wr_strb),.sp_wr_tag(sp_wr_tag),
  .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_tag(rsp_tag),.rsp_seed(rsp_seed),.phase(phase)
 );
 reg [127:0] expected_image[0:BEATS-1],memory[0:BEATS-1];
 reg [511:0] initial_seed[0:0],expected_seed[0:0];
 reg [15:0] active_tag=0;
 reg run_active=0,held_write=0,held_response=0;
 reg [180:0] saved_write;
 reg [527:0] saved_response;
 wire [180:0] now_write={sp_wr_tag,sp_wr_addr,sp_wr_strb,sp_wr_data};
 wire [527:0] now_response={rsp_tag,rsp_seed};
 string directory,path,mode="ideal";
 integer cycles=0,requests=0,completed=0,full_images=0,verified_writes=0;
 integer run_writes=0,run_start=0,first_availability=0,primary_writes=0;
 integer stall_cycles=0,held_response_cycles=0,held_request_cycles=0,aborts=0,aborted_writes=0;
 integer i,old_requests,old_completed,old_writes,stalled=0;

 function [127:0] sentinel;
  input integer index;
  begin sentinel=128'hd3adbeef9182736455aacc00fe12ba34^index;end
 endfunction

 // Observe accepted bus writes, with no memory mutation on a stalled transfer.
 always @(posedge clk)begin
  cycles=cycles+1;
  if(rst||cancel)begin
   if(req_ready||sp_wr_valid||rsp_valid)$fatal(1,"reset/cancel did not suppress handshakes");
   held_write=0;held_response=0;run_active=0;
  end else begin
   if(held_write&&(!sp_wr_valid||now_write!==saved_write))$fatal(1,"stalled write changed");
   if(held_response&&(!rsp_valid||now_response!==saved_response))$fatal(1,"held response changed");
   if(req_valid&&req_ready)begin
    if(run_active||phase!==0||req_seed!==initial_seed[0])$fatal(1,"unexpected request admission");
    requests=requests+1;active_tag=req_tag;run_writes=0;run_start=cycles;run_active=1;
   end else if(req_valid&&!req_ready)held_request_cycles=held_request_cycles+1;
   if(sp_wr_valid)begin
    if(!run_active||phase!==1||rsp_valid||req_ready)$fatal(1,"write ownership/phase");
    if(sp_wr_tag!==active_tag||sp_wr_addr!==run_writes*16||sp_wr_strb!==16'hffff)
     $fatal(1,"write descriptor index=%0d address=%h tag=%h",run_writes,sp_wr_addr,sp_wr_tag);
    if(run_writes>=BEATS||sp_wr_data!==expected_image[run_writes])$fatal(1,"native fill word mismatch index=%0d",run_writes);
    if(sp_wr_ready)begin
     memory[run_writes]=sp_wr_data;run_writes=run_writes+1;verified_writes=verified_writes+1;
    end else stall_cycles=stall_cycles+1;
   end
   if(rsp_valid)begin
    if(!run_active||run_writes!=BEATS||phase!==2||sp_wr_valid||req_ready)
     $fatal(1,"response before complete memory ownership transfer");
    if(rsp_tag!==active_tag||rsp_seed!==expected_seed[0])$fatal(1,"postfill native seed/tag mismatch");
    if(rsp_ready)begin completed=completed+1;run_active=0;end
    else held_response_cycles=held_response_cycles+1;
   end
   held_write=sp_wr_valid&&!sp_wr_ready;saved_write=now_write;
   held_response=rsp_valid&&!rsp_ready;saved_response=now_response;
  end
 end

 task check_memory;
  input integer count;
  integer index;
  begin
   for(index=0;index<BEATS;index=index+1)
    if(memory[index]!==(index<count?expected_image[index]:sentinel(index)))
     $fatal(1,"accepted memory writes did not persist index=%0d accepted=%0d",index,count);
  end
 endtask

 task launch;
  input [15:0] tag;
  begin
   @(negedge clk);req_tag=tag;req_seed=initial_seed[0];req_valid=1;sp_wr_ready=0;rsp_ready=0;
   #1;if(!req_ready||sp_wr_valid||rsp_valid||phase!==0)$fatal(1,"fill not idle before request");
   old_requests=requests;
   @(posedge clk);#1;
   if(requests!=old_requests+1||req_ready||phase!==1)$fatal(1,"request capture");
   req_valid=0;req_tag=~tag;req_seed=~initial_seed[0];
  end
 endtask

 task step;
  input integer add_stalls;
  begin
   @(negedge clk);sp_wr_ready=!add_stalls||(cycles%5>=2);rsp_ready=0;
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
    if(cycles-began>BEATS*4+64)$fatal(1,"fill response timeout");
   end
   if(run_writes!=BEATS||rsp_seed!==expected_seed[0]||rsp_tag!==active_tag)$fatal(1,"complete response payload");
   if(!first_availability)begin first_availability=cycles-run_start;primary_writes=run_writes;end
   for(i=0;i<BEATS;i=i+1)if(memory[i]!==expected_image[i])$fatal(1,"full image mismatch index=%0d",i);
   full_images=full_images+1;
  end
 endtask

 task hold_result;
  integer count;
  begin
   for(count=0;count<5;count=count+1)begin
    @(negedge clk);sp_wr_ready=1;rsp_ready=0;
    @(posedge clk);#1;
    if(!rsp_valid||rsp_tag!==active_tag||rsp_seed!==expected_seed[0]||sp_wr_valid||req_ready)
     $fatal(1,"response was not stable under backpressure");
   end
  end
 endtask

 task consume_result;
  begin
   @(negedge clk);rsp_ready=1;sp_wr_ready=1;old_completed=completed;
   @(posedge clk);#1;
   if(completed!=old_completed+1||!req_ready||sp_wr_valid||rsp_valid||phase!==0)$fatal(1,"response release");
   rsp_ready=0;
  end
 endtask

 task abort_and_release;
  input integer use_reset;
  input integer accepted;
  begin
   check_memory(accepted);old_requests=requests;old_writes=verified_writes;
   @(negedge clk);rst=use_reset;cancel=!use_reset;sp_wr_ready=1;rsp_ready=1;
   req_valid=1;req_tag=16'hdead;req_seed=~initial_seed[0];
   #1;if(req_ready||sp_wr_valid||rsp_valid||phase!==0)$fatal(1,"abort gating before edge");
   @(posedge clk);#1;
   if(req_ready||sp_wr_valid||rsp_valid||requests!=old_requests||verified_writes!=old_writes)
    $fatal(1,"abort accepted a transfer");
   check_memory(accepted);aborts=aborts+1;aborted_writes=accepted;
   @(negedge clk);rst=0;cancel=0;req_valid=0;sp_wr_ready=0;rsp_ready=0;
   @(posedge clk);#1;
   if(!req_ready||sp_wr_valid||rsp_valid||phase!==0)$fatal(1,"abort did not restore idle");
   check_memory(accepted);
  end
 endtask

 initial begin
  if(!$value$plusargs("DIR=%s",directory))$fatal(1,"missing fixture directory");
  i=$value$plusargs("MODE=%s",mode);
  $sformat(path,"%0s/seed-in.hex",directory);$readmemh(path,initial_seed);
  $sformat(path,"%0s/seed-out.hex",directory);$readmemh(path,expected_seed);
  $sformat(path,"%0s/image.hex",directory);$readmemh(path,expected_image);
  if(^initial_seed[0]===1'bx||^expected_seed[0]===1'bx)$fatal(1,"unknown native seed fixture");
  for(i=0;i<BEATS;i=i+1)begin
   if(^expected_image[i]===1'bx)$fatal(1,"unknown native image fixture index=%0d",i);
   memory[i]=sentinel(i);
  end
  @(posedge clk);#1;@(negedge clk);rst=0;
  if(mode=="cancel_before"||mode=="reset_before")begin
   abort_and_release(mode=="reset_before",0);
   launch(16'h7102);await_result(0);hold_result();consume_result();
  end else if(mode=="cancel_stream"||mode=="reset_stream"||mode=="cancel_stall"||mode=="reset_stall")begin
   launch(16'h7101);
   while(run_writes<3)step(0);
   if(mode=="cancel_stall"||mode=="reset_stall")begin
    repeat(3)begin @(negedge clk);sp_wr_ready=0;@(posedge clk);#1;end
   end
   abort_and_release(mode=="reset_stream"||mode=="reset_stall",3);
   launch(16'h7102);await_result(1);hold_result();consume_result();
  end else if(mode=="cancel_return"||mode=="reset_return")begin
   launch(16'h7101);await_result(0);hold_result();
   abort_and_release(mode=="reset_return",BEATS);
   launch(16'h7102);await_result(1);hold_result();consume_result();
  end else if(mode=="held_request")begin
   launch(16'h7101);
   @(negedge clk);req_valid=1;req_tag=16'h7102;req_seed=initial_seed[0];
   await_result(1);hold_result();consume_result();
   // The waiting request cannot transfer on the preceding response edge.
   if(requests!=1)$fatal(1,"held request was admitted before idle");
   @(posedge clk);#1;
   if(requests!=2||req_ready||phase!==1)$fatal(1,"held request was not captured once idle");
   req_valid=0;req_tag=16'hffff;req_seed=~initial_seed[0];
   await_result(1);hold_result();consume_result();
  end else if(mode=="ideal"||mode=="stalled"||mode=="held_response")begin
   stalled=mode=="stalled";
   launch(16'h7101);await_result(stalled);hold_result();consume_result();
   if(!stalled&&first_availability!=BEATS)$fatal(1,"ideal recurrence cost differs from accepted beats");
  end else $fatal(1,"unknown mode %0s",mode);
  if(completed<1||full_images<1||!first_availability)$fatal(1,"missing complete differential result");
  if((mode=="held_request")&&(requests!=2||completed!=2||held_request_cycles<1))$fatal(1,"held request coverage");
  if((mode=="stalled")&&stall_cycles<1)$fatal(1,"write stall coverage");
  if(held_response_cycles<5)$fatal(1,"held response coverage");
  if((mode=="cancel_stream"||mode=="reset_stream"||mode=="cancel_stall"||mode=="reset_stall")&&aborted_writes!=3)
   $fatal(1,"partial memory persistence coverage");
  $display("PASS initial_scratchpad_fill bytes=%0d mode=%0s requests=%0d completed=%0d full_images=%0d verified_writes=%0d primary_writes=%0d availability_cycles=%0d stall_cycles=%0d held_request_cycles=%0d held_response_cycles=%0d aborts=%0d aborted_writes=%0d native_final_seed=1 accepted_writes_persist=1",SCRATCHPAD_BYTES,mode,requests,completed,full_images,verified_writes,primary_writes,first_availability,stall_cycles,held_request_cycles,held_response_cycles,aborts,aborted_writes);
  $finish;
 end
 initial begin #1000000000;$fatal(1,"initial fill test deadlock");end
endmodule
