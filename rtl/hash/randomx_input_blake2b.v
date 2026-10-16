// SPDX-License-Identifier: BSD-3-Clause
// Bounded native unkeyed BLAKE2b-512 over0..80 captured input bytes.
// Reuses the accepted compression core without arithmetic/IP changes.
`default_nettype none
module randomx_input_blake2b(
 input wire clk,rst,cancel,
 input wire req_valid,output wire req_ready,
 input wire [15:0] req_tag,input wire [639:0] req_input,input wire [6:0] req_input_bytes,
 output wire rsp_valid,input wire rsp_ready,
 output wire [15:0] rsp_tag,output wire [511:0] rsp_seed,output wire rsp_error,
 output wire [1:0] phase
);
 localparam [1:0] IDLE=0,START=1,WAIT=2,RETURN=3;
 reg [1:0] state_q;
 reg [15:0] tag_q;
 reg [639:0] input_q;
 reg [6:0] bytes_q;
 reg [511:0] seed_q;
 reg error_q;
 wire active=!rst&&!cancel;
 wire [1023:0] core_block;
 wire [511:0] core_digest,native_digest;
 wire core_ready,core_valid;
 wire [127:0] core_length={121'b0,bytes_q};
 genvar b;
 generate
  for(b=0;b<128;b=b+1)begin:input_bytes
   if(b<80)assign core_block[1023-8*b-:8]=b<bytes_q?input_q[8*b+:8]:8'b0;
   else assign core_block[1023-8*b-:8]=8'b0;
  end
  for(b=0;b<64;b=b+1)begin:output_bytes
   assign native_digest[8*b+:8]=core_digest[511-8*b-:8];
  end
 endgenerate
 randomx_blake2b_chain_core #(.DIGEST_LENGTH(64),.KEY_LENGTH(0),.NUM_ROUNDS(12)) core(
  .clk(clk),.reset_n(active),.init(active&&state_q==START),.next(1'b0),.final_block(1'b1),
  .block(core_block),.data_length(core_length),.ready(core_ready),
  .digest(core_digest),.digest_valid(core_valid)
 );
 assign req_ready=active&&state_q==IDLE;
 assign rsp_valid=active&&state_q==RETURN;
 assign rsp_tag=tag_q;assign rsp_seed=seed_q;assign rsp_error=error_q;
 assign phase=!active||state_q==IDLE?2'd0:state_q==RETURN?2'd2:2'd1;
 always @(posedge clk)begin
  if(rst||cancel)begin state_q<=IDLE;tag_q<=0;input_q<=0;bytes_q<=0;seed_q<=0;error_q<=0;end
  else case(state_q)
   IDLE:if(req_valid)begin
    tag_q<=req_tag;input_q<=req_input;bytes_q<=req_input_bytes;
    seed_q<=0;error_q<=req_input_bytes>80;state_q<=req_input_bytes>80?RETURN:START;
   end
   // START gives the reused core its own init acceptance edge, clearing a prior
   // held digest_valid. Length and padded block remain captured through WAIT.
   START:if(core_ready)state_q<=WAIT;
   WAIT:if(core_valid)begin seed_q<=native_digest;state_q<=RETURN;end
   RETURN:if(rsp_ready)state_q<=IDLE;
   default:begin seed_q<=0;error_q<=1;state_q<=RETURN;end
  endcase
 end
endmodule
`default_nettype wire
