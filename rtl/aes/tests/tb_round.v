// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_round;
    reg [127:0] state_in, key_in, expected;
    reg decrypt;
    wire [127:0] state_out;
    integer fd, rc, direction, count;
    reg [4095:0] vector_path;
    randomx_aes_round dut (state_in,key_in,decrypt,state_out);
    initial begin
        if (!$value$plusargs("vectors=%s",vector_path)) $fatal(1,"missing vectors");
        fd=$fopen(vector_path,"r");
        if (!fd) $fatal(1,"cannot open round vectors");
        count=0;
        while (!$feof(fd)) begin
            rc=$fscanf(fd,"%d %h %h %h\n",direction,state_in,key_in,expected);
            if (rc!=4) $fatal(1,"malformed round vector %0d",count);
            decrypt=direction; #1;
            if (state_out !== expected) $fatal(1,"round mismatch %0d dec=%0d got=%h expected=%h",count,direction,state_out,expected);
            count=count+1;
        end
        if (count!=1024) $fatal(1,"missing round vectors");
        $fclose(fd);
        $display("PASS rounds=%0d",count);$finish;
    end
endmodule
