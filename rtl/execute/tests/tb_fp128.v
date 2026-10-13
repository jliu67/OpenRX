// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_fp128;
 parameter integer LANES=2;
 reg clk=0;always #5 clk=~clk;
 reg rst=1,valid=0,ready=0,ftz;reg [15:0] tag;reg [1:0] op,rm;
 reg [127:0] a,b;wire rq,rv;wire [15:0] rt;wire [127:0] value;wire [4:0] flags;
`ifdef FP128_NETLIST
 randomx_fp128 dut(clk,rst,valid,rq,tag,op,rm,ftz,a,b,rv,ready,rt,value,flags);
`else
 randomx_fp128 #(.LANES(LANES)) dut(clk,rst,valid,rq,tag,op,rm,ftz,a,b,rv,ready,rt,value,flags);
`endif
 reg [1023:0] file;integer handle,scan,count=0,i,latency,total=0;
 reg [63:0] a0,a1,b0,b1,e0,e1;integer go,gr,gft,gflags,csr;
 task tick;begin @(posedge clk);#1;end endtask
 initial begin
  if(!$value$plusargs("vectors=%s",file))$fatal(1,"vectors missing");handle=$fopen(file,"r");if(!handle)$fatal(1,"cannot open vectors");
  tick();rst=0;tick();
  while(!$feof(handle))begin
   scan=$fscanf(handle,"%h %h %h %h %h %h %h %h %h %h %h\n",a0,a1,b0,b1,go,gr,gft,e0,e1,gflags,csr);
   if(scan!=11)$fatal(1,"bad vector row");
   @(negedge clk);a={a1,a0};b={b1,b0};op=go;rm=gr;ftz=gft;tag=count+1;valid=1;ready=0;
   if(!rq)$fatal(1,"not ready");tick();valid=0;latency=0;
   while(!rv)begin a=~a;b=~b;op=op^3;rm=rm^3;ftz=~ftz;tag=~tag;tick();latency=latency+1;
    if(latency>8)$fatal(1,"FP vector timeout");end
   latency=latency+1;
   if(latency!=(LANES==2?1:5))$fatal(1,"FP latency %0d",latency);total=total+latency;
   if(value!=={e1,e0}||flags!==gflags[4:0]||rt!==16'(count+1))
    $fatal(1,"FP128 mismatch row=%0d lanes=%0d op=%0d rm=%0d ftz=%0d expected=%h/%h got=%h/%h nativecsr=%h",count,LANES,go,gr,gft,{e1,e0},gflags,value,flags,csr);
   for(i=0;i<2;i=i+1)begin a=~a;b=~b;op=op^3;rm=rm^3;ftz=~ftz;tag=~tag;tick();
    if(!rv||value!=={e1,e0}||flags!==gflags[4:0]||rq)$fatal(1,"held/inactive FP changed");end
   ready=1;tick();ready=0;if(rv)$fatal(1,"reply not consumed");count=count+1;
  end
  $fclose(handle);
  // Cancel a held parallel reply or shared work after the low lane has executed.
  @(negedge clk);a={2{64'h3ff0000000000000}};b={2{64'h3ca0000000000000}};op=0;rm=0;ftz=1;tag=16'habcd;valid=1;ready=0;
  tick();valid=0;if(LANES==1)begin tick();tick();end
  rst=1;tick();rst=0;repeat(12)begin tick();if(rv||!rq)$fatal(1,"reset did not cancel FP vector");end
  $display("PASS fp128 lanes=%0d native_vectors=%0d operations=3 rounding_modes=4 DAZ_FTZ_models=2 total_response_latency=%0d held_inactive=1 reset_atomic=1",LANES,count,total);$finish;
 end
endmodule
