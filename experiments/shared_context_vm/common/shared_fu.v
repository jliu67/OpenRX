// One actual FU per KIND, one active request plus four reserved return slots.
// Instrumentation/assertions are experimental; no physical implementation claim.
`timescale 1ns/1ps
module openrx_shared_fu #(parameter integer KIND=0)(
 input wire clk,rst,input wire [31:0] cycle,input wire [3:0][5:0] epochs,
 input wire cancel_valid,input wire [1:0] cancel_context,
 input wire [1:0] context_index,input wire selected,
 input wire req_valid,output wire req_ready,input wire [15:0] core_owner,
 input wire [127:0] a,b,input wire [1:0] op,round_mode,input wire high,signed_high,
 output wire rsp_valid,input wire rsp_ready,output wire [15:0] rsp_owner,
 output wire [127:0] result,output wire [4:0] flags,
 output wire [3:0] request_available,return_available,input wire [2:0] hold_cycles,
 output reg busy=0,output reg [31:0] accepted=0,returned=0,consumed=0,stale_dropped=0,held_cycles=0,
 output reg [2:0] peak_reserved=0
);
 reg [3:0] reserved=0,mail_valid=0;
 reg [7:0] next_sequence[0:3];reg[15:0]mail_token[0:3],mail_owner[0:3];
 reg[127:0]mail_data[0:3];reg[4:0]mail_flags[0:3];
 reg[15:0] inflight_token=0,inflight_owner=0;
 reg[2:0] delay_q=0;
 wire[15:0] token={epochs[context_index],context_index,next_sequence[context_index]};
 wire unit_ready,unit_valid;wire[15:0]unit_tag;wire[127:0]unit_result;wire[4:0]unit_flags;
 wire owner_current=inflight_token[15:10]==epochs[inflight_token[9:8]]&&
     !(cancel_valid&&cancel_context==inflight_token[9:8]);
 wire unit_take=busy&&delay_q==0;
 wire fire=selected&&!cancel_valid&&req_valid&&req_ready;
 assign req_ready=!rst&&!busy&&!reserved[context_index]&&unit_ready;
 genvar g;
 generate for(g=0;g<4;g=g+1)begin: availability
  assign request_available[g]=!rst&&!busy&&!reserved[g]&&unit_ready;
  assign return_available[g]=!rst&&mail_valid[g]&&mail_token[g][15:10]==epochs[g];
 end endgenerate
 assign rsp_valid=selected&&return_available[context_index];
 assign rsp_owner=mail_owner[context_index];
 assign result=mail_data[context_index];assign flags=mail_flags[context_index];
 generate if(KIND==0)begin: multiply
  wire[63:0] value;
  randomx_mul64 #(.RADIX4(0)) unit(clk,rst,fire,unit_ready,token,a[63:0],b[63:0],high,signed_high,
   unit_valid,unit_take,unit_tag,value);
  assign unit_result={64'b0,value};assign unit_flags=0;
 end else if(KIND==1)begin: floating
  randomx_fp128 #(.LANES(2)) unit(clk,rst,fire,unit_ready,token,op,round_mode,1'b1,a,b,
   unit_valid,unit_take,unit_tag,unit_result,unit_flags);
 end else if(KIND==2)begin: division
  randomx_divsqrt128 #(.LANES(2)) unit(clk,rst,fire,unit_ready,token,op[0],round_mode,1'b1,a,b,
   unit_valid,unit_take,unit_tag,unit_result,unit_flags);
 end else begin: invalid_kind
  shared_fu_kind_must_be_0_1_2 invalid();
 end endgenerate
 reg was_held=0;reg[148:0]held_packet=0;
 integer i,n;
 always @(posedge clk)begin
  if(rst)begin
   busy<=0;reserved<=0;mail_valid<=0;delay_q<=0;accepted<=0;returned<=0;consumed<=0;stale_dropped<=0;held_cycles<=0;peak_reserved<=0;was_held<=0;
   for(i=0;i<4;i=i+1)begin next_sequence[i]<=0;mail_token[i]<=0;mail_owner[i]<=0;mail_data[i]<=0;mail_flags[i]<=0;end
  end else begin
   if(was_held&&(!unit_valid||{unit_tag,unit_result,unit_flags}!==held_packet))$fatal(1,"shared held return changed kind=%0d",KIND);
   was_held<=unit_valid&&!unit_take;held_packet<={unit_tag,unit_result,unit_flags};
   n=0;for(i=0;i<4;i=i+1)n=n+(reserved[i]?1:0);
   if(n>4)$fatal(1,"shared return credit bound");if(n>peak_reserved)peak_reserved<=n[2:0];
   if(fire)begin
    if(next_sequence[context_index]==8'hff||core_owner!=={epochs[context_index],context_index,8'b0})$fatal(1,"shared request sequence/owner bound");
    busy<=1;reserved[context_index]<=1;inflight_token<=token;inflight_owner<=core_owner;next_sequence[context_index]<=next_sequence[context_index]+1'b1;
    delay_q<=hold_cycles;accepted<=accepted+1;
    $display("FQ %0h %0h %0h %0h %0h %0h %0h %0h %0h %0h %0h %0h %0h",cycle,KIND,context_index,epochs[context_index],next_sequence[context_index],token,core_owner,op,round_mode,high,signed_high,a,b);
   end
   if(unit_valid)begin
    if(!busy||unit_tag!==inflight_token)$fatal(1,"unowned shared FU result kind=%0d",KIND);
    if(delay_q!=0)begin delay_q<=delay_q-1'b1;held_cycles<=held_cycles+1;end
    if(unit_take)begin
     busy<=0;returned<=returned+1;
     $display("FR %0h %0h %0h %0h %0h %0h %0h %0h",cycle,KIND,inflight_token[9:8],inflight_token[15:10],inflight_token,unit_result,unit_flags,!owner_current);
     if(owner_current)begin
      if(!reserved[inflight_token[9:8]]||mail_valid[inflight_token[9:8]])$fatal(1,"unreserved/overwritten shared mailbox");
      mail_data[inflight_token[9:8]]<=unit_result;mail_flags[inflight_token[9:8]]<=unit_flags;
      mail_token[inflight_token[9:8]]<=inflight_token;mail_owner[inflight_token[9:8]]<=inflight_owner;mail_valid[inflight_token[9:8]]<=1;
     end else stale_dropped<=stale_dropped+1;
    end
   end
   if(rsp_valid&&rsp_ready)begin
    if(!reserved[context_index]||rsp_owner!==core_owner)$fatal(1,"wrong epoch/context return recipient");
    reserved[context_index]<=0;mail_valid[context_index]<=0;consumed<=consumed+1;
    $display("FC %0h %0h %0h %0h %0h",cycle,KIND,context_index,epochs[context_index],mail_token[context_index]);
   end
   if(cancel_valid)begin
    reserved[cancel_context]<=0;mail_valid[cancel_context]<=0;next_sequence[cancel_context]<=0;
   end
  end
 end
endmodule
