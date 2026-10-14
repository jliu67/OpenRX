// SPDX-License-Identifier: BSD-3-Clause
// Bind a prepared fetch packet to the exact captured program and instruction.
`default_nettype none
module randomx_prepared_rcp_guard(
    input wire [15:0] expected_epoch,packet_epoch,
    input wire [8:0] expected_pc,packet_pc,
    input wire [63:0] instruction,packet_value,
    input wire packet_error,packet_rcp_valid,packet_nop,
    input wire [31:0] packet_divisor,
    output wire valid,output wire [63:0] value
);
`include "randomx_opcode_ceils.vh"
    wire is_rcp=instruction[7:0]>=CEIL_ISMULH_M&&instruction[7:0]<CEIL_IMUL_RCP;
    wire [31:0] divisor=instruction[63:32];
    wire nop=divisor==0||(divisor&(divisor-32'd1))==0;
    assign valid=!packet_error&&expected_epoch==packet_epoch&&expected_pc==packet_pc&&
        packet_rcp_valid==is_rcp&&
        (is_rcp?(packet_divisor==divisor&&packet_nop==nop&&(!nop||packet_value==0)):
                (packet_divisor==0&&!packet_nop&&packet_value==0));
    assign value=packet_value;
endmodule
`default_nettype wire
