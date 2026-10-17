// SPDX-License-Identifier: BSD-3-Clause
// One prepared native superscalar program. Program/cache preparation and the
// immutable instruction/reciprocal service remain external to this component.
`default_nettype none
module randomx_superscalar_execute #(parameter integer MUL_RADIX4=1)(
    input wire clk,rst,cancel,
    input wire req_valid,output wire req_ready,
    input wire [15:0] req_tag,req_epoch,
    input wire [511:0] req_r,
    input wire [9:0] req_count,
    input wire [7:0] req_address_reg,
    input wire [31:0] req_rcp_count,
    output wire fetch_valid,input wire fetch_ready,
    output wire [31:0] fetch_tag,
    output wire [15:0] fetch_epoch,
    output wire [8:0] fetch_pc,
    input wire fetch_rsp_valid,output wire fetch_rsp_ready,
    input wire [31:0] fetch_rsp_tag,
    input wire [15:0] fetch_rsp_epoch,
    input wire [8:0] fetch_rsp_pc,
    input wire [63:0] fetch_rsp_instruction,
    input wire fetch_rsp_error,fetch_rsp_rcp_valid,
    input wire [31:0] fetch_rsp_rcp_index,
    input wire [63:0] fetch_rsp_rcp_value,
    output wire rsp_valid,input wire rsp_ready,
    output wire [15:0] rsp_tag,rsp_epoch,
    output wire [511:0] rsp_r,
    output wire [63:0] rsp_selected,
    output wire rsp_error,
    output wire [8:0] rsp_error_pc,
    output wire [63:0] rsp_cycles,
    output wire [9:0] rsp_retired,rsp_muls,
    output wire commit_valid,
    output wire [15:0] commit_tag,commit_epoch,
    output wire [8:0] commit_pc,
    output wire [7:0] commit_opcode,
    output wire [511:0] commit_r,
    output wire [2:0] phase,
    output wire generation_exhausted
);
    localparam [2:0] IDLE=0,FETCH_REQ=1,FETCH_RSP=2,EXEC=3,
        MUL_REQ=4,MUL_WAIT=5,RETURN=6;
    reg [2:0] state_q;
    reg [15:0] generation_q,tag_q,epoch_q;
    reg [31:0] service_tag_q,rcp_count_q;
    reg [511:0] r_q;
    reg [9:0] count_q,retired_q,muls_q;
    reg [2:0] address_q;
    reg [8:0] pc_q,error_pc_q,commit_pc_q;
    reg [63:0] instruction_q,rcp_value_q,cycles_q;
    reg error_q,commit_q;
    reg [7:0] commit_opcode_q;
    wire active=!rst&&!cancel;
    assign req_ready=active&&state_q==IDLE&&generation_q!=16'hffff;
    assign generation_exhausted=!rst&&generation_q==16'hffff;
    assign fetch_valid=active&&state_q==FETCH_REQ;
    assign fetch_tag=service_tag_q;
    assign fetch_epoch=epoch_q;
    assign fetch_pc=pc_q;
    // Never consume a current-tag response until its request was accepted.
    // All other tags (including canceled requests) drain in every state.
    assign fetch_rsp_ready=active&&
        (state_q!=FETCH_REQ||fetch_rsp_tag!=service_tag_q);
    assign rsp_valid=active&&state_q==RETURN;
    assign rsp_tag=tag_q;
    assign rsp_epoch=epoch_q;
    assign rsp_r=r_q;
    assign rsp_selected=error_q?64'b0:r_q[address_q*64+:64];
    assign rsp_error=error_q;
    assign rsp_error_pc=error_pc_q;
    assign rsp_cycles=cycles_q;
    assign rsp_retired=retired_q;
    assign rsp_muls=muls_q;
    assign commit_valid=active&&commit_q;
    assign commit_tag=tag_q;
    assign commit_epoch=epoch_q;
    assign commit_pc=commit_pc_q;
    assign commit_opcode=commit_opcode_q;
    assign commit_r=r_q;
    assign phase=state_q;

    wire [7:0] incoming_op=fetch_rsp_instruction[7:0];
    wire incoming_uses_src=incoming_op==0||incoming_op==1||incoming_op==2||
        incoming_op==3||incoming_op==11||incoming_op==12;
    // These are native superscalar opcodes, not RandomX VM bytecode. In
    // particular IMUL_RCP carries a prepared table INDEX, not a divisor.
    wire malformed_instruction=incoming_op>=14||fetch_rsp_instruction[15:8]>=8||
        (incoming_uses_src&&fetch_rsp_instruction[23:16]>=8)||
        (incoming_op==4&&fetch_rsp_instruction[63:32]>63)||
        (incoming_op==13&&(!fetch_rsp_rcp_valid||
          fetch_rsp_rcp_index!=fetch_rsp_instruction[63:32]||
          fetch_rsp_instruction[63:32]>=rcp_count_q));

    wire [7:0] opcode=instruction_q[7:0];
    wire [2:0] dst=instruction_q[10:8],src=instruction_q[18:16];
    wire [63:0] a=r_q[dst*64+:64],b=r_q[src*64+:64];
    wire [63:0] imm={{32{instruction_q[63]}},instruction_q[63:32]};
    wire [5:0] rotate=instruction_q[37:32];
    wire is_multiply=opcode==3||opcode==11||opcode==12||opcode==13;
    reg [63:0] simple_result;
    always @* begin
        simple_result=a;
        case(opcode)
            0:simple_result=a-b;
            1:simple_result=a^b;
            2:simple_result=a+(b<<instruction_q[27:26]);
            4:simple_result=rotate==0?a:(a>>rotate)|(a<<(64-rotate));
            5,7,9:simple_result=a+imm;
            6,8,10:simple_result=a^imm;
            default:simple_result=a;
        endcase
    end
    wire mul_req_ready,mul_rsp_valid;
    wire [15:0] mul_rsp_tag;
    wire [63:0] mul_result;
    randomx_mul64 #(.RADIX4(MUL_RADIX4)) multiplier(
        .clk(clk),.rst(rst||cancel),
        .req_valid(active&&state_q==MUL_REQ),.req_ready(mul_req_ready),
        .req_tag({7'b0,pc_q}),.req_a(a),.req_b(opcode==13?rcp_value_q:b),
        .req_high(opcode==11||opcode==12),.req_signed(opcode==12),
        .rsp_valid(mul_rsp_valid),.rsp_ready(active&&state_q==MUL_WAIT),
        .rsp_tag(mul_rsp_tag),.rsp_result(mul_result)
    );

    // Generation advances once for EVERY accepted program, including empty or
    // invalid ones, and survives cancel. Exhaustion fails closed before wrap.
    // Hard reset may recycle identities only with an externally quiescent
    // service: no pre-reset response may survive that reset.
    always @(posedge clk) begin
        if(rst)generation_q<=0;
        else if(req_valid&&req_ready)generation_q<=generation_q+1'b1;
        if(rst||cancel)begin
            state_q<=IDLE;tag_q<=0;epoch_q<=0;service_tag_q<=0;rcp_count_q<=0;
            r_q<=0;count_q<=0;retired_q<=0;muls_q<=0;address_q<=0;
            pc_q<=0;error_pc_q<=0;instruction_q<=0;rcp_value_q<=0;cycles_q<=0;
            error_q<=0;commit_q<=0;commit_pc_q<=0;commit_opcode_q<=0;
        end else begin
            commit_q<=0;
            // Availability latency, excluding held return-response clocks.
            if(state_q!=IDLE&&state_q!=RETURN)cycles_q<=cycles_q+1'b1;
            case(state_q)
                IDLE:if(req_valid&&req_ready)begin
                    tag_q<=req_tag;epoch_q<=req_epoch;
                    service_tag_q<={generation_q+16'd1,req_tag};
                    r_q<=req_r;count_q<=req_count;address_q<=req_address_reg[2:0];
                    rcp_count_q<=req_rcp_count;pc_q<=0;error_pc_q<=0;
                    retired_q<=0;muls_q<=0;cycles_q<=0;
                    error_q<=req_count>512||req_address_reg>=8;
                    if(req_count>512||req_address_reg>=8||req_count==0)state_q<=RETURN;
                    else state_q<=FETCH_REQ;
                end
                FETCH_REQ:if(fetch_valid&&fetch_ready)state_q<=FETCH_RSP;
                FETCH_RSP:if(fetch_rsp_valid&&fetch_rsp_ready&&fetch_rsp_tag==service_tag_q)begin
                    if(fetch_rsp_error||fetch_rsp_epoch!=epoch_q||fetch_rsp_pc!=pc_q||
                       malformed_instruction)begin
                        error_q<=1;error_pc_q<=pc_q;state_q<=RETURN;
                    end else begin
                        instruction_q<=fetch_rsp_instruction;rcp_value_q<=fetch_rsp_rcp_value;
                        state_q<=EXEC;
                    end
                end
                EXEC:if(is_multiply)state_q<=MUL_REQ;
                else begin
                    r_q[dst*64+:64]<=simple_result;retired_q<=retired_q+1'b1;
                    commit_q<=1;commit_pc_q<=pc_q;commit_opcode_q<=opcode;
                    if({1'b0,pc_q}+10'd1==count_q)state_q<=RETURN;
                    else begin pc_q<=pc_q+1'b1;state_q<=FETCH_REQ;end
                end
                MUL_REQ:if(mul_req_ready)state_q<=MUL_WAIT;
                MUL_WAIT:if(mul_rsp_valid)begin
                    if(mul_rsp_tag!={7'b0,pc_q})begin
                        error_q<=1;error_pc_q<=pc_q;state_q<=RETURN;
                    end else begin
                        r_q[dst*64+:64]<=mul_result;retired_q<=retired_q+1'b1;muls_q<=muls_q+1'b1;
                        commit_q<=1;commit_pc_q<=pc_q;commit_opcode_q<=opcode;
                        if({1'b0,pc_q}+10'd1==count_q)state_q<=RETURN;
                        else begin pc_q<=pc_q+1'b1;state_q<=FETCH_REQ;end
                    end
                end
                RETURN:if(rsp_ready)state_q<=IDLE;
                default:state_q<=IDLE;
            endcase
        end
    end
endmodule
`default_nettype wire
