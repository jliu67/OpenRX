// SPDX-License-Identifier: BSD-3-Clause
// VALIDATION ONLY: immutable, zero-initialization-free behavioral row storage.
// No technology, PVT, ports/area/energy, read latency or timing closure is proven.
`timescale 1ns/1ps
`default_nettype none
module prepared_fetch_sram_behavioral (
    input wire clk,
    input wire read_en,
    input wire [11:0] read_address,
    output reg read_valid=1'b0,
    output reg [255:0] read_data=256'b0,
    output reg sealed=1'b0,
    output wire [79:0] program_counts
);
    reg [255:0] rows [0:4095];
    reg [9:0] counts [0:7];
    string image_dir;
    integer i, program_number, pc;
    genvar g;
    generate for(g=0;g<8;g=g+1) begin: bind_counts
        assign program_counts[g*10+:10]=counts[g];
    end endgenerate

    // Only an admitted offline image may be loaded. There is intentionally no
    // runtime write/reload/reset port and no software service callback.
    initial begin
        if(!$value$plusargs("IMAGE_DIR=%s",image_dir))
            $fatal(1,"IMAGE_DIR is required; no fallback image");
        $readmemh({image_dir,"/rows.mem"},rows);
        $readmemh({image_dir,"/counts.mem"},counts);
        for(i=0;i<8;i=i+1)
            if((^counts[i]===1'bx)||counts[i]>10'd512)
                $fatal(1,"invalid admitted program count %0d",i);
        for(i=0;i<4096;i=i+1) begin
            program_number=i/512; pc=i%512;
            if((^rows[i]===1'bx)||rows[i][255:161]!==95'b0)
                $fatal(1,"missing/malformed/reserved row %0d",i);
            if(pc>=counts[program_number]&&rows[i]!==256'b0)
                $fatal(1,"nonzero inactive padding row %0d",i);
        end
        sealed=1'b1;
    end

    always @(posedge clk) begin
        if(read_en) begin
            if(!sealed) $fatal(1,"read before offline image admission");
            read_data<=rows[read_address];
            read_valid<=1'b1;
        end
    end
endmodule
`default_nettype wire
