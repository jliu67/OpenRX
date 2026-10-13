// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_engine #(parameter integer LANES=4,SERIAL_CONVERT=0,COALESCE_LINES=1,STALL=0);
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
    reg [127:0] ram[0:131071],gold_ram[0:131071];
    reg [85:0] events[0:8191];
    integer versions[0:31],chains[0:31],ev_start[0:31],ev_count[0:31];
    integer read0[0:31],read1[0:31],read2[0:31],read3[0:31],round_in[0:31],round_out[0:31];
    reg [31:0] sp0[0:31],sp1[0:31],mx[0:31],ma[0:31],outmx[0:31],outma[0:31];
    reg [14:0] fline[0:31],rline[0:31];
    reg [63:0] em0[0:31],em1[0:31],offset[0:31],dsaddr[0:31],pfaddr[0:31];
    reg [511:0] rin[0:31],ain[0:31],loadr[0:31],loadf[0:31],loade[0:31];
    reg [511:0] expr[0:31],expf[0:31],expe[0:31],dsdata[0:31];
    reg [511:0] outr[0:31],outf[0:31],oute[0:31],fmem[0:31],rmem[0:31];
    integer accepted,received,cycle,i,j,k,entry_reads,tail_writes,total_entry,total_reads,total_writes;
    integer event_index,core_wait,core_stall,rd_stall,wr_stall,ds_stall,pkt_stall,done_stall;
    integer sp_pending,sp_delay,sp_injected,ds_pending,ds_delay,ds_injected;
    integer ex_taken,ex_returned,ds_taken,accept_cycle[0:31],front_cycles,front_total,aliases;
    integer stalled_cycles,stale_sp_count,stale_ds_count,stale_ex_count,premature_blocks;
    reg [127:0] sp_data_q;reg [15:0] sp_tag_q;reg [511:0] ds_data_q;reg [15:0] ds_tag_q;
    reg [4095:0] path;
    reg held_rd,held_wr,held_packet,held_done;
    reg [255:0] rd_payload,wr_payload;
    reg [4095:0] packet_payload,done_payload;
    wire [255:0] rd_now={sp_rd_tag,sp_rd_addr};
    wire [255:0] wr_now={sp_wr_tag,sp_wr_addr,sp_wr_strb,sp_wr_data};
    wire [4095:0] pkt_now={ex_req_tag,ex_req_v2,ex_req_round_mode,ex_req_r,ex_req_f,
        ex_req_e,ex_req_a,ex_req_emask0,ex_req_emask1,ex_req_program_addr};
    wire [4095:0] done_now={done_tag,done_round_mode,done_r,done_f,done_e,done_mx,done_ma,done_spaddr0,done_spaddr1};
    reg [63:0] committed_canary;
    task start_abort_context;
        input [15:0] tag;
        begin
            @(negedge clk);req_valid=1;req_tag=tag;req_v2=1;req_r=rin[0];req_a=ain[0];
            req_spaddr0=sp0[0];req_spaddr1=sp1[0];req_mx=mx[0];req_ma=ma[0];
            req_read0=read0[0];req_read1=read1[0];req_read2=read2[0];req_read3=read3[0];
            req_emask0=em0[0];req_emask1=em1[0];req_dataset_offset=offset[0];
            req_round_mode=round_in[0];req_program_addr=64'h10000000;
            sp_rd_ready=0;sp_wr_ready=1;sp_rsp_valid=0;ds_rsp_valid=0;
            ex_ret_valid=0;ex_wr_valid=0;ex_rd_valid=0;ex_req_ready=0;done_ready=0;
            #1;if(!req_ready)$fatal(1,"abort context not ready");
            @(posedge clk);#1;@(negedge clk);req_valid=0;
        end
    endtask
    task pulse_reset;
        begin
            @(negedge clk);rst=1;
            @(posedge clk);#1;
            if(req_ready || sp_rd_valid || sp_wr_valid || ex_req_valid || ds_req_valid || done_valid || sp_rsp_ready || ds_rsp_ready || ex_ret_ready)$fatal(1,"reset handshake suppression");
            @(negedge clk);rst=0;
        end
    endtask
    task reach_execution_packet;
        integer pending,steps;
        reg [127:0] data;
        reg [15:0] tag;
        begin
            pending=0;steps=0;sp_rd_ready=1;sp_rsp_valid=0;
            while(!ex_req_valid)begin
                @(posedge clk);
                if(sp_rsp_valid && sp_rsp_ready)pending=0;
                if(sp_rd_valid && sp_rd_ready)begin pending=1;data=ram[sp_rd_addr>>4];tag=sp_rd_tag;end
                #1;steps=steps+1;if(steps>80)$fatal(1,"abort prefix did not complete");
                @(negedge clk);sp_rsp_valid=pending;sp_rsp_data=data;sp_rsp_tag=tag;
            end
            @(negedge clk);sp_rsp_valid=0;
        end
    endtask
    task abort_checks;
        integer n;
        reg [127:0] cancelled_data;
        reg [4095:0] held;
        begin
            // Abort an accepted SRAM read; late replies cannot advance a new tag.
            start_abort_context(16'hfe00);
            sp_rd_ready=1;
            @(posedge clk);if(!sp_rd_valid || !sp_rd_ready)$fatal(1,"abort read missing");
            cancelled_data=ram[sp_rd_addr>>4];#1;
            pulse_reset();
            sp_rsp_valid=1;sp_rsp_tag=16'hfe00;sp_rsp_data=cancelled_data;
            ex_ret_valid=1;ex_ret_tag=16'hfe00;ds_rsp_valid=1;ds_rsp_tag=16'hfe00;
            ex_mem_tag=16'hfe00;ex_wr_valid=1;ex_wr_addr=0;ex_wr_data=0;ex_wr_strb=16'hffff;
            @(posedge clk);#1;
            if(!sp_rsp_ready || !ds_rsp_ready || !ex_ret_ready || !ex_wr_ready || sp_wr_valid || done_valid)$fatal(1,"cancelled context not discarded");
            @(negedge clk);req_valid=1;req_tag=16'hfe01;
            @(posedge clk);#1;@(negedge clk);req_valid=0;
            for(n=0;n<4;n=n+1)begin
                @(posedge clk);#1;
                if(sp_wr_valid || ex_req_valid || ds_req_valid || done_valid)$fatal(1,"late reply advanced new context");
                if(!sp_rsp_ready || !ds_rsp_ready || !ex_ret_ready || !ex_wr_ready)$fatal(1,"late response drain blocked");
            end
            pulse_reset();sp_rsp_valid=0;ds_rsp_valid=0;ex_ret_valid=0;ex_wr_valid=0;

            // Abort a stalled execute packet, then drop its delayed completion.
            start_abort_context(16'hfe02);reach_execution_packet();held=pkt_now;
            for(n=0;n<3;n=n+1)begin
                @(posedge clk);#1;if(!ex_req_valid || pkt_now!==held)$fatal(1,"abort execution packet unstable");
            end
            pulse_reset();ex_ret_valid=1;ex_ret_tag=16'hfe02;
            for(n=0;n<3;n=n+1)begin
                @(posedge clk);#1;if(!ex_ret_ready || sp_wr_valid || ds_req_valid || done_valid)$fatal(1,"cancelled execute completion leaked");
            end
            @(negedge clk);ex_ret_valid=0;
            for(n=0;n<131072;n=n+1)if(ram[n]!==gold_ram[n])$fatal(1,"read/execute abort altered memory");

            // An already committed bytecode store survives reset without retirement.
            start_abort_context(16'hfe03);reach_execution_packet();
            ex_req_ready=1;@(posedge clk);#1;@(negedge clk);ex_req_ready=0;
            ex_mem_tag=16'hfe03;ex_wr_valid=1;ex_wr_addr=0;ex_wr_strb=16'h00ff;
            committed_canary=~ram[0][63:0];ex_wr_data={64'b0,committed_canary};
            @(posedge clk);
            if(!ex_wr_ready || !sp_wr_valid || sp_wr_data!==ex_wr_data || sp_wr_strb!==16'h00ff)$fatal(1,"abort committed store missing");
            ram[0][63:0]=sp_wr_data[63:0];#1;
            pulse_reset();ex_wr_valid=0;
            for(n=0;n<3;n=n+1)begin @(posedge clk);#1;if(sp_wr_valid || done_valid || ds_req_valid)$fatal(1,"aborted writer leaked");end
            if(ram[0]!=={gold_ram[0][127:64],committed_canary})$fatal(1,"reset rolled back committed bytes");
            for(n=1;n<131072;n=n+1)if(ram[n]!==gold_ram[n])$fatal(1,"abort touched uncommitted bytes");
        end
    endtask
    initial begin #10000000;$fatal(1,"engine deadlock");end
    initial begin
`include "case_vectors.vh"
        if(!$value$plusargs("initial=%s",path))$fatal(1,"missing initial");$readmemh(path,ram);
        if(!$value$plusargs("final=%s",path))$fatal(1,"missing final");$readmemh(path,gold_ram);
        if(!$value$plusargs("events=%s",path))$fatal(1,"missing events");$readmemh(path,events,0,TOTAL_EVENTS-1);
        rst=1;@(posedge clk);#1;@(negedge clk);rst=0;
        accepted=0;received=0;cycle=0;entry_reads=0;tail_writes=0;total_entry=0;total_reads=0;total_writes=0;
        event_index=0;core_wait=0;core_stall=0;rd_stall=0;wr_stall=0;ds_stall=0;pkt_stall=0;done_stall=0;
        sp_pending=0;sp_delay=0;sp_injected=0;ds_pending=0;ds_delay=0;ds_injected=0;
        ex_taken=0;ex_returned=0;ds_taken=0;front_total=0;aliases=0;stalled_cycles=0;
        stale_sp_count=0;stale_ds_count=0;stale_ex_count=0;premature_blocks=0;
        held_rd=0;held_wr=0;held_packet=0;held_done=0;
        while(received<32)begin
            @(negedge clk);
            req_valid=accepted<32;
            if(accepted<32)begin
                req_tag=16'h0100+accepted;req_v2=versions[accepted];req_r=rin[accepted];req_a=ain[accepted];
                req_spaddr0=sp0[accepted];req_spaddr1=sp1[accepted];req_mx=mx[accepted];req_ma=ma[accepted];
                req_read0=read0[accepted];req_read1=read1[accepted];req_read2=read2[accepted];req_read3=read3[accepted];
                req_emask0=em0[accepted];req_emask1=em1[accepted];req_dataset_offset=offset[accepted];
                req_round_mode=round_in[accepted];req_program_addr=64'h10000000+accepted*4096;
            end
            if(sp_delay>0)sp_delay=sp_delay-1;
            sp_rsp_valid=sp_pending && sp_delay==0;
            sp_rsp_data=sp_data_q;sp_rsp_tag=sp_tag_q;
            if(sp_rsp_valid && STALL && !sp_injected)begin sp_rsp_tag=16'hffff;sp_rsp_data=~sp_data_q;end
            sp_rd_ready=!sp_pending && (!STALL || rd_stall>=2);
            sp_wr_ready=!sp_pending && (!STALL || wr_stall>=2);
            ex_req_ready=!ex_taken && (!STALL || pkt_stall>=2);
            ex_rd_valid=0;ex_wr_valid=0;ex_rsp_ready=!STALL || core_stall>=2;
            ex_mem_tag=16'h0100+received;ex_ret_tag=16'h0100+received;
            ex_ret_r=expr[received];ex_ret_f=expf[received];ex_ret_e=expe[received];ex_ret_round_mode=round_out[received];
            ex_ret_valid=ex_taken && !ex_returned && event_index==ev_start[received]+ev_count[received];
            if(ex_taken && !ex_returned && event_index<ev_start[received]+ev_count[received])begin
                if(events[event_index][85])begin
                    ex_wr_valid=1;ex_wr_addr={events[event_index][84:68],4'b0};
                    ex_wr_strb=events[event_index][67] ? 16'hff00 :16'h00ff;
                    ex_wr_data=events[event_index][67] ? {events[event_index][63:0],64'b0}:{64'b0,events[event_index][63:0]};
                end else if(!core_wait)begin
                    ex_rd_valid=1;ex_rd_addr={events[event_index][84:68],4'b0};
                end
                // Deliberately present the completed register bundle before the final memory operation drains.
                if(STALL && event_index==ev_start[received]+ev_count[received]-1)ex_ret_valid=1;
            end
            // A cancelled execution may send late traffic during the new context's entry.
            if(STALL && !ex_taken)begin
                ex_ret_valid=1;ex_ret_tag=16'hffff;ex_mem_tag=16'hffff;
                ex_wr_valid=1;ex_wr_addr=0;ex_wr_data=0;ex_wr_strb=16'hffff;
            end
            ds_req_ready=!ds_pending && (!STALL || ds_stall>=2);
            if(ds_delay>0)ds_delay=ds_delay-1;
            ds_rsp_valid=ds_pending && ds_delay==0;ds_rsp_data=ds_data_q;ds_rsp_tag=ds_tag_q;
            if(ds_rsp_valid && STALL && !ds_injected)begin ds_rsp_tag=16'hffff;ds_rsp_data=~ds_data_q;end
            done_ready=!STALL || done_stall>=3;
            @(posedge clk);cycle=cycle+1;
            if(held_rd && (!sp_rd_valid || rd_now!==rd_payload))$fatal(1,"read request changed under stall");
            if(held_wr && (!sp_wr_valid || wr_now!==wr_payload))$fatal(1,"write changed under stall");
            if(held_packet && (!ex_req_valid || pkt_now!==packet_payload))$fatal(1,"execution packet changed under stall");
            if(held_done && (!done_valid || done_now!==done_payload))$fatal(1,"retirement changed under stall");
            if(sp_rd_valid && sp_rd_ready && sp_wr_valid && sp_wr_ready)$fatal(1,"single-port command collision");
            if(sp_rd_valid && !sp_rd_ready && !sp_pending)rd_stall=rd_stall+1;
            if(sp_wr_valid && !sp_wr_ready && !sp_pending)wr_stall=wr_stall+1;
            if(ex_req_valid && !ex_req_ready)pkt_stall=pkt_stall+1;
            if(ex_rsp_valid && !ex_rsp_ready)core_stall=core_stall+1;
            if(ds_req_valid && !ds_req_ready)ds_stall=ds_stall+1;
            if(done_valid && !done_ready)done_stall=done_stall+1;
            if(ex_ret_valid && ex_ret_tag!=16'hffff && !ex_ret_ready)premature_blocks=premature_blocks+1;
            if(sp_rsp_valid && sp_rsp_ready)begin
                if(sp_rsp_tag==16'hffff)begin sp_injected=1;stale_sp_count=stale_sp_count+1;end
                else sp_pending=0;
            end
            if(sp_rd_valid && sp_rd_ready)begin
                if(sp_pending || sp_rd_addr[3:0]!=0 || sp_rd_tag!==16'h0100+received)$fatal(1,"bad scratchpad read");
                if(!ex_taken)begin
                    if(entry_reads>=(COALESCE_LINES && fline[received]==rline[received]?4:8))$fatal(1,"excess entry read");
                    if(sp_rd_addr!=={(entry_reads<4?fline[received]:rline[received]),entry_reads[1:0],4'b0})$fatal(1,"entry address");
                    entry_reads=entry_reads+1;total_entry=total_entry+1;
                end else if(!ex_rd_valid || sp_rd_addr!==ex_rd_addr)$fatal(1,"execution read routing");
                sp_data_q=ram[sp_rd_addr>>4];sp_tag_q=sp_rd_tag;sp_pending=1;sp_delay=STALL?3:1;sp_injected=0;
                total_reads=total_reads+1;rd_stall=0;
            end
            if(ex_rd_valid && ex_rd_ready && ex_mem_tag!=16'hffff)core_wait=1;
            if(ex_rsp_valid && ex_rsp_ready)begin
                if(!core_wait || ex_rsp_tag!==16'h0100+received)$fatal(1,"unrequested execution response");
                if((events[event_index][67] ? ex_rsp_data[127:64]:ex_rsp_data[63:0])!==events[event_index][63:0])$fatal(1,"actual bytecode load data mismatch event %0d",event_index);
                event_index=event_index+1;core_wait=0;core_stall=0;
            end
            if(sp_wr_valid && sp_wr_ready)begin
                if(sp_wr_addr[3:0]!=0 || sp_wr_tag!==16'h0100+received)$fatal(1,"bad scratchpad write");
                if(ex_taken && !ex_returned)begin
                    if(!ex_wr_valid || ex_mem_tag==16'hffff || sp_wr_addr!==ex_wr_addr || sp_wr_data!==ex_wr_data || sp_wr_strb!==ex_wr_strb)$fatal(1,"execution write routing");
                end else begin
                    if(!ds_taken || tail_writes>=8 || sp_wr_strb!==16'hffff)$fatal(1,"unrequested tail write");
                    if(tail_writes<4)begin
                        if(sp_wr_addr!=={rline[received],tail_writes[1:0],4'b0} || sp_wr_data!==outr[received][128*tail_writes+:128])$fatal(1,"tail R data/order");
                    end else if(sp_wr_addr!=={fline[received],tail_writes[1:0],4'b0} || sp_wr_data!==outf[received][128*(tail_writes-4)+:128])$fatal(1,"tail F data/order");
                    tail_writes=tail_writes+1;
                end
                for(k=0;k<16;k=k+1)if(sp_wr_strb[k])ram[sp_wr_addr>>4][8*k+:8]=sp_wr_data[8*k+:8];
                total_writes=total_writes+1;wr_stall=0;
            end
            if(ex_wr_valid && ex_wr_ready && ex_mem_tag!=16'hffff)event_index=event_index+1;
            if(ex_req_valid && ex_req_ready)begin
                if(ex_taken || ex_req_tag!==16'h0100+received || ex_req_v2!==versions[received][0])$fatal(1,"bad execution request");
                if(ex_req_r!==loadr[received] || ex_req_f!==loadf[received] || ex_req_e!==loade[received] || ex_req_a!==ain[received])$fatal(1,"native R/F/E/A operand formation mismatch case %0d",received);
                if(ex_req_emask0!==em0[received] || ex_req_emask1!==em1[received] || ex_req_program_addr!==64'h10000000+received*4096 || ex_req_round_mode!==round_in[received][1:0])$fatal(1,"execution descriptor");
                front_cycles=cycle-accept_cycle[received];front_total=front_total+front_cycles;
                if(!STALL && front_cycles!=2*entry_reads+1+16*SERIAL_CONVERT)$fatal(1,"front cycles got %0d",front_cycles);
                ex_taken=1;event_index=ev_start[received];pkt_stall=0;
            end
            if(ex_ret_valid && ex_ret_ready)begin
                if(ex_ret_tag==16'hffff)stale_ex_count=stale_ex_count+1;
                else begin
                    if(!ex_taken || ex_returned || core_wait || event_index!=ev_start[received]+ev_count[received])$fatal(1,"kernel return before memory drain");
                    ex_returned=1;
                end
            end
            if(ds_rsp_valid && ds_rsp_ready)begin
                if(ds_rsp_tag==16'hffff)begin ds_injected=1;stale_ds_count=stale_ds_count+1;end
                else ds_pending=0;
            end
            if(ds_req_valid && ds_req_ready)begin
                if(!ex_returned || ds_taken || ds_req_tag!==16'h0100+received || ds_req_addr!==dsaddr[received] || !ds_prefetch_valid || ds_prefetch_addr!==pfaddr[received])$fatal(1,"dataset read/prefetch address or order");
                ds_pending=1;ds_delay=STALL?3:1;ds_data_q=dsdata[received];ds_tag_q=ds_req_tag;ds_injected=0;ds_taken=1;ds_stall=0;
            end
            held_rd=sp_rd_valid && !sp_rd_ready;rd_payload=rd_now;
            held_wr=sp_wr_valid && !sp_wr_ready;wr_payload=wr_now;
            held_packet=ex_req_valid && !ex_req_ready;packet_payload=pkt_now;
            held_done=done_valid && !done_ready;done_payload=done_now;
            if(req_valid && req_ready)begin accept_cycle[accepted]=cycle;accepted=accepted+1;end
            if(done_valid && done_ready)begin
                if(tail_writes!=8 || done_tag!==16'h0100+received || done_r!==outr[received] || done_f!==outf[received] || done_e!==oute[received] || done_mx!==outmx[received] || done_ma!==outma[received] || done_round_mode!==round_out[received][1:0] || done_spaddr0!==0 || done_spaddr1!==0)$fatal(1,"architectural retirement case %0d",received);
                for(j=0;j<4;j=j+1)if(ram[(fline[received]<<2)+j]!==fmem[received][128*j+:128] || ram[(rline[received]<<2)+j]!==rmem[received][128*j+:128])$fatal(1,"iteration regions/alias");
                if(fline[received]==rline[received])aliases=aliases+1;
                if(chains[received] && received>0 && (rin[received]!==outr[received-1] || mx[received]!==outmx[received-1] || ma[received]!==outma[received-1] || round_in[received]!=round_out[received-1] || sp0[received]!=0 || sp1[received]!=0))$fatal(1,"chain context mismatch");
                received=received+1;entry_reads=0;tail_writes=0;ex_taken=0;ex_returned=0;ds_taken=0;done_stall=0;core_wait=0;
            end
            #1;
        end
        if(total_reads!=total_entry+BYTECODE_READS || total_writes!=256+BYTECODE_STORES || accepted!=32)$fatal(1,"memory accounting");
        if(STALL && (stale_sp_count==0 || stale_ds_count!=32 || stale_ex_count==0 || premature_blocks==0))$fatal(1,"missing adverse-channel coverage");
        for(i=0;i<131072;i=i+1)if(ram[i]!==gold_ram[i])$fatal(1,"full2MiB memory mismatch word %0d",i);
        @(negedge clk);req_valid=0;ex_ret_valid=0;ex_wr_valid=0;ex_rd_valid=0;done_ready=1;
        @(posedge clk);#1;if(done_valid || sp_wr_valid || sp_rd_valid || ex_req_valid || ds_req_valid)$fatal(1,"duplicate completion/command");
        abort_checks();
        $display("PASS engine lanes=%0d serial=%0d coalesce=%0d stall=%0d iterations=32 v2=16 v1=16 chained=16 aliases=%0d entry_reads=%0d bytecode_reads=%0d bytecode_stores=%0d tail_writes=256 full_memory_bytes=2097152 reset_aborts=3 committed_abort_writes=1 front_total_cycles=%0d elapsed_cycles=%0d stale_sp=%0d stale_ds=%0d stale_ex=%0d premature_blocks=%0d",LANES,SERIAL_CONVERT,COALESCE_LINES,STALL,aliases,total_entry,BYTECODE_READS,BYTECODE_STORES,front_total,cycle,stale_sp_count,stale_ds_count,stale_ex_count,premature_blocks);
        $finish;
    end
endmodule
