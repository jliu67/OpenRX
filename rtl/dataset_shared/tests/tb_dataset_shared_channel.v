// SPDX-License-Identifier: BSD-3-Clause
// Directed transport checks only. Native item/session checks are separate.
// No reset is applied with live client/fabric/provider traffic.
`timescale 1ns/1ps
`default_nettype none
module tb_dataset_shared_channel;
    localparam integer TAG_WIDTH=64, REQ_WIDTH=28, RSP_WIDTH=190;
    reg clk=0;
    always #5 clk=~clk;
    reg rst=1;
    reg [1:0] client_cancel=0,client_req_valid=0,client_rsp_ready=0;
    wire [1:0] client_req_ready,client_rsp_valid;
    reg [127:0] client_req_tag=0;
    reg [55:0] client_req_payload=0;
    wire [127:0] client_rsp_tag;
    wire [379:0] client_rsp_payload;
    wire backend_req_valid,backend_rsp_ready;
    reg backend_req_ready=0,backend_rsp_valid=0;
    wire [64:0] backend_req_tag;
    wire [27:0] backend_req_payload;
    reg [64:0] backend_rsp_tag=0;
    reg [189:0] backend_rsp_payload=0;
    wire busy,issued,owner,owner_cancelled;
    wire [127:0] accepted_count,delivered_count,arbitration_wait_cycles;
    wire [63:0] backend_request_count,backend_response_count;
    wire [63:0] cancelled_response_count,orphan_response_count,occupied_cycles;

