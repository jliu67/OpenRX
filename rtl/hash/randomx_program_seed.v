// SPDX-License-Identifier: BSD-3-Clause
// Held native program result and exactly PROGRAMS-1 inter-program digests.
`default_nettype none
module randomx_program_seed #(parameter integer PROGRAMS=8)(
 input wire clk,rst,req_valid,output wire req_ready,input wire [15:0] req_tag,
 input wire [2:0] req_index,input wire [11:0] req_iterations,input wire [1:0] req_round_mode,
 input wire [511:0] req_r,req_f,req_e,req_a,
 output wire rsp_valid,input wire rsp_ready,output wire [15:0] rsp_tag,
 output wire [2:0] rsp_index,output wire [11:0] rsp_iterations,output wire [1:0] rsp_round_mode,
 output wire [511:0] rsp_r,rsp_f,rsp_e,rsp_a,rsp_seed,output wire rsp_seed_valid,rsp_error
);
 localparam [1:0] IDLE=0,HASH_START=1,HASH_WAIT=2,RETURN=3;
 reg [1:0] state_q;reg [15:0] tag_q;reg [2:0] index_q;reg [11:0] iterations_q;reg [1:0] round_q;
 reg [511:0] r_q,f_q,e_q,a_q,seed_q;reg error_q,seed_valid_q;
 wire hash_req_ready,hash_rsp_valid,hash_rsp_error;wire [15:0] hash_rsp_tag;wire [511:0] hash_rsp_digest;
 generate if(PROGRAMS<1||PROGRAMS>8)begin:invalid_parameters
  program_seed_requires_PROGRAMS_1_to_8 invalid();end endgenerate
`ifdef REGFILE_BLAKE2B_NETLIST
 randomx_regfile_blake2b hash(
`else
 randomx_regfile_blake2b #(.DIGEST_BYTES(64)) hash(
`endif
  .clk(clk),.rst(rst),.req_valid(!rst&&state_q==HASH_START),.req_ready(hash_req_ready),.req_tag(tag_q),.req_bytes(9'd256),
  .req_r(r_q),.req_f(f_q),.req_e(e_q),.req_a(a_q),.rsp_valid(hash_rsp_valid),.rsp_ready(!rst&&state_q==HASH_WAIT),
  .rsp_tag(hash_rsp_tag),.rsp_digest(hash_rsp_digest),.rsp_error(hash_rsp_error)
 );
 assign req_ready=!rst&&state_q==IDLE;assign rsp_valid=!rst&&state_q==RETURN;
 assign rsp_tag=tag_q;assign rsp_index=index_q;assign rsp_iterations=iterations_q;assign rsp_round_mode=round_q;
 assign rsp_r=r_q;assign rsp_f=f_q;assign rsp_e=e_q;assign rsp_a=a_q;
 assign rsp_seed=seed_q;assign rsp_seed_valid=seed_valid_q;assign rsp_error=error_q;
 always @(posedge clk)begin
  if(rst)begin state_q<=IDLE;tag_q<=0;index_q<=0;iterations_q<=0;round_q<=0;r_q<=0;f_q<=0;e_q<=0;a_q<=0;seed_q<=0;error_q<=0;seed_valid_q<=0;end
  else case(state_q)
   IDLE:if(req_valid)begin
    tag_q<=req_tag;index_q<=req_index;iterations_q<=req_iterations;round_q<=req_round_mode;
    r_q<=req_r;f_q<=req_f;e_q<=req_e;a_q<=req_a;seed_q<=0;seed_valid_q<=0;
    error_q<=req_index>=PROGRAMS||req_iterations==0||req_iterations>2048;
    if(req_index>=PROGRAMS||req_iterations==0||req_iterations>2048||req_index==PROGRAMS-1)state_q<=RETURN;
    else state_q<=HASH_START;
   end
   HASH_START:if(hash_req_ready)state_q<=HASH_WAIT;
   HASH_WAIT:if(hash_rsp_valid)begin
    error_q<=hash_rsp_error||hash_rsp_tag!=tag_q;
    seed_q<=hash_rsp_digest;seed_valid_q<=!hash_rsp_error&&hash_rsp_tag==tag_q;state_q<=RETURN;
   end
   RETURN:if(rsp_ready)state_q<=IDLE;
   default:begin error_q<=1;seed_valid_q<=0;seed_q<=0;state_q<=RETURN;end
  endcase
 end
endmodule
`default_nettype wire
