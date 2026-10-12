// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_iteration #(parameter integer LANES=1, OVERLAP_R=1);
    localparam integer N=16/LANES;
    localparam integer INTERVAL=OVERLAP_R ? (N+5>9 ? N+5 : 9) : N+9;
    reg clk=0;always #5 clk=~clk;
    reg rst=1,req_valid=0,req_v2=0,wr_ready=0,done_ready=0;
    reg [511:0] req_r=0,req_f=0,req_e=0;
    reg [14:0] req_f_line=0,req_r_line=0;
    wire req_ready,wr_valid,done_valid;
    wire [20:0] wr_addr;wire [127:0] wr_data;wire [15:0] wr_strb;
    wire [511:0] done_f;wire [31:0] next0,next1;
    reg version[0:127];reg [14:0] fline[0:127],rline[0:127];
    reg [511:0] r[0:127],f[0:127],e[0:127],gold_f[0:127],gold_r_mem[0:127],gold_f_mem[0:127];
    reg [127:0] ram[0:131071],gold_ram[0:131071];
    reg [4095:0] path;
    reg [127:0] held_data;reg [20:0] held_addr;reg [511:0] held_done;
    reg wr_stalled,done_stalled;
    integer fd,rc,i,j,ver,accepted,received,beats,cycle,last_accept,first_accept,v2_elapsed,transfers,aliases;
`ifdef ITERATION_NETLIST
    randomx_iteration_store dut (
`else
    randomx_iteration_store #(.LANES(LANES),.OVERLAP_R(OVERLAP_R)) dut (
