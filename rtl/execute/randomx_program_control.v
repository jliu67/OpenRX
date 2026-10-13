// SPDX-License-Identifier: BSD-3-Clause
// Native program initialization and iteration/program sequencing above a tagged backend.
`default_nettype none
module randomx_program_control #(parameter integer PROGRAMS=8,ITERATIONS=2048)(
 input wire clk,rst,start_valid,output wire start_ready,input wire [15:0] start_tag,input wire start_v2,
 output wire meta_req_valid,input wire meta_req_ready,output wire [15:0] meta_req_tag,output wire [2:0] meta_req_program,
 input wire meta_rsp_valid,output wire meta_rsp_ready,input wire [15:0] meta_rsp_tag,input wire [2:0] meta_rsp_program,
 input wire [1023:0] meta_rsp_entropy,input wire [63:0] meta_rsp_program_addr,
 output wire program_done_valid,input wire program_done_ready,output wire [15:0] program_done_tag,
 output wire [2:0] program_done_index,output wire [11:0] program_done_iterations,
 output wire [511:0] program_done_r,program_done_f,program_done_e,program_done_a,
 output wire [1:0] program_done_round_mode,
 output wire done_valid,input wire done_ready,output wire [15:0] done_tag,
 output wire [511:0] done_r,done_f,done_e,done_a,output wire [1:0] done_round_mode,
 output wire [31:0] done_mx,done_ma,done_spaddr0,done_spaddr1,
 output wire error_valid,input wire error_ready,output wire [15:0] error_tag,output wire [2:0] error_program,
 output wire [1:0] error_code,output wire [8:0] error_pc,output wire [7:0] error_opcode,
 output wire iter_req_valid,input wire iter_req_ready,output wire [15:0] iter_req_tag,output wire iter_req_v2,
 output wire [1:0] iter_req_round_mode,output wire [511:0] iter_req_r,iter_req_a,
 output wire [31:0] iter_req_spaddr0,iter_req_spaddr1,iter_req_mx,iter_req_ma,
 output wire [2:0] iter_req_read0,iter_req_read1,iter_req_read2,iter_req_read3,
 output wire [63:0] iter_req_emask0,iter_req_emask1,iter_req_dataset_offset,iter_req_program_addr,
 input wire iter_done_valid,output wire iter_done_ready,input wire [15:0] iter_done_tag,
 input wire [511:0] iter_done_r,iter_done_f,iter_done_e,input wire [1:0] iter_done_round_mode,
 input wire [31:0] iter_done_mx,iter_done_ma,iter_done_spaddr0,iter_done_spaddr1,
 input wire iter_error_valid,output wire iter_error_ready,input wire [15:0] iter_error_tag,
 input wire [8:0] iter_error_pc,input wire [7:0] iter_error_opcode,
 output wire iteration_commit_valid,output wire [15:0] iteration_commit_tag,iteration_commit_backend_tag,
 output wire [2:0] iteration_commit_program,output wire [10:0] iteration_commit_index,
 output wire [511:0] iteration_commit_r,iteration_commit_f,iteration_commit_e,iteration_commit_a,
 output wire [1:0] iteration_commit_round_mode,
 output wire [31:0] iteration_commit_mx,iteration_commit_ma,iteration_commit_spaddr0,iteration_commit_spaddr1
);
 localparam [2:0] IDLE=0,META_REQ=1,META_WAIT=2,ITER_REQ=3,ITER_WAIT=4,PROGRAM_RET=5,RETURN=6,ERROR=7;
 reg [2:0] state_q,program_q;reg [10:0] iteration_q;
 reg [15:0] tag_q,backend_tag_q;reg v2_q;reg [1:0] round_q;
 reg [511:0] r_q,f_q,e_q,a_q;reg [31:0] mx_q,ma_q,sp0_q,sp1_q;
 reg [2:0] read0_q,read1_q,read2_q,read3_q;
 reg [63:0] emask0_q,emask1_q,offset_q,addr_q;
 reg commit_q;reg [2:0] commit_program_q;reg [10:0] commit_iteration_q;reg [15:0] commit_backend_q;
 reg [1:0] error_code_q;reg [8:0] error_pc_q;reg [7:0] error_opcode_q;
 wire old_meta=meta_rsp_tag!=tag_q||meta_rsp_program!=program_q;
 wire old_done=iter_done_tag!=backend_tag_q,old_error=iter_error_tag!=backend_tag_q;
 function [63:0] positive_float;input [63:0] entropy;reg [10:0] exponent;begin
  exponent=11'd1023+{6'b0,entropy[63:59]};positive_float={1'b0,exponent,entropy[51:0]};end endfunction
 function [63:0] float_mask;input [63:0] entropy;begin
  float_mask={1'b0,3'b011,entropy[63:60],4'b0000,30'b0,entropy[21:0]};end endfunction
 generate if(PROGRAMS<1||PROGRAMS>8||ITERATIONS<1||ITERATIONS>2048)begin: invalid_parameters
  program_control_requires_PROGRAMS_1_to_8_and_ITERATIONS_1_to_2048 invalid();end endgenerate
 assign start_ready=!rst&&state_q==IDLE;
 assign meta_req_valid=!rst&&state_q==META_REQ;assign meta_req_tag=tag_q;assign meta_req_program=program_q;
 assign meta_rsp_ready=!rst&&(old_meta||state_q==IDLE||state_q==META_WAIT);
 assign iter_req_valid=!rst&&state_q==ITER_REQ;assign iter_req_tag=backend_tag_q;assign iter_req_v2=v2_q;
 assign iter_req_round_mode=round_q;assign iter_req_r=r_q;assign iter_req_a=a_q;
 assign iter_req_mx=mx_q;assign iter_req_ma=ma_q;assign iter_req_spaddr0=sp0_q;assign iter_req_spaddr1=sp1_q;
 assign iter_req_read0=read0_q;assign iter_req_read1=read1_q;assign iter_req_read2=read2_q;assign iter_req_read3=read3_q;
 assign iter_req_emask0=emask0_q;assign iter_req_emask1=emask1_q;assign iter_req_dataset_offset=offset_q;assign iter_req_program_addr=addr_q;
 assign iter_done_ready=!rst&&(old_done||state_q==IDLE||(state_q==ITER_WAIT&&!iter_error_valid));
 assign iter_error_ready=!rst&&(old_error||state_q==IDLE||state_q==ITER_WAIT);
 assign program_done_valid=!rst&&state_q==PROGRAM_RET;assign program_done_tag=tag_q;assign program_done_index=program_q;
 assign program_done_iterations=ITERATIONS;assign program_done_r=r_q;assign program_done_f=f_q;assign program_done_e=e_q;assign program_done_a=a_q;
 assign program_done_round_mode=round_q;
 assign done_valid=!rst&&state_q==RETURN;assign done_tag=tag_q;assign done_r=r_q;assign done_f=f_q;assign done_e=e_q;assign done_a=a_q;
 assign done_round_mode=round_q;assign done_mx=mx_q;assign done_ma=ma_q;assign done_spaddr0=sp0_q;assign done_spaddr1=sp1_q;
 assign error_valid=!rst&&state_q==ERROR;assign error_tag=tag_q;assign error_program=program_q;
 assign error_code=error_code_q;assign error_pc=error_pc_q;assign error_opcode=error_opcode_q;
 assign iteration_commit_valid=!rst&&commit_q;assign iteration_commit_tag=tag_q;assign iteration_commit_backend_tag=commit_backend_q;
 assign iteration_commit_program=commit_program_q;assign iteration_commit_index=commit_iteration_q;
 assign iteration_commit_r=r_q;assign iteration_commit_f=f_q;assign iteration_commit_e=e_q;assign iteration_commit_a=a_q;
 assign iteration_commit_round_mode=round_q;assign iteration_commit_mx=mx_q;assign iteration_commit_ma=ma_q;
 assign iteration_commit_spaddr0=sp0_q;assign iteration_commit_spaddr1=sp1_q;
 integer i;
 always @(posedge clk)begin
  if(rst)begin
   state_q<=IDLE;program_q<=0;iteration_q<=0;tag_q<=0;backend_tag_q<=0;v2_q<=0;round_q<=0;
   r_q<=0;f_q<=0;e_q<=0;a_q<=0;mx_q<=0;ma_q<=0;sp0_q<=0;sp1_q<=0;
   read0_q<=0;read1_q<=0;read2_q<=0;read3_q<=0;emask0_q<=0;emask1_q<=0;offset_q<=0;addr_q<=0;
   commit_q<=0;commit_program_q<=0;commit_iteration_q<=0;commit_backend_q<=0;error_code_q<=0;error_pc_q<=0;error_opcode_q<=0;
  end else begin
   commit_q<=0;
   case(state_q)
    IDLE:if(start_valid)begin tag_q<=start_tag;backend_tag_q<=start_tag;v2_q<=start_v2;round_q<=0;program_q<=0;iteration_q<=0;state_q<=META_REQ;end
    META_REQ:if(meta_req_ready)state_q<=META_WAIT;
    META_WAIT:if(meta_rsp_valid&&!old_meta)begin
     if(meta_rsp_program_addr[2:0]!=0)begin error_code_q<=1;error_pc_q<=0;error_opcode_q<=0;state_q<=ERROR;end
     else begin
      for(i=0;i<8;i=i+1)a_q[64*i+:64]<=positive_float(meta_rsp_entropy[64*i+:64]);
      mx_q<=meta_rsp_entropy[64*10+:32];sp0_q<=meta_rsp_entropy[64*10+:32];
      ma_q<=meta_rsp_entropy[64*8+:32]&32'h7fffffc0;sp1_q<=meta_rsp_entropy[64*8+:32]&32'h7fffffc0;
      read0_q<={2'b00,meta_rsp_entropy[64*12]};read1_q<={2'b01,meta_rsp_entropy[64*12+1]};
      read2_q<={2'b10,meta_rsp_entropy[64*12+2]};read3_q<={2'b11,meta_rsp_entropy[64*12+3]};
      offset_q<={39'b0,meta_rsp_entropy[64*13+:19],6'b0};
      emask0_q<=float_mask(meta_rsp_entropy[64*14+:64]);emask1_q<=float_mask(meta_rsp_entropy[64*15+:64]);addr_q<=meta_rsp_program_addr;
      r_q<=0;f_q<=0;e_q<=0;iteration_q<=0;state_q<=ITER_REQ;
     end
    end
    ITER_REQ:if(iter_req_ready)state_q<=ITER_WAIT;
    ITER_WAIT:if(iter_error_valid&&!old_error)begin error_code_q<=2;error_pc_q<=iter_error_pc;error_opcode_q<=iter_error_opcode;state_q<=ERROR;end
     else if(iter_done_valid&&!old_done&&!iter_error_valid)begin
      r_q<=iter_done_r;f_q<=iter_done_f;e_q<=iter_done_e;round_q<=iter_done_round_mode;
      mx_q<=iter_done_mx;ma_q<=iter_done_ma;sp0_q<=iter_done_spaddr0;sp1_q<=iter_done_spaddr1;
      commit_q<=1;commit_program_q<=program_q;commit_iteration_q<=iteration_q;commit_backend_q<=backend_tag_q;
      backend_tag_q<=backend_tag_q+16'd1;
      if(iteration_q==ITERATIONS-1)state_q<=PROGRAM_RET;
      else begin iteration_q<=iteration_q+11'd1;state_q<=ITER_REQ;end
     end
    PROGRAM_RET:if(program_done_ready)begin
     if(program_q==PROGRAMS-1)state_q<=RETURN;
     else begin program_q<=program_q+3'd1;state_q<=META_REQ;end
    end
    RETURN:if(done_ready)state_q<=IDLE;
    ERROR:if(error_ready)state_q<=IDLE;
    default:begin error_code_q<=3;state_q<=ERROR;end
   endcase
  end
 end
endmodule
`default_nettype wire
