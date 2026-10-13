// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_arbitration #(parameter integer LANES=4,SERIAL_CONVERT=0,COALESCE_LINES=1);
    reg  clk=0;
    reg  rst=0;
    reg  req_valid=0;
    wire  req_ready;
    reg [15:0] req_tag=0;
    reg  req_v2=0;
    reg [1:0] req_round_mode=0;
    reg [511:0] req_r=0;
    reg [511:0] req_a=0;
    reg [31:0] req_spaddr0=0;
    reg [31:0] req_spaddr1=0;
    reg [31:0] req_mx=0;
    reg [31:0] req_ma=0;
    reg [2:0] req_read0=0;
    reg [2:0] req_read1=0;
    reg [2:0] req_read2=0;
    reg [2:0] req_read3=0;
    reg [63:0] req_emask0=0;
    reg [63:0] req_emask1=0;
    reg [63:0] req_dataset_offset=0;
    reg [63:0] req_program_addr=0;
    wire  sp_rd_valid;
    reg  sp_rd_ready=0;
    wire [20:0] sp_rd_addr;
    wire [15:0] sp_rd_tag;
    reg  sp_rsp_valid=0;
    wire  sp_rsp_ready;
    reg [127:0] sp_rsp_data=0;
    reg [15:0] sp_rsp_tag=0;
    wire  sp_wr_valid;
    reg  sp_wr_ready=0;
    wire [20:0] sp_wr_addr;
    wire [127:0] sp_wr_data;
    wire [15:0] sp_wr_strb;
    wire [15:0] sp_wr_tag;
    wire  ex_req_valid;
    reg  ex_req_ready=0;
    wire [15:0] ex_req_tag;
    wire  ex_req_v2;
    wire [1:0] ex_req_round_mode;
    wire [511:0] ex_req_r;
    wire [511:0] ex_req_f;
    wire [511:0] ex_req_e;
    wire [511:0] ex_req_a;
    wire [63:0] ex_req_emask0;
    wire [63:0] ex_req_emask1;
    wire [63:0] ex_req_program_addr;
    reg  ex_ret_valid=0;
    wire  ex_ret_ready;
    reg [15:0] ex_ret_tag=0;
    reg [511:0] ex_ret_r=0;
    reg [511:0] ex_ret_f=0;
    reg [511:0] ex_ret_e=0;
    reg [1:0] ex_ret_round_mode=0;
    reg [15:0] ex_mem_tag=0;
    reg  ex_rd_valid=0;
    wire  ex_rd_ready;
    reg [20:0] ex_rd_addr=0;
    wire  ex_rsp_valid;
    reg  ex_rsp_ready=0;
    wire [127:0] ex_rsp_data;
    wire [15:0] ex_rsp_tag;
    reg  ex_wr_valid=0;
    wire  ex_wr_ready;
    reg [20:0] ex_wr_addr=0;
    reg [127:0] ex_wr_data=0;
    reg [15:0] ex_wr_strb=0;
    wire  ds_req_valid;
    reg  ds_req_ready=0;
    wire [63:0] ds_req_addr;
    wire [63:0] ds_prefetch_addr;
    wire [15:0] ds_req_tag;
    wire  ds_prefetch_valid;
    reg  ds_rsp_valid=0;
    wire  ds_rsp_ready;
    reg [15:0] ds_rsp_tag=0;
    reg [511:0] ds_rsp_data=0;
    wire  done_valid;
    reg  done_ready=0;
    wire [15:0] done_tag;
    wire [1:0] done_round_mode;
    wire [511:0] done_r;
    wire [511:0] done_f;
    wire [511:0] done_e;
    wire [31:0] done_mx;
    wire [31:0] done_ma;
    wire [31:0] done_spaddr0;
    wire [31:0] done_spaddr1;
    always #5 clk=~clk;
`ifdef ENGINE_NETLIST
    randomx_iteration_engine dut(
`else
    randomx_iteration_engine #(.LANES(LANES),.SERIAL_CONVERT(SERIAL_CONVERT),.COALESCE_LINES(COALESCE_LINES)) dut(
