// SPDX-License-Identifier: BSD-3-Clause
// Native RandomX integer subset. Unsupported operations terminate with an error.
`default_nettype none
module randomx_integer_execute #(parameter integer SERIAL_IADD=0) (
    input wire clk,rst,
    input wire req_valid,output wire req_ready,input wire [15:0] req_tag,
    input wire req_v2,input wire [1:0] req_round_mode,
    input wire [511:0] req_r,req_f,req_e,req_a,
    input wire [63:0] req_emask0,req_emask1,req_program_addr,
    output wire prog_valid,input wire prog_ready,output wire [63:0] prog_addr,
    output wire [15:0] prog_tag,input wire prog_rsp_valid,output wire prog_rsp_ready,
    input wire [15:0] prog_rsp_tag,input wire [63:0] prog_rsp_instruction,
    output wire [15:0] mem_tag,
    output wire rd_valid,input wire rd_ready,output wire [20:0] rd_addr,
    input wire rsp_valid,output wire rsp_ready,input wire [15:0] rsp_tag,
    input wire [127:0] rsp_data,
    output wire wr_valid,input wire wr_ready,output wire [20:0] wr_addr,
    output wire [127:0] wr_data,output wire [15:0] wr_strb,
    output wire ret_valid,input wire ret_ready,output wire [15:0] ret_tag,
    output wire [511:0] ret_r,ret_f,ret_e,output wire [1:0] ret_round_mode,
    output wire error_valid,input wire error_ready,output wire [15:0] error_tag,
    output wire [8:0] error_pc,output wire [7:0] error_opcode,
    output wire commit_valid,output wire [15:0] commit_tag,
    output wire [8:0] commit_pc,output wire [7:0] commit_opcode,output wire [511:0] commit_r
);
`include "randomx_opcode_ceils.vh"
    localparam [3:0] IDLE=0,FETCH_REQ=1,FETCH_RSP=2,EXEC=3,MEM_REQ=4,MEM_RSP=5,
        STORE_REQ=6,IADD_SECOND=7,RETURN=8,ERROR=9;
    localparam [3:0] ADD_RS=0,ADD_M=1,SUB_R=2,SUB_M=3,NEG_R=4,XOR_R=5,XOR_M=6,
        ROR_R=7,ROL_R=8,SWAP_R=9,STORE=10,BAD=15;
    reg [3:0] state_q;
    reg [8:0] pc_q;
    reg [15:0] tag_q;
    reg v2_q;
    reg [1:0] round_q;
    reg [63:0] program_q,instruction_q,tmp_q;
    reg [511:0] r_q,f_q,e_q;
    reg [20:0] address_q;
    reg commit_q;
    reg [8:0] commit_pc_q;
    reg [7:0] commit_opcode_q;
    wire [2:0] dst=instruction_q[10:8],src=instruction_q[18:16];
    wire [63:0] rd=r_q[64*dst+:64],rs=r_q[64*src+:64];
    wire [63:0] immediate={{32{instruction_q[63]}},instruction_q[63:32]};
    wire [63:0] register_operand=dst==src ? immediate : rs;
    wire [63:0] displacement=dst==3'd5 ? immediate : 64'b0;
    wire [63:0] shifted=rs<<instruction_q[27:26];
    wire [5:0] rotate=dst==src ? instruction_q[37:32] : rs[5:0];
    function [3:0] decode;
        input [7:0] opcode;
        begin
            if(opcode<CEIL_IADD_RS)decode=ADD_RS;
            else if(opcode<CEIL_IADD_M)decode=ADD_M;
            else if(opcode<CEIL_ISUB_R)decode=SUB_R;
            else if(opcode<CEIL_ISUB_M)decode=SUB_M;
            else if(opcode<CEIL_IMUL_RCP)decode=BAD;
            else if(opcode<CEIL_INEG_R)decode=NEG_R;
            else if(opcode<CEIL_IXOR_R)decode=XOR_R;
            else if(opcode<CEIL_IXOR_M)decode=XOR_M;
            else if(opcode<CEIL_IROR_R)decode=ROR_R;
            else if(opcode<CEIL_IROL_R)decode=ROL_R;
            else if(opcode<CEIL_ISWAP_R)decode=SWAP_R;
            else if(opcode<CEIL_CFROUND)decode=BAD;
            else decode=STORE;
        end
    endfunction
    wire [3:0] kind=decode(instruction_q[7:0]);
    wire [31:0] memory_mask=kind==STORE ?
        (instruction_q[31:28]>=14 ? 32'h001ffff8 :
            (instruction_q[25:24]!=0 ? 32'h00003ff8 : 32'h0003fff8)) :
        (dst==src ? 32'h001ffff8 :
            (instruction_q[25:24]!=0 ? 32'h00003ff8 : 32'h0003fff8));
    wire [31:0] memory_base=kind==STORE ? rd[31:0] : (dst==src ? 32'b0 : rs[31:0]);
    // Address masks retain <=21 bits, so modulo32 addition equals native low64 bits.
    wire [31:0] memory_address=(memory_base+instruction_q[63:32])&memory_mask;
    wire [63:0] memory_value=address_q[3] ? rsp_data[127:64] : rsp_data[63:0];
    wire [63:0] first_iadd;
    generate
        if(SERIAL_IADD==0)begin: two_adds
            assign first_iadd=shifted+displacement;
        end else begin: shared_add
            assign first_iadd=0;
        end
        if(SERIAL_IADD!=0 && SERIAL_IADD!=1)begin: invalid_parameter
            integer_execute_requires_SERIAL_IADD_0_or_1 invalid();
        end
    endgenerate
    wire [63:0] add_left=state_q==EXEC && kind==ADD_RS && SERIAL_IADD!=0 ? shifted : rd;
    wire [63:0] add_right=state_q==IADD_SECOND ? tmp_q :
        state_q==MEM_RSP ? memory_value : (SERIAL_IADD!=0 ? displacement : first_iadd);
    wire [63:0] add_result=add_left+add_right;
    wire old_program=prog_rsp_tag!=tag_q,old_memory=rsp_tag!=tag_q;
    assign req_ready=!rst && state_q==IDLE;
    assign prog_valid=!rst && state_q==FETCH_REQ;
    assign prog_addr=program_q+{52'b0,pc_q,3'b0};assign prog_tag=tag_q;
    assign prog_rsp_ready=!rst && (old_program || state_q==IDLE || state_q==FETCH_RSP);
    assign mem_tag=tag_q;
    assign rd_valid=!rst && state_q==MEM_REQ;assign rd_addr={address_q[20:4],4'b0};
    assign rsp_ready=!rst && (old_memory || state_q==IDLE || state_q==MEM_RSP);
    assign wr_valid=!rst && state_q==STORE_REQ;assign wr_addr={address_q[20:4],4'b0};
    assign wr_data=address_q[3] ? {rs,64'b0} : {64'b0,rs};
    assign wr_strb=address_q[3] ? 16'hff00 : 16'h00ff;
    assign ret_valid=!rst && state_q==RETURN;assign ret_tag=tag_q;
    assign ret_r=r_q;assign ret_f=f_q;assign ret_e=e_q;assign ret_round_mode=round_q;
    assign error_valid=!rst && state_q==ERROR;assign error_tag=tag_q;
    assign error_pc=pc_q;assign error_opcode=instruction_q[7:0];
    assign commit_valid=!rst && commit_q;assign commit_tag=tag_q;
    assign commit_pc=commit_pc_q;assign commit_opcode=commit_opcode_q;assign commit_r=r_q;
    task retire_instruction;
        begin
            commit_q<=1;commit_pc_q<=pc_q;commit_opcode_q<=instruction_q[7:0];
            if(pc_q==(v2_q ? 9'd383 : 9'd255))state_q<=RETURN;
            else begin pc_q<=pc_q+1'b1;state_q<=FETCH_REQ;end
        end
    endtask
    always @(posedge clk)begin
        if(rst)begin
            state_q<=IDLE;pc_q<=0;tag_q<=0;v2_q<=0;round_q<=0;program_q<=0;
            instruction_q<=0;tmp_q<=0;r_q<=0;f_q<=0;e_q<=0;address_q<=0;
            commit_q<=0;commit_pc_q<=0;commit_opcode_q<=0;
        end else begin
            commit_q<=0;
            case(state_q)
                IDLE:if(req_valid)begin
                    tag_q<=req_tag;v2_q<=req_v2;round_q<=req_round_mode;program_q<=req_program_addr;
                    r_q<=req_r;f_q<=req_f;e_q<=req_e;pc_q<=0;state_q<=FETCH_REQ;
                end
                FETCH_REQ:if(prog_ready)state_q<=FETCH_RSP;
                FETCH_RSP:if(prog_rsp_valid && !old_program)begin
                    instruction_q<=prog_rsp_instruction;state_q<=EXEC;
                end
                EXEC:case(kind)
                    ADD_RS:if(SERIAL_IADD!=0)begin tmp_q<=add_result;state_q<=IADD_SECOND;end
                        else begin r_q[64*dst+:64]<=add_result;retire_instruction();end
                    SUB_R:begin r_q[64*dst+:64]<=rd-register_operand;retire_instruction();end
                    NEG_R:begin r_q[64*dst+:64]<=~rd+64'd1;retire_instruction();end
                    XOR_R:begin r_q[64*dst+:64]<=rd^register_operand;retire_instruction();end
                    ROR_R:begin r_q[64*dst+:64]<=(rd>>rotate)|(rd<<(64-rotate));retire_instruction();end
                    ROL_R:begin r_q[64*dst+:64]<=(rd<<rotate)|(rd>>(64-rotate));retire_instruction();end
                    SWAP_R:begin
                        if(dst!=src)begin r_q[64*dst+:64]<=rs;r_q[64*src+:64]<=rd;end
                        retire_instruction();
                    end
                    ADD_M,SUB_M,XOR_M:begin address_q<=memory_address[20:0];state_q<=MEM_REQ;end
                    STORE:begin address_q<=memory_address[20:0];state_q<=STORE_REQ;end
                    default:state_q<=ERROR;
                endcase
                IADD_SECOND:begin r_q[64*dst+:64]<=add_result;retire_instruction();end
                MEM_REQ:if(rd_ready)state_q<=MEM_RSP;
                MEM_RSP:if(rsp_valid && !old_memory)begin
                    if(kind==ADD_M)r_q[64*dst+:64]<=add_result;
                    else if(kind==SUB_M)r_q[64*dst+:64]<=rd-memory_value;
                    else r_q[64*dst+:64]<=rd^memory_value;
                    retire_instruction();
                end
                STORE_REQ:if(wr_ready)retire_instruction();
                RETURN:if(ret_ready)state_q<=IDLE;
                ERROR:if(error_ready)state_q<=IDLE;
                default:state_q<=IDLE;
            endcase
        end
    end
endmodule
`default_nettype wire