`endif
        .clk(clk),.rst(rst),.req_valid(req_valid),.req_ready(req_ready),.req_v2(req_v2),
        .req_r(req_r),.req_f(req_f),.req_e(req_e),.req_f_line(req_f_line),.req_r_line(req_r_line),
        .wr_valid(wr_valid),.wr_ready(wr_ready),.wr_addr(wr_addr),.wr_data(wr_data),.wr_strb(wr_strb),
        .done_valid(done_valid),.done_ready(done_ready),.done_f(done_f),
        .done_spaddr0(next0),.done_spaddr1(next1)
    );
    initial begin #2000000;$fatal(1,"iteration deadlock");end
    task abort_after;
        input integer wanted;
        integer committed,k;
        begin
            @(negedge clk);req_valid=1;req_v2=1;req_r=r[0];req_f=f[0];req_e=e[0];
            req_f_line=fline[0];req_r_line=rline[0];wr_ready=1;done_ready=0;
            #1;if(!req_ready) $fatal(1,"reset test not ready");
            @(posedge clk);#1;@(negedge clk);req_valid=0;
            committed=0;
            while(committed<wanted) begin
                @(posedge clk);
                if(wr_valid) begin ram[wr_addr>>4]=wr_data;committed=committed+1;end
                #1;
            end
            @(negedge clk);rst=1;
            @(posedge clk);#1;if(wr_valid || done_valid || req_ready) $fatal(1,"reset handshake");
            @(negedge clk);rst=0;
            for(k=0;k<N+12;k=k+1) begin
                @(posedge clk);#1;if(wr_valid || done_valid) $fatal(1,"aborted tail leaked");
            end
            if(wanted==3) begin
                for(k=0;k<3;k=k+1)if(ram[(rline[0]<<2)+k]!==r[0][128*k+:128]) $fatal(1,"reset rolled back R stores");
            end else if(ram[fline[0]<<2]!==gold_f[0][127:0]) $fatal(1,"reset rolled back F store");
        end
    endtask
    initial begin
        if(!$value$plusargs("initial=%s",path)) $fatal(1,"missing initial memory");$readmemh(path,ram);
        if(!$value$plusargs("final=%s",path)) $fatal(1,"missing final memory");$readmemh(path,gold_ram);
        if(!$value$plusargs("trace=%s",path)) $fatal(1,"missing iteration trace");
        fd=$fopen(path,"r");if(!fd) $fatal(1,"trace open failed");aliases=0;
        for(i=0;i<128;i=i+1) begin
            rc=$fscanf(fd,"%d %h %h %h %h %h %h %h %h\n",ver,fline[i],rline[i],r[i],f[i],e[i],gold_f[i],gold_r_mem[i],gold_f_mem[i]);
            if(rc!=9) $fatal(1,"bad trace row");version[i]=ver;if(fline[i]==rline[i])aliases=aliases+1;
        end
        $fclose(fd);
        @(posedge clk);#1;
        @(negedge clk);rst=0;
        accepted=0;received=0;beats=0;cycle=0;last_accept=-1;first_accept=-1;v2_elapsed=-1;
        transfers=0;wr_stalled=0;done_stalled=0;
        while(received<128) begin
            @(negedge clk);
            req_valid=accepted<128;
            if(accepted<128) begin
                req_v2=version[accepted];req_r=r[accepted];req_f=f[accepted];req_e=e[accepted];
                req_f_line=fline[accepted];req_r_line=rline[accepted];
            end
            wr_ready=received<64 || cycle%11>=3;
            done_ready=received<64 || cycle%13>=4;
            @(posedge clk);cycle=cycle+1;
            if(wr_stalled && (!wr_valid || wr_data!==held_data || wr_addr!==held_addr || wr_strb!==16'hffff)) $fatal(1,"stalled store changed");
            if(done_stalled && (!done_valid || done_f!==held_done)) $fatal(1,"stalled retirement changed");
            if(wr_valid && wr_ready) begin
                if(beats>=8 || received>=accepted || wr_strb!==16'hffff) $fatal(1,"extra/unrequested store");
                if(beats<4) begin
                    if(wr_addr!=={rline[received],beats[1:0],4'b0} || wr_data!==r[received][128*beats+:128]) $fatal(1,"R store order/data");
                end else begin
                    if(wr_addr!=={fline[received],beats[1:0],4'b0} || wr_data!==gold_f[received][128*(beats-4)+:128]) $fatal(1,"F store order/data");
                end
                ram[wr_addr>>4]=wr_data;beats=beats+1;transfers=transfers+1;
            end
            wr_stalled=wr_valid && !wr_ready;held_data=wr_data;held_addr=wr_addr;
            done_stalled=done_valid && !done_ready;held_done=done_f;
            if(done_valid && done_ready) begin
                if(beats!=8 || done_f!==gold_f[received] || next0!==0 || next1!==0) $fatal(1,"early/bad retirement");
                for(j=0;j<4;j=j+1) begin
                    if(ram[(rline[received]<<2)+j]!==gold_r_mem[received][128*j+:128]) $fatal(1,"R region mismatch/alias order");
                    if(ram[(fline[received]<<2)+j]!==gold_f_mem[received][128*j+:128]) $fatal(1,"F region mismatch");
                end
                received=received+1;beats=0;
                if(received==64)v2_elapsed=cycle-first_accept;
            end
            if(req_valid && req_ready) begin
                if(accepted<64 && last_accept>=0 && cycle-last_accept!=INTERVAL) $fatal(1,"tail interval mismatch");
                if(first_accept<0)first_accept=cycle;
                last_accept=cycle;accepted=accepted+1;
            end
            #1;
        end
        if(transfers!=1024 || v2_elapsed!=64*INTERVAL || aliases!=32) $fatal(1,"tail accounting/cycles");
        for(i=0;i<131071+1;i=i+1)if(ram[i]!==gold_ram[i]) $fatal(1,"full scratchpad mismatch word %0d",i);
        @(negedge clk);req_valid=0;done_ready=1;
        @(posedge clk);#1;if(done_valid || wr_valid) $fatal(1,"duplicate completion");
        abort_after(3);abort_after(5);
        $display("PASS tail lanes=%0d overlap=%0d iterations=128 v2=64 v1=64 writes=1024 aliases=32 full_memory_bytes=2097152 reset_aborts=2 interval_cycles=%0d v2_elapsed_cycles=%0d",LANES,OVERLAP_R,INTERVAL,v2_elapsed);
        $finish;
    end
endmodule
