// SPDX-License-Identifier: BSD-3-Clause
// Immutable program image plus optional once-per-admission native reciprocals.
// Logical invalidation protects unreset memory. External generations must not
// be reused while a canceled response can still arrive.
`default_nettype none
module randomx_program_reciprocals #(parameter integer PREPARE_RCP=1)(
    input wire clk,rst,cancel,
    input wire prep_valid,output wire prep_ready,
    input wire [15:0] prep_epoch,input wire prep_v2,
    input wire [63:0] prep_program_addr,
    output wire load_req_valid,input wire load_req_ready,
    output wire [63:0] load_req_addr,output wire [24:0] load_req_tag,
    input wire load_rsp_valid,output wire load_rsp_ready,
    input wire [24:0] load_rsp_tag,input wire [63:0] load_rsp_instruction,
    input wire load_rsp_error,
    output wire prep_rsp_valid,input wire prep_rsp_ready,
    output wire [15:0] prep_rsp_epoch,output wire prep_rsp_error,
    output wire image_valid,output wire [15:0] image_epoch,
    output wire image_v2,output wire [63:0] image_program_addr,
    input wire fetch_req_valid,output wire fetch_req_ready,
    input wire [8:0] fetch_req_pc,input wire [15:0] fetch_req_tag,fetch_req_epoch,
    output wire fetch_rsp_valid,input wire fetch_rsp_ready,
    output wire [15:0] fetch_rsp_tag,fetch_rsp_epoch,
    output wire [8:0] fetch_rsp_pc,output wire [63:0] fetch_rsp_instruction,
    output wire fetch_rsp_rcp_valid,fetch_rsp_rcp_nop,
    output wire [31:0] fetch_rsp_rcp_divisor,
    output wire [63:0] fetch_rsp_rcp_value,output wire fetch_rsp_error
);
`include "randomx_opcode_ceils.vh"
    localparam [2:0] IDLE=0,LOAD_REQ=1,LOAD_WAIT=2,RCP_REQ=3,RCP_WAIT=4,PREP_RETURN=5;
    reg [2:0] state_q;
    reg [15:0] epoch_q;
    reg v2_q,image_valid_q,prep_error_q;
    reg [63:0] program_addr_q,word_q;
    reg [8:0] pc_q;
    reg [63:0] instructions_q[0:383];
    reg [63:0] reciprocals_q[0:383];
    reg fetch_valid_q,fetch_error_q,fetch_rcp_valid_q,fetch_rcp_nop_q;
    reg [15:0] fetch_tag_q,fetch_epoch_q;
    reg [8:0] fetch_pc_q;
    reg [63:0] fetch_word_q,fetch_value_q;
    reg [31:0] fetch_divisor_q;
    wire [8:0] last_pc=v2_q?9'd383:9'd255;
    wire [24:0] expected_load_tag={epoch_q,pc_q};
    wire load_is_rcp=load_rsp_instruction[7:0]>=CEIL_ISMULH_M &&
                     load_rsp_instruction[7:0]<CEIL_IMUL_RCP;
    wire [31:0] load_divisor=load_rsp_instruction[63:32];
    wire load_nop=load_divisor==0 || (load_divisor&(load_divisor-32'd1))==0;
    wire [63:0] fetch_word=instructions_q[fetch_req_pc];
    wire fetch_is_rcp=fetch_word[7:0]>=CEIL_ISMULH_M && fetch_word[7:0]<CEIL_IMUL_RCP;
    wire [31:0] fetch_divisor=fetch_word[63:32];
    wire fetch_nop=fetch_divisor==0 || (fetch_divisor&(fetch_divisor-32'd1))==0;
    wire rcp_ready,rcp_valid,rcp_nop;
    wire [15:0] rcp_tag;
    wire [63:0] rcp_value;
    generate
        if(PREPARE_RCP==1)begin: prepared
            randomx_reciprocal32 reciprocal(
                .clk(clk),.rst(rst|cancel),.req_valid(!rst&&!cancel&&state_q==RCP_REQ),
                .req_ready(rcp_ready),.req_tag(epoch_q),.req_divisor(word_q[63:32]),
                .rsp_valid(rcp_valid),.rsp_ready(!rst&&!cancel&&state_q==RCP_WAIT),
                .rsp_tag(rcp_tag),.rsp_result(rcp_value),.rsp_nop(rcp_nop));
        end else if(PREPARE_RCP==0)begin: baseline
            assign rcp_ready=0;assign rcp_valid=0;assign rcp_tag=0;
            assign rcp_value=0;assign rcp_nop=0;
        end else begin: invalid_parameter
            program_reciprocals_requires_PREPARE_RCP_0_or_1 invalid();
        end
    endgenerate
    assign prep_ready=!rst&&!cancel&&state_q==IDLE&&!fetch_valid_q;
    assign load_req_valid=!rst&&!cancel&&state_q==LOAD_REQ;
    assign load_req_addr=program_addr_q+{52'b0,pc_q,3'b0};
    assign load_req_tag=expected_load_tag;
    // A matching reply cannot be accepted before its read request. Stale tags
    // (including their error flags) are drained without altering private state.
    assign load_rsp_ready=!rst&&!cancel&&(state_q!=LOAD_REQ||load_rsp_tag!=expected_load_tag);
    assign prep_rsp_valid=!rst&&!cancel&&state_q==PREP_RETURN;
    assign prep_rsp_epoch=epoch_q;assign prep_rsp_error=prep_error_q;
    assign image_valid=!rst&&!cancel&&image_valid_q;
    assign image_epoch=epoch_q;assign image_v2=v2_q;assign image_program_addr=program_addr_q;
    assign fetch_req_ready=!rst&&!cancel&&state_q==IDLE&&!prep_valid&&(!fetch_valid_q||fetch_rsp_ready);
    assign fetch_rsp_valid=!rst&&!cancel&&fetch_valid_q;
    assign fetch_rsp_tag=fetch_tag_q;assign fetch_rsp_epoch=fetch_epoch_q;assign fetch_rsp_pc=fetch_pc_q;
    assign fetch_rsp_instruction=fetch_word_q;assign fetch_rsp_rcp_value=fetch_value_q;
    assign fetch_rsp_rcp_valid=fetch_rcp_valid_q;assign fetch_rsp_rcp_nop=fetch_rcp_nop_q;
    assign fetch_rsp_rcp_divisor=fetch_divisor_q;assign fetch_rsp_error=fetch_error_q;
    task next_word;
        begin
            if(pc_q==last_pc)begin image_valid_q<=1;state_q<=PREP_RETURN;end
            else begin pc_q<=pc_q+9'd1;state_q<=LOAD_REQ;end
        end
    endtask
    always @(posedge clk)begin
        if(rst||cancel)begin
            state_q<=IDLE;epoch_q<=0;v2_q<=0;image_valid_q<=0;prep_error_q<=0;
            program_addr_q<=0;word_q<=0;pc_q<=0;
            fetch_valid_q<=0;fetch_error_q<=0;fetch_rcp_valid_q<=0;fetch_rcp_nop_q<=0;
            fetch_tag_q<=0;fetch_epoch_q<=0;fetch_pc_q<=0;fetch_word_q<=0;fetch_value_q<=0;fetch_divisor_q<=0;
        end else begin
            if(fetch_valid_q&&fetch_rsp_ready)fetch_valid_q<=0;
            if(fetch_req_valid&&fetch_req_ready)begin
                fetch_valid_q<=1;fetch_tag_q<=fetch_req_tag;fetch_epoch_q<=epoch_q;fetch_pc_q<=fetch_req_pc;
                fetch_word_q<=0;fetch_value_q<=0;fetch_divisor_q<=0;fetch_rcp_valid_q<=0;fetch_rcp_nop_q<=0;
                fetch_error_q<=!image_valid_q||fetch_req_epoch!=epoch_q||fetch_req_pc>last_pc;
                if(image_valid_q&&fetch_req_epoch==epoch_q&&fetch_req_pc<=last_pc)begin
                    fetch_word_q<=fetch_word;
                    if(PREPARE_RCP==1&&fetch_is_rcp)begin
                        fetch_rcp_valid_q<=1;fetch_rcp_nop_q<=fetch_nop;
                        fetch_divisor_q<=fetch_divisor;fetch_value_q<=reciprocals_q[fetch_req_pc];
                    end
                end
            end
            case(state_q)
                IDLE:if(prep_valid&&prep_ready)begin
                    epoch_q<=prep_epoch;v2_q<=prep_v2;program_addr_q<=prep_program_addr;
                    pc_q<=0;image_valid_q<=0;prep_error_q<=0;state_q<=LOAD_REQ;
                end
                LOAD_REQ:if(load_req_ready)state_q<=LOAD_WAIT;
                LOAD_WAIT:if(load_rsp_valid&&load_rsp_tag==expected_load_tag)begin
                    if(load_rsp_error)begin image_valid_q<=0;prep_error_q<=1;state_q<=PREP_RETURN;end
                    else begin
                        instructions_q[pc_q]<=load_rsp_instruction;word_q<=load_rsp_instruction;
                        if(PREPARE_RCP==1)reciprocals_q[pc_q]<=0;
                        if(PREPARE_RCP==1&&load_is_rcp&&!load_nop)state_q<=RCP_REQ;
                        else next_word();
                    end
                end
                RCP_REQ:if(rcp_ready)state_q<=RCP_WAIT;
                RCP_WAIT:if(rcp_valid)begin
                    if(rcp_tag!=epoch_q||rcp_nop)begin image_valid_q<=0;prep_error_q<=1;state_q<=PREP_RETURN;end
                    else begin reciprocals_q[pc_q]<=rcp_value;next_word();end
                end
                PREP_RETURN:if(prep_rsp_ready)state_q<=IDLE;
                default:begin image_valid_q<=0;prep_error_q<=1;state_q<=PREP_RETURN;end
            endcase
        end
    end
endmodule
`default_nettype wire
