// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_integer_transport #(parameter integer SERIAL_IADD=0);
    reg clk=0,rst=0,req_valid=0,req_v2=0;
    wire req_ready;
    reg [15:0] req_tag=0;
    reg [1:0] req_round_mode=0;
    reg [63:0] req_program_addr=0,saved_program;
    reg [511:0] req_r=0,req_f=0,req_e=0;
    wire prog_valid,prog_rsp_ready;
    reg prog_ready=0,prog_rsp_valid=0;
    wire [63:0] prog_addr;
    wire [15:0] prog_tag;
    reg [15:0] prog_rsp_tag=0;
    reg [63:0] prog_rsp_instruction=0;
    wire [15:0] mem_tag,ret_tag,error_tag,commit_tag;
    wire rd_valid,wr_valid,rsp_ready,ret_valid,error_valid,commit_valid;
    wire [20:0] rd_addr,wr_addr;
    wire [127:0] wr_data;
    wire [15:0] wr_strb;
    wire [511:0] ret_r,ret_f,ret_e,commit_r;
    wire [1:0] ret_round_mode;
    wire [8:0] error_pc,commit_pc;
    wire [7:0] error_opcode,commit_opcode;
    reg ret_ready=0;
    reg [511:0] saved_r,saved_f,saved_e;
    reg [15:0] saved_tag;
    reg [1:0] saved_mode;
    integer context_index,pc,fetches,commits,steps,pending,stale_sent,n,size,holds;
    wire [7:0] nop_opcode=8'd116+(pc%4);
    always #5 clk=~clk;
`ifdef INTEGER_EXECUTE_NETLIST
    randomx_integer_execute dut(
`else
    randomx_integer_execute #(.SERIAL_IADD(SERIAL_IADD)) dut(
