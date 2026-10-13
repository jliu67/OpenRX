// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_divsqrt64;
 reg clk=0;always #5 clk=~clk;
 reg rst=1,valid=0,ready=0,ftz;reg [15:0] tag;reg op;reg [1:0] rm;
 reg [63:0] a,b;wire rq,rv;wire [15:0] rt;wire [63:0] value;wire [4:0] flags;
 randomx_divsqrt64 dut(clk,rst,valid,rq,tag,op,rm,ftz,a,b,rv,ready,rt,value,flags);
 reg [1023:0] file;integer handle,scan,count=0,i,latency,total=0,minlat=999,maxlat=0;reg [63:0] ga,gb,expected;integer go,gr,gft,gflags,csr;
 task tick;begin @(posedge clk);#1;end endtask
 initial begin
  if(!$value$plusargs("vectors=%s",file))$fatal(1,"vectors missing");handle=$fopen(file,"r");if(!handle)$fatal(1,"cannot open vectors");
  tick();rst=0;tick();
  while(!$feof(handle))begin
   scan=$fscanf(handle,"%h %h %h %h %h %h %h %h\n",ga,gb,go,gr,gft,expected,gflags,csr);
   if(scan!=8)$fatal(1,"bad vector row");
   @(negedge clk);a=ga;b=gb;op=go;rm=gr;ftz=gft;tag=count+1;valid=1;ready=0;
   if(!rq)$fatal(1,"not ready");tick();valid=0;latency=1;
   while(!rv)begin a=~a;b=~b;op=~op;rm=rm^3;ftz=~ftz;tag=~tag;tick();latency=latency+1;
    if(latency>60)$fatal(1,"DIVSQRT timeout");end
   total=total+latency;if(latency<minlat)minlat=latency;if(latency>maxlat)maxlat=latency;
   if(!rv||value!==expected||flags!==gflags[4:0]||rt!==16'(count+1))
    $fatal(1,"FP mismatch row=%0d op=%0d rm=%0d ftz=%0d a=%h b=%h expected=%h/%h got=%h/%h nativecsr=%h",count,go,gr,gft,ga,gb,expected,gflags,value,flags,csr);
   for(i=0;i<2;i=i+1)begin a=~a;b=~b;op=~op;rm=rm^3;ftz=~ftz;tag=~tag;tick();
    if(!rv||value!==expected||flags!==gflags[4:0]||rq)$fatal(1,"held/inactive FP changed");end
   ready=1;tick();ready=0;if(rv)$fatal(1,"reply not consumed");count=count+1;
  end
  $fclose(handle);$display("PASS divsqrt64 native_vectors=%0d operations=2 rounding_modes=4 DAZ_FTZ_models=2 held_inactive=1",count);$display("LATENCY scalar min=%0d max=%0d total=%0d",minlat,maxlat,total);$finish;
 end
endmodule
