// SPDX-License-Identifier: BSD-3-Clause
// VM completion to F-register writeback boundary. v1 bypasses the v2-only stage.
`default_nettype none
module randomx_exec_aes_commit #(
    parameter integer LANES=1
) (
    input wire clk,
    input wire rst,
    input wire vm_valid,
    output wire vm_ready,
    input wire vm_v2,
    input wire [511:0] vm_f,
    input wire [511:0] vm_e,
    output wire wb_valid,
    input wire wb_ready,
    output wire [511:0] wb_f
);
    localparam [1:0] IDLE=2'd0, V1=2'd1, V2=2'd2;
    reg [1:0] state_q;
    reg [511:0] bypass_q;
    wire mix_ready,mix_valid;
    wire [511:0] mix_f;
    wire advance = (state_q==IDLE) || (wb_valid && wb_ready);
    assign vm_ready = !rst && advance && (!vm_v2 || mix_ready);
    assign wb_valid = !rst && ((state_q==V1) || ((state_q==V2) && mix_valid));
    assign wb_f = state_q==V1 ? bypass_q : mix_f;
    randomx_v2_aes_mix #(.LANES(LANES)) mixer (
        .clk(clk),.rst(rst),.req_valid(vm_valid && vm_v2 && advance),
        .req_ready(mix_ready),.req_f(vm_f),.req_e(vm_e),
        .rsp_valid(mix_valid),.rsp_ready(state_q==V2 && wb_ready),.rsp_f(mix_f)
    );
    always @(posedge clk) begin
        if(rst) begin state_q<=IDLE;bypass_q<=512'b0;end
        else if(vm_valid && vm_ready) begin
            state_q<=vm_v2 ? V2 : V1;
            if(!vm_v2) bypass_q<=vm_f;
        end else if(wb_valid && wb_ready) state_q<=IDLE;
    end
endmodule
`default_nettype wire
