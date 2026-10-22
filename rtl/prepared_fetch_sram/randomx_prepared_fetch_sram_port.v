// SPDX-License-Identifier: BSD-3-Clause
// One-credit adapter for an admitted immutable prepared-fetch image.
// The row port below is an interface contract, not a physical SRAM macro.
`default_nettype none
module randomx_prepared_fetch_sram_port (
    input wire clk, rst,
    input wire image_sealed,
    input wire [79:0] program_counts,
    input wire req_valid,
    output wire req_ready,
    input wire [64:0] req_tag,
    input wire [27:0] req_payload,
    output wire rsp_valid,
    input wire rsp_ready,
    output wire [64:0] rsp_tag,
    output wire [189:0] rsp_payload,
    output wire row_read_en,
    output wire [11:0] row_read_address,
    input wire row_read_valid,
    input wire [255:0] row_read_data,
    output wire busy
);
    reg pending_q;
    reg invalid_address_q;
    reg [64:0] tag_q;
    reg [27:0] payload_q;
    wire [2:0] program_number=req_payload[11:9];
    wire [8:0] program_pc=req_payload[8:0];
    wire [9:0] selected_count=program_counts[program_number*10+:10];
    wire invalid_address=(selected_count>10'd512)||
                         ({1'b0,program_pc}>=selected_count);
    assign req_ready=!rst&&image_sealed&&!pending_q;
    wire request_fire=req_valid&&req_ready;

    // Address and enable are sampled by a synchronous read port on this edge.
    // That port must register data and keep it stable until the next read.
    assign row_read_en=request_fire&&!invalid_address;
    assign row_read_address=req_payload[11:0];
    assign rsp_valid=!rst&&pending_q&&(invalid_address_q||row_read_valid);
    assign rsp_tag=tag_q;
    wire bad_reserved_bits=(row_read_data[255:161]!=95'b0);
    wire response_error=invalid_address_q||bad_reserved_bits;
    // An invalid address does not read memory or execute a padding row.
    // The complete epoch/program/PC echo and owner/full tag are captured.
    assign rsp_payload={payload_q,response_error,
                        (response_error?161'b0:row_read_data[160:0])};
    assign busy=pending_q;

    // rst is legal only after channel, client and provider quiescence.
    // Neither cancellation nor rst modifies the external frozen row image.
    // Cancellation is drained by the unchanged shared channel, not by this port.
    always @(posedge clk) begin
        if(rst) begin
            pending_q<=1'b0;
            invalid_address_q<=1'b0;
            tag_q<=65'b0;
            payload_q<=28'b0;
        end else begin
            if(request_fire) begin
                pending_q<=1'b1;
                invalid_address_q<=invalid_address;
                tag_q<=req_tag;
                payload_q<=req_payload;
            end
            if(rsp_valid&&rsp_ready) pending_q<=1'b0;
        end
    end
endmodule
`default_nettype wire
