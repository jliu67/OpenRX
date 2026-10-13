// SPDX-License-Identifier: BSD-3-Clause
// Shared unsigned product; signed high uses the exact two's-complement correction.
`default_nettype none
module randomx_mul64 #(parameter integer RADIX4=0)(
    input wire clk,rst,input wire req_valid,output wire req_ready,
    input wire [15:0] req_tag,input wire [63:0] req_a,req_b,
    input wire req_high,req_signed,
    output wire rsp_valid,input wire rsp_ready,output wire [15:0] rsp_tag,
    output wire [63:0] rsp_result
);
    reg valid_q,busy_q;
    reg [15:0] tag_q;
    reg [63:0] result_q;
    assign req_ready=!rst && !busy_q && (!valid_q || rsp_ready);
    assign rsp_valid=!rst && valid_q;assign rsp_tag=tag_q;assign rsp_result=result_q;
    function [63:0] select_result;
        input [127:0] product;
        input [63:0] a,b;
        input high,signed_high;
        begin
            if(!high)select_result=product[63:0];
            else if(!signed_high)select_result=product[127:64];
            else select_result=product[127:64]-(a[63]?b:64'b0)-(b[63]?a:64'b0);
        end
    endfunction
    generate
        if(RADIX4==0)begin: direct
            wire [127:0] product={64'b0,req_a}*{64'b0,req_b};
            always @(posedge clk)begin
                if(rst)begin valid_q<=0;busy_q<=0;tag_q<=0;result_q<=0;end
                else begin
                    if(valid_q && rsp_ready)valid_q<=0;
                    if(req_valid && req_ready)begin
                        result_q<=select_result(product,req_a,req_b,req_high,req_signed);
                        tag_q<=req_tag;valid_q<=1;
                    end
                end
            end
        end else if(RADIX4==1)begin: iterative
            reg [127:0] accumulator_q,multiplicand_q;
            reg [63:0] multiplier_q,a_q,b_q;
            reg high_q,signed_q;
            reg [4:0] step_q;
            wire [127:0] digit=multiplier_q[1:0]==0?128'b0:
                multiplier_q[1:0]==1?multiplicand_q:
                multiplier_q[1:0]==2?(multiplicand_q<<1):multiplicand_q+(multiplicand_q<<1);
            wire [127:0] sum=accumulator_q+digit;
            always @(posedge clk)begin
                if(rst)begin
                    valid_q<=0;busy_q<=0;tag_q<=0;result_q<=0;accumulator_q<=0;
                    multiplicand_q<=0;multiplier_q<=0;a_q<=0;b_q<=0;
                    high_q<=0;signed_q<=0;step_q<=0;
                end else begin
                    if(valid_q && rsp_ready)valid_q<=0;
                    if(req_valid && req_ready)begin
                        tag_q<=req_tag;a_q<=req_a;b_q<=req_b;high_q<=req_high;signed_q<=req_signed;
                        accumulator_q<=0;multiplicand_q<={64'b0,req_a};multiplier_q<=req_b;
                        step_q<=0;busy_q<=1;
                    end else if(busy_q)begin
                        accumulator_q<=sum;multiplicand_q<=multiplicand_q<<2;multiplier_q<=multiplier_q>>2;
                        step_q<=step_q+1'b1;
                        if(step_q==31)begin
                            result_q<=select_result(sum,a_q,b_q,high_q,signed_q);busy_q<=0;valid_q<=1;
                        end
                    end
                end
            end
        end else begin: invalid_parameter
            multiplier_requires_RADIX4_0_or_1 invalid();
        end
    endgenerate
endmodule
`default_nettype wire
