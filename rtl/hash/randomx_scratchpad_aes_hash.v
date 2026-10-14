// SPDX-License-Identifier: BSD-3-Clause
// Native hashAes1Rx4 over exclusive, quiescent scratchpad bytes.
// One outstanding 128-bit read; raw byte zero is bits[7:0].
`default_nettype none
module randomx_scratchpad_aes_hash #(
 parameter integer SCRATCHPAD_BYTES=2097152
)(
 input wire clk,rst,req_valid,output wire req_ready,
 input wire [15:0] req_tag,input wire [21:0] req_scratchpad_bytes,
 output wire sp_rd_valid,input wire sp_rd_ready,
 output wire [20:0] sp_rd_addr,output wire [32:0] sp_rd_tag,
 input wire sp_rsp_valid,output wire sp_rsp_ready,
 input wire [127:0] sp_rsp_data,input wire [32:0] sp_rsp_tag,
 input wire sp_rsp_error,
 output wire rsp_valid,input wire rsp_ready,output wire [15:0] rsp_tag,
 output wire [511:0] rsp_hash,output wire rsp_error
);
 localparam [2:0] IDLE=0,READ_REQ=1,READ_WAIT=2,ROUND=3,EXTRA0=4,EXTRA1=5,RETURN=6;
 localparam [16:0] LAST_BEAT=(SCRATCHPAD_BYTES/16)-1;
 localparam [127:0] S0=128'hd7983aadcc82db479fa856de92b52c0d;
 localparam [127:0] S1=128'hace78057f59e125a15c7b798338d996e;
 localparam [127:0] S2=128'he8a07ce45079506bae62c7d06a770017;
 localparam [127:0] S3=128'h7e99494879a1000507ad828d630a240c;
 localparam [127:0] XKEY0=128'h0689020190dc56bf8b24949ff6fa8389;
 localparam [127:0] XKEY1=128'hed18f99bee1043c651f4e03c61b263d1;
 reg [2:0] state_q;
 reg [16:0] beat_q;
 reg [1:0] extra_lane_q;
 reg [15:0] tag_q;
 reg [511:0] lanes_q,hash_q;
 reg [127:0] key_q;
 reg error_q;
 wire [1:0] lane=state_q==ROUND?beat_q[1:0]:extra_lane_q;
 wire [127:0] round_key=state_q==EXTRA0?XKEY0:state_q==EXTRA1?XKEY1:key_q;
 wire [127:0] round_result;
 wire [32:0] read_tag={tag_q,beat_q};
 generate if(SCRATCHPAD_BYTES<64 || SCRATCHPAD_BYTES>2097152 || SCRATCHPAD_BYTES%64!=0)begin:invalid_parameters
  scratchpad_aes_hash_requires_multiple_of_64_between_64_and_2097152 invalid();
 end endgenerate
 randomx_aes_round round_unit(.state_in(lanes_q[128*lane+:128]),
  .key_in(round_key),.decrypt(lane[0]),.state_out(round_result));
 assign req_ready=!rst&&state_q==IDLE;
 assign sp_rd_valid=!rst&&state_q==READ_REQ;
 assign sp_rd_addr={beat_q,4'b0};
 assign sp_rd_tag=read_tag;
 // Drain stale traffic even while the next read is stalled. A matching response
 // cannot be accepted before its read request; the fabric holds it until WAIT.
 assign sp_rsp_ready=!rst&&(state_q!=READ_REQ||sp_rsp_tag!=read_tag);
 assign rsp_valid=!rst&&state_q==RETURN;
 assign rsp_tag=tag_q;assign rsp_hash=hash_q;assign rsp_error=error_q;
 always @(posedge clk)begin
  if(rst)begin state_q<=IDLE;beat_q<=0;extra_lane_q<=0;tag_q<=0;
   lanes_q<=0;hash_q<=0;key_q<=0;error_q<=0;end
  else case(state_q)
   IDLE:if(req_valid)begin
    tag_q<=req_tag;beat_q<=0;extra_lane_q<=0;lanes_q<={S3,S2,S1,S0};
    hash_q<=0;key_q<=0;error_q<=req_scratchpad_bytes!=SCRATCHPAD_BYTES;
    state_q<=req_scratchpad_bytes==SCRATCHPAD_BYTES?READ_REQ:RETURN;
   end
   READ_REQ:if(sp_rd_ready)state_q<=READ_WAIT;
   READ_WAIT:if(sp_rsp_valid&&sp_rsp_tag==read_tag)begin
    if(sp_rsp_error)begin hash_q<=0;error_q<=1;state_q<=RETURN;end
    else begin key_q<=sp_rsp_data;state_q<=ROUND;end
   end
   ROUND:begin
    lanes_q[128*lane+:128]<=round_result;
    if(beat_q==LAST_BEAT)begin extra_lane_q<=0;state_q<=EXTRA0;end
    else begin beat_q<=beat_q+1'b1;state_q<=READ_REQ;end
   end
   EXTRA0:begin
    lanes_q[128*lane+:128]<=round_result;
    if(extra_lane_q==3)begin extra_lane_q<=0;state_q<=EXTRA1;end
    else extra_lane_q<=extra_lane_q+1'b1;
   end
   EXTRA1:begin
    lanes_q[128*lane+:128]<=round_result;
    if(extra_lane_q==3)begin hash_q<={round_result,lanes_q[383:0]};state_q<=RETURN;end
    else extra_lane_q<=extra_lane_q+1'b1;
   end
   RETURN:if(rsp_ready)state_q<=IDLE;
   default:begin hash_q<=0;error_q<=1;state_q<=RETURN;end
  endcase
 end
endmodule
`default_nettype wire
