// SPDX-License-Identifier: BSD-3-Clause
// Tagged iterative binary64 division/square root; held completion wraps the IP pulse.
`default_nettype none
`include "HardFloat_consts.vi"
`include "HardFloat_specialize.vi"
module randomx_divsqrt64(
 input wire clk,rst,req_valid,output wire req_ready,input wire [15:0] req_tag,
 input wire req_sqrt,input wire [1:0] req_round,input wire req_ftz_daz,
 input wire [63:0] req_a,req_b,
 output reg rsp_valid,input wire rsp_ready,output reg [15:0] rsp_tag,
 output reg [63:0] rsp_result,output reg [4:0] rsp_flags
);
 wire sub_a=req_a[62:52]==0 && req_a[51:0]!=0;
 wire sub_b=req_b[62:52]==0 && req_b[51:0]!=0;
 wire [63:0] a=req_ftz_daz&&sub_a ? {req_a[63],63'b0}:req_a;
 wire [63:0] b=req_ftz_daz&&sub_b ? {req_b[63],63'b0}:req_b;
 wire [2:0] rm=req_round==0?3'd0:req_round==1?3'd2:req_round==2?3'd3:3'd1;
 wire [64:0] ar,br,out_r;wire ip_ready,ip_valid,ip_sqrt;
 wire [4:0] out_flags;wire [63:0] ieee;
 reg busy_q,ftz_q;reg [15:0] tag_q;
 fNToRecFN #(11,53) rec_a(a,ar);
 fNToRecFN #(11,53) rec_b(b,br);
 assign req_ready=!rst&&!busy_q&&(!rsp_valid||rsp_ready)&&ip_ready;
 divSqrtRecFN_small #(11,53,0) arithmetic(
  .nReset(!rst),.clock(clk),.control(`flControl_default),.inReady(ip_ready),
  .inValid(req_valid&&req_ready),.sqrtOp(req_sqrt),.a(ar),.b(br),.roundingMode(rm),
  .outValid(ip_valid),.sqrtOpOut(ip_sqrt),.out(out_r),.exceptionFlags(out_flags));
 recFNToFN #(11,53) encode(out_r,ieee);
 wire sub_out=ieee[62:52]==0 && ieee[51:0]!=0;
 // Match native SSE FTZ, including underflow rounded to minimum normal.
 wire flush=ftz_q&&(sub_out||out_flags[1]);
 always @(posedge clk)begin
  if(rst)begin busy_q<=0;ftz_q<=0;tag_q<=0;rsp_valid<=0;rsp_tag<=0;rsp_result<=0;rsp_flags<=0;end
  else begin
   if(rsp_valid&&rsp_ready)rsp_valid<=0;
   if(req_valid&&req_ready)begin busy_q<=1;ftz_q<=req_ftz_daz;tag_q<=req_tag;end
   if(busy_q&&ip_valid)begin
    busy_q<=0;rsp_valid<=1;rsp_tag<=tag_q;
    rsp_result<=flush?{ieee[63],63'b0}:ieee;
    rsp_flags<=out_flags|(flush?5'b00011:5'b0);
   end
  end
 end
endmodule
`default_nettype wire
