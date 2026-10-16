// SPDX-License-Identifier: BSD-3-Clause
// Native fillAes4Rx4 with one reused AES round and private lane state.
// The input seed is captured once; unlike fillAes1Rx4 it is not returned/mutated.
`default_nettype none
module randomx_program_generation #(
 parameter integer OUTPUT_BYTES=3200
)(
 input wire clk,rst,cancel,
 input wire req_valid,output wire req_ready,
 input wire [15:0] req_tag,input wire [511:0] req_seed,
 output wire out_valid,input wire out_ready,
 output wire [11:0] out_addr,output wire [127:0] out_data,output wire [15:0] out_tag,
 output wire rsp_valid,input wire rsp_ready,output wire [15:0] rsp_tag,
 output wire [1:0] phase
);
 localparam [1:0] IDLE=0,STREAM=1,RETURN=2;
 localparam [7:0] LAST_BEAT=(OUTPUT_BYTES/16)-1;
 // Native rx_set_int_vec_i128 arguments name the most-significant word first.
 localparam [127:0] KEY0=128'h99e5d23f2f546d2bd1833ddb6421aadd;
 localparam [127:0] KEY1=128'ha5dfcde506f79d53b6913f55b20e3450;
 localparam [127:0] KEY2=128'h171c02bf0aa4679f515e7baf5c3ed904;
 localparam [127:0] KEY3=128'hd8ded291cd673785e78f5d0885623763;
 localparam [127:0] KEY4=128'h229effb43d518b6de3d6a7a6b5826f73;
 localparam [127:0] KEY5=128'hb272b7d2e9024d4e9c10b3d9c7566bf3;
 localparam [127:0] KEY6=128'hf63befa72ba9660af765a38bf273c9e7;
 localparam [127:0] KEY7=128'hc0b0762d0c06d1fd915839de7a7cd609;
 reg [1:0] state_q,round_q;
 reg [7:0] beat_q;
 reg [15:0] tag_q;
 reg [511:0] lanes_q;
 wire active=!rst&&!cancel;
 wire [1:0] lane=beat_q[1:0];
 wire [2:0] key_index={lane[1],round_q};
 wire [127:0] key=key_index==0?KEY0:key_index==1?KEY1:key_index==2?KEY2:
                    key_index==3?KEY3:key_index==4?KEY4:key_index==5?KEY5:
                    key_index==6?KEY6:KEY7;
 wire [127:0] round_result;
 generate if(OUTPUT_BYTES<64 || OUTPUT_BYTES>3200 || OUTPUT_BYTES%64!=0)begin:invalid_parameters
  program_generation_requires_multiple_of_64_between_64_and_3200 invalid();
 end endgenerate
 randomx_aes_round round_unit(.state_in(lanes_q[128*lane+:128]),
  .key_in(key),.decrypt(!lane[0]),.state_out(round_result));
 assign req_ready=active&&state_q==IDLE;
 assign out_valid=active&&state_q==STREAM&&round_q==3;
 assign out_addr={beat_q,4'b0};
 assign out_data=round_result;
 assign out_tag=tag_q;
 assign rsp_valid=active&&state_q==RETURN;
 assign rsp_tag=tag_q;
 assign phase=active?state_q:IDLE;
 always @(posedge clk)begin
  if(rst||cancel)begin state_q<=IDLE;round_q<=0;beat_q<=0;tag_q<=0;lanes_q<=0;end
  else case(state_q)
   IDLE:if(req_valid)begin
    tag_q<=req_tag;lanes_q<=req_seed;beat_q<=0;round_q<=0;state_q<=STREAM;
   end
   STREAM:begin
    // The first three rounds are private computation. The fourth result is
    // committed only with its output beat, so all offered fields remain stable.
    if(round_q!=3)begin
     lanes_q[128*lane+:128]<=round_result;round_q<=round_q+2'd1;
    end else if(out_ready)begin
     lanes_q[128*lane+:128]<=round_result;round_q<=0;
     if(beat_q==LAST_BEAT)state_q<=RETURN;
     else beat_q<=beat_q+8'd1;
    end
   end
   RETURN:if(rsp_ready)state_q<=IDLE;
   default:begin state_q<=IDLE;round_q<=0;beat_q<=0;tag_q<=0;lanes_q<=0;end
  endcase
 end
endmodule
`default_nettype wire
