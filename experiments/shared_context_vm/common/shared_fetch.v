// One shared request path, four reserved one-entry prepared-instruction queues.
// Flat ports keep this same functional source usable by installed Yosys.
`default_nettype none
module openrx_shared_fetch(
 input wire clk,rst,enable,input wire[31:0]cycle,input wire[23:0]epochs,
 input wire cancel_valid,input wire[1:0]cancel_context,
 input wire[3:0]need,credit,input wire[35:0]pcs,input wire[255:0]bases,
 input wire[63:0]owners,image_epochs,
 input wire bypass_valid,input wire[1:0]bypass_context,
 input wire[63:0]bypass_addr,input wire[15:0]bypass_owner,bypass_epoch,
 input wire bypass_rsp_ready,
 output wire req_valid,input wire req_ready,output wire[1:0]req_context,
 output wire[63:0]req_addr,output wire[15:0]req_owner,req_epoch,output wire[31:0]req_token,
 input wire rsp_valid,output wire rsp_ready,input wire[31:0]rsp_token,
 input wire[15:0]rsp_owner,rsp_epoch,input wire[8:0]rsp_pc,
 input wire[63:0]rsp_word,rsp_value,input wire[31:0]rsp_divisor,
 input wire rsp_error,rsp_rcp,rsp_nop,
 input wire[1:0]pop_context,input wire pop,
 output wire[3:0]available,output wire[63:0]head_word,head_value,
 output wire[31:0]head_divisor,output wire[15:0]head_owner,head_epoch,
 output wire[8:0]head_pc,output wire head_error,head_rcp,head_nop,
 output reg[1:0]fault=0
);
 reg[3:0]reserved=0,valid=0;
 reg[31:0]token_q[0:3];reg[8:0]pc_q[0:3];reg[15:0]owner_q[0:3],epoch_q[0:3];
 reg[63:0]word_q[0:3],value_q[0:3];reg[31:0]divisor_q[0:3];
 reg error_q[0:3],rcp_q[0:3],nop_q[0:3];
 reg[10:0]next_sequence[0:3];reg[1:0]rr=0;
 reg held=0;reg[1:0]held_context=0;reg[63:0]held_addr=0;
 reg[15:0]held_owner=0,held_epoch=0;reg[8:0]held_pc=0;reg[31:0]held_token=0;
 reg pick_valid;reg[1:0]pick_context;integer i,k,c;
 wire[3:0]eligible=need&credit&~reserved&~valid;
 always @*begin
  pick_valid=0;pick_context=rr;c=0;
  for(k=0;k<4;k=k+1)begin
   c=(rr+k)&3;
   if(!pick_valid&&eligible[c]&&!(cancel_valid&&c==cancel_context))begin
    pick_context=c[1:0];pick_valid=1;
   end
  end
 end
 wire use_held=enable&&held;
 assign req_context=!enable?bypass_context:use_held?held_context:pick_context;
 wire req_cancel=cancel_valid&&req_context==cancel_context;
 assign req_valid=!rst&&fault==0&&next_sequence[req_context]<1024&&!req_cancel&&(!enable?bypass_valid:use_held||pick_valid);
 assign req_addr=!enable?bypass_addr:use_held?held_addr:bases[64*pick_context+:64]+{52'b0,pcs[9*pick_context+:9],3'b0};
 assign req_owner=!enable?bypass_owner:use_held?held_owner:owners[16*pick_context+:16];
 assign req_epoch=!enable?bypass_epoch:use_held?held_epoch:image_epochs[16*pick_context+:16];
 wire[8:0]request_pc=use_held?held_pc:pcs[9*req_context+:9];
 assign req_token=use_held?held_token:{epochs[6*req_context+:6],req_context,13'b0,next_sequence[req_context]};
 wire request_fire=req_valid&&req_ready;
 wire[1:0]response_context=rsp_token[25:24];
 wire obsolete=rsp_token[31:26]<epochs[6*response_context+:6]||
     (cancel_valid&&response_context==cancel_context);
 wire response_owned=reserved[response_context]&&!valid[response_context]&&token_q[response_context]==rsp_token;
 wire metadata_owned=owner_q[response_context]==rsp_owner&&epoch_q[response_context]==rsp_epoch&&pc_q[response_context]==rsp_pc;
 assign rsp_ready=!rst&&(enable?fault==0:bypass_rsp_ready);
 wire response_fire=rsp_valid&&rsp_ready;
 wire incoming=enable&&rsp_valid&&!obsolete&&response_owned&&metadata_owned&&fault==0;
 genvar g;
 generate for(g=0;g<4;g=g+1)begin: heads
  assign available[g]=enable&&!rst&&fault==0&&!(cancel_valid&&cancel_context==g)&&
    ((valid[g]&&token_q[g][31:26]==epochs[6*g+:6])||(incoming&&response_context==g));
 end endgenerate
 wire fallthrough=!valid[pop_context]&&incoming&&response_context==pop_context;
 assign head_word=fallthrough?rsp_word:word_q[pop_context];
 assign head_value=fallthrough?rsp_value:value_q[pop_context];
 assign head_divisor=fallthrough?rsp_divisor:divisor_q[pop_context];
 assign head_owner=owner_q[pop_context];assign head_epoch=epoch_q[pop_context];assign head_pc=pc_q[pop_context];
 assign head_error=fallthrough?rsp_error:error_q[pop_context];
 assign head_rcp=fallthrough?rsp_rcp:rcp_q[pop_context];assign head_nop=fallthrough?rsp_nop:nop_q[pop_context];
 always @(posedge clk)begin
  if(rst)begin
   reserved<=0;valid<=0;rr<=0;held<=0;held_context<=0;held_addr<=0;held_owner<=0;held_epoch<=0;held_pc<=0;held_token<=0;fault<=0;
   for(i=0;i<4;i=i+1)begin
    token_q[i]<=0;pc_q[i]<=0;owner_q[i]<=0;epoch_q[i]<=0;word_q[i]<=0;value_q[i]<=0;divisor_q[i]<=0;
    error_q[i]<=0;rcp_q[i]<=0;nop_q[i]<=0;next_sequence[i]<=0;
   end
  end else begin
   if(!req_cancel&&(!enable?bypass_valid:use_held||pick_valid)&&next_sequence[req_context]>=1024)fault<=3;
   if(req_valid&&!req_ready&&enable&&!held)begin
    held<=1;held_context<=req_context;held_addr<=req_addr;held_owner<=req_owner;held_epoch<=req_epoch;held_pc<=request_pc;held_token<=req_token;
   end
   if(request_fire)begin
    if(next_sequence[req_context]>=1024)fault<=3;
    else begin
     next_sequence[req_context]<=next_sequence[req_context]+1'b1;
     if(enable)begin
      if(reserved[req_context]||valid[req_context])fault<=3;
      else begin
       reserved[req_context]<=1;valid[req_context]<=0;token_q[req_context]<=req_token;
       pc_q[req_context]<=request_pc;owner_q[req_context]<=req_owner;epoch_q[req_context]<=req_epoch;
      end
      rr<=req_context+2'd1;held<=0;
     end
    end
   end
   if(response_fire&&enable&&!obsolete)begin
    if(!response_owned)fault<=1;
    else if(!metadata_owned)fault<=2;
    else begin
     word_q[response_context]<=rsp_word;value_q[response_context]<=rsp_value;divisor_q[response_context]<=rsp_divisor;
     error_q[response_context]<=rsp_error;rcp_q[response_context]<=rsp_rcp;nop_q[response_context]<=rsp_nop;
     valid[response_context]<=1;
    end
   end
   if(pop&&enable)begin
    if(!available[pop_context])fault<=3;
    else begin reserved[pop_context]<=0;valid[pop_context]<=0;end
   end
   // Cancellation frees only its context's queue; accepted old external reads
   // retain external credit until an obsolete response is explicitly drained.
   if(cancel_valid)begin
    reserved[cancel_context]<=0;valid[cancel_context]<=0;next_sequence[cancel_context]<=0;
    if(held&&held_context==cancel_context)held<=0;
   end
  end
 end
`ifndef SYNTHESIS
 // Diagnostic state is excluded from generic area/state accounting.
 integer requests=0,responses=0,pops=0,stale=0,flushed_valid=0;
 integer peak_reserved=0,peak_valid=0,reserved_cycles=0,valid_cycles=0,backpressure=0,peak_age=0;
 integer age[0:3],nr,nv,a;reg[3:0]was_queued=0;reg[235:0]saved_packet[0:3];
 reg was_held=0;reg[129:0]held_snapshot=0;
 always @(posedge clk)begin
  if(rst)begin
   requests=0;responses=0;pops=0;stale=0;flushed_valid=0;peak_reserved=0;peak_valid=0;
   reserved_cycles=0;valid_cycles=0;backpressure=0;peak_age=0;was_held=0;was_queued=0;
   for(a=0;a<4;a=a+1)age[a]=0;
  end else begin
   if(was_held&&!(cancel_valid&&req_context==cancel_context)&&(!req_valid||{req_context,req_addr,req_owner,req_epoch,req_token}!==held_snapshot))$fatal(1,"held shared instruction request changed");
   was_held=req_valid&&!req_ready;held_snapshot={req_context,req_addr,req_owner,req_epoch,req_token};
   for(a=0;a<4;a=a+1)begin
    if(was_queued[a]&&!(pop&&pop_context==a)&&!(cancel_valid&&cancel_context==a)&&
       (!valid[a]||{token_q[a],pc_q[a],owner_q[a],epoch_q[a],word_q[a],value_q[a],divisor_q[a],error_q[a],rcp_q[a],nop_q[a]}!==saved_packet[a]))$fatal(1,"held instruction queue packet changed");
    was_queued[a]=valid[a]&&!(pop&&pop_context==a)&&!(cancel_valid&&cancel_context==a);
    saved_packet[a]={token_q[a],pc_q[a],owner_q[a],epoch_q[a],word_q[a],value_q[a],divisor_q[a],error_q[a],rcp_q[a],nop_q[a]};
   end
   nr=0;nv=0;for(a=0;a<4;a=a+1)begin nr=nr+(reserved[a]?1:0);nv=nv+(valid[a]?1:0);end
   if(nr>4||nv>4||((valid&~reserved)!=0))$fatal(1,"one-entry fetch credit invariant");
   if(nr>peak_reserved)peak_reserved=nr;if(nv>peak_valid)peak_valid=nv;
   reserved_cycles=reserved_cycles+nr;valid_cycles=valid_cycles+nv;
   if(req_valid&&!req_ready)backpressure=backpressure+1;
   if(request_fire)requests=requests+1;
   if(response_fire)responses=responses+1;
   if(enable&&response_fire)begin
    if(obsolete)stale=stale+1;
    $display("IR %0h %0h %0h %0h %0h",cycle,response_context,rsp_token,rsp_pc,obsolete);
   end
   if(enable&&pop)begin
    pops=pops+1;
    $display("IP %0h %0h %0h %0h %0h %0h %0h %0h %0h %0h %0h %0h",cycle,pop_context,token_q[pop_context],head_pc,head_owner,head_epoch,head_word,head_value,head_divisor,head_error,head_rcp,head_nop);
   end
   if(cancel_valid&&valid[cancel_context])flushed_valid=flushed_valid+1;
   for(a=0;a<4;a=a+1)begin
    if(!enable||!eligible[a]||(cancel_valid&&cancel_context==a))age[a]=0;
    else if(request_fire)begin
     if(req_context==a)age[a]=0;
     else begin age[a]=age[a]+1;if(age[a]>3)$fatal(1,"shared instruction RR fairness");end
    end
    if(age[a]>peak_age)peak_age=age[a];
   end
  end
 end
`endif
endmodule
`default_nettype wire
