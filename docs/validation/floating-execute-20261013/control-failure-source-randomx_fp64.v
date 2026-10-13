// SPDX-License-Identifier: BSD-3-Clause
// Tagged binary64 operations using byte-identical Berkeley HardFloat1/8086-SSE.
`default_nettype none
module randomx_fp64(
 input wire clk,rst,req_valid,output wire req_ready,input wire [15:0] req_tag,
 input wire [1:0] req_op,req_round,input wire req_ftz_daz,input wire [63:0] req_a,req_b,
 output reg rsp_valid,input wire rsp_ready,output reg [15:0] rsp_tag,
 output reg [63:0] rsp_result,output reg [4:0] rsp_flags
);
 wire sub_a=req_a[62:52]==0 && req_a[51:0]!=0;
 wire sub_b=req_b[62:52]==0 && req_b[51:0]!=0;
 wire [63:0] a=req_ftz_daz&&sub_a ? {req_a[63],63'b0}:req_a;
 wire [63:0] b=req_ftz_daz&&sub_b ? {req_b[63],63'b0}:req_b;
 wire [2:0] rm=req_round==0?3'd0:req_round==1?3'd2:req_round==2?3'd3:3'd1;
 wire [64:0] ar,br,add_r,mul_r,out_r;
 wire [4:0] add_flags,mul_flags,out_flags;
 wire [63:0] ieee;
 fNToRecFN #(11,53) rec_a(a,ar);
 fNToRecFN #(11,53) rec_b(b,br);
 addRecFN #(11,53) add_sub(1'b0,req_op==1,ar,br,rm,add_r,add_flags);
 mulRecFN #(11,53) multiply(1'b0,ar,br,rm,mul_r,mul_flags);
 assign out_r=req_op==2?mul_r:add_r;
 assign out_flags=req_op==2?mul_flags:add_flags;
 recFNToFN #(11,53) encode(out_r,ieee);
 wire sub_out=ieee[62:52]==0 && ieee[51:0]!=0;
 wire flush=req_ftz_daz && sub_out;
 assign req_ready=!rst && (!rsp_valid||rsp_ready);
 always @(posedge clk)begin
  if(rst)begin rsp_valid<=0;rsp_tag<=0;rsp_result<=0;rsp_flags<=0;end
  else begin
   if(rsp_valid&&rsp_ready)rsp_valid<=0;
   if(req_valid&&req_ready)begin
    rsp_valid<=1;rsp_tag<=req_tag;rsp_result<=flush?{ieee[63],63'b0}:ieee;
    rsp_flags<=out_flags|(flush?5'b00011:5'b0);
   end
  end
 end
endmodule
`default_nettype wire