`ifdef SHARED_CHANNEL_NETLIST
    randomx_dataset_shared_channel dut(
`else
    randomx_dataset_shared_channel #(.TAG_WIDTH(TAG_WIDTH),
        .REQ_WIDTH(REQ_WIDTH),.RSP_WIDTH(RSP_WIDTH)) dut(
`endif
        .clk(clk),.rst(rst),.client_cancel(client_cancel),
        .client_req_valid(client_req_valid),.client_req_ready(client_req_ready),
        .client_req_tag(client_req_tag),.client_req_payload(client_req_payload),
        .client_rsp_valid(client_rsp_valid),.client_rsp_ready(client_rsp_ready),
        .client_rsp_tag(client_rsp_tag),.client_rsp_payload(client_rsp_payload),
        .backend_req_valid(backend_req_valid),.backend_req_ready(backend_req_ready),
        .backend_req_tag(backend_req_tag),.backend_req_payload(backend_req_payload),
        .backend_rsp_valid(backend_rsp_valid),.backend_rsp_ready(backend_rsp_ready),
        .backend_rsp_tag(backend_rsp_tag),.backend_rsp_payload(backend_rsp_payload),
        .busy(busy),.issued(issued),.owner(owner),.owner_cancelled(owner_cancelled),
        .accepted_count(accepted_count),.delivered_count(delivered_count),
        .arbitration_wait_cycles(arbitration_wait_cycles),
        .backend_request_count(backend_request_count),
        .backend_response_count(backend_response_count),
        .cancelled_response_count(cancelled_response_count),
        .orphan_response_count(orphan_response_count),.occupied_cycles(occupied_cycles)
    );

    integer checks=0,cycles=0,counter_closure_checks=0;
    integer fairness_pairs=0,identical_tag_pairs=0;
    integer descriptor_hold_cycles=0,response_hold_cycles=0;
    integer early_reply_hold_cycles=0,same_edge_request_response_cases=0;
    integer queued_cancel_cases=0,issued_cancel_cases=0,held_cancel_cases=0;
    integer foreign_owner_packets=0,wrong_low_tag_packets=0,idle_orphan_packets=0;
    integer malformed_payload_forwarded=0,other_client_progress_cases=0;
    integer nonowner_cancel_cases=0,quiescent_reset_cases=0;
    integer high_water_mark=0;

    reg sb_busy=0,sb_issued=0,sb_owner=0,sb_cancelled=0;
    reg [63:0] sb_tag=0;
    reg [27:0] sb_payload=0;
    reg [63:0] sb_accepted[0:1],sb_delivered[0:1],sb_wait[0:1];
    reg [63:0] sb_requests=0,sb_responses=0,sb_cancelled_responses=0;
    reg [63:0] sb_orphans=0,sb_occupied=0;
    reg req_was_held=0,provider_rsp_was_held=0;
    reg [1:0] client_rsp_was_held=0;
    reg [64:0] held_req_tag=0,held_provider_rsp_tag=0;
    reg [27:0] held_req_payload=0;
    reg [189:0] held_provider_rsp_payload=0;
    reg [127:0] held_client_rsp_tag=0;
    reg [379:0] held_client_rsp_payload=0;
    reg req_fire,rsp_fire,matching,eligible,cancel_now;
    reg [1:0] expected_valid;
    integer i,accepted_this_edge;

    reg [63:0] final_accepted[0:1],final_delivered[0:1],final_wait[0:1];
    reg [63:0] final_requests,final_responses,final_cancelled,final_orphans,final_occupied;
    string output_path;
    integer output_fd,grant_index,grant_owner;
    reg [63:0] transaction_tag;
    reg [189:0] value0,value1;

    task check;
        input condition;
        input [8*180-1:0] message;
    begin
        checks=checks+1;
        if(condition!==1'b1)$fatal(1,"shared-channel check failed cycle=%0d: %0s",cycles,message);
    end endtask

    // Calls return on a negative edge. Only negative-edge code drives inputs.
    task clock_step;
    begin
        @(posedge clk); #1;
        @(negedge clk);
    end endtask

    task wait_capture;
        input integer who;
        integer attempts;
        reg completed;
    begin
        completed=0;
        for(attempts=0;attempts<16;attempts=attempts+1)begin
            if(!completed)begin
                #1;
                if(client_req_valid[who]&&client_req_ready[who])begin
                    clock_step;
                    client_req_valid[who]=0;
                    completed=1;
                end else clock_step;
            end
        end
        check(completed,"bounded frontend request capture");
        #1;
        check(busy&&owner==who,"captured descriptor has correct owner");
    end endtask

    task start_single;
        input integer who;
        input [63:0] tag;
        input [27:0] payload;
    begin
        #1;
        check(!busy&&client_req_valid==0&&!backend_rsp_valid,"start from an empty credit");
        client_req_tag[who*64+:64]=tag;
        client_req_payload[who*28+:28]=payload;
        client_req_valid[who]=1;
        wait_capture(who);
    end endtask

    task issue_request;
    begin
        #1;
        check(busy&&!issued&&backend_req_valid,"captured request waits for backend acceptance");
        backend_req_ready=1;
        #1;
        check(backend_req_valid,"backend request valid before handshake");
        clock_step;
        backend_req_ready=0;
        #1;
        check(busy&&issued&&!backend_req_valid,"accepted request owns credit while awaiting response");
    end endtask

    task normal_response;
        input integer who;
        input [63:0] tag;
        input [189:0] payload;
        input integer hold_clocks;
        integer k;
    begin
        backend_rsp_tag={who[0],tag};
        backend_rsp_payload=payload;
        backend_rsp_valid=1;
        client_rsp_ready[who]=0;
        for(k=0;k<hold_clocks;k=k+1)begin
            #1;
            check(client_rsp_valid==(who==0?2'b01:2'b10),"held reply reaches only its owner");
            check(client_rsp_tag[who*64+:64]===tag,"held reply retains full original tag");
            check(client_rsp_payload[who*190+:190]===payload,"held reply preserves opaque payload");
            check(!backend_rsp_ready&&busy,"held reply consumes the only credit");
            response_hold_cycles=response_hold_cycles+1;
            clock_step;
        end
        client_rsp_ready[who]=1;
        #1;
        check(client_rsp_valid==(who==0?2'b01:2'b10)&&backend_rsp_ready,
              "ready owner consumes matching response");
        check(client_rsp_payload[who*190+:190]===payload,"all matching response bits are transparent");
        clock_step;
        backend_rsp_valid=0;
        client_rsp_ready[who]=0;
        #1;
        check(!busy,"matching consumed response returns credit");
    end endtask

    task orphan_packet;
        input [64:0] tag;
        input [189:0] payload;
        input expected_busy;
    begin
        backend_rsp_tag=tag;backend_rsp_payload=payload;backend_rsp_valid=1;
        #1;
        check(client_rsp_valid==0&&backend_rsp_ready,"foreign full identity drains without client delivery");
        clock_step;
        backend_rsp_valid=0;
        #1;
        check(busy===expected_busy,"orphan drain does not release another owner's credit");
    end endtask

    // Independent edge scoreboard; no DUT internal state is inspected.
    always @(posedge clk)begin
        cycles=cycles+1;
        if(cycles>4000)$fatal(1,"shared-channel watchdog");
        if(rst)begin
            sb_busy=0;sb_issued=0;sb_owner=0;sb_cancelled=0;
            sb_tag=0;sb_payload=0;
            sb_requests=0;sb_responses=0;sb_cancelled_responses=0;
            sb_orphans=0;sb_occupied=0;
            for(i=0;i<2;i=i+1)begin sb_accepted[i]=0;sb_delivered[i]=0;sb_wait[i]=0;end
            req_was_held=0;provider_rsp_was_held=0;client_rsp_was_held=0;
        end else begin
            if(req_was_held)begin
                check(backend_req_valid,"captured backend request cannot vanish under hold/cancel");
                check(backend_req_tag===held_req_tag&&backend_req_payload===held_req_payload,
                      "captured backend descriptor remains stable under hold/cancel");
            end
            if(provider_rsp_was_held)begin
                check(backend_rsp_valid&&backend_rsp_tag===held_provider_rsp_tag&&
                    backend_rsp_payload===held_provider_rsp_payload,"bench provider obeys held-response contract");
            end
            for(i=0;i<2;i=i+1)begin
                if(client_rsp_was_held[i]&&!client_cancel[i])begin
                    check(client_rsp_valid[i]&&client_rsp_tag[i*64+:64]===held_client_rsp_tag[i*64+:64]&&
                        client_rsp_payload[i*190+:190]===held_client_rsp_payload[i*190+:190],
                        "client response remains stable until consumption or explicit cancellation");
                end
                if(client_req_valid[i]&&!client_req_ready[i]&&!client_cancel[i])sb_wait[i]=sb_wait[i]+1;
                check(!(client_req_valid[i]&&client_req_ready[i]&&client_cancel[i]),
                      "cancelled client cannot admit a new descriptor");
            end
            req_fire=backend_req_valid&&backend_req_ready;
            rsp_fire=backend_rsp_valid&&backend_rsp_ready;
            matching=sb_busy&&backend_rsp_tag=={sb_owner,sb_tag};
            eligible=sb_issued||req_fire;
            cancel_now=sb_cancelled||(sb_busy&&client_cancel[sb_owner]);
            expected_valid=0;
            if(sb_busy&&eligible&&matching&&backend_rsp_valid&&!cancel_now)
                expected_valid[sb_owner]=1;
            check(client_rsp_valid===expected_valid,"response valid is owned, accepted and uncancelled");
            if(expected_valid!=0)begin
                check(client_rsp_tag[sb_owner*64+:64]===sb_tag,"response restores owner's original full tag");
                check(client_rsp_payload[sb_owner*190+:190]===backend_rsp_payload,
                      "matching metadata and data are forwarded without interpretation");
                check(backend_rsp_ready===client_rsp_ready[sb_owner],"response backpressure reaches provider");
            end
            if(sb_busy)begin
                sb_occupied=sb_occupied+1;
                high_water_mark=1;
                if(client_cancel[sb_owner])sb_cancelled=1;
                if(!sb_issued)begin
                    check(backend_req_valid,"queued credit exposes a backend request");
                    check(backend_req_tag==={sb_owner,sb_tag}&&backend_req_payload===sb_payload,
                          "backend request uses captured owner, full tag and payload");
                end
            end
            if(req_fire)begin
                check(sb_busy&&!sb_issued,"no unsolicited or duplicate backend request");
                sb_issued=1;sb_requests=sb_requests+1;
            end
            if(rsp_fire)begin
                sb_responses=sb_responses+1;
                if(req_fire&&matching)same_edge_request_response_cases=same_edge_request_response_cases+1;
                if(matching)begin
                    check(eligible,"matching early response cannot precede backend request acceptance");
                    if(cancel_now)begin
                        check(client_rsp_valid==0,"cancelled reply drains without delivery");
                        sb_cancelled_responses=sb_cancelled_responses+1;
                    end else begin
                        check(client_rsp_valid[sb_owner]&&client_rsp_ready[sb_owner],"matching reply delivered once");
                        sb_delivered[sb_owner]=sb_delivered[sb_owner]+1;
                    end
                    sb_busy=0;sb_issued=0;sb_cancelled=0;
                end else sb_orphans=sb_orphans+1;
            end
            accepted_this_edge=0;
            for(i=0;i<2;i=i+1)begin
                if(client_req_valid[i]&&client_req_ready[i])begin
                    check(!sb_busy&&accepted_this_edge==0,"one-credit channel accepts at most one owner");
                    sb_busy=1;sb_issued=0;sb_cancelled=0;sb_owner=i[0];
                    sb_tag=client_req_tag[i*64+:64];sb_payload=client_req_payload[i*28+:28];
                    sb_accepted[i]=sb_accepted[i]+1;accepted_this_edge=accepted_this_edge+1;
                end
            end
            req_was_held=backend_req_valid&&!backend_req_ready;
            held_req_tag=backend_req_tag;held_req_payload=backend_req_payload;
            provider_rsp_was_held=backend_rsp_valid&&!backend_rsp_ready;
            held_provider_rsp_tag=backend_rsp_tag;held_provider_rsp_payload=backend_rsp_payload;
            client_rsp_was_held=client_rsp_valid&~client_rsp_ready&~client_cancel;
            held_client_rsp_tag=client_rsp_tag;held_client_rsp_payload=client_rsp_payload;
        end
        #1;
        check(busy===sb_busy&&issued===sb_issued,"observable credit/issued state closes independently");
        if(sb_busy)check(owner===sb_owner&&owner_cancelled===sb_cancelled,"retained owner/cancel state closes");
        for(i=0;i<2;i=i+1)begin
            check(accepted_count[i*64+:64]===sb_accepted[i],"frontend request counter closes");
            check(delivered_count[i*64+:64]===sb_delivered[i],"frontend delivery counter closes");
            check(arbitration_wait_cycles[i*64+:64]===sb_wait[i],"arbitration wait counter closes");
        end
        check(backend_request_count===sb_requests,"backend request counter closes");
        check(backend_response_count===sb_responses,"all backend response handshakes counted");
        check(cancelled_response_count===sb_cancelled_responses,"cancelled reply counter closes");
        check(orphan_response_count===sb_orphans,"orphan reply counter closes");
        check(occupied_cycles===sb_occupied,"occupied clocks close without counting capture edge");
        check(backend_response_count===delivered_count[63:0]+delivered_count[127:64]+
              cancelled_response_count+orphan_response_count,"response classes are disjoint and exhaustive");
        counter_closure_checks=counter_closure_checks+1;
    end

    initial begin
        if(!$value$plusargs("output=%s",output_path))$fatal(1,"+output=PATH required");
        sb_accepted[0]=0;sb_accepted[1]=0;sb_delivered[0]=0;sb_delivered[1]=0;sb_wait[0]=0;sb_wait[1]=0;
        value0={16'h1234,3'd2,9'd17,1'b0,1'b1,32'h34,64'h123456789abcdef0,64'h00ff11ee22dd33cc};
        value1={16'habcd,3'd7,9'd511,1'b1,1'b0,32'hffffffff,64'hfedcba9876543210,64'hcc33dd22ee11ff00};
        clock_step;clock_step;rst=0;

        // Both clients deliberately present identical original tags. Their
        // backend tags differ only in the explicit client identity bit.
        client_req_tag={64'h0000000100000100,64'h0000000100000100};
        client_req_payload={28'h7654321,28'h1234567};client_req_valid=2'b11;
        for(grant_index=0;grant_index<16;grant_index=grant_index+1)begin
            grant_owner=grant_index%2;
            transaction_tag=64'h0000000100000100+grant_index/2;
            #1;
            if(grant_owner==0)begin
                check(client_req_valid==2'b11&&client_req_tag[63:0]===transaction_tag&&
                      client_req_tag[127:64]===transaction_tag,"each pair actually offers identical full client tags");
                identical_tag_pairs=identical_tag_pairs+1;
            end
            check(client_req_ready==(grant_owner==0?2'b01:2'b10),
                  "round-robin alternates grants while both contenders are offered");
            wait_capture(grant_owner);
            check(backend_req_tag==={grant_owner[0],transaction_tag},"backend identity retains owner and full client tag");
            issue_request;
            normal_response(grant_owner,transaction_tag,grant_owner==0?value0:value1,grant_index==0?3:0);
            if(grant_owner==1)fairness_pairs=fairness_pairs+1;
            // Reoffer the completed client with a new identity before the
            // waiting contender is selected. A fixed-priority arbiter would
            // fail the next grant. Stop replenishing only to drain the pair.
            if(grant_index<14)begin
                client_req_tag[grant_owner*64+:64]=transaction_tag+64'd1;
                client_req_valid[grant_owner]=1;
            end
        end

        // Captured descriptor must not depend on live frontend wires. Cancel
        // of the other, unaccepted client must not cancel the real owner.
        transaction_tag=64'h0000000200000200;
        start_single(0,transaction_tag,28'h2468ace);
        client_req_tag[63:0]=~transaction_tag;client_req_payload[27:0]=28'hbadbeef;
        client_cancel[1]=1;client_req_valid[1]=1;
        client_req_tag[127:64]=64'h0000000200000201;client_req_payload[55:28]=28'h1112223;
        repeat(3)begin
            #1;
            check(backend_req_tag==={1'b0,transaction_tag}&&backend_req_payload===28'h2468ace,
                  "live frontend mutations cannot rewrite captured request");
            check(!client_req_ready[1]&&!owner_cancelled,"nonowner cancel cannot alter active request");
            descriptor_hold_cycles=descriptor_hold_cycles+1;clock_step;
        end
        issue_request;
        normal_response(0,transaction_tag,value0,0);
        client_req_valid[1]=0;client_cancel[1]=0;nonowner_cancel_cases=nonowner_cancel_cases+1;

        // Matching early response is held. It may transfer on the very same
        // edge that its backend request finally transfers, but never earlier.
        transaction_tag=64'h0000000300000300;
        start_single(1,transaction_tag,28'h13579bd);
        backend_rsp_tag={1'b1,transaction_tag};backend_rsp_payload=value1;
        backend_rsp_valid=1;client_rsp_ready[1]=1;
        repeat(3)begin
            #1;check(!backend_rsp_ready&&client_rsp_valid==0&&!issued,
                "matching early reply held until backend request accepted");
            early_reply_hold_cycles=early_reply_hold_cycles+1;clock_step;
        end
        backend_req_ready=1;
        #1;check(backend_req_valid&&backend_rsp_ready&&client_rsp_valid==2'b10,
                 "same-edge request/reply is enabled only with backend acceptance");
        clock_step;backend_req_ready=0;backend_rsp_valid=0;client_rsp_ready[1]=0;
        #1;check(!busy,"same-edge backend request/reply returns credit once");

        // Wrong client identity with an identical low tag and a stale low tag
        // are both orphans. Matching opaque malformed metadata is forwarded.
        transaction_tag=64'h0000000400000400;
        start_single(0,transaction_tag,28'h456789a);issue_request;
        orphan_packet({1'b1,transaction_tag},value1,1'b1);foreign_owner_packets=foreign_owner_packets+1;
        orphan_packet({1'b0,64'h0000000200000200},value1,1'b1);
        wrong_low_tag_packets=wrong_low_tag_packets+1;
        normal_response(0,transaction_tag,{190{1'b1}},2);
        malformed_payload_forwarded=malformed_payload_forwarded+1;
        orphan_packet({1'b1,64'hdeadbeef},value0,1'b0);idle_orphan_packets=idle_orphan_packets+1;

        // Cancel a queued request: its original backend descriptor survives,
        // and the response drains only after request acceptance.
        transaction_tag=64'h0000000500000500;
        start_single(0,transaction_tag,28'h557799b);
        client_cancel[0]=1;clock_step;client_cancel[0]=0;
        client_req_tag[63:0]=0;client_req_payload[27:0]=0;
        #1;check(owner_cancelled&&busy&&backend_req_valid&&
                 backend_req_tag==={1'b0,transaction_tag}&&backend_req_payload===28'h557799b,
                 "queued cancel retains captured request and credit");
        backend_rsp_tag={1'b0,transaction_tag};backend_rsp_payload=value0;backend_rsp_valid=1;
        #1;check(!backend_rsp_ready&&client_rsp_valid==0,"cancelled early reply cannot precede request acceptance");
        clock_step;
        backend_req_ready=1;
        #1;check(backend_rsp_ready&&client_rsp_valid==0,"cancelled same-edge request/reply drains without delivery");
        clock_step;backend_req_ready=0;backend_rsp_valid=0;
        #1;check(!busy,"queued cancelled owner returns credit only after reply drain");
        queued_cancel_cases=queued_cancel_cases+1;

        // Cancel an already issued owner while the other client waits. A
        // foreign reply cannot release it; its own reply drains, then the
        // other client proceeds with no misrouting or refunded identity.
        transaction_tag=64'h0000000600000600;
        start_single(0,transaction_tag,28'h6600112);issue_request;
        client_cancel[0]=1;clock_step;client_cancel[0]=0;
        client_req_valid[1]=1;client_req_tag[127:64]=64'h0000000600000601;
        client_req_payload[55:28]=28'h6600223;
        orphan_packet({1'b1,transaction_tag},value1,1'b1);foreign_owner_packets=foreign_owner_packets+1;
        backend_rsp_valid=1;backend_rsp_tag={1'b0,transaction_tag};backend_rsp_payload=value0;
        #1;check(backend_rsp_ready&&client_rsp_valid==0&&owner_cancelled,"issued cancelled owner drains independently of client readiness");
        clock_step;backend_rsp_valid=0;
        issued_cancel_cases=issued_cancel_cases+1;
        wait_capture(1);issue_request;
        normal_response(1,64'h0000000600000601,value1,0);
        other_client_progress_cases=other_client_progress_cases+1;

        // Explicit cancel may withdraw a held client response immediately;
        // the still-stable backend packet is consumed as a cancelled drain.
        transaction_tag=64'h0000000700000700;
        start_single(1,transaction_tag,28'h7700334);issue_request;
        backend_rsp_valid=1;backend_rsp_tag={1'b1,transaction_tag};backend_rsp_payload=value1;
        client_rsp_ready[1]=0;
        repeat(2)begin
            #1;check(client_rsp_valid==2'b10&&!backend_rsp_ready,"owned reply is held before cancellation");
            response_hold_cycles=response_hold_cycles+1;clock_step;
        end
        client_cancel[1]=1;
        #1;check(client_rsp_valid==0&&backend_rsp_ready,"cancel immediately suppresses held response and permits drain");
        clock_step;backend_rsp_valid=0;client_cancel[1]=0;
        #1;check(!busy,"held cancelled reply returns credit after drain");
        held_cancel_cases=held_cancel_cases+1;

        // Snapshot completed traffic before a genuine shared quiescent reset.
        // Providers have no pending packet and every client valid is low.
        #1;
        check(!busy&&!issued&&!backend_req_valid&&!backend_rsp_valid&&client_req_valid==0&&
              client_rsp_valid==0&&client_cancel==0,"genuine client/fabric/provider quiescence before hard reset");
        for(i=0;i<2;i=i+1)begin
            final_accepted[i]=accepted_count[i*64+:64];final_delivered[i]=delivered_count[i*64+:64];
            final_wait[i]=arbitration_wait_cycles[i*64+:64];
        end
        final_requests=backend_request_count;final_responses=backend_response_count;
        final_cancelled=cancelled_response_count;final_orphans=orphan_response_count;final_occupied=occupied_cycles;
        check(final_accepted[0]+final_accepted[1]===final_requests,"every accepted descriptor issued exactly once");
        check(final_requests===final_delivered[0]+final_delivered[1]+final_cancelled,
              "every accepted request ended in delivery or cancelled drain");
        check(final_cancelled==3&&final_orphans==4,"directed cancellation/orphan coverage matches observed handshakes");
        check(same_edge_request_response_cases==2,"both intended simultaneous request/reply handshakes were observed");
        check(high_water_mark==1&&final_wait[0]+final_wait[1]>0,"finite credit and actual arbitration wait observed");
        rst=1;clock_step;
        check(accepted_count==0&&delivered_count==0&&arbitration_wait_cycles==0&&
              backend_request_count==0&&backend_response_count==0&&cancelled_response_count==0&&
              orphan_response_count==0&&occupied_cycles==0&&!busy&&!issued,
              "genuinely quiescent hard reset clears channel diagnostics");
        rst=0;clock_step;quiescent_reset_cases=quiescent_reset_cases+1;

        output_fd=$fopen(output_path,"w");
        if(!output_fd)$fatal(1,"cannot open protocol summary %s",output_path);
        $fdisplay(output_fd,"{");
        $fdisplay(output_fd,"  \"schema\": \"openrx.shared-dataset-channel-protocol.v1\",");
        $fdisplay(output_fd,"  \"status\": \"pass\",");
        $fdisplay(output_fd,"  \"checks\": %0d, \"cycles\": %0d, \"counter_closure_checks\": %0d,",checks,cycles,counter_closure_checks);
        $fdisplay(output_fd,"  \"fairness_pairs\": %0d, \"identical_tag_pairs\": %0d,",fairness_pairs,identical_tag_pairs);
        $fdisplay(output_fd,"  \"descriptor_hold_cycles\": %0d, \"response_hold_cycles\": %0d,",descriptor_hold_cycles,response_hold_cycles);
        $fdisplay(output_fd,"  \"early_reply_hold_cycles\": %0d, \"same_edge_request_response_cases\": %0d,",early_reply_hold_cycles,same_edge_request_response_cases);
        $fdisplay(output_fd,"  \"queued_cancel_cases\": %0d, \"issued_cancel_cases\": %0d, \"held_cancel_cases\": %0d,",queued_cancel_cases,issued_cancel_cases,held_cancel_cases);
        $fdisplay(output_fd,"  \"foreign_owner_packets\": %0d, \"wrong_low_tag_packets\": %0d, \"idle_orphan_packets\": %0d,",foreign_owner_packets,wrong_low_tag_packets,idle_orphan_packets);
        $fdisplay(output_fd,"  \"malformed_payload_forwarded\": %0d, \"other_client_progress_cases\": %0d,",malformed_payload_forwarded,other_client_progress_cases);
        $fdisplay(output_fd,"  \"nonowner_cancel_cases\": %0d, \"quiescent_reset_cases\": %0d,",nonowner_cancel_cases,quiescent_reset_cases);
        $fdisplay(output_fd,"  \"accepted_count\": [%0d, %0d],",final_accepted[0],final_accepted[1]);
        $fdisplay(output_fd,"  \"delivered_count\": [%0d, %0d],",final_delivered[0],final_delivered[1]);
        $fdisplay(output_fd,"  \"arbitration_wait_cycles\": [%0d, %0d],",final_wait[0],final_wait[1]);
        $fdisplay(output_fd,"  \"backend_request_count\": %0d, \"backend_response_count\": %0d,",final_requests,final_responses);
        $fdisplay(output_fd,"  \"cancelled_response_count\": %0d, \"orphan_response_count\": %0d,",final_cancelled,final_orphans);
        $fdisplay(output_fd,"  \"occupied_cycles\": %0d, \"high_water_mark\": %0d,",final_occupied,high_water_mark);
        $fdisplay(output_fd,"  \"counter_snapshot_scope\": \"before_final_quiescent_reset\"");
        $fdisplay(output_fd,"}");$fclose(output_fd);
        $display("PASS shared dataset channel checks=%0d cycles=%0d requests=%0d responses=%0d",checks,cycles,final_requests,final_responses);
        $finish;
    end
endmodule
`default_nettype wire
