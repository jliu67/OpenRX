// SPDX-License-Identifier: BSD-3-Clause
// One AESENC/AESDEC round, with an arbitrary raw key, as used by RandomX.
`default_nettype none
module randomx_aes_round (
    input wire [127:0] state_in,
    input wire [127:0] key_in,
    input wire decrypt,
    output wire [127:0] state_out
);
    wire [127:0] sub_enc;
    wire [127:0] sub_dec;
    wire [127:0] shifted;
    wire [127:0] mixed_enc;
    wire [127:0] mixed_dec;

    // The matrix byte (r,c) is state_in[8*(4*c+r) +: 8].
    genvar word_idx, row, col;
    generate
        for (word_idx = 0; word_idx < 4; word_idx = word_idx + 1) begin: sboxes
            aes_sbox enc (.sboxw(state_in[32*word_idx +: 32]),
                          .new_sboxw(sub_enc[32*word_idx +: 32]));
            aes_inv_sbox dec (.sboxw(state_in[32*word_idx +: 32]),
                              .new_sboxw(sub_dec[32*word_idx +: 32]));
        end
        for (col = 0; col < 4; col = col + 1) begin: columns
            for (row = 0; row < 4; row = row + 1) begin: rows
                assign shifted[8*(4*col+row) +: 8] = decrypt ?
                    sub_dec[8*(4*((col-row+4)%4)+row) +: 8] :
                    sub_enc[8*(4*((col+row)%4)+row) +: 8];
            end
            wire [7:0] a = shifted[32*col +: 8];
            wire [7:0] b = shifted[32*col+8 +: 8];
            wire [7:0] c = shifted[32*col+16 +: 8];
            wire [7:0] d = shifted[32*col+24 +: 8];
            assign mixed_enc[32*col +: 32] = {
                (mul3(a)^b^c^xtime(d)),
                (a^b^xtime(c)^mul3(d)),
                (a^xtime(b)^mul3(c)^d),
                (xtime(a)^mul3(b)^c^d)
            };
            assign mixed_dec[32*col +: 32] = {
                (mul9(a)^mul13(b)^mul11(c)^mul14(d)),
                (mul13(a)^mul11(b)^mul14(c)^mul9(d)),
                (mul11(a)^mul14(b)^mul9(c)^mul13(d)),
                (mul14(a)^mul9(b)^mul13(c)^mul11(d))
            };
        end
    endgenerate

    function [7:0] xtime;
        input [7:0] x;
        begin xtime = {x[6:0],1'b0} ^ (8'h1b & {8{x[7]}}); end
    endfunction
    function [7:0] mul3;
        input [7:0] x;
        begin mul3 = xtime(x) ^ x; end
    endfunction
    function [7:0] mul9;
        input [7:0] x;
        begin mul9 = xtime(xtime(xtime(x))) ^ x; end
    endfunction
    function [7:0] mul11;
        input [7:0] x;
        begin mul11 = xtime(xtime(xtime(x))) ^ xtime(x) ^ x; end
    endfunction
    function [7:0] mul13;
        input [7:0] x;
        begin mul13 = xtime(xtime(xtime(x))) ^ xtime(xtime(x)) ^ x; end
    endfunction
    function [7:0] mul14;
        input [7:0] x;
        begin mul14 = xtime(xtime(xtime(x))) ^ xtime(xtime(x)) ^ xtime(x); end
    endfunction

    // AESDEC also adds its raw round key after InvMixColumns.
    assign state_out = (decrypt ? mixed_dec : mixed_enc) ^ key_in;
endmodule
`default_nettype wire
