// SPDX-License-Identifier: BSD-3-Clause
// Two-client, one-credit transport. Payloads remain opaque to this fabric.
// Clients must not reuse a full tag while any packet with that identity remains.
`default_nettype none
module randomx_dataset_shared_channel #(
    parameter integer TAG_WIDTH=64,
    parameter integer REQ_WIDTH=28,
    parameter integer RSP_WIDTH=190
)(
    input wire clk,rst,
    input wire [1:0] client_cancel,
    input wire [1:0] client_req_valid,
    output wire [1:0] client_req_ready,
    input wire [2*TAG_WIDTH-1:0] client_req_tag,
    input wire [2*REQ_WIDTH-1:0] client_req_payload,
    output reg [1:0] client_rsp_valid,
    input wire [1:0] client_rsp_ready,
    output reg [2*TAG_WIDTH-1:0] client_rsp_tag,
    output reg [2*RSP_WIDTH-1:0] client_rsp_payload,
    output wire backend_req_valid,
    input wire backend_req_ready,
    output wire [TAG_WIDTH:0] backend_req_tag,
    output wire [REQ_WIDTH-1:0] backend_req_payload,
    input wire backend_rsp_valid,
    output wire backend_rsp_ready,
    input wire [TAG_WIDTH:0] backend_rsp_tag,
    input wire [RSP_WIDTH-1:0] backend_rsp_payload,
    output wire busy,issued,owner,owner_cancelled,
    output wire [127:0] accepted_count,delivered_count,arbitration_wait_cycles,
    output wire [63:0] backend_request_count,backend_response_count,
    output wire [63:0] cancelled_response_count,orphan_response_count,occupied_cycles
);
    generate if(TAG_WIDTH<1||REQ_WIDTH<1||RSP_WIDTH<1)begin: invalid_width
        dataset_shared_channel_requires_positive_widths invalid();
    end endgenerate

    reg busy_q,issued_q,owner_q,cancelled_q,next_owner_q;
    reg [TAG_WIDTH-1:0] tag_q;
    reg [REQ_WIDTH-1:0] payload_q;
    reg [127:0] accepted_q,delivered_q,wait_q;
    reg [63:0] backend_requests_q,backend_responses_q;
    reg [63:0] cancelled_responses_q,orphan_responses_q,occupied_q;
    integer i;

    wire active=!rst;
    wire [1:0] offered=client_req_valid&~client_cancel;
    wire grant_valid=|offered;
    wire grant_owner=offered[1]&&(!offered[0]||next_owner_q);
    wire capture=active&&!busy_q&&grant_valid;
    // No new capture on a return edge: one credit includes the full held reply.
    assign client_req_ready=(!active||busy_q||!grant_valid)?2'b00:
        (grant_owner?2'b10:2'b01);
    assign backend_req_valid=active&&busy_q&&!issued_q;
    assign backend_req_tag={owner_q,tag_q};
    assign backend_req_payload=payload_q;
    wire request_fire=backend_req_valid&&backend_req_ready;
    wire matching=busy_q&&backend_rsp_tag=={owner_q,tag_q};
    wire response_permitted=issued_q||request_fire;
    wire cancelled_now=cancelled_q||(busy_q&&client_cancel[owner_q]);
    // Matching early packets are held until the request is actually accepted.
    // Orphans can drain while idle, queued, issued or holding a different reply.
    assign backend_rsp_ready=active&&(!matching||
        (response_permitted&&(cancelled_now||client_rsp_ready[owner_q])));
    wire response_fire=backend_rsp_valid&&backend_rsp_ready;
    wire matching_fire=response_fire&&matching&&response_permitted;

    always @* begin
        client_rsp_valid=2'b00;
        client_rsp_tag={2*TAG_WIDTH{1'b0}};
        client_rsp_payload={2*RSP_WIDTH{1'b0}};
        if(active&&backend_rsp_valid&&matching&&response_permitted&&!cancelled_now)begin
            client_rsp_valid[owner_q]=1'b1;
            client_rsp_tag[owner_q*TAG_WIDTH+:TAG_WIDTH]=backend_rsp_tag[TAG_WIDTH-1:0];
            client_rsp_payload[owner_q*RSP_WIDTH+:RSP_WIDTH]=backend_rsp_payload;
        end
    end

    assign busy=busy_q;
    assign issued=issued_q;
    assign owner=owner_q;
    assign owner_cancelled=busy_q&&cancelled_now;
    assign accepted_count=accepted_q;
    assign delivered_count=delivered_q;
    assign arbitration_wait_cycles=wait_q;
    assign backend_request_count=backend_requests_q;
    assign backend_response_count=backend_responses_q;
    assign cancelled_response_count=cancelled_responses_q;
    assign orphan_response_count=orphan_responses_q;
    assign occupied_cycles=occupied_q;

    // External rst is only valid after genuine client/fabric/provider quiescence
    // and removal of all pre-reset packets. Cancel never resets diagnostics or
    // changes the captured identity. The accepted client owns namespace burn.
    always @(posedge clk)begin
        if(rst)begin
            busy_q<=1'b0;issued_q<=1'b0;owner_q<=1'b0;cancelled_q<=1'b0;
            next_owner_q<=1'b0;tag_q<={TAG_WIDTH{1'b0}};payload_q<={REQ_WIDTH{1'b0}};
            accepted_q<=128'b0;delivered_q<=128'b0;wait_q<=128'b0;
            backend_requests_q<=64'b0;backend_responses_q<=64'b0;
            cancelled_responses_q<=64'b0;orphan_responses_q<=64'b0;occupied_q<=64'b0;
        end else begin
            for(i=0;i<2;i=i+1)begin
                if(offered[i]&&!client_req_ready[i])
                    wait_q[i*64+:64]<=wait_q[i*64+:64]+64'd1;
            end
            if(busy_q)occupied_q<=occupied_q+64'd1;
            if(capture)begin
                busy_q<=1'b1;issued_q<=1'b0;owner_q<=grant_owner;cancelled_q<=1'b0;
                tag_q<=client_req_tag[grant_owner*TAG_WIDTH+:TAG_WIDTH];
                payload_q<=client_req_payload[grant_owner*REQ_WIDTH+:REQ_WIDTH];
                next_owner_q<=!grant_owner;
                accepted_q[grant_owner*64+:64]<=accepted_q[grant_owner*64+:64]+64'd1;
            end
            if(busy_q&&client_cancel[owner_q])cancelled_q<=1'b1;
            if(request_fire)begin
                issued_q<=1'b1;
                backend_requests_q<=backend_requests_q+64'd1;
            end
            if(response_fire)begin
                backend_responses_q<=backend_responses_q+64'd1;
                if(!matching)orphan_responses_q<=orphan_responses_q+64'd1;
            end
            if(matching_fire)begin
                if(cancelled_now)cancelled_responses_q<=cancelled_responses_q+64'd1;
                else delivered_q[owner_q*64+:64]<=delivered_q[owner_q*64+:64]+64'd1;
                busy_q<=1'b0;issued_q<=1'b0;cancelled_q<=1'b0;
            end
        end
    end
endmodule
`default_nettype wire
