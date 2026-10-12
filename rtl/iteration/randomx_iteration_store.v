// SPDX-License-Identifier: BSD-3-Clause
// Post-dataset iteration tail: ordered R then F stores, plus architectural F.
`default_nettype none
module randomx_iteration_store #(
    parameter integer LANES=1,
    parameter integer OVERLAP_R=1
) (
    input wire clk,
    input wire rst,
    input wire req_valid,
    output wire req_ready,
    input wire req_v2,
    input wire [511:0] req_r,
    input wire [511:0] req_f,
    input wire [511:0] req_e,
    input wire [14:0] req_f_line, // spAddr0[20:6], 64-byte aligned in 2MiB.
    input wire [14:0] req_r_line, // spAddr1[20:6].
    output wire wr_valid,
    input wire wr_ready,         // Acceptance commits an ordered SRAM write.
    output wire [20:0] wr_addr,
    output wire [127:0] wr_data,
    output wire [15:0] wr_strb,
    output wire done_valid,
    input wire done_ready,
    output wire [511:0] done_f,
    output wire [31:0] done_spaddr0,
    output wire [31:0] done_spaddr1
);
    localparam [1:0] IDLE=0, R_STORE=1, F_STORE=2, DONE=3;
    reg [1:0] phase_q;
    reg [1:0] beat_q;
    reg [511:0] r_q;
    reg [511:0] final_f_q;
    reg [14:0] f_line_q,r_line_q;
    wire core_ready,core_valid;
    wire [511:0] core_f;
    wire accept = req_valid && req_ready;
    assign req_ready = !rst && core_ready &&
                       (phase_q==IDLE || (phase_q==DONE && done_ready));
    assign wr_valid = !rst && ((phase_q==R_STORE && (OVERLAP_R!=0 || core_valid)) ||
                              (phase_q==F_STORE && core_valid));
    assign wr_addr = {phase_q==R_STORE ? r_line_q : f_line_q,beat_q,4'b0};
    // R pairs preserve little-endian store64 order; F uses full 128-bit lanes.
    assign wr_data = phase_q==R_STORE ? r_q[128*beat_q +: 128] :
                                      core_f[128*beat_q +: 128];
    assign wr_strb = 16'hffff;
    assign done_valid = !rst && phase_q==DONE;
    assign done_f = final_f_q;
    assign done_spaddr0 = 32'b0; // Pinned interpreter clears both cursors.
    assign done_spaddr1 = 32'b0;
    randomx_exec_aes_commit #(.LANES(LANES)) core (
        .clk(clk),.rst(rst),.vm_valid(accept),.vm_ready(core_ready),
        .vm_v2(req_v2),.vm_f(req_f),.vm_e(req_e),
        .wb_valid(core_valid),
        .wb_ready(phase_q==F_STORE && beat_q==3 && wr_ready && !rst),
        .wb_f(core_f)
    );
    generate
        if(OVERLAP_R!=0 && OVERLAP_R!=1) begin: invalid_overlap
            randomx_iteration_store_requires_OVERLAP_R_0_or_1 invalid ();
        end
    endgenerate
    always @(posedge clk) begin
        if(rst) begin
            phase_q<=IDLE;beat_q<=0;r_q<=0;final_f_q<=0;
            f_line_q<=0;r_line_q<=0;
        end else if(accept) begin
            phase_q<=R_STORE;beat_q<=0;r_q<=req_r;
            f_line_q<=req_f_line;r_line_q<=req_r_line;
        end else if(wr_valid && wr_ready) begin
            if(beat_q==3) begin
                beat_q<=0;
                if(phase_q==R_STORE) phase_q<=F_STORE;
                else begin phase_q<=DONE;final_f_q<=core_f;end
            end else beat_q<=beat_q+1'b1;
        end else if(done_valid && done_ready) phase_q<=IDLE;
    end
endmodule
`default_nettype wire
