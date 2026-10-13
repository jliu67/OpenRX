// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_divsqrt128;
 parameter integer LANES=2;
 reg clk=0;always #5 clk=~clk;
 reg rst=1,valid=0,ready=0,ftz;reg [15:0] tag;reg op;reg [1:0] rm;
 reg [127:0] a,b;wire rq,rv;wire [15:0] rt;wire [127:0] value;wire [4:0] flags;
`ifdef DIVSQRT128_NETLIST
 randomx_divsqrt128 dut(clk,rst,valid,rq,tag,op,rm,ftz,a,b,rv,ready,rt,value,flags);
`else
 randomx_divsqrt128 #(.LANES(LANES)) dut(clk,rst,valid,rq,tag,op,rm,ftz,a,b,rv,ready,rt,value,flags);
`endif
 reg [1023:0] file;integer handle,scan,count=0,i,latency,total=0,minlat=999,maxlat=0;
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
   while(!rv)begin a=~a;b=~b;op=~op;rm=rm^3;ftz=~ftz;tag=~tag;tick();latency=latency+1;
    if(latency>120)$fatal(1,"FP vector timeout");end
   latency=latency+1;
   total=total+latency;if(latency<minlat)minlat=latency;if(latency>maxlat)maxlat=latency;
   if(value!=={e1,e0}||flags!==gflags[4:0]||rt!==16'(count+1))
    $fatal(1,"FP128 mismatch row=%0d lanes=%0d op=%0d rm=%0d ftz=%0d expected=%h/%h got=%h/%h nativecsr=%h",count,LANES,go,gr,gft,{e1,e0},gflags,value,flags,csr);
   for(i=0;i<2;i=i+1)begin a=~a;b=~b;op=~op;rm=rm^3;ftz=~ftz;tag=~tag;tick();
    if(!rv||value!=={e1,e0}||flags!==gflags[4:0]||rq)$fatal(1,"held/inactive FP changed");end
   ready=1;tick();ready=0;if(rv)$fatal(1,"reply not consumed");count=count+1;
  end
  $fclose(handle);
  // Cancel normal in-flight work, a completed low lane waiting for its high lane,
  // and a held atomic reply. The parallel low special completes before the high normal.
  for(i=0;i<3;i=i+1)begin
   @(negedge clk);a={64'h3ff0000000000001,i==1?64'b0:64'h3ff0000000000001};
   b={2{64'h4008000000000000}};op=0;rm=0;ftz=1;tag=16'habcd+i;valid=1;ready=0;
   if(i==2)begin a=0;b=0;end
   tick();valid=0;
   if(i==2)begin latency=0;while(!rv)begin tick();latency=latency+1;if(latency>120)$fatal(1,"held reset setup");end end
   else repeat(8)begin tick();if(rv)$fatal(1,"normal pair unexpectedly finished before reset");end
   rst=1;tick();rst=0;
   repeat(125)begin tick();if(rv||!rq)$fatal(1,"reset did not cancel DIVSQRT vector");end
  end
  $display("PASS divsqrt128 lanes=%0d native_vectors=%0d operations=2 rounding_modes=4 DAZ_FTZ_models=2 total_response_latency=%0d held_inactive=1 reset_busy=1 reset_partial=1 reset_held=1",LANES,count,total);$display("LATENCY vector min=%0d max=%0d total=%0d",minlat,maxlat,total);$finish;
 end
endmodule