`endif
        .clk(clk),
        .rst(rst),
        .req_valid(req_valid),
        .req_ready(req_ready),
        .req_tag(req_tag),
        .req_v2(req_v2),
        .req_round_mode(req_round_mode),
        .req_r(req_r),
        .req_a(req_a),
        .req_spaddr0(req_spaddr0),
        .req_spaddr1(req_spaddr1),
        .req_mx(req_mx),
        .req_ma(req_ma),
        .req_read0(req_read0),
        .req_read1(req_read1),
        .req_read2(req_read2),
        .req_read3(req_read3),
        .req_emask0(req_emask0),
        .req_emask1(req_emask1),
        .req_dataset_offset(req_dataset_offset),
        .req_program_addr(req_program_addr),
        .sp_rd_valid(sp_rd_valid),
        .sp_rd_ready(sp_rd_ready),
        .sp_rd_addr(sp_rd_addr),
        .sp_rd_tag(sp_rd_tag),
        .sp_rsp_valid(sp_rsp_valid),
        .sp_rsp_ready(sp_rsp_ready),
        .sp_rsp_data(sp_rsp_data),
        .sp_rsp_tag(sp_rsp_tag),
        .sp_wr_valid(sp_wr_valid),
        .sp_wr_ready(sp_wr_ready),
        .sp_wr_addr(sp_wr_addr),
        .sp_wr_data(sp_wr_data),
        .sp_wr_strb(sp_wr_strb),
        .sp_wr_tag(sp_wr_tag),
        .ex_req_valid(ex_req_valid),
        .ex_req_ready(ex_req_ready),
        .ex_req_tag(ex_req_tag),
        .ex_req_v2(ex_req_v2),
        .ex_req_round_mode(ex_req_round_mode),
        .ex_req_r(ex_req_r),
        .ex_req_f(ex_req_f),
        .ex_req_e(ex_req_e),
        .ex_req_a(ex_req_a),
        .ex_req_emask0(ex_req_emask0),
        .ex_req_emask1(ex_req_emask1),
        .ex_req_program_addr(ex_req_program_addr),
        .ex_ret_valid(ex_ret_valid),
        .ex_ret_ready(ex_ret_ready),
        .ex_ret_tag(ex_ret_tag),
        .ex_ret_r(ex_ret_r),
        .ex_ret_f(ex_ret_f),
        .ex_ret_e(ex_ret_e),
        .ex_ret_round_mode(ex_ret_round_mode),
        .ex_mem_tag(ex_mem_tag),
        .ex_rd_valid(ex_rd_valid),
        .ex_rd_ready(ex_rd_ready),
        .ex_rd_addr(ex_rd_addr),
        .ex_rsp_valid(ex_rsp_valid),
        .ex_rsp_ready(ex_rsp_ready),
        .ex_rsp_data(ex_rsp_data),
        .ex_rsp_tag(ex_rsp_tag),
        .ex_wr_valid(ex_wr_valid),
        .ex_wr_ready(ex_wr_ready),
        .ex_wr_addr(ex_wr_addr),
        .ex_wr_data(ex_wr_data),
        .ex_wr_strb(ex_wr_strb),
        .ds_req_valid(ds_req_valid),
        .ds_req_ready(ds_req_ready),
        .ds_req_addr(ds_req_addr),
        .ds_prefetch_addr(ds_prefetch_addr),
        .ds_req_tag(ds_req_tag),
        .ds_prefetch_valid(ds_prefetch_valid),
        .ds_rsp_valid(ds_rsp_valid),
        .ds_rsp_ready(ds_rsp_ready),
        .ds_rsp_tag(ds_rsp_tag),
        .ds_rsp_data(ds_rsp_data),
        .done_valid(done_valid),
        .done_ready(done_ready),
        .done_tag(done_tag),
        .done_round_mode(done_round_mode),
        .done_r(done_r),
        .done_f(done_f),
        .done_e(done_e),
        .done_mx(done_mx),
        .done_ma(done_ma),
        .done_spaddr0(done_spaddr0),
        .done_spaddr1(done_spaddr1));

    integer reads,writes,read_stalls,write_stalls,response_stalls,stale_drops,cases,mode,n;
    reg [127:0] committed,expected,read_data;
    reg [15:0] active_tag;
    localparam [20:0] READ_ADDR=21'h001230,WRITE_ADDR=21'h001240,SECOND_ADDR=21'h001250;
    function [127:0] memory_word;
        input [20:0] address;
        begin
            memory_word=address==WRITE_ADDR ? committed :
                {64'h5566778899aabbcc^{43'b0,address},64'h0123456789abcdef^{43'b0,address}};
        end
    endfunction
    task start_context;
        input [15:0] tag;
        input version;
        integer pending,steps;
        reg [127:0] data;
        begin
            @(negedge clk);
            req_valid=1;req_tag=tag;req_v2=version;req_round_mode=0;
            req_r=0;req_a={8{64'h3ff4000000000000}};
            req_spaddr0=0;req_spaddr1=0;req_mx=0;req_ma=0;
            req_read0=0;req_read1=2;req_read2=4;req_read3=6;
            req_emask0=64'h3000000000000000;req_emask1=64'h3000000000000000;
            req_dataset_offset=0;req_program_addr=64'h10000000;
            sp_rd_ready=0;sp_wr_ready=0;sp_rsp_valid=0;
            ex_req_ready=0;ex_rd_valid=0;ex_wr_valid=0;ex_rsp_ready=0;
            ex_ret_valid=0;ds_rsp_valid=0;ds_req_ready=0;done_ready=0;
            #1;if(!req_ready)$fatal(1,"arbitration context not ready");
            @(posedge clk);#1;@(negedge clk);req_valid=0;
            sp_rd_ready=1;pending=0;steps=0;
            while(!ex_req_valid)begin
                @(posedge clk);
                if(sp_rsp_valid && sp_rsp_ready)pending=0;
                if(sp_rd_valid && sp_rd_ready)begin
                    if(pending || sp_rd_tag!==tag || sp_rd_addr[3:0]!=0)$fatal(1,"entry read contract");
                    pending=1;data=memory_word(sp_rd_addr);
                end
                #1;steps=steps+1;if(steps>80)$fatal(1,"arbitration entry timeout");
                @(negedge clk);sp_rsp_valid=pending;sp_rsp_tag=tag;sp_rsp_data=data;
            end
            sp_rsp_valid=0;sp_rd_ready=0;ex_req_ready=1;
            @(posedge clk);
            if(!ex_req_valid || ex_req_tag!==tag || ex_req_v2!==version)$fatal(1,"execution context descriptor");
            #1;@(negedge clk);ex_req_ready=0;ex_mem_tag=tag;active_tag=tag;
        end
    endtask
    task reset_context;
        begin
            @(negedge clk);rst=1;
            #1;if(sp_rd_valid || sp_wr_valid || ex_req_valid || ex_rsp_valid ||
                ex_rd_ready || ex_wr_ready || ex_ret_ready || sp_rsp_ready || done_valid)
                $fatal(1,"reset must suppress every arbitration handshake");
            @(posedge clk);#1;@(negedge clk);rst=0;
        end
    endtask
    task held_read;
        begin
            if(!sp_rd_valid || sp_rd_addr!==READ_ADDR || sp_rd_tag!==active_tag ||
                ex_rd_ready || sp_wr_valid || ex_wr_ready || ex_ret_ready)
                $fatal(1,"stalled execution read was preempted by arriving write");
            read_stalls=read_stalls+1;
        end
    endtask
    task held_write;
        begin
            if(!sp_wr_valid || sp_wr_addr!==WRITE_ADDR || sp_wr_tag!==active_tag ||
                sp_wr_data!==ex_wr_data || sp_wr_strb!==ex_wr_strb || ex_wr_ready ||
                sp_rd_valid || ex_rd_ready || ex_ret_ready)
                $fatal(1,"pending write grant/payload changed or fresh read preempted it");
            write_stalls=write_stalls+1;
        end
    endtask
    task accept_read;
        input [20:0] address;
        begin
            @(posedge clk);
            if(!sp_rd_valid || !sp_rd_ready || !ex_rd_ready || sp_rd_addr!==address ||
                sp_rd_tag!==active_tag || sp_wr_valid || ex_wr_ready || ex_ret_ready)
                $fatal(1,"read acceptance/order or premature return");
            read_data=memory_word(address);reads=reads+1;
            #1;@(negedge clk);ex_rd_valid=0;
        end
    endtask
    task return_read;
        input integer stall_cycles;
        integer j;
        begin
            sp_rsp_valid=1;sp_rsp_tag=active_tag;sp_rsp_data=read_data;ex_rsp_ready=0;
            for(j=0;j<stall_cycles;j=j+1)begin
                @(posedge clk);
                if(!ex_rsp_valid || ex_rsp_tag!==active_tag || ex_rsp_data!==read_data ||
                    sp_rsp_ready || sp_wr_valid || ex_wr_ready || ex_ret_ready)
                    $fatal(1,"read response stall failed to retain order/data/tag");
                response_stalls=response_stalls+1;
                #1;@(negedge clk);
            end
            ex_rsp_ready=1;
            @(posedge clk);
            if(!sp_rsp_ready || !ex_rsp_valid || ex_rsp_data!==read_data || sp_wr_valid || ex_wr_ready)
                $fatal(1,"write issued before read response drained");
            #1;@(negedge clk);sp_rsp_valid=0;ex_rsp_ready=0;
        end
    endtask
    task accept_write;
        integer b;
        begin
            sp_wr_ready=1;
            @(posedge clk);
            if(!sp_wr_valid || !ex_wr_ready || sp_wr_addr!==WRITE_ADDR || sp_wr_tag!==active_tag ||
                sp_wr_data!==ex_wr_data || sp_wr_strb!==ex_wr_strb || sp_rd_valid || ex_rd_ready || ex_ret_ready)
                $fatal(1,"write acceptance/order or premature return");
            for(b=0;b<16;b=b+1)if(sp_wr_strb[b])committed[8*b+:8]=sp_wr_data[8*b+:8];
            writes=writes+1;
            #1;@(negedge clk);ex_wr_valid=0;sp_wr_ready=0;
        end
    endtask
    task overlapping_read_then_write;
        input version;
        begin
            start_context(16'hd100+version,version);
            ex_rd_valid=1;ex_rd_addr=READ_ADDR;sp_rd_ready=0;
            ex_ret_valid=1;ex_ret_tag=active_tag;
            @(posedge clk);held_read();#1;
            @(negedge clk);ex_wr_valid=1;ex_wr_addr=WRITE_ADDR;
            ex_wr_data={64'hfedcba9876543210,64'h8877665544332211};ex_wr_strb=version?16'hff00:16'h00ff;
            for(n=0;n<3;n=n+1)begin @(posedge clk);held_read();#1;@(negedge clk);end
            // An old-generation SRAM reply cannot retract or accept the held grant.
            sp_rsp_valid=1;sp_rsp_tag=16'hffff;sp_rsp_data=~read_data;
            @(posedge clk);held_read();
            if(!sp_rsp_ready || ex_rsp_valid)$fatal(1,"stale reply leaked during held read");
            stale_drops=stale_drops+1;#1;@(negedge clk);sp_rsp_valid=0;
            sp_rd_ready=1;sp_wr_ready=1;accept_read(READ_ADDR);sp_wr_ready=0;
            // Same wrong tag while the accepted read is outstanding must not clear busy.
            sp_rsp_valid=1;sp_rsp_tag=16'hffff;sp_rsp_data=~read_data;
            @(posedge clk);
            if(!sp_rsp_ready || ex_rsp_valid || sp_wr_valid || ex_wr_ready || ex_ret_ready)
                $fatal(1,"stale reply cleared active read or released pending write");
            stale_drops=stale_drops+1;#1;@(negedge clk);sp_rsp_valid=0;
            return_read(3);
            // A fresh read arriving behind the stalled write must respect write priority.
            ex_rd_valid=1;ex_rd_addr=SECOND_ADDR;
            for(n=0;n<3;n=n+1)begin @(posedge clk);held_write();#1;@(negedge clk);end
            expected=version ? {ex_wr_data[127:64],committed[63:0]} : {committed[127:64],ex_wr_data[63:0]};
            accept_write();if(committed!==expected)$fatal(1,"committed byte-strobe data");
            accept_read(SECOND_ADDR);ex_ret_valid=0;return_read(0);
            reset_context();
            if(committed!==expected)$fatal(1,"reset changed already committed write");
            cases=cases+1;
        end
    endtask
    task reset_held_grant;
        begin
            start_context(16'hd200,1);
            ex_rd_valid=1;ex_rd_addr=READ_ADDR;sp_rd_ready=0;
            ex_ret_valid=1;ex_ret_tag=active_tag;
            @(posedge clk);held_read();#1;@(negedge clk);
            ex_wr_valid=1;ex_wr_addr=WRITE_ADDR;ex_wr_data=0;ex_wr_strb=16'hffff;
            @(posedge clk);held_read();#1;reset_context();
            sp_rsp_valid=1;sp_rsp_tag=16'hd200;sp_rsp_data=0;
            @(posedge clk);
            if(!ex_rd_ready || !ex_wr_ready || !ex_ret_ready || !sp_rsp_ready || sp_rd_valid ||
                sp_wr_valid || ex_rsp_valid || done_valid)$fatal(1,"cancelled requests/reply not dropped");
            stale_drops=stale_drops+1;#1;
            if(committed!==expected)$fatal(1,"unaccepted write committed across reset");
            start_context(16'hd201,1);
            ex_mem_tag=16'hd200;ex_rd_valid=1;ex_wr_valid=1;sp_rd_ready=1;sp_wr_ready=1;
            @(posedge clk);
            if(!ex_rd_ready || !ex_wr_ready || sp_rd_valid || sp_wr_valid)
                $fatal(1,"old-generation kernel commands leaked into new context");
            stale_drops=stale_drops+1;#1;@(negedge clk);
            ex_mem_tag=active_tag;ex_rd_addr=READ_ADDR;ex_wr_addr=WRITE_ADDR;
            ex_wr_data={64'h0123456789abcdef,64'h1020304050607080};ex_wr_strb=16'h00ff;
            sp_wr_ready=0;ex_ret_valid=1;ex_ret_tag=active_tag;
            // Both fresh requests: write wins, proving reset released the old read grant.
            for(n=0;n<2;n=n+1)begin @(posedge clk);held_write();#1;@(negedge clk);end
            expected={committed[127:64],ex_wr_data[63:0]};
            accept_write();accept_read(READ_ADDR);ex_ret_valid=0;return_read(0);
            if(committed!==expected)$fatal(1,"fresh-context commit corrupted");
            reset_context();cases=cases+1;
        end
    endtask
    initial begin #100000;$fatal(1,"arbitration regression deadlock");end
    initial begin
        reads=0;writes=0;read_stalls=0;write_stalls=0;response_stalls=0;stale_drops=0;cases=0;
        committed=128'h5555555555555555aaaaaaaaaaaaaaaa;expected=committed;
        rst=1;@(posedge clk);#1;@(negedge clk);rst=0;
        overlapping_read_then_write(0);overlapping_read_then_write(1);reset_held_grant();
        if(cases!=3 || reads!=5 || writes!=3 || read_stalls!=12 || write_stalls!=8 ||
            response_stalls!=6 || stale_drops!=6)$fatal(1,"directed arbitration coverage accounting");
        $display("PASS arbitration lanes=%0d serial=%0d coalesce=%0d cases=3 v1=1 v2=2 reads=5 writes=3 read_stall_cycles=12 write_stall_cycles=8 response_stall_cycles=6 stale_drops=6 reset_held_grant=1 committed_bytes_preserved=1",LANES,SERIAL_CONVERT,COALESCE_LINES);
        $finish;
    end
endmodule
