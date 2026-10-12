// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_mix #(
    parameter integer LANES=1
);
    localparam integer STEPS=16/LANES;
    reg clk=0;
    always #5 clk=~clk;
    reg rst=1,req_valid=0,rsp_ready=0;
    reg [511:0] req_f=0,req_e=0;
    wire req_ready,rsp_valid;
    wire [511:0] rsp_f;
    reg [511:0] f[0:255],e[0:255],expected[0:255];
    reg [511:0] held;
    reg [4095:0] vector_path;
    integer fd,rc,count,i,j,cycle=0,accepted,received,last_accept,first_accept,last_receive,stall;
    randomx_v2_aes_mix #(.LANES(LANES)) dut (
        .clk(clk),.rst(rst),.req_valid(req_valid),.req_ready(req_ready),
        .req_f(req_f),.req_e(req_e),.rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_f(rsp_f)
    );
    // Deterministic deadlock guard including both directed and streaming tests.
    initial begin #200000; $fatal(1,"timeout LANES=%0d",LANES); end
    task reset;
        begin
            @(negedge clk);rst=1;req_valid=0;rsp_ready=0;
            @(posedge clk);#1;
            if (rsp_valid || req_ready) $fatal(1,"reset handshake");
            @(negedge clk);rst=0;
            #1;if (!req_ready || rsp_valid) $fatal(1,"reset release");
        end
    endtask
    initial begin
        if (!$value$plusargs("vectors=%s",vector_path)) $fatal(1,"missing vectors");
        fd=$fopen(vector_path,"r");if(!fd) $fatal(1,"cannot open mix vectors");
        count=0;
        while (!$feof(fd) && count<256) begin
            rc=$fscanf(fd,"%h %h %h\n",f[count],e[count],expected[count]);
            if(rc!=3) $fatal(1,"malformed mix vector");count=count+1;
        end
        if(count!=256 || !$feof(fd)) $fatal(1,"wrong vector count");$fclose(fd);
        reset;
        // Abort work in progress, then abort a held result; neither may leak.
        req_valid=1;req_f=f[0];req_e=e[0];@(posedge clk);#1;
        @(negedge clk);req_valid=0;
        @(posedge clk);#1;reset;
        for(j=0;j<STEPS+2;j=j+1) begin @(posedge clk);#1;if(rsp_valid) $fatal(1,"aborted work leaked");end
        @(negedge clk);req_valid=1;req_f=f[1];req_e=e[1];
        @(posedge clk);#1;@(negedge clk);req_valid=0;
        for(j=0;j<STEPS;j=j+1) begin @(posedge clk);#1;end
        if(!rsp_valid || rsp_f!==expected[1]) $fatal(1,"pre-reset held response");
        reset;
        for(j=0;j<STEPS+2;j=j+1) begin @(posedge clk);#1;if(rsp_valid) $fatal(1,"aborted result leaked");end
        // Directed latency and backpressure, with changing unaccepted inputs.
        for(i=0;i<32;i=i+1) begin
            @(negedge clk);req_valid=1;req_f=f[i];req_e=e[i];rsp_ready=0;
            #1;if(!req_ready) $fatal(1,"idle not ready");
            @(posedge clk);#1;
            for(j=1;j<=STEPS;j=j+1) begin
                @(negedge clk);req_valid=1;req_f=~f[i];req_e=~e[i];
                #1;if(req_ready) $fatal(1,"accepted while busy");
                @(posedge clk);#1;
                if(j<STEPS && rsp_valid) $fatal(1,"early result");
            end
            if(!rsp_valid || rsp_f!==expected[i]) $fatal(1,"mix mismatch %0d LANES=%0d",i,LANES);
            held=rsp_f;stall=i%7+1;
            for(j=0;j<stall;j=j+1) begin
                @(negedge clk);req_f=~req_f;req_e=~req_e;
                @(posedge clk);#1;
                if(!rsp_valid || req_ready || rsp_f!==held) $fatal(1,"backpressure stability");
            end
            @(negedge clk);req_valid=0;rsp_ready=1;
            @(posedge clk);#1;if(rsp_valid) $fatal(1,"duplicate result");
            @(negedge clk);rsp_ready=0;
        end
        reset;
        // Consecutive no-stall requests exercise same-edge result/re-request.
        accepted=0;received=0;last_accept=-1;first_accept=-1;last_receive=-1;
        while(received<256) begin
            @(negedge clk);
            rsp_ready=1;req_valid=(accepted<256);
            if(accepted<256) begin req_f=f[accepted];req_e=e[accepted];end
            @(posedge clk);
            cycle=cycle+1;
            // Sample transfers before registered state changes at this edge.
            if(rsp_valid) begin
                if(received>=accepted || rsp_f!==expected[received]) $fatal(1,"stream mix mismatch %0d",received);
                received=received+1;last_receive=cycle;
            end
            if(req_valid && req_ready) begin
                if(last_accept>=0 && cycle-last_accept!=STEPS+1) $fatal(1,"acceptance interval");
                if(first_accept<0) first_accept=cycle;
                last_accept=cycle;accepted=accepted+1;
            end
            #1;
        end
        if(accepted!=256) $fatal(1,"transaction accounting");
        if(last_receive-first_accept!=256*(STEPS+1)) $fatal(1,"stream elapsed cycles");
        @(negedge clk);req_valid=0;
        @(posedge clk);#1;if(rsp_valid) $fatal(1,"stream duplicate result");
        $display("PASS lanes=%0d mixes=256 directed=32 reset_aborts=2 stalls=32 availability_cycles=%0d interval_cycles=%0d stream_cycles=%0d",LANES,STEPS,STEPS+1,last_receive-first_accept);
        $finish;
    end
endmodule
