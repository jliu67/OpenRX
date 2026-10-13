// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_arithmetic #(parameter integer RADIX4=0);
    reg clk=0,rst=0,mvalid=0,mready=0,rvalid=0,rready=0;
    wire mqready,mrsp,rqready,rrsp,rnop;
    reg [63:0] a=0,b=0,expected;
    reg high=0,signed_high=0;
    reg [31:0] divisor=0;
    reg [15:0] mtag=0,rtag=0;
    wire [15:0] mtout,rtout;
    wire [63:0] mout,rout;
    integer fd,rc,n,count,rcount,nops,latency,total_mul_clocks,total_rcp_clocks,mode;
    reg [4095:0] path;
    reg expected_nop;
    always #5 clk=~clk;
`ifdef MUL64_NETLIST
    randomx_mul64 mul(
`else
    randomx_mul64 #(.RADIX4(RADIX4)) mul(
`endif
        .clk(clk),.rst(rst),.req_valid(mvalid),.req_ready(mqready),.req_tag(mtag),.req_a(a),.req_b(b),
        .req_high(high),.req_signed(signed_high),.rsp_valid(mrsp),.rsp_ready(mready),.rsp_tag(mtout),.rsp_result(mout));
    randomx_reciprocal32 reciprocal(.clk(clk),.rst(rst),.req_valid(rvalid),.req_ready(rqready),.req_tag(rtag),
        .req_divisor(divisor),.rsp_valid(rrsp),.rsp_ready(rready),.rsp_tag(rtout),.rsp_result(rout),.rsp_nop(rnop));
    initial begin #3000000;$fatal(1,"arithmetic deadlock");end
    initial begin
        rst=1;@(posedge clk);#1;@(negedge clk);rst=0;#1;
        count=0;rcount=0;nops=0;total_mul_clocks=0;total_rcp_clocks=0;
        if(!$value$plusargs("multiply=%s",path))$fatal(1,"missing native multiply vectors");fd=$fopen(path,"r");
        while(!$feof(fd))begin
            rc=$fscanf(fd,"%h %h %h %h %h\n",a,b,high,signed_high,expected);
            if(rc!=5)$fatal(1,"multiply vector format");
            mtag=16'h1000+count;mvalid=1;mready=0;
            if(!mqready)$fatal(1,"multiply unavailable");
            @(posedge clk);#1;@(negedge clk);mvalid=0;a=~a;b=~b;high=~high;signed_high=~signed_high;
            latency=1;
            while(!mrsp)begin @(posedge clk);#1;latency=latency+1;@(negedge clk);end
            if(latency!=(RADIX4?33:1))$fatal(1,"multiply latency");total_mul_clocks=total_mul_clocks+latency;
            for(n=0;n<3;n=n+1)begin
                @(posedge clk);
                if(!mrsp || mqready || mtout!==mtag || mout!==expected)$fatal(1,"native multiply/held transport mismatch vector=%0d",count);
                #1;@(negedge clk);
            end
            mready=1;@(posedge clk);#1;@(negedge clk);mready=0;count=count+1;
        end
        $fclose(fd);if(count!=2304)$fatal(1,"multiply vector coverage");
        if(!$value$plusargs("reciprocal=%s",path))$fatal(1,"missing native reciprocal vectors");fd=$fopen(path,"r");
        while(!$feof(fd))begin
            rc=$fscanf(fd,"%h %h %h\n",divisor,expected_nop,expected);if(rc!=3)$fatal(1,"reciprocal vector format");
            rtag=16'h4000+rcount;rvalid=1;rready=0;
            if(!rqready)$fatal(1,"reciprocal unavailable");
            @(posedge clk);#1;@(negedge clk);rvalid=0;divisor=~divisor;
            latency=1;
            while(!rrsp)begin @(posedge clk);#1;latency=latency+1;@(negedge clk);end
            if(latency!=(expected_nop?1:65))$fatal(1,"reciprocal latency");total_rcp_clocks=total_rcp_clocks+latency;nops=nops+expected_nop;
            for(n=0;n<3;n=n+1)begin
                @(posedge clk);
                if(!rrsp || rqready || rtout!==rtag || rnop!==expected_nop || rout!==expected)$fatal(1,"native reciprocal/held transport mismatch divisor-vector=%0d",rcount);
                #1;@(negedge clk);
            end
            rready=1;@(posedge clk);#1;@(negedge clk);rready=0;rcount=rcount+1;
        end
        $fclose(fd);if(nops!=33 || rcount<600)$fatal(1,"reciprocal class coverage");
        // Cancel busy operations or a held direct result, then restart cleanly.
        mvalid=1;a=64'hffffffffffffffff;b=64'hffffffffffffffff;high=1;signed_high=1;
        rvalid=1;divisor=32'hffffffff;
        @(posedge clk);#1;@(negedge clk);mvalid=0;rvalid=0;
        repeat(4)begin @(posedge clk);#1;@(negedge clk);end
        rst=1;#1;if(mrsp || rrsp || mqready || rqready)$fatal(1,"arithmetic reset suppression");
        @(posedge clk);#1;@(negedge clk);rst=0;#1;
        if(!mqready || !rqready || mrsp || rrsp)$fatal(1,"arithmetic reset restart");
        repeat(70)begin @(posedge clk);#1;if(mrsp || rrsp)$fatal(1,"cancelled arithmetic leaked late response");end
        $display("PASS arithmetic radix4=%0d products=%0d reciprocal=%0d nop_divisors=%0d multiply_clocks=%0d reciprocal_clocks=%0d held_results=1 inactive_inputs_ignored=1 reset_cancel=2",RADIX4,count,rcount,nops,total_mul_clocks,total_rcp_clocks);
        $finish;
    end
endmodule
