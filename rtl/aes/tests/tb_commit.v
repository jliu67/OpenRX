// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_commit #(parameter integer LANES=1);
    reg clk=0;always #5 clk=~clk;
    reg rst=1,vm_valid=0,vm_v2=0,wb_ready=0;
    reg [511:0] vm_f=0,vm_e=0;
    wire vm_ready,wb_valid;wire [511:0] wb_f;
    reg [511:0] f[0:255],e[0:255],expected[0:255];
    reg [511:0] expected_v1[0:255];
    reg [511:0] held;
    reg [4095:0] vector_path;
    integer fd,rc,count,accepted,received,ticks,phase,v1_count,v2_count;
    reg stalled;
`ifdef AES_NETLIST
    randomx_exec_aes_commit dut (
`else
    randomx_exec_aes_commit #(.LANES(LANES)) dut (
`endif
        .clk(clk),.rst(rst),.vm_valid(vm_valid),.vm_ready(vm_ready),
        .vm_v2(vm_v2),.vm_f(vm_f),.vm_e(vm_e),
        .wb_valid(wb_valid),.wb_ready(wb_ready),.wb_f(wb_f)
    );
    initial begin #200000;$fatal(1,"commit timeout");end
    initial begin
        if(!$value$plusargs("vectors=%s",vector_path)) $fatal(1,"missing vectors");
        fd=$fopen(vector_path,"r");if(!fd) $fatal(1,"cannot open vectors");
        for(count=0;count<256;count=count+1) begin
            rc=$fscanf(fd,"%h %h %h\n",f[count],e[count],expected[count]);
            if(rc!=3) $fatal(1,"bad vector");
        end
        $fclose(fd);
        if(!$value$plusargs("v1vectors=%s",vector_path)) $fatal(1,"missing v1 vectors");
        fd=$fopen(vector_path,"r");if(!fd) $fatal(1,"cannot open v1 vectors");
        for(count=0;count<256;count=count+1) begin
            rc=$fscanf(fd,"%h\n",expected_v1[count]);
            if(rc!=1) $fatal(1,"bad v1 vector");
        end
        $fclose(fd);
        // First run all v2 without stalls: compare integrated cycle intervals.
        // Then interleave v1/v2 with stalls and producer gaps, preserving order.
        for(phase=0;phase<2;phase=phase+1) begin
            @(negedge clk);rst=1;vm_valid=0;wb_ready=0;
            @(posedge clk);#1;if(vm_ready || wb_valid) $fatal(1,"commit reset");
            @(negedge clk);rst=0;
            accepted=0;received=0;ticks=0;stalled=0;v1_count=0;v2_count=0;
            while(received<256) begin
                @(negedge clk);
                wb_ready=(phase==0 || ticks%11>=3);
                vm_valid=(accepted<256 && (phase==0 || ticks%5!=1));
                if(accepted<256) begin
                    vm_v2=(phase==0 || accepted%4<2);
                    vm_f=f[accepted];vm_e=e[accepted];
                end
                @(posedge clk);ticks=ticks+1;
                if(stalled && (!wb_valid || wb_f!==held)) $fatal(1,"commit stalled writeback changed");
                if(wb_valid && wb_ready) begin
                    if(received>=accepted) $fatal(1,"unrequested commit");
                    if(phase==0 || received%4<2) begin
                        if(wb_f!==expected[received]) $fatal(1,"v2 commit mismatch");v2_count=v2_count+1;
                    end else begin
                        if(wb_f!==expected_v1[received]) $fatal(1,"v1 XOR mismatch");v1_count=v1_count+1;
                    end
                    received=received+1;
                end
                stalled=wb_valid && !wb_ready;held=wb_f;
                if(vm_valid && vm_ready) accepted=accepted+1;
                #1;
            end
            if(accepted!=256) $fatal(1,"commit accounting");
            if(phase==0 && ticks-1!=256*(16/LANES+1)) $fatal(1,"integrated throughput cycles");
            $display("PASS commit lanes=%0d phase=%0d v2=%0d v1=%0d cycles=%0d",LANES,phase,v2_count,v1_count,ticks-1);
            @(negedge clk);vm_valid=0;wb_ready=1;
            @(posedge clk);#1;if(wb_valid) $fatal(1,"duplicate commit");
        end
        $finish;
    end
endmodule
