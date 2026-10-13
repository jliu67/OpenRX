// SPDX-License-Identifier: BSD-3-Clause
module tb_i32;
    reg [31:0] word_i;
    wire [63:0] actual;
    reg [63:0] gold;
    reg [4095:0] path;
    integer fd,n,rc;
    randomx_i32_to_f64 dut(.word_i(word_i),.bits_o(actual));
    initial begin
        if(!$value$plusargs("vectors=%s",path))$fatal(1,"missing signed-conversion vectors");
        fd=$fopen(path,"r");if(!fd)$fatal(1,"vector open");n=0;
        while(!$feof(fd))begin
            rc=$fscanf(fd,"%h %h\n",word_i,gold);
            if(rc!=2)$fatal(1,"bad conversion row");
            #1;if(actual!==gold)$fatal(1,"signed32 conversion input=%h actual=%h expected=%h",word_i,actual,gold);
            n=n+1;
        end
        $fclose(fd);if(n!=4096)$fatal(1,"conversion coverage");
        $display("PASS native signed32-to-binary64 vectors=4096 rounding_modes=4");$finish;
    end
endmodule
