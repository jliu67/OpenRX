// SPDX-License-Identifier: BSD-3-Clause
// floor(2^(63+bit_length(divisor))/divisor), for nonzero/non-power-of-two imm32.
`default_nettype none
module randomx_reciprocal32(
    input wire clk,rst,input wire req_valid,output wire req_ready,
    input wire [15:0] req_tag,input wire [31:0] req_divisor,
    output wire rsp_valid,input wire rsp_ready,output wire [15:0] rsp_tag,
    output wire [63:0] rsp_result,output wire rsp_nop
);
    reg valid_q,busy_q,nop_q;
    reg [15:0] tag_q;
    reg [31:0] divisor_q,remainder_q;
    reg [63:0] quotient_q;
    reg [5:0] step_q;
    integer bit_length,k;
    always @*begin
        bit_length=0;
        for(k=0;k<32;k=k+1)if(req_divisor[k])bit_length=k+1;
    end
    wire is_nop=req_divisor==0 || (req_divisor&(req_divisor-32'd1))==0;
    wire [32:0] doubled={remainder_q,1'b0};
    wire subtract=doubled>={1'b0,divisor_q};
    wire [32:0] reduced=subtract?doubled-{1'b0,divisor_q}:doubled;
    assign req_ready=!rst && !busy_q && (!valid_q || rsp_ready);
    assign rsp_valid=!rst && valid_q;assign rsp_tag=tag_q;
    assign rsp_result=quotient_q;assign rsp_nop=nop_q;
    always @(posedge clk)begin
        if(rst)begin valid_q<=0;busy_q<=0;nop_q<=0;tag_q<=0;divisor_q<=0;remainder_q<=0;quotient_q<=0;step_q<=0;end
        else begin
            if(valid_q && rsp_ready)valid_q<=0;
            if(req_valid && req_ready)begin
                tag_q<=req_tag;nop_q<=is_nop;divisor_q<=req_divisor;quotient_q<=0;step_q<=0;
                if(is_nop)begin valid_q<=1;busy_q<=0;remainder_q<=0;end
                else begin remainder_q<=32'd1<<(bit_length-1);busy_q<=1;end
            end else if(busy_q)begin
                remainder_q<=reduced[31:0];quotient_q<={quotient_q[62:0],subtract};step_q<=step_q+1'b1;
                if(step_q==63)begin busy_q<=0;valid_q<=1;end
            end
        end
    end
endmodule
`default_nettype wire
