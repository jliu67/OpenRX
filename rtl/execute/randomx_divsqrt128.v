// SPDX-License-Identifier: BSD-3-Clause
// Atomic two-lane iterative division/square root: lane completions may differ.
`default_nettype none
module randomx_divsqrt128 #(parameter integer LANES=2)(
 input wire clk,rst,req_valid,output wire req_ready,input wire [15:0] req_tag,
 input wire req_sqrt,input wire [1:0] req_round,input wire req_ftz_daz,input wire [127:0] req_a,req_b,
 output wire rsp_valid,input wire rsp_ready,output wire [15:0] rsp_tag,
 output wire [127:0] rsp_result,output wire [4:0] rsp_flags
);
 generate
  if(LANES==2)begin: parallel
   wire q0,q1,v0,v1;wire [15:0] t0,t1;wire [63:0] r0,r1;wire [4:0] f0,f1;
   randomx_divsqrt64 lane0(clk,rst,req_valid&&q1,q0,req_tag,req_sqrt,req_round,req_ftz_daz,
    req_a[63:0],req_b[63:0],v0,rsp_ready&&v1,t0,r0,f0);
   randomx_divsqrt64 lane1(clk,rst,req_valid&&q0,q1,req_tag,req_sqrt,req_round,req_ftz_daz,
    req_a[127:64],req_b[127:64],v1,rsp_ready&&v0,t1,r1,f1);
   assign req_ready=q0&&q1;assign rsp_valid=v0&&v1;assign rsp_tag=t0;
   assign rsp_result={r1,r0};assign rsp_flags=f0|f1;
  end else if(LANES==1)begin: shared
   localparam [2:0] IDLE=0,REQ0=1,WAIT0=2,REQ1=3,WAIT1=4,RETURN=5;
   reg [2:0] state_q;reg [127:0] a_q,b_q,result_q;
   reg [63:0] low_q;reg [4:0] low_flags_q,flags_q;reg [15:0] tag_q;
   reg sqrt_q;reg [1:0] round_q;reg ftz_q;
   wire q,v;wire [15:0] t;wire [63:0] r;wire [4:0] flags;
   randomx_divsqrt64 lane(clk,rst,!rst&&(state_q==REQ0||state_q==REQ1),q,tag_q,sqrt_q,round_q,ftz_q,
    state_q==REQ1?a_q[127:64]:a_q[63:0],state_q==REQ1?b_q[127:64]:b_q[63:0],
    v,!rst&&(state_q==WAIT0||state_q==WAIT1),t,r,flags);
   assign req_ready=!rst&&state_q==IDLE;assign rsp_valid=!rst&&state_q==RETURN;
   assign rsp_tag=tag_q;assign rsp_result=result_q;assign rsp_flags=flags_q;
   always @(posedge clk)begin
    if(rst)begin state_q<=IDLE;a_q<=0;b_q<=0;result_q<=0;low_q<=0;low_flags_q<=0;flags_q<=0;tag_q<=0;sqrt_q<=0;round_q<=0;ftz_q<=0;end
    else case(state_q)
     IDLE:if(req_valid)begin a_q<=req_a;b_q<=req_b;sqrt_q<=req_sqrt;round_q<=req_round;ftz_q<=req_ftz_daz;tag_q<=req_tag;state_q<=REQ0;end
     REQ0:if(q)state_q<=WAIT0;
     WAIT0:if(v&&t==tag_q)begin low_q<=r;low_flags_q<=flags;state_q<=REQ1;end
     REQ1:if(q)state_q<=WAIT1;
     WAIT1:if(v&&t==tag_q)begin result_q<={r,low_q};flags_q<=flags|low_flags_q;state_q<=RETURN;end
     RETURN:if(rsp_ready)state_q<=IDLE;
     default:state_q<=IDLE;
    endcase
   end
  end else begin: invalid_parameter
   divsqrt_vector_requires_LANES_1_or_2 invalid();
  end
 endgenerate
endmodule
`default_nettype wire
