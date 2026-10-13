// SPDX-License-Identifier: BSD-3-Clause
// All signed32 inputs fit exactly in binary64's53-bit significand: no rounding.
`default_nettype none
module randomx_i32_to_f64(input wire [31:0] word_i,output reg [63:0] bits_o);
    reg [31:0] magnitude;
    reg [5:0] leading;
    reg [10:0] exponent;
    reg [63:0] normalized;
    integer i;
    always @* begin
        magnitude=word_i[31] ? (~word_i+32'd1) : word_i;
        leading=0;
        for(i=0;i<32;i=i+1)if(magnitude[i])leading=i;
        exponent=11'd1023+leading;
        normalized={32'b0,magnitude} << (52-leading);
        bits_o=magnitude==0 ? 64'b0 : {word_i[31],exponent,normalized[51:0]};
    end
endmodule
`default_nettype wire
