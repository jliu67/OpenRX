// Experimental four-context iteration shell. One shared converter view and
// one unchanged golden AES/tail unit; no replicated execution engines/FUs.
`default_nettype none
module openrx_iteration_shell(
 input wire clk,rst,interleave,input wire[31:0]cycle,
 input wire[1:0]core_context,input wire core_selected,core_start,core_return,
 output wire[3:0]starts,core_memory_available,core_memory_credit,
 output wire[511:0]entry_r,entry_f,entry_e,entry_a,
 output wire[63:0]entry_em0,entry_em1,program_base,
 input wire[511:0]kernel_r,kernel_f,kernel_e,input wire[1:0]kernel_round,
 input wire core_rd,core_wr,core_rsp_ready,input wire[20:0]core_ra,core_wa,
 input wire[127:0]core_wd,input wire[15:0]core_strb,
 output wire core_rd_ready,core_wr_ready,core_rsp_valid,
 output wire[127:0]core_rsp_data,output wire[15:0]core_rsp_tag,
 output wire mem_valid,mem_write,output wire[1:0]mem_context,
 output wire[20:0]mem_addr,output wire[127:0]mem_data,output wire[15:0]mem_strb,
 output wire[1:0]mem_kind,input wire[3:0]mem_credit,mem_available,
 input wire mem_rsp_valid,output wire mem_rsp_ready,input wire[1:0]mem_rsp_context,
 input wire[127:0]mem_rsp_data,input wire[15:0]mem_rsp_tag,
 output wire ds_valid,output wire[1:0]ds_context,output wire[63:0]ds_addr,ds_prefetch,
 output wire[15:0]ds_tag,input wire ds_ready,ds_rsp_valid,output wire ds_rsp_ready,
 input wire[1:0]ds_rsp_context,input wire[15:0]ds_rsp_tag,input wire[511:0]ds_data,
 output wire[3:0]completed
);
 `include "fixture.vh"
 localparam E0Q=0,E0W=1,E1Q=2,E1W=3,READY=4,RUN=5,DQ=6,DW=7,TQ=8,TW=9,DONE=10;
 reg[3:0]phase[0:3];reg[1:0]beat[0:3];
 reg[511:0]line0[0:3],line1[0:3],rr[0:3],ff[0:3],ee[0:3];reg[1:0]round_q[0:3];
 reg[31:0]mx[0:3],ma[0:3];reg[63:0]daddr[0:3],prefetch[0:3];
 reg[1:0]serial_cursor=0,mem_rr=0,ds_rr=0,tail_rr=0,tail_owner=0;
 reg tail_busy=0;wire[3:0]active;
 genvar g;
 generate for(g=0;g<4;g=g+1)begin: context_state
  assign active[g]=interleave||g==serial_cursor;
  assign starts[g]=!rst&&active[g]&&phase[g]==READY;
  assign completed[g]=phase[g]==DONE;
  assign core_memory_available[g]=phase[g]==RUN&&mem_available[g];
  assign core_memory_credit[g]=phase[g]==RUN&&mem_credit[g];
 end endgenerate
 wire[63:0]converted[0:15];
 generate for(g=0;g<16;g=g+1)begin: conversion
  randomx_i32_to_f64 convert(line1[core_context][32*g+:32],converted[g]);
 end
 for(g=0;g<8;g=g+1)begin: converted_registers
  assign entry_f[64*g+:64]=converted[g];
  assign entry_e[64*g+:64]=(converted[g+8]&64'h00ffffffffffffff)|(g%2==0?EM0[core_context]:EM1[core_context]);
 end endgenerate
 assign entry_r=line0[core_context];assign entry_a=A[core_context];
 assign entry_em0=EM0[core_context];assign entry_em1=EM1[core_context];
 assign program_base=64'h10000000+{50'b0,core_context,12'b0};
 reg mq_valid;reg[1:0]mq_context;integer k,c;
 always @*begin
  mq_valid=0;mq_context=mem_rr;c=0;
  for(k=0;k<4;k=k+1)begin
   c=(integer'(mem_rr)+k)&3;
   if(!mq_valid&&active[c]&&mem_credit[c]&&
    (phase[c]==E0Q||phase[c]==E1Q||
     (phase[c]==RUN&&core_selected&&core_context==c&&(core_rd||core_wr))||
     (phase[c]==TW&&tail_busy&&tail_owner==c&&tail_wr_valid)))begin mq_valid=1;mq_context=c[1:0];end
  end
 end
 assign mem_context=mq_context;assign mem_valid=!rst&&mq_valid;
 assign mem_kind=phase[mq_context]==RUN?2'd1:phase[mq_context]==TW?2'd2:2'd0;
 assign mem_write=mem_kind==2||(mem_kind==1&&core_wr);
 assign mem_addr=mem_kind==1?(core_wr?core_wa:core_ra):mem_kind==2?tail_addr:
  (phase[mq_context]==E0Q?L0[mq_context]:L1[mq_context])+{15'b0,beat[mq_context],4'b0};
 assign mem_data=mem_kind==1?core_wd:tail_data;assign mem_strb=mem_kind==1?core_strb:tail_strb;
 assign core_rd_ready=mem_valid&&mem_kind==1&&!mem_write;
 assign core_wr_ready=mem_valid&&mem_kind==1&&mem_write;
 assign core_rsp_valid=mem_rsp_valid&&phase[mem_rsp_context]==RUN&&mem_rsp_context==core_context;
 // Invalid cycles must not feed a different physical context's tag into
 // the core's stale/ready combinational path. Actual returns are checked
 // against the physical owner below before any data is consumed.
 assign core_rsp_data=mem_rsp_data;assign core_rsp_tag={6'd1,core_context,8'b0};
 assign mem_rsp_ready=!rst&&(phase[mem_rsp_context]==E0W||phase[mem_rsp_context]==E1W||
  (phase[mem_rsp_context]==RUN&&mem_rsp_context==core_context&&core_rsp_ready));
 reg dq_valid,tq_valid;reg[1:0]dq_context,tq_context;integer d,j,t,h;
 always @*begin
  dq_valid=0;dq_context=ds_rr;d=0;
  for(j=0;j<4;j=j+1)begin d=(integer'(ds_rr)+j)&3;if(!dq_valid&&active[d]&&phase[d]==DQ)begin dq_valid=1;dq_context=d[1:0];end end
  tq_valid=0;tq_context=tail_rr;t=0;
  for(h=0;h<4;h=h+1)begin t=(integer'(tail_rr)+h)&3;if(!tq_valid&&active[t]&&phase[t]==TQ)begin tq_valid=1;tq_context=t[1:0];end end
 end
 assign ds_valid=!rst&&dq_valid;assign ds_context=dq_context;assign ds_addr=daddr[dq_context];assign ds_prefetch=prefetch[dq_context];
 assign ds_tag={6'd1,dq_context,8'b0};assign ds_rsp_ready=!rst&&phase[ds_rsp_context]==DW;
 wire tail_ready,tail_done,tail_wr_valid;wire[20:0]tail_addr;wire[127:0]tail_data;wire[15:0]tail_strb;
 wire[511:0]tail_f;wire[31:0]next0,next1;
 wire tail_start=!rst&&!tail_busy&&tq_valid;
 randomx_iteration_store #(.LANES(1),.OVERLAP_R(1)) shared_tail(
  .clk(clk),.rst(rst),.req_valid(tail_start),.req_ready(tail_ready),.req_v2(1'b1),
  .req_r(rr[tq_context]),.req_f(ff[tq_context]),.req_e(ee[tq_context]),
  .req_f_line(L0[tq_context][20:6]),.req_r_line(L1[tq_context][20:6]),
  .wr_valid(tail_wr_valid),.wr_ready(mem_valid&&mem_kind==2),.wr_addr(tail_addr),.wr_data(tail_data),.wr_strb(tail_strb),
  .done_valid(tail_done),.done_ready(tail_busy),.done_f(tail_f),.done_spaddr0(next0),.done_spaddr1(next1));
 integer i;
 wire[63:0]mix=kernel_r[64*READ2[core_context]+:64]^kernel_r[64*READ3[core_context]+:64];
 always @(posedge clk)begin
  if(rst)begin
   serial_cursor<=0;mem_rr<=0;ds_rr<=0;tail_rr<=0;tail_owner<=0;tail_busy<=0;
   for(i=0;i<4;i=i+1)begin phase[i]<=E0Q;beat[i]<=0;line0[i]<=0;line1[i]<=0;rr[i]<=0;ff[i]<=0;ee[i]<=0;round_q[i]<=0;mx[i]<=MX[i];ma[i]<=MA[i];daddr[i]<=0;prefetch[i]<=0;end
  end else begin
   if(mem_valid)begin
    mem_rr<=mem_context+2'd1;
    if(mem_kind==0)phase[mem_context]<=phase[mem_context]==E0Q?E0W:E1W;
   end
   if(mem_rsp_valid&&mem_rsp_ready)begin
    if(mem_rsp_tag!=={6'd1,mem_rsp_context,8'b0})$fatal(1,"iteration SP response owner");
    if(phase[mem_rsp_context]==E0W)begin
     line0[mem_rsp_context][128*beat[mem_rsp_context]+:128]<=mem_rsp_data;
     if(beat[mem_rsp_context]==3)begin beat[mem_rsp_context]<=0;phase[mem_rsp_context]<=E1Q;end
     else begin beat[mem_rsp_context]<=beat[mem_rsp_context]+1'b1;phase[mem_rsp_context]<=E0Q;end
    end else if(phase[mem_rsp_context]==E1W)begin
     line1[mem_rsp_context][128*beat[mem_rsp_context]+:128]<=mem_rsp_data;
     if(beat[mem_rsp_context]==3)begin beat[mem_rsp_context]<=0;phase[mem_rsp_context]<=READY;end
     else begin beat[mem_rsp_context]<=beat[mem_rsp_context]+1'b1;phase[mem_rsp_context]<=E1Q;end
    end
   end
   if(core_start)begin
    if(phase[core_context]!=READY||entry_r!==ENTRY_R[core_context]||entry_f!==ENTRY_F[core_context]||entry_e!==ENTRY_E[core_context])$fatal(1,"actual native entry read/convert mismatch");
    phase[core_context]<=RUN;
   end
   if(core_return)begin
    if(phase[core_context]!=RUN)$fatal(1,"iteration kernel return owner");
    rr[core_context]<=kernel_r;ff[core_context]<=kernel_f;ee[core_context]<=kernel_e;round_q[core_context]<=kernel_round;
    daddr[core_context]<=OFFSET[core_context]+{32'b0,ma[core_context]&32'h7fffffc0};
    prefetch[core_context]<=OFFSET[core_context]+{32'b0,(ma[core_context]^mix[31:0])&32'h7fffffc0};
    mx[core_context]<=ma[core_context]^mix[31:0];ma[core_context]<=mx[core_context];phase[core_context]<=DQ;
   end
   if(ds_valid&&ds_ready)begin phase[ds_context]<=DW;ds_rr<=ds_context+2'd1;end
   if(ds_rsp_valid&&ds_rsp_ready)begin
    if(ds_rsp_tag!=={6'd1,ds_rsp_context,8'b0})$fatal(1,"iteration dataset response owner");
    rr[ds_rsp_context]<=rr[ds_rsp_context]^ds_data;phase[ds_rsp_context]<=TQ;
   end
   if(tail_start&&tail_ready)begin tail_busy<=1;tail_owner<=tq_context;phase[tq_context]<=TW;end
   if(tail_done&&tail_busy)begin
    if(phase[tail_owner]!=TW||next0!=0||next1!=0||rr[tail_owner]!==GR[tail_owner]||tail_f!==GF[tail_owner]||ee[tail_owner]!==GE[tail_owner]||round_q[tail_owner]!==ROUND[tail_owner]||mx[tail_owner]!==NEXT_MX[tail_owner]||ma[tail_owner]!==NEXT_MA[tail_owner])$fatal(1,"native full iteration RF/control closure context=%0d",tail_owner);
    ff[tail_owner]<=tail_f;phase[tail_owner]<=DONE;tail_busy<=0;tail_rr<=tail_owner+2'd1;
    if(!interleave&&serial_cursor!=3)serial_cursor<=serial_cursor+2'd1;
    $display("ITER_DONE %0h %0h %0h %0h %0h %0h %0h",cycle,tail_owner,rr[tail_owner],tail_f,ee[tail_owner],mx[tail_owner],ma[tail_owner]);
   end
  end
 end
endmodule
`default_nettype wire
