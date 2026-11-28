// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module activity68 #(parameter W=70,ID=0)(input wire [W-1:0] value,input wire [1:0] phase);
 reg [W-1:0] prior={W{1'bx}};integer binary[0:3],fourstate[0:3];integer i,j;
 integer first0=0,first1=0,first2=0,first3=0;reg log_first;
 initial for(i=0;i<4;i=i+1)begin binary[i]=0;fourstate[i]=0;end
 always @(value)begin
  log_first=0;
  if(ID>=8)case(phase)
   0:if(first0<3)begin first0=first0+1;log_first=1;end
   1:if(first1<2)begin first1=first1+1;log_first=1;end
   2:if(first2<2)begin first2=first2+1;log_first=1;end
   3:if(first3<2)begin first3=first3+1;log_first=1;end
  endcase
  if(log_first)$display("FIRST id=%0d phase=%0d time=%0t prior=%h value=%h",ID,phase,$time,prior,value);
  if(phase!=0)for(j=0;j<W;j=j+1)if(value[j]!==prior[j])begin
   if((value[j]===1'b0||value[j]===1'b1)&&(prior[j]===1'b0||prior[j]===1'b1))binary[phase]=binary[phase]+1;
   else fourstate[phase]=fourstate[phase]+1;
  end
  prior=value;
 end
 task snapshot(input integer label);integer n;begin
  n=0;for(integer b=0;b<W;b=b+1)if(value[b]!==1'b0&&value[b]!==1'b1)n=n+1;
  $display("SNAP label=%0d id=%0d time=%0t unknown=%0d prior=%h value=%h",label,ID,$time,n,prior,value);
  if(n!=0)$fatal(1,"isolated observed vector not known label=%0d id=%0d unknown=%0d",label,ID,n);
  if(prior!==value)$fatal(1,"monitor history disagrees with vector label=%0d id=%0d",label,ID);
 end endtask
 task report;integer p;begin for(p=1;p<4;p=p+1)$display("ACT id=%0d phase=%0d binary=%0d fourstate=%0d",ID,p,binary[p],fourstate[p]);end endtask
endmodule

module tb_compare;
 reg clk=0;always #5 clk=~clk;
 reg rst=1,valid=0,ready=1,ftz=1;reg [15:0] tag=0;reg [1:0] op=0,rm=0,phase=0;
 reg [127:0] a=0,b=0;wire q0,q1,v0,v1;wire [15:0] t0,t1;wire [127:0] r0,r1;wire [4:0] f0,f1;
 randomx_fp128 #(.LANES(2)) base(clk,rst,valid,q0,tag,op,rm,ftz,a,b,v0,ready,t0,r0,f0);
 randomx_fp128_iso68 #(.LANES(2)) isolated(clk,rst,valid,q1,tag,op,rm,ftz,a,b,v1,ready,t1,r1,f1);
 integer nexttag=1,accepted=0,native_rows=0,corner_rows=0,cycles=0,i,j,k,z,scan,handle;
 reg [1023:0] file;reg [127:0] aa,bb,expected;integer go,gr,gft;
 reg [63:0] ca[0:7],cb[0:7];reg [127:0] held;reg [4:0] heldflags;reg [15:0] heldtag;
 task same;begin
  if({q0,v0,t0,r0,f0}!=={q1,v1,t1,r1,f1})$fatal(1,"equivalence cycle=%0d tag=%h op=%b round=%b",cycles,tag,op,rm);
 end endtask
 task tick;begin @(posedge clk);#1;cycles=cycles+1;same();if(cycles>600)$fatal(1,"cycle guard");end endtask
 task junk(input integer n);begin
  a={64'h0123456789abcdef^(64'h9e3779b97f4a7c15*n),64'hfedcba9876543210^(64'hbf58476d1ce4e5b9*n)};
  b={a[63:0]^64'hbaddecaf01234567,a[127:64]^64'h082efa98ec4e6c89};
  op=n%4;rm=(n/3)%4;ftz=n%2;tag=n;
 end endtask
 task send(input [127:0] x,y,input [1:0] o,m,input f,check_native,input [127:0] expect_result);
 begin
  @(negedge clk);a=x;b=y;op=o;rm=m;ftz=f;tag=nexttag;nexttag=nexttag+1;valid=1;ready=1;
  #1;if(q0!==1'b1||q1!==1'b1)$fatal(1,"acceptance blocked");tick();accepted=accepted+1;
  if(!v0||t0!==16'(nexttag-1))$fatal(1,"one-cycle tag/valid");
  if(check_native&&r0!==expect_result)$fatal(1,"retained native result row=%0d got=%h expected=%h",native_rows,r0,expect_result);
 end endtask
 activity68 #(.W(134),.ID(0)) mon0({base.parallel.lane0.rm,(base.parallel.lane0.req_op==1),base.parallel.lane0.ar,base.parallel.lane0.br},phase);
 activity68 #(.W(70),.ID(1)) mon1({base.parallel.lane0.add_flags,base.parallel.lane0.add_r},phase);
 activity68 #(.W(133),.ID(2)) mon2({base.parallel.lane0.rm,base.parallel.lane0.ar,base.parallel.lane0.br},phase);
 activity68 #(.W(70),.ID(3)) mon3({base.parallel.lane0.mul_flags,base.parallel.lane0.mul_r},phase);
 activity68 #(.W(134),.ID(4)) mon4({base.parallel.lane1.rm,(base.parallel.lane1.req_op==1),base.parallel.lane1.ar,base.parallel.lane1.br},phase);
 activity68 #(.W(70),.ID(5)) mon5({base.parallel.lane1.add_flags,base.parallel.lane1.add_r},phase);
 activity68 #(.W(133),.ID(6)) mon6({base.parallel.lane1.rm,base.parallel.lane1.ar,base.parallel.lane1.br},phase);
 activity68 #(.W(70),.ID(7)) mon7({base.parallel.lane1.mul_flags,base.parallel.lane1.mul_r},phase);
 activity68 #(.W(134),.ID(8)) mon8({isolated.parallel.lane0.add_rm,isolated.parallel.lane0.add_subtract,isolated.parallel.lane0.add_a,isolated.parallel.lane0.add_b},phase);
 activity68 #(.W(70),.ID(9)) mon9({isolated.parallel.lane0.add_flags,isolated.parallel.lane0.add_r},phase);
 activity68 #(.W(133),.ID(10)) mon10({isolated.parallel.lane0.mul_rm,isolated.parallel.lane0.mul_a,isolated.parallel.lane0.mul_b},phase);
 activity68 #(.W(70),.ID(11)) mon11({isolated.parallel.lane0.mul_flags,isolated.parallel.lane0.mul_r},phase);
 activity68 #(.W(134),.ID(12)) mon12({isolated.parallel.lane1.add_rm,isolated.parallel.lane1.add_subtract,isolated.parallel.lane1.add_a,isolated.parallel.lane1.add_b},phase);
 activity68 #(.W(70),.ID(13)) mon13({isolated.parallel.lane1.add_flags,isolated.parallel.lane1.add_r},phase);
 activity68 #(.W(133),.ID(14)) mon14({isolated.parallel.lane1.mul_rm,isolated.parallel.lane1.mul_a,isolated.parallel.lane1.mul_b},phase);
 activity68 #(.W(70),.ID(15)) mon15({isolated.parallel.lane1.mul_flags,isolated.parallel.lane1.mul_r},phase);
 task known_quiet(input integer label);begin
  $display("GATE label=%0d time=%0t accepted=%b/%b add=%b/%b mul=%b/%b",label,$time,isolated.parallel.lane0.accepted,isolated.parallel.lane1.accepted,isolated.parallel.lane0.add_active,isolated.parallel.lane1.add_active,isolated.parallel.lane0.mul_active,isolated.parallel.lane1.mul_active);
  mon8.snapshot(label);
  mon9.snapshot(label);
  mon10.snapshot(label);
  mon11.snapshot(label);
  mon12.snapshot(label);
  mon13.snapshot(label);
  mon14.snapshot(label);
  mon15.snapshot(label);
  if({isolated.parallel.lane0.add_active,isolated.parallel.lane0.mul_active,isolated.parallel.lane1.add_active,isolated.parallel.lane1.mul_active}!==4'b0000)$fatal(1,"idle gates not known disabled");
 end endtask
 initial begin
  ca[0]=0;cb[0]=64'h8000000000000000;
  ca[1]=1;cb[1]=64'h0010000000000000;
  ca[2]=64'h7ff0000000000000;cb[2]=0;
  ca[3]=64'h7ff8000000001234;cb[3]=64'hfff8000000005678;
  ca[4]=64'h7ff0000000001234;cb[4]=64'hfff0000000005678;
  ca[5]=64'h7fefffffffffffff;cb[5]=64'h4000000000000000;
  ca[6]=64'h0010000000000000;cb[6]=64'h3fefffffffffffff;
  ca[7]=64'h3ff0000000000000;cb[7]=64'h3ca0000000000000;
  tick();tick();rst=0;tick();#1;known_quiet(1);#1;known_quiet(2);phase=1;
  for(i=0;i<64;i=i+1)begin @(negedge clk);junk(i+1);valid=0;tick();end
  phase=0;valid=0;tick();phase=2;
  if(!$value$plusargs("vectors=%s",file))$fatal(1,"vectors missing");handle=$fopen(file,"r");if(!handle)$fatal(1,"vector open");
  while(!$feof(handle))begin
   scan=$fscanf(handle,"%h %h %h %h %h %h\n",go,gr,gft,aa,bb,expected);if(scan!=6)$fatal(1,"vector row");
   send(aa,bb,go,gr,gft,1,expected);native_rows=native_rows+1;
  end
  $fclose(handle);if(native_rows!=12)$fatal(1,"exact native subset");
  for(i=0;i<8;i=i+1)for(j=0;j<3;j=j+1)for(k=0;k<4;k=k+1)for(z=0;z<2;z=z+1)begin
   send({cb[i],ca[i]},{ca[i],cb[i]},j,k,z,0,0);corner_rows=corner_rows+1;
  end
  // Alias op3 and accepted unknown controls retain original four-state behavior.
  phase=0;send({2{64'h3ff0000000000000}},{2{64'h4000000000000000}},3,0,1,0,0);
  send({2{64'h3ff0000000000000}},{2{64'h4000000000000000}},2'bx1,0,1,0,0);
  send({2{64'h3ff0000000000000}},{2{64'h4000000000000000}},2,2'bxx,1,0,0);
  send({2{64'h3ff0000000000000}},{2{64'h4000000000000000}},0,0,1'bx,0,0);
  @(negedge clk);valid=1'bx;tick();@(negedge clk);valid=1'bz;tick();
  @(negedge clk);valid=0;ready=1;tick();
  @(negedge clk);ready=0;valid=1;a={2{64'h3ff0000000000000}};b={2{64'h3ca0000000000000}};op=0;rm=0;ftz=1;tag=16'hbabe;
  tick();accepted=accepted+1;valid=0;held=r0;heldflags=f0;heldtag=t0;#2;phase=3;
  for(i=0;i<32;i=i+1)begin
   @(negedge clk);junk(i+91);valid=i%2;
   if(i==7)begin a=128'bx;b=128'bz;op=2'bxx;rm=2'bzz;ftz=1'bx;end
   tick();if(!v0||q0||r0!==held||f0!==heldflags||t0!==heldtag)$fatal(1,"held response/backpressure");
  end
  phase=0;@(negedge clk);rst=1;valid=1;tick();if(v0||r0!==0||f0!==0||t0!==0)$fatal(1,"reset/cancel");
  @(negedge clk);rst=0;valid=0;ready=1;repeat(8)begin tick();if(v0||!q0)$fatal(1,"stale response");end
  mon0.report();
  mon1.report();
  mon2.report();
  mon3.report();
  mon4.report();
  mon5.report();
  mon6.report();
  mon7.report();
  mon8.report();
  mon9.report();
  mon10.report();
  mon11.report();
  mon12.report();
  mon13.report();
  mon14.report();
  mon15.report();
  $display("PASS isolation68 native=12 corners=192 op3=1 unknown_controls=3 unknown_valid=2 idle=64 held=32 reset_cancel=1 accepted=%0d cycles=%0d",accepted,cycles);$finish;
 end
endmodule
