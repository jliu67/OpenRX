// SPDX-License-Identifier: BSD-3-Clause
// Finite functional/controller-cadence experiment only. ALL VALIDATION UNRUN.
`timescale 1ns/1ps
`default_nettype none
module tb_prepared_fetch_sram_port;
    reg clk=0;
    always #5 clk=~clk;
    reg rst=1;
    reg [1:0] client_cancel=0,client_req_valid=0,client_rsp_ready=0;
    reg [127:0] client_req_tag=0;
    reg [55:0] client_req_payload=0;
    wire [1:0] client_req_ready,client_rsp_valid;
    wire [127:0] client_rsp_tag;
    wire [379:0] client_rsp_payload;
    wire backend_req_valid,backend_req_ready,backend_rsp_valid,backend_rsp_ready;
    wire [64:0] backend_req_tag,backend_rsp_tag;
    wire [27:0] backend_req_payload;
    wire [189:0] backend_rsp_payload;
    wire channel_busy,issued,owner,owner_cancelled;
    wire [127:0] accepted_count,delivered_count,arbitration_wait_cycles;
    wire [63:0] backend_request_count,backend_response_count;
    wire [63:0] cancelled_response_count,orphan_response_count,occupied_cycles;
    reg image_admitted=0,issue_allow=1;
    wire row_read_en,row_read_valid,sealed,adapter_busy;
    wire [11:0] row_read_address;
    wire [255:0] row_read_data;
    wire [79:0] program_counts;
    wire adapter_req_ready;

    randomx_dataset_shared_channel channel (
        .clk(clk),.rst(rst),.client_cancel(client_cancel),
        .client_req_valid(client_req_valid),.client_req_ready(client_req_ready),
        .client_req_tag(client_req_tag),.client_req_payload(client_req_payload),
        .client_rsp_valid(client_rsp_valid),.client_rsp_ready(client_rsp_ready),
        .client_rsp_tag(client_rsp_tag),.client_rsp_payload(client_rsp_payload),
        .backend_req_valid(backend_req_valid),.backend_req_ready(backend_req_ready),
        .backend_req_tag(backend_req_tag),.backend_req_payload(backend_req_payload),
        .backend_rsp_valid(backend_rsp_valid),.backend_rsp_ready(backend_rsp_ready),
        .backend_rsp_tag(backend_rsp_tag),.backend_rsp_payload(backend_rsp_payload),
        .busy(channel_busy),.issued(issued),.owner(owner),.owner_cancelled(owner_cancelled),
        .accepted_count(accepted_count),.delivered_count(delivered_count),
        .arbitration_wait_cycles(arbitration_wait_cycles),
        .backend_request_count(backend_request_count),.backend_response_count(backend_response_count),
        .cancelled_response_count(cancelled_response_count),
        .orphan_response_count(orphan_response_count),.occupied_cycles(occupied_cycles)
    );
    // This directed-test gate models external request-side stalls only. It
    // changes no accepted channel RTL and is continuously open in cadence mode.
    assign backend_req_ready=adapter_req_ready&&issue_allow;
    randomx_prepared_fetch_sram_port adapter (
        .clk(clk),.rst(rst),.image_sealed(sealed&&image_admitted),
        .program_counts(program_counts),.req_valid(backend_req_valid&&issue_allow),
        .req_ready(adapter_req_ready),.req_tag(backend_req_tag),
        .req_payload(backend_req_payload),.rsp_valid(backend_rsp_valid),
        .rsp_ready(backend_rsp_ready),.rsp_tag(backend_rsp_tag),
        .rsp_payload(backend_rsp_payload),.row_read_en(row_read_en),
        .row_read_address(row_read_address),.row_read_valid(row_read_valid),
        .row_read_data(row_read_data),.busy(adapter_busy)
    );
    prepared_fetch_sram_behavioral memory_port (
        .clk(clk),.read_en(row_read_en),.read_address(row_read_address),
        .read_valid(row_read_valid),.read_data(row_read_data),
        .sealed(sealed),.program_counts(program_counts)
    );

    reg [160:0] gold_payload [0:4095];
    reg [9:0] counts [0:7];
    string image_dir,output_path;
    integer out_fd;
    integer ticks=0,checks=0,scenarios=0,tag_serial=0;
    integer active_requests=0,error_requests=0;
    integer total_accepted[0:1],total_delivered[0:1];
    integer total_requests=0,total_responses=0,total_cancelled=0,total_row_reads=0;
    integer accepted_base[0:1],delivered_base[0:1];
    integer requests_base=0,responses_base=0,cancelled_base=0,occupied_base=0;
    integer total_occupied=0;
    integer last_capture_tick=-1,last_issue_tick=-1,last_delivery_tick=-1;
    integer cadence_mode=0,cadence_captures=0,cadence_deliveries=0;
    integer cadence_first=-1,cadence_last=-1,cadence_previous=-1;
    integer cadence_owner_count[0:1];
    integer expected_program,expected_pc,expected_slot,who;
    reg sb_busy=0,sb_cancelled=0,sb_issued=0;
    reg sb_owner=0;
    reg [63:0] sb_tag=0;
    reg [27:0] sb_payload=0;
    reg [189:0] sb_response=0;
    reg [1:0] expected_client_valid;
    reg provider_held=0;
    reg initial_reset_seen=0;
    reg [64:0] held_tag=0;
    reg [189:0] held_payload=0;
    integer monitor_owner;

    task check;
        input condition;
        input [8*180-1:0] message;
    begin
        checks=checks+1;
        if(condition!==1'b1)
            $fatal(1,"prepared-fetch SRAM check failed tick=%0d: %0s",ticks,message);
    end endtask

    // Independent transaction scoreboard uses raw-fixture-derived oracle rows,
    // not the adapter row array or a copy of its selected address expression.
    always @(posedge clk) begin
        ticks=ticks+1;
        if(ticks>100000) $fatal(1,"100000-clock watchdog exhausted");
        if(rst) begin
            if(initial_reset_seen)
                check(!sb_busy&&!channel_busy&&!adapter_busy,
                      "reset is restricted to genuine quiescence");
            // Initial cold reset establishes known registers before traffic;
            // every later reset is checked against real provider quiescence.
            initial_reset_seen=1;
            accepted_base[0]=total_accepted[0];accepted_base[1]=total_accepted[1];
            delivered_base[0]=total_delivered[0];delivered_base[1]=total_delivered[1];
            requests_base=total_requests;responses_base=total_responses;
            cancelled_base=total_cancelled;occupied_base=total_occupied;
            provider_held=0;
        end else begin
            check(channel_busy===sb_busy,"channel credit matches independent scoreboard");
            if(channel_busy) total_occupied=total_occupied+1;
            if(sb_busy&&client_cancel[sb_owner]) sb_cancelled=1;
            if(provider_held) begin
                check(backend_rsp_valid,"held provider response remains valid");
                check(backend_rsp_tag===held_tag&&backend_rsp_payload===held_payload,
                      "held provider tag and row payload remain immutable");
            end
            if(backend_req_valid&&backend_req_ready) begin
                check(sb_busy&&!sb_issued,"exactly one backend request per captured credit");
                check(backend_req_tag==={sb_owner,sb_tag}&&backend_req_payload===sb_payload,
                      "backend preserves owner, full tag and captured descriptor");
                sb_issued=1; total_requests=total_requests+1;last_issue_tick=ticks;
                if(cadence_mode) check(ticks==last_capture_tick+1,
                                      "synchronous row request is one edge after capture");
            end
            if(row_read_en) begin
                check(backend_req_valid&&backend_req_ready,"row read requires admitted request handshake");
                check(!sb_response[161],"address error does not issue a row read");
                total_row_reads=total_row_reads+1;
            end
            expected_client_valid=0;
            if(backend_rsp_valid) begin
                check(sb_busy&&sb_issued,"provider response has one captured issued owner");
                check(backend_rsp_tag==={sb_owner,sb_tag},"provider preserves complete captured tag");
                check(backend_rsp_payload===sb_response,"all190 response bits match independent source oracle");
                if(!sb_cancelled) expected_client_valid=sb_owner?2'b10:2'b01;
            end
            check(client_rsp_valid===expected_client_valid,"response appears only at uncancelled captured owner");
            if(expected_client_valid) begin
                check(client_rsp_tag[sb_owner*64+:64]===sb_tag,"client full tag exact");
                check(client_rsp_payload[sb_owner*190+:190]===sb_response,"client payload exact");
            end
            provider_held=backend_rsp_valid&&!backend_rsp_ready;
            held_tag=backend_rsp_tag;held_payload=backend_rsp_payload;
            if(backend_rsp_valid&&backend_rsp_ready) begin
                total_responses=total_responses+1;
                if(sb_cancelled) begin
                    total_cancelled=total_cancelled+1;
                    check(client_rsp_valid==0,"cancel drains response without client delivery");
                end else begin
                    check(client_rsp_ready[sb_owner],"uncancelled return requires owner readiness");
                    total_delivered[sb_owner]=total_delivered[sb_owner]+1;
                    last_delivery_tick=ticks;
                    if(cadence_mode) begin
                        cadence_deliveries=cadence_deliveries+1;
                        check(ticks==last_capture_tick+2,
                              "this SRAM-port response is consumed two edges after capture");
                    end
                end
                sb_busy=0;sb_issued=0;sb_cancelled=0;
            end
            for(monitor_owner=0;monitor_owner<2;monitor_owner=monitor_owner+1) begin
                if(client_req_valid[monitor_owner]&&client_req_ready[monitor_owner]) begin
                    check(!sb_busy,"no second capture while the prior credit is live");
                    // Channel explicitly forbids a capture on a response edge.
                    check(!(backend_rsp_valid&&backend_rsp_ready),"no capture on return edge");
                    sb_busy=1;sb_issued=0;sb_cancelled=0;sb_owner=monitor_owner[0];
                    sb_tag=client_req_tag[monitor_owner*64+:64];
                    sb_payload=client_req_payload[monitor_owner*28+:28];
                    expected_program=sb_payload[11:9]; expected_pc=sb_payload[8:0];
                    expected_slot=expected_program*512+expected_pc;
                    if(expected_pc>=counts[expected_program]) begin
                        sb_response={sb_payload,1'b1,161'b0};
                        error_requests=error_requests+1;
                    end else begin
                        sb_response={sb_payload,1'b0,gold_payload[expected_slot]};
                        active_requests=active_requests+1;
                    end
                    total_accepted[monitor_owner]=total_accepted[monitor_owner]+1;
                    last_capture_tick=ticks;
                    if(cadence_mode) begin
                        if(cadence_previous>=0) check(ticks-cadence_previous==3,
                            "minimum continuous capture spacing is exactly three clocks for this controller");
                        if(cadence_first<0) cadence_first=ticks;
                        cadence_previous=ticks;cadence_last=ticks;
                        cadence_captures=cadence_captures+1;
                        cadence_owner_count[monitor_owner]=cadence_owner_count[monitor_owner]+1;
                    end
                end
            end
        end
    end

    // Calls return at a negative edge; drivers do not race sampled transfers.
    task step;
    begin
        @(posedge clk); #1; @(negedge clk);
    end endtask

    task set_offer;
        input integer client;
        input [27:0] payload;
    begin
        tag_serial=tag_serial+1;
        check(tag_serial>0&&tag_serial<100000,"finite full-tag namespace never wraps or reuses");
        client_req_tag[client*64+:64]=64'h5a00000000000000+tag_serial;
        client_req_payload[client*28+:28]=payload;
    end endtask

    task capture;
        input integer client;
        input [27:0] payload;
        integer tries;
        reg captured;
    begin
        check(!channel_busy&&!adapter_busy&&client_req_valid==0,"single request begins quiescent");
        set_offer(client,payload);client_req_valid[client]=1;
        captured=0;
        for(tries=0;tries<16;tries=tries+1) begin
            if(!captured) begin
                #1;
                if(client_req_ready[client]) begin
                    step;client_req_valid[client]=0;captured=1;
                end else step;
            end
        end
        check(captured&&channel_busy&&owner==client,"bounded request capture and owner selection");
        // Input replacements must not change the already captured descriptor.
        client_req_tag[client*64+:64]=~client_req_tag[client*64+:64];
        client_req_payload[client*28+:28]=~payload;
    end endtask

    task wait_response;
        input integer client;
        integer tries;
        reg found;
    begin
        found=0;
        for(tries=0;tries<16;tries=tries+1) begin
            if(!found) begin
                #1;
                if(client_rsp_valid[client]) found=1;
                else step;
            end
        end
        check(found,"bounded registered read response");
    end endtask

    task consume;
        input integer client;
        input integer hold_clocks;
        integer k;
        reg [253:0] held;
    begin
        wait_response(client);
        held={client_rsp_tag[client*64+:64],client_rsp_payload[client*190+:190]};
        for(k=0;k<hold_clocks;k=k+1) begin
            check(!backend_rsp_ready&&channel_busy&&adapter_busy,"backpressure retains one occupied credit");
            step;
            check(client_rsp_valid[client]&&
                  {client_rsp_tag[client*64+:64],client_rsp_payload[client*190+:190]}===held,
                  "held response preserves full tag, row and echoed address");
        end
        client_rsp_ready[client]=1;step;client_rsp_ready[client]=0;
        #1;check(!channel_busy&&!adapter_busy,"response consume returns both credits");
    end endtask

    task wait_drain;
        integer tries;
    begin
        for(tries=0;tries<16;tries=tries+1) if(channel_busy||adapter_busy) step;
        check(!channel_busy&&!adapter_busy&&!sb_busy,"cancelled transaction completely drains");
        check(client_rsp_valid==0,"no stale cancelled response remains");
    end endtask

    task scenario;
        input [8*80-1:0] name;
    begin
        scenarios=scenarios+1;
        $display("SCENARIO %0d %0s",scenarios,name);
    end endtask

    integer p,pc,c,k,previous_cancelled,before0,before1;
    integer captured_lane;
    reg [15:0] epoch;
    initial begin
        total_accepted[0]=0;total_accepted[1]=0;
        total_delivered[0]=0;total_delivered[1]=0;
        cadence_owner_count[0]=0;cadence_owner_count[1]=0;
        if(!$value$plusargs("IMAGE_DIR=%s",image_dir)||!$value$plusargs("OUT=%s",output_path))
            $fatal(1,"IMAGE_DIR and OUT required; no defaults or fallbacks");
        $readmemh({image_dir,"/gold-payload.mem"},gold_payload);
        $readmemh({image_dir,"/counts.mem"},counts);
        #1;
        check(sealed,"complete image admitted before traffic");
        for(p=0;p<8;p=p+1) begin
            check(counts[p]===program_counts[p*10+:10],"oracle and row-store count metadata exact");
            for(pc=0;pc<512;pc=pc+1)
                check((^gold_payload[p*512+pc]!==1'bx),"complete independently derived oracle rows");
        end
        check(counts[0]==447&&counts[1]==438&&counts[2]==449&&counts[3]==447&&
              counts[4]==444&&counts[5]==449&&counts[6]==452&&counts[7]==437,
              "one retained admitted image with exact eight program counts");
        // Avoid testing an initial unknown pre-reset channel state.
        step;step;rst=0;

        scenario("sealed_image_admission");
        capture(0,{16'h1234,3'd0,9'd0});
        repeat(3) begin
            check(!backend_req_ready&&!row_read_en&&!issued,"unsealed admission cannot issue a row read");
            step;
        end
        image_admitted=1;consume(0,0);

        scenario("all_3563_active_rows_through_both_clients");
        for(p=0;p<8;p=p+1) begin
            for(pc=0;pc<counts[p];pc=pc+1) begin
                for(c=0;c<2;c=c+1) begin
                    epoch=(pc*13+p*127+c*4093)&16'hffff;
                    capture(c,{epoch,p[2:0],pc[8:0]});consume(c,0);
                end
            end
        end

        scenario("first_padding_and_last_slot_errors_both_clients");
        for(p=0;p<8;p=p+1) begin
            for(c=0;c<2;c=c+1) begin
                capture(c,{16'hcafe,p[2:0],counts[p][8:0]});consume(c,1);
                capture(c,{16'hbabe,p[2:0],9'd511});consume(c,1);
            end
        end

        scenario("held_reply_and_captured_input_replacement");
        capture(1,{16'h00ff,3'd7,9'd17});consume(1,5);

        scenario("cancel_before_backend_issue");
        issue_allow=0;previous_cancelled=total_cancelled;
        capture(1,{16'hc001,3'd2,9'd12});
        repeat(3) step;
        client_cancel=2'b10;step;client_cancel=0;
        check(owner_cancelled&&!issued,"queued cancellation burns captured identity without refund");
        issue_allow=1;wait_drain;
        check(total_cancelled==previous_cancelled+1,"queued cancellation drains exactly one response");

        scenario("cancel_after_backend_issue");
        previous_cancelled=total_cancelled;
        capture(0,{16'hc002,3'd3,9'd13});step;
        check(issued&&backend_rsp_valid,"synchronous row returned before cancellation edge");
        client_cancel=2'b01;step;client_cancel=0;wait_drain;
        check(total_cancelled==previous_cancelled+1,"issued cancellation drains exactly one response");

        scenario("cancel_held_reply");
        previous_cancelled=total_cancelled;
        capture(1,{16'hc003,3'd4,9'd14});wait_response(1);
        repeat(3) step;
        client_cancel=2'b10;step;client_cancel=0;wait_drain;
        check(total_cancelled==previous_cancelled+1,"held cancellation drains exactly one response");

        scenario("nonowner_cancel_does_not_cancel_owner");
        previous_cancelled=total_cancelled;
        capture(0,{16'hc004,3'd5,9'd15});
        client_cancel=2'b10;step;client_cancel=0;consume(0,0);
        check(total_cancelled==previous_cancelled,"nonowner cancellation changes no captured identity");

        scenario("opaque_epoch_echo_without_address_selection");
        capture(0,{16'h0000,3'd6,9'd16});consume(0,0);
        capture(1,{16'hffff,3'd6,9'd16});consume(1,0);

        scenario("continuous_two_client_three_clock_cadence");
        before0=total_delivered[0];before1=total_delivered[1];
        cadence_mode=1;client_rsp_ready=2'b11;
        set_offer(0,{16'h1010,3'd0,9'd0});set_offer(1,{16'h2020,3'd1,9'd0});
        client_req_valid=2'b11;
        while(cadence_captures<32) begin
            #1;captured_lane=-1;
            if(client_req_ready[0]) captured_lane=0;
            if(client_req_ready[1]) captured_lane=1;
            step;
            if(captured_lane>=0) begin
                if(cadence_captures<32)
                    set_offer(captured_lane,{tag_serial[15:0],captured_lane[2:0],9'd0});
                else client_req_valid=0;
            end
        end
        wait_drain;client_rsp_ready=0;cadence_mode=0;
        check(cadence_captures==32&&cadence_deliveries==32&&
              cadence_owner_count[0]==16&&cadence_owner_count[1]==16,
              "continuous traffic completes32 unique requests fairly across both owners");
        check(cadence_last-cadence_first==93&&
              total_delivered[0]==before0+16&&total_delivered[1]==before1+16,
              "31 capture intervals close exactly at93 clocks, no throughput extrapolation");

        scenario("quiescent_reset_retains_immutable_image");
        check(!channel_busy&&!adapter_busy&&!sb_busy&&client_req_valid==0,
              "genuinely quiescent reset precondition");
        rst=1;step;step;rst=0;
        check(accepted_count==0&&delivered_count==0&&backend_request_count==0&&
              backend_response_count==0&&cancelled_response_count==0&&orphan_response_count==0,
              "quiescent reset clears diagnostics, not image or external namespace history");
        capture(1,{16'hbeef,3'd0,9'd0});consume(1,0);

        scenario("terminal_counter_and_clock_ledger_closure");
        check(scenarios==12,"exact12 named simulation scenarios");
        check(total_requests==total_accepted[0]+total_accepted[1]&&
              total_responses==total_requests&&total_cancelled==3,
              "every captured request issued and completed once, three cancels drained");
        check(total_requests==7199&&active_requests==7167&&error_requests==32,
              "exact prepared scenario request counts, without skipped rows or fallbacks");
        check(total_delivered[0]+total_delivered[1]+total_cancelled==total_responses,
              "client delivery plus cancellation equals backend response count");
        check(total_row_reads==active_requests&&total_row_reads+error_requests==total_requests,
              "active rows read once; every invalid PC returns error without memory access");
        check(accepted_count[63:0]==total_accepted[0]-accepted_base[0]&&
              accepted_count[127:64]==total_accepted[1]-accepted_base[1]&&
              delivered_count[63:0]==total_delivered[0]-delivered_base[0]&&
              delivered_count[127:64]==total_delivered[1]-delivered_base[1],
              "post-reset per-client diagnostics close against cumulative oracle ledger");
        check(backend_request_count==total_requests-requests_base&&
              backend_response_count==total_responses-responses_base&&
              cancelled_response_count==total_cancelled-cancelled_base&&orphan_response_count==0&&
              occupied_cycles==total_occupied-occupied_base,
              "post-reset backend and occupied-clock diagnostics close exactly");
        check(!channel_busy&&!adapter_busy&&!sb_busy&&client_rsp_valid==0,
              "terminal client/channel/provider quiescence");
        out_fd=$fopen(output_path,"w");if(!out_fd)$fatal(1,"cannot create OUT");
        $fwrite(out_fd,"{\"status\":\"pass\",\"scope\":\"behavioral_prepared_fetch_port_only\",\"scenarios\":12,\"checks\":%0d,\"modeled_clocks\":%0d,",checks,ticks);
        $fwrite(out_fd,"\"active_row_queries_both_clients\":7126,\"active_requests\":%0d,\"error_requests\":%0d,\"row_reads\":%0d,",active_requests,error_requests,total_row_reads);
        $fwrite(out_fd,"\"accepted\":[%0d,%0d],\"delivered\":[%0d,%0d],\"backend_requests\":%0d,\"backend_responses\":%0d,\"cancelled_responses\":%0d,",total_accepted[0],total_accepted[1],total_delivered[0],total_delivered[1],total_requests,total_responses,total_cancelled);
        $fwrite(out_fd,"\"controller_cadence\":{\"capture_to_read_edges\":1,\"capture_to_consume_edges\":2,\"capture_spacing\":3,\"captures\":32,\"intervals\":31,\"interval_clocks\":93},");
        $fwrite(out_fd,"\"clock_ledger\":{\"total_modeled_clocks\":%0d,\"cumulative_channel_occupied_clocks\":%0d,\"before_last_reset_occupied_clocks\":%0d,\"after_last_reset_occupied_clocks\":%0d,\"cadence_interval_clocks\":93},",ticks,total_occupied,occupied_base,occupied_cycles);
        $fwrite(out_fd,"\"last_reset_baseline\":{\"accepted\":[%0d,%0d],\"delivered\":[%0d,%0d],\"backend_requests\":%0d,\"backend_responses\":%0d,\"cancelled_responses\":%0d},",accepted_base[0],accepted_base[1],delivered_base[0],delivered_base[1],requests_base,responses_base,cancelled_base);
        $fwrite(out_fd,"\"post_reset_counters\":{\"accepted\":[%0d,%0d],\"delivered\":[%0d,%0d],\"backend_requests\":%0d,\"backend_responses\":%0d,\"cancelled_responses\":%0d,\"orphan_responses\":%0d},",accepted_count[63:0],accepted_count[127:64],delivered_count[63:0],delivered_count[127:64],backend_request_count,backend_response_count,cancelled_response_count,orphan_response_count);
        $fwrite(out_fd,"\"image_rows\":4096,\"row_bits\":256,\"active_image_rows\":3563,\"padding_rows\":533,\"simulation_watchdog_clocks\":100000,\"physical_acceptance\":false,\"full_hash_run\":false}\n");
        $fclose(out_fd);
        $display("PASS prepared_fetch_sram scenarios=12 checks=%0d clocks=%0d",checks,ticks);
        $finish;
    end
endmodule
`default_nettype wire
