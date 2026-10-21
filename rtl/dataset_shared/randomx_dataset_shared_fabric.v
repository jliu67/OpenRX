// SPDX-License-Identifier: BSD-3-Clause
// Independent finite instruction/cache channels for a bounded two-client trial.
`default_nettype none
module randomx_dataset_shared_fabric(
    input wire clk,rst,
    input wire [1:0] client_cancel,

    input wire [1:0] fetch_client_req_valid,
    output wire [1:0] fetch_client_req_ready,
    input wire [127:0] fetch_client_req_tag,
    input wire [55:0] fetch_client_req_payload,
    output wire [1:0] fetch_client_rsp_valid,
    input wire [1:0] fetch_client_rsp_ready,
    output wire [127:0] fetch_client_rsp_tag,
    output wire [379:0] fetch_client_rsp_payload,
    output wire fetch_backend_req_valid,
    input wire fetch_backend_req_ready,
    output wire [64:0] fetch_backend_req_tag,
    output wire [27:0] fetch_backend_req_payload,
    input wire fetch_backend_rsp_valid,
    output wire fetch_backend_rsp_ready,
    input wire [64:0] fetch_backend_rsp_tag,
    input wire [189:0] fetch_backend_rsp_payload,
    output wire fetch_busy,fetch_issued,fetch_owner,fetch_owner_cancelled,
    output wire [127:0] fetch_accepted_count,fetch_delivered_count,fetch_arbitration_wait_cycles,
    output wire [63:0] fetch_backend_request_count,fetch_backend_response_count,
    output wire [63:0] fetch_cancelled_response_count,fetch_orphan_response_count,fetch_occupied_cycles,

    input wire [1:0] cache_client_req_valid,
    output wire [1:0] cache_client_req_ready,
    input wire [127:0] cache_client_req_tag,
    input wire [81:0] cache_client_req_payload,
    output wire [1:0] cache_client_rsp_valid,
    input wire [1:0] cache_client_rsp_ready,
    output wire [127:0] cache_client_rsp_tag,
    output wire [1107:0] cache_client_rsp_payload,
    output wire cache_backend_req_valid,
    input wire cache_backend_req_ready,
    output wire [64:0] cache_backend_req_tag,
    output wire [40:0] cache_backend_req_payload,
    input wire cache_backend_rsp_valid,
    output wire cache_backend_rsp_ready,
    input wire [64:0] cache_backend_rsp_tag,
    input wire [553:0] cache_backend_rsp_payload,
    output wire cache_busy,cache_issued,cache_owner,cache_owner_cancelled,
    output wire [127:0] cache_accepted_count,cache_delivered_count,cache_arbitration_wait_cycles,
    output wire [63:0] cache_backend_request_count,cache_backend_response_count,
    output wire [63:0] cache_cancelled_response_count,cache_orphan_response_count,cache_occupied_cycles,
    output wire quiescent
);
    randomx_dataset_shared_channel #(.TAG_WIDTH(64),.REQ_WIDTH(28),.RSP_WIDTH(190)) fetch(
        .clk(clk),.rst(rst),.client_cancel(client_cancel),
        .client_req_valid(fetch_client_req_valid),.client_req_ready(fetch_client_req_ready),
        .client_req_tag(fetch_client_req_tag),.client_req_payload(fetch_client_req_payload),
        .client_rsp_valid(fetch_client_rsp_valid),.client_rsp_ready(fetch_client_rsp_ready),
        .client_rsp_tag(fetch_client_rsp_tag),.client_rsp_payload(fetch_client_rsp_payload),
        .backend_req_valid(fetch_backend_req_valid),.backend_req_ready(fetch_backend_req_ready),
        .backend_req_tag(fetch_backend_req_tag),.backend_req_payload(fetch_backend_req_payload),
        .backend_rsp_valid(fetch_backend_rsp_valid),.backend_rsp_ready(fetch_backend_rsp_ready),
        .backend_rsp_tag(fetch_backend_rsp_tag),.backend_rsp_payload(fetch_backend_rsp_payload),
        .busy(fetch_busy),.issued(fetch_issued),.owner(fetch_owner),.owner_cancelled(fetch_owner_cancelled),
        .accepted_count(fetch_accepted_count),.delivered_count(fetch_delivered_count),
        .arbitration_wait_cycles(fetch_arbitration_wait_cycles),
        .backend_request_count(fetch_backend_request_count),.backend_response_count(fetch_backend_response_count),
        .cancelled_response_count(fetch_cancelled_response_count),.orphan_response_count(fetch_orphan_response_count),
        .occupied_cycles(fetch_occupied_cycles)
    );
    randomx_dataset_shared_channel #(.TAG_WIDTH(64),.REQ_WIDTH(41),.RSP_WIDTH(554)) cache(
        .clk(clk),.rst(rst),.client_cancel(client_cancel),
        .client_req_valid(cache_client_req_valid),.client_req_ready(cache_client_req_ready),
        .client_req_tag(cache_client_req_tag),.client_req_payload(cache_client_req_payload),
        .client_rsp_valid(cache_client_rsp_valid),.client_rsp_ready(cache_client_rsp_ready),
        .client_rsp_tag(cache_client_rsp_tag),.client_rsp_payload(cache_client_rsp_payload),
        .backend_req_valid(cache_backend_req_valid),.backend_req_ready(cache_backend_req_ready),
        .backend_req_tag(cache_backend_req_tag),.backend_req_payload(cache_backend_req_payload),
        .backend_rsp_valid(cache_backend_rsp_valid),.backend_rsp_ready(cache_backend_rsp_ready),
        .backend_rsp_tag(cache_backend_rsp_tag),.backend_rsp_payload(cache_backend_rsp_payload),
        .busy(cache_busy),.issued(cache_issued),.owner(cache_owner),.owner_cancelled(cache_owner_cancelled),
        .accepted_count(cache_accepted_count),.delivered_count(cache_delivered_count),
        .arbitration_wait_cycles(cache_arbitration_wait_cycles),
        .backend_request_count(cache_backend_request_count),.backend_response_count(cache_backend_response_count),
        .cancelled_response_count(cache_cancelled_response_count),.orphan_response_count(cache_orphan_response_count),
        .occupied_cycles(cache_occupied_cycles)
    );
    // This excludes only fabric-owned credits. Client and provider quiescence,
    // including absence of every old packet, remains an external reset gate.
    assign quiescent=!fetch_busy&&!cache_busy;
endmodule
`default_nettype wire
