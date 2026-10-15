// SPDX-License-Identifier: BSD-3-Clause
// Native VM finalization only: hash actual scratchpad into A, then BLAKE2b-256.
// R/F/E and round mode are captured and preserved bit-for-bit.
`default_nettype none
module randomx_scratchpad_finalizer #(
 parameter integer SCRATCHPAD_BYTES=2097152
)(
 input wire clk,rst,req_valid,output wire req_ready,
 input wire [15:0] req_tag,input wire [21:0] req_scratchpad_bytes,
 input wire [1:0] req_round_mode,input wire [511:0] req_r,req_f,req_e,req_a,
 output wire sp_rd_valid,input wire sp_rd_ready,
 output wire [20:0] sp_rd_addr,output wire [32:0] sp_rd_tag,
 input wire sp_rsp_valid,output wire sp_rsp_ready,
 input wire [127:0] sp_rsp_data,input wire [32:0] sp_rsp_tag,
 input wire sp_rsp_error,
 output wire rsp_valid,input wire rsp_ready,output wire [15:0] rsp_tag,
 output wire [1:0] rsp_round_mode,output wire [511:0] rsp_r,rsp_f,rsp_e,rsp_a,
 output wire [255:0] rsp_digest,output wire rsp_error
);
 localparam [2:0] IDLE=0,AES_START=1,AES_WAIT=2,HASH_START=3,HASH_WAIT=4,RETURN=5;
 reg [2:0] state_q;
 reg [15:0] tag_q;reg [21:0] size_q;reg [1:0] round_q;
 reg [511:0] r_q,f_q,e_q,a_q,final_a_q;reg [255:0] digest_q;reg error_q;
 wire aes_req_ready,aes_rsp_valid,aes_rsp_error;
 wire [15:0] aes_rsp_tag;wire [511:0] aes_rsp_hash;
 wire hash_req_ready,hash_rsp_valid,hash_rsp_error;
 wire [15:0] hash_rsp_tag;wire [511:0] hash_rsp_digest;
 randomx_scratchpad_aes_hash #(.SCRATCHPAD_BYTES(SCRATCHPAD_BYTES)) aes(
  .clk(clk),.rst(rst),.req_valid(!rst&&state_q==AES_START),.req_ready(aes_req_ready),
  .req_tag(tag_q),.req_scratchpad_bytes(size_q),.sp_rd_valid(sp_rd_valid),
  .sp_rd_ready(sp_rd_ready),.sp_rd_addr(sp_rd_addr),.sp_rd_tag(sp_rd_tag),
  .sp_rsp_valid(sp_rsp_valid),.sp_rsp_ready(sp_rsp_ready),.sp_rsp_data(sp_rsp_data),
  .sp_rsp_tag(sp_rsp_tag),.sp_rsp_error(sp_rsp_error),.rsp_valid(aes_rsp_valid),
  .rsp_ready(!rst&&state_q==AES_WAIT),.rsp_tag(aes_rsp_tag),.rsp_hash(aes_rsp_hash),.rsp_error(aes_rsp_error));
 randomx_regfile_blake2b #(.DIGEST_BYTES(32)) hash(
  .clk(clk),.rst(rst),.req_valid(!rst&&state_q==HASH_START),.req_ready(hash_req_ready),
  .req_tag(tag_q),.req_bytes(9'd256),.req_r(r_q),.req_f(f_q),.req_e(e_q),.req_a(final_a_q),
  .rsp_valid(hash_rsp_valid),.rsp_ready(!rst&&state_q==HASH_WAIT),.rsp_tag(hash_rsp_tag),
  .rsp_digest(hash_rsp_digest),.rsp_error(hash_rsp_error));
 assign req_ready=!rst&&state_q==IDLE;assign rsp_valid=!rst&&state_q==RETURN;
 assign rsp_tag=tag_q;assign rsp_round_mode=round_q;
 assign rsp_r=r_q;assign rsp_f=f_q;assign rsp_e=e_q;assign rsp_a=a_q;
 assign rsp_digest=digest_q;assign rsp_error=error_q;
 always @(posedge clk)begin
  if(rst)begin state_q<=IDLE;tag_q<=0;size_q<=0;round_q<=0;
   r_q<=0;f_q<=0;e_q<=0;a_q<=0;final_a_q<=0;digest_q<=0;error_q<=0;end
  else case(state_q)
   IDLE:if(req_valid)begin
    tag_q<=req_tag;size_q<=req_scratchpad_bytes;round_q<=req_round_mode;
    r_q<=req_r;f_q<=req_f;e_q<=req_e;a_q<=req_a;final_a_q<=0;digest_q<=0;error_q<=0;state_q<=AES_START;
   end
   AES_START:if(aes_req_ready)state_q<=AES_WAIT;
   AES_WAIT:if(aes_rsp_valid)begin
    if(aes_rsp_error||aes_rsp_tag!=tag_q)begin error_q<=1;state_q<=RETURN;end
    else begin final_a_q<=aes_rsp_hash;state_q<=HASH_START;end
   end
   HASH_START:if(hash_req_ready)state_q<=HASH_WAIT;
   HASH_WAIT:if(hash_rsp_valid)begin
    error_q<=hash_rsp_error||hash_rsp_tag!=tag_q;
    digest_q<=hash_rsp_error||hash_rsp_tag!=tag_q?256'b0:hash_rsp_digest[255:0];
    if(!hash_rsp_error&&hash_rsp_tag==tag_q)a_q<=final_a_q;
    state_q<=RETURN;
   end
   RETURN:if(rsp_ready)state_q<=IDLE;
   default:begin digest_q<=0;error_q<=1;state_q<=RETURN;end
  endcase
 end
endmodule
`default_nettype wire
