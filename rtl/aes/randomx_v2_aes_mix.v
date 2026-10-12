// SPDX-License-Identifier: BSD-3-Clause
// Post-VM v2 F/E register mixing. See vendor/randomx/src/vm_interpreted.cpp.
`default_nettype none
module randomx_v2_aes_mix #(
    parameter integer LANES = 1  // Supported values: 1 (shared), 4 (parallel).
) (
    input wire clk,
    input wire rst,               // Synchronous, active high; aborts in-flight work.
    input wire req_valid,
    output wire req_ready,
    input wire [511:0] req_f,
    input wire [511:0] req_e,
    output wire rsp_valid,
    input wire rsp_ready,
    output wire [511:0] rsp_f
);
    reg [511:0] f_q;
    reg [511:0] e_q;
    reg [1:0] key_idx_q;
    reg [1:0] lane_idx_q;
    reg busy_q;
    reg valid_q;
    wire [127:0] key = e_q[128*key_idx_q +: 128];
    wire [511:0] parallel_result;
    wire [127:0] serial_result;

    // Allows a new request on the response-consumption edge. No request queue.
    assign req_ready = !rst && !busy_q && (!valid_q || rsp_ready);
    assign rsp_valid = !rst && valid_q;
    assign rsp_f = f_q;

    genvar lane;
    generate
        if (LANES == 4) begin: parallel
            for (lane = 0; lane < 4; lane = lane + 1) begin: rounds
                randomx_aes_round unit (
                    .state_in(f_q[128*lane +: 128]), .key_in(key),
                    .decrypt((lane%2) == 1),
                    .state_out(parallel_result[128*lane +: 128])
                );
            end
        end else if (LANES == 1) begin: serial
            randomx_aes_round unit (
                .state_in(f_q[128*lane_idx_q +: 128]), .key_in(key),
                .decrypt(lane_idx_q[0]), .state_out(serial_result)
            );
        end else begin: invalid_configuration
            // Deliberately unresolved: reject invalid parameters in synthesis too.
            randomx_v2_aes_mix_requires_LANES_1_or_4 invalid ();
        end
    endgenerate

    always @(posedge clk) begin
        if (rst) begin
            f_q <= 512'b0;
            e_q <= 512'b0;
            key_idx_q <= 2'b0;
            lane_idx_q <= 2'b0;
            busy_q <= 1'b0;
            valid_q <= 1'b0;
        end else begin
            if (valid_q && rsp_ready) valid_q <= 1'b0;
            if (req_valid && req_ready) begin
                f_q <= req_f;
                e_q <= req_e;
                key_idx_q <= 2'b0;
                lane_idx_q <= 2'b0;
                busy_q <= 1'b1;
                valid_q <= 1'b0;
            end else if (busy_q) begin
                if (LANES == 4) begin
                    f_q <= parallel_result;
                    if (key_idx_q == 2'd3) begin
                        busy_q <= 1'b0;
                        valid_q <= 1'b1;
                    end else key_idx_q <= key_idx_q + 1'b1;
                end else begin
                    f_q[128*lane_idx_q +: 128] <= serial_result;
                    if (lane_idx_q == 2'd3) begin
                        lane_idx_q <= 2'b0;
                        if (key_idx_q == 2'd3) begin
                            busy_q <= 1'b0;
                            valid_q <= 1'b1;
                        end else key_idx_q <= key_idx_q + 1'b1;
                    end else lane_idx_q <= lane_idx_q + 1'b1;
                end
            end
        end
    end
endmodule
`default_nettype wire
