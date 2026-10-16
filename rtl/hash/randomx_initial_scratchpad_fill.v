// SPDX-License-Identifier: BSD-3-Clause
// Pinned RandomX fillAes1Rx4: one shared raw AES round per accepted 16-byte write.
// The caller supplies the input BLAKE2b-512 state and owns request-tag uniqueness.
`default_nettype none
module randomx_initial_scratchpad_fill #(
 parameter integer SCRATCHPAD_BYTES=2097152
)(
 input wire clk,rst,cancel,
 input wire req_valid,output wire req_ready,
 input wire [15:0] req_tag,input wire [511:0] req_seed,
 output wire sp_wr_valid,input wire sp_wr_ready,
 output wire [20:0] sp_wr_addr,output wire [127:0] sp_wr_data,
 output wire [15:0] sp_wr_strb,output wire [15:0] sp_wr_tag,
 output wire rsp_valid,input wire rsp_ready,
 output wire [15:0] rsp_tag,output wire [511:0] rsp_seed,
 output wire [1:0] phase
);
 localparam [1:0] IDLE=0,STREAM=1,RETURN=2;
 localparam [16:0] LAST_BEAT=(SCRATCHPAD_BYTES/16)-1;
 // rx_set_int_vec_i128 takes its most-significant 32-bit word first.
 localparam [127:0] KEY0=128'hb4f44917dbb5552b627166096daca553;
 localparam [127:0] KEY1=128'h0da1dc4e1725d378846a710d6d7caf07;
 localparam [127:0] KEY2=128'h3e20e345f4c0794f9f947ec63f1262f1;
 localparam [127:0] KEY3=128'h4916915416314c88b1ba317c6aef8135;
 reg [1:0] state_q;
 reg [16:0] beat_q;
 reg [15:0] tag_q;
 reg [511:0] seed_q;
 wire active=!rst&&!cancel;
 wire [1:0] lane=beat_q[1:0];
 wire [127:0] key=lane==0?KEY0:lane==1?KEY1:lane==2?KEY2:KEY3;
 wire [127:0] round_result;
 generate if(SCRATCHPAD_BYTES<64 || SCRATCHPAD_BYTES>2097152 || SCRATCHPAD_BYTES%64!=0)begin:invalid_parameters
  initial_scratchpad_fill_requires_multiple_of_64_between_64_and_2097152 invalid();
 end endgenerate
 randomx_aes_round round_unit(.state_in(seed_q[128*lane+:128]),
  .key_in(key),.decrypt(!lane[0]),.state_out(round_result));
 assign req_ready=active&&state_q==IDLE;
 assign sp_wr_valid=active&&state_q==STREAM;
 assign sp_wr_addr={beat_q,4'b0};
 assign sp_wr_data=round_result;
 assign sp_wr_strb=16'hffff;
 assign sp_wr_tag=tag_q;
 assign rsp_valid=active&&state_q==RETURN;
 assign rsp_tag=tag_q;
 assign rsp_seed=seed_q;
 assign phase=active?state_q:IDLE;
 always @(posedge clk)begin
  if(rst||cancel)begin state_q<=IDLE;beat_q<=0;tag_q<=0;seed_q<=0;end
  else case(state_q)
   IDLE:if(req_valid)begin
    tag_q<=req_tag;seed_q<=req_seed;beat_q<=0;state_q<=STREAM;
   end
   STREAM:if(sp_wr_ready)begin
    // Commit the recurrence together with its memory write. Backpressure cannot
    // advance a lane or change the currently offered address/data/tag.
    seed_q[128*lane+:128]<=round_result;
    if(beat_q==LAST_BEAT)state_q<=RETURN;
    else beat_q<=beat_q+17'd1;
   end
   RETURN:if(rsp_ready)state_q<=IDLE;
   default:begin state_q<=IDLE;beat_q<=0;tag_q<=0;seed_q<=0;end
  endcase
 end
endmodule
`default_nettype wire