`endif
        .clk(clk),.rst(rst),.req_valid(req_valid),.req_ready(req_ready),.req_tag(req_tag),
        .req_v2(req_v2),.req_round_mode(req_round_mode),.req_r(req_r),.req_f(req_f),.req_e(req_e),
        .req_a(512'b0),.req_emask0(64'b0),.req_emask1(64'b0),.req_program_addr(req_program_addr),
        .prog_valid(prog_valid),.prog_ready(prog_ready),.prog_addr(prog_addr),.prog_tag(prog_tag),
        .prog_rsp_valid(prog_rsp_valid),.prog_rsp_ready(prog_rsp_ready),.prog_rsp_tag(prog_rsp_tag),
        .prog_rsp_instruction(prog_rsp_instruction),.mem_tag(mem_tag),.rd_valid(rd_valid),.rd_ready(1'b0),
        .rd_addr(rd_addr),.rsp_valid(1'b0),.rsp_ready(rsp_ready),.rsp_tag(16'b0),.rsp_data(128'b0),
        .wr_valid(wr_valid),.wr_ready(1'b0),.wr_addr(wr_addr),.wr_data(wr_data),.wr_strb(wr_strb),
        .ret_valid(ret_valid),.ret_ready(ret_ready),.ret_tag(ret_tag),.ret_r(ret_r),.ret_f(ret_f),.ret_e(ret_e),
        .ret_round_mode(ret_round_mode),.error_valid(error_valid),.error_ready(1'b0),.error_tag(error_tag),
        .error_pc(error_pc),.error_opcode(error_opcode),.commit_valid(commit_valid),.commit_tag(commit_tag),
        .commit_pc(commit_pc),.commit_opcode(commit_opcode),.commit_r(commit_r)
    );
    initial begin #1000000;$fatal(1,"integer transport timeout");end
    initial begin
        rst=1;@(posedge clk);#1;@(negedge clk);rst=0;#1;fetches=0;commits=0;holds=0;
        for(context_index=0;context_index<8;context_index=context_index+1)begin
            req_valid=1;req_tag=16'h4000+context_index;req_v2=context_index>=4;req_round_mode=context_index%4;
            req_program_addr=64'h20000000+context_index*4096;saved_program=req_program_addr;size=req_v2?384:256;
            req_r={8{64'h8000000000000001^context_index}};
            req_f={64'h0000000000000000,64'h8000000000000000,64'h7ff0000000000000,64'hfff0000000000000,
                   64'h7ff800000000cafe,64'h7ff0000000000001,64'h0000000000000001,64'hffffffffffffffff};
            req_e=~req_f;saved_r=req_r;saved_f=req_f;saved_e=req_e;saved_tag=req_tag;saved_mode=req_round_mode;
            if(!req_ready)$fatal(1,"transport descriptor unavailable");
            @(posedge clk);#1;@(negedge clk);req_valid=0;
            // Change the inactive request bus: the captured raw fields must survive.
            req_r=~saved_r;req_f=~saved_f;req_e=~saved_e;req_round_mode=~saved_mode;
            req_tag=~saved_tag;req_v2=~req_v2;req_program_addr=~saved_program;
            pc=0;pending=0;stale_sent=0;steps=0;
            while(!ret_valid)begin
                prog_ready=!pending;prog_rsp_valid=pending;
                prog_rsp_tag=stale_sent?saved_tag:16'hffff;
                // Native ISWAP_R normalizes raw dst/src F8 modulo8 to R0; equal is a NOP.
                prog_rsp_instruction={32'b0,8'hff,8'hf8,8'hf8,nop_opcode};
                @(posedge clk);
                if(rd_valid || wr_valid || error_valid || req_ready)$fatal(1,"transport NOP program side effect/overlap");
                if(commit_valid)begin
                    if(commit_tag!==saved_tag || commit_pc!==pc || commit_opcode!==116+(pc%4) || commit_r!==saved_r)$fatal(1,"transport native swap retirement");
                    pc=pc+1;commits=commits+1;
                end
                if(prog_rsp_valid && prog_rsp_ready)begin
                    if(!stale_sent)stale_sent=1;
                    else pending=0;
                end
                if(prog_valid && prog_ready)begin
                    if(prog_addr!==saved_program+pc*8 || prog_tag!==saved_tag || pc>=size)$fatal(1,"transport actual program fetch");
                    pending=1;stale_sent=0;fetches=fetches+1;
                end
                #1;steps=steps+1;if(steps>2500)$fatal(1,"transport execution stalled");@(negedge clk);
            end
            // Last instruction commit pulse may coincide with RETURN becoming valid.
            for(n=0;n<3;n=n+1)begin
                @(posedge clk);
                if(commit_valid)begin
                    if(n!=0 || commit_pc!==size-1 || commit_r!==saved_r)$fatal(1,"transport final native commit");
                    pc=pc+1;commits=commits+1;
                end
                if(!ret_valid || req_ready || ret_tag!==saved_tag || ret_round_mode!==saved_mode ||
                    ret_r!==saved_r || ret_f!==saved_f || ret_e!==saved_e || rd_valid || wr_valid || error_valid)
                    $fatal(1,"captured raw F/E/rounding or held return changed");
                holds=holds+1;#1;@(negedge clk);
            end
            if(pc!=size)$fatal(1,"transport program length/commit coverage");
            ret_ready=1;@(posedge clk);#1;@(negedge clk);ret_ready=0;req_valid=0;
            if(!req_ready || ret_valid)$fatal(1,"transport return handshake/restart");
        end
        if(fetches!=2560 || commits!=2560 || holds!=24)$fatal(1,"transport coverage");
        $display("PASS integer_transport serial_iadd=%0d contexts=8 v1=4 v2=4 rounding_modes=4 native_swap_nops=2560 stale_program_drops=2560 return_stall_clocks=24 raw_FE_bits_preserved=1 inactive_request_bus_ignored=1",SERIAL_IADD);
        $finish;
    end
endmodule
