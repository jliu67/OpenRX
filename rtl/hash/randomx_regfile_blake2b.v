// SPDX-License-Identifier: BSD-3-Clause
// Unkeyed native RegisterFile: little-endian R/F/E/A, exactly256 bytes.
// Digest32 is independently parameterized; it is not a truncated digest64.
`default_nettype none
module randomx_regfile_blake2b #(parameter integer DIGEST_BYTES=64)(
 input wire clk,rst,req_valid,output wire req_ready,
 input wire [15:0] req_tag,input wire [8:0] req_bytes,
 input wire [511:0] req_r,req_f,req_e,req_a,
 output wire rsp_valid,input wire rsp_ready,output wire [15:0] rsp_tag,
 output wire [511:0] rsp_digest,output wire rsp_error
);
 localparam [2:0] IDLE=0,FIRST_START=1,FIRST_WAIT=2,SECOND_START=3,SECOND_WAIT=4,RETURN=5;
 reg [2:0] state_q;reg [2047:0] register_q;reg [15:0] tag_q;
 reg [511:0] digest_q;reg error_q;
 wire [1023:0] native_block=state_q==SECOND_START||state_q==SECOND_WAIT?register_q[2047:1024]:register_q[1023:0];
 wire [1023:0] core_block;wire [511:0] core_digest;wire core_ready,core_valid;
 wire core_init=!rst&&state_q==FIRST_START;
 wire core_next=!rst&&state_q==SECOND_START;
 wire core_final=state_q==SECOND_START||state_q==SECOND_WAIT;
 wire [127:0] core_length=core_final?128'd256:128'd128;
 wire [511:0] native_digest;
 genvar b;
 generate
  if(DIGEST_BYTES!=32&&DIGEST_BYTES!=64)begin:invalid_parameters
   regfile_blake2b_requires_DIGEST_BYTES_32_or_64 invalid();
  end
  for(b=0;b<128;b=b+1)begin:input_bytes
   assign core_block[1023-8*b-:8]=native_block[8*b+:8];
  end
  for(b=0;b<64;b=b+1)begin:output_bytes
   assign native_digest[8*b+:8]=b<DIGEST_BYTES?core_digest[511-8*b-:8]:8'b0;
  end
 endgenerate
`ifdef REGFILE_BLAKE2B_CORE_NETLIST
 randomx_blake2b_chain_core core(
`else
 randomx_blake2b_chain_core #(.DIGEST_LENGTH(DIGEST_BYTES),.KEY_LENGTH(0),.NUM_ROUNDS(12)) core(
`endif
  .clk(clk),.reset_n(!rst),.init(core_init),.next(core_next),.final_block(core_final),
  .block(core_block),.data_length(core_length),.ready(core_ready),.digest(core_digest),.digest_valid(core_valid)
 );
 assign req_ready=!rst&&state_q==IDLE;
 assign rsp_valid=!rst&&state_q==RETURN;
 assign rsp_tag=tag_q;assign rsp_digest=digest_q;assign rsp_error=error_q;
 always @(posedge clk)begin
  if(rst)begin state_q<=IDLE;register_q<=0;tag_q<=0;digest_q<=0;error_q<=0;end
  else case(state_q)
   IDLE:if(req_valid)begin
    tag_q<=req_tag;register_q<={req_a,req_e,req_f,req_r};digest_q<=0;error_q<=req_bytes!=9'd256;
    state_q<=req_bytes==9'd256 ? FIRST_START : RETURN;
   end
   FIRST_START:if(core_ready)state_q<=FIRST_WAIT;
   FIRST_WAIT:if(core_valid)state_q<=SECOND_START;
   SECOND_START:if(core_ready)state_q<=SECOND_WAIT;
   SECOND_WAIT:if(core_valid)begin digest_q<=native_digest;state_q<=RETURN;end
   RETURN:if(rsp_ready)state_q<=IDLE;
   default:begin digest_q<=0;error_q<=1;state_q<=RETURN;end
  endcase
 end
endmodule
`default_nettype wire
