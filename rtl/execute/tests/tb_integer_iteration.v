// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_integer_iteration #(parameter integer SERIAL_IADD=0,STALL=0);
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
    wire  prog_valid;
    reg  prog_ready=0;
    wire [63:0] prog_addr;
    wire [15:0] prog_tag;
    reg  prog_rsp_valid=0;
    wire  prog_rsp_ready;
    reg [15:0] prog_rsp_tag=0;
    reg [63:0] prog_rsp_instruction=0;
    wire  error_valid;
    reg  error_ready=0;
    wire [15:0] error_tag;
    wire [8:0] error_pc;
    wire [7:0] error_opcode;
    wire  commit_valid;
    wire [15:0] commit_tag;
    wire [8:0] commit_pc;
    wire [7:0] commit_opcode;
    wire [511:0] commit_r;
    always #5 clk=~clk;
`ifdef INTEGER_ITERATION_NETLIST
    randomx_integer_iteration dut(
`else
    randomx_integer_iteration #(.SERIAL_IADD(SERIAL_IADD)) dut(
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
        .done_spaddr1(done_spaddr1),
        .prog_valid(prog_valid),
        .prog_ready(prog_ready),
        .prog_addr(prog_addr),
        .prog_tag(prog_tag),
        .prog_rsp_valid(prog_rsp_valid),
        .prog_rsp_ready(prog_rsp_ready),
        .prog_rsp_tag(prog_rsp_tag),
        .prog_rsp_instruction(prog_rsp_instruction),
        .error_valid(error_valid),
        .error_ready(error_ready),
        .error_tag(error_tag),
        .error_pc(error_pc),
        .error_opcode(error_opcode),
        .commit_valid(commit_valid),
        .commit_tag(commit_tag),
        .commit_pc(commit_pc),
        .commit_opcode(commit_opcode),
        .commit_r(commit_r)
    );
    reg [127:0] ram[0:131071],gold_ram[0:131071];
    reg [63:0] programs[0:4095];
    reg [511:0] gold_steps[0:4095];
    reg [85:0] events[0:2047];
    integer versions[0:7],chains[0:7],ev_start[0:7],ev_count[0:7];
    integer read0[0:7],read1[0:7],read2[0:7],read3[0:7],round_in[0:7],round_out[0:7];
    reg [31:0] sp0[0:7],sp1[0:7],mx[0:7],ma[0:7],outmx[0:7],outma[0:7];
    reg [14:0] fline[0:7],rline[0:7];
    reg [63:0] em0[0:7],em1[0:7],offset[0:7],dsaddr[0:7],pfaddr[0:7];
    reg [511:0] rin[0:7],ain[0:7],loadr[0:7],loadf[0:7],loade[0:7];
    reg [511:0] expr[0:7],expf[0:7],expe[0:7],dsdata[0:7];
    reg [511:0] outr[0:7],outf[0:7],oute[0:7],fmem[0:7],rmem[0:7];
    reg [511:0] previous_r;
    reg [31:0] previous_mx,previous_ma;
    reg [1:0] previous_round;
    reg [4095:0] path;
    integer accepted,received,cycle,i,j,b,entry_reads,tail_writes,total_reads,total_writes;
    integer event_index,kernel_started,dataset_taken,pc_expected,total_commits,total_fetches,iadd_commits;
    integer sp_pending,sp_delay,sp_injected,prog_pending,prog_delay,prog_injected,ds_pending,ds_delay,ds_injected;
    integer rd_stall,wr_stall,prog_stall,ds_stall,done_stall,stale_sp,stale_prog,stale_ds;
    integer pc_address,program_length,aliases,expected_entry,kernel_begin_cycle,kernel_total_cycles;
    reg [127:0] sp_data_q;
    reg [15:0] sp_tag_q,prog_tag_q,ds_tag_q;
    reg [63:0] prog_data_q;
    reg [511:0] ds_data_q;
    reg held_read,held_write,held_prog,held_done;
    reg [255:0] read_payload,write_payload;
    reg [127:0] prog_payload;
    reg [4095:0] done_payload;
    wire [255:0] read_now={sp_rd_tag,sp_rd_addr};
    wire [255:0] write_now={sp_wr_tag,sp_wr_addr,sp_wr_strb,sp_wr_data};
    wire [127:0] prog_now={prog_tag,prog_addr};
    wire [4095:0] done_now={done_tag,done_round_mode,done_r,done_f,done_e,done_mx,done_ma,done_spaddr0,done_spaddr1};
    function [511:0] dataset_line;
        input [63:0] address;
        reg [63:0] x;
        integer n;
        begin
            x=address^64'hdabacafe13456789;
            for(n=0;n<8;n=n+1)begin
                x=x^(x<<13);x=x^(x>>7);x=x^(x<<17);
                dataset_line[64*n+:64]=x;
            end
        end
    endfunction
    initial begin #2000000;$fatal(1,"integer hardware execution deadlock");end
    initial begin
`include "integer_vectors.vh"
        if(!$value$plusargs("initial=%s",path))$fatal(1,"missing initial");$readmemh(path,ram);
        if(!$value$plusargs("final=%s",path))$fatal(1,"missing final");$readmemh(path,gold_ram);
        if(!$value$plusargs("programs=%s",path))$fatal(1,"missing programs");$readmemh(path,programs);
        if(!$value$plusargs("steps=%s",path))$fatal(1,"missing steps");$readmemh(path,gold_steps);
        if(!$value$plusargs("events=%s",path))$fatal(1,"missing events");$readmemh(path,events,0,TOTAL_EVENTS-1);
        rst=1;@(posedge clk);#1;@(negedge clk);rst=0;
        accepted=0;received=0;cycle=0;entry_reads=0;tail_writes=0;total_reads=0;total_writes=0;
        event_index=0;kernel_started=0;dataset_taken=0;pc_expected=0;total_commits=0;total_fetches=0;iadd_commits=0;
        sp_pending=0;sp_delay=0;sp_injected=0;prog_pending=0;prog_delay=0;prog_injected=0;
        ds_pending=0;ds_delay=0;ds_injected=0;rd_stall=0;wr_stall=0;prog_stall=0;ds_stall=0;done_stall=0;
        stale_sp=0;stale_prog=0;stale_ds=0;aliases=0;kernel_total_cycles=0;kernel_begin_cycle=0;
        held_read=0;held_write=0;held_prog=0;held_done=0;
        while(received<8)begin
            @(negedge clk);
            req_valid=accepted<8 && accepted==received;
            if(req_valid)begin
                req_tag=16'h0100+accepted;req_v2=versions[accepted];req_a=ain[accepted];
                req_r=chains[accepted]?previous_r:rin[accepted];
                req_mx=chains[accepted]?previous_mx:mx[accepted];req_ma=chains[accepted]?previous_ma:ma[accepted];
                req_round_mode=chains[accepted]?previous_round:round_in[accepted];
                req_spaddr0=sp0[accepted];req_spaddr1=sp1[accepted];
                req_read0=read0[accepted];req_read1=read1[accepted];req_read2=read2[accepted];req_read3=read3[accepted];
                req_emask0=em0[accepted];req_emask1=em1[accepted];req_dataset_offset=offset[accepted];
                req_program_addr=64'h10000000+accepted*4096;
            end
            sp_rd_ready=!sp_pending && (!STALL || rd_stall>=2);
            sp_wr_ready=!sp_pending && (!STALL || wr_stall>=2);
            prog_ready=!prog_pending && (!STALL || prog_stall>=2);
            ds_req_ready=!ds_pending && (!STALL || ds_stall>=2);
            done_ready=!STALL || done_stall>=3;
            if(sp_delay>0)sp_delay=sp_delay-1;
            sp_rsp_valid=sp_pending && sp_delay==0;sp_rsp_tag=sp_tag_q;sp_rsp_data=sp_data_q;
            if(sp_rsp_valid && STALL && !sp_injected)begin sp_rsp_tag=16'hffff;sp_rsp_data=~sp_data_q;end
            if(prog_delay>0)prog_delay=prog_delay-1;
            prog_rsp_valid=prog_pending && prog_delay==0;prog_rsp_tag=prog_tag_q;prog_rsp_instruction=prog_data_q;
            if(prog_rsp_valid && STALL && !prog_injected)begin prog_rsp_tag=16'hffff;prog_rsp_instruction=~prog_data_q;end
            if(ds_delay>0)ds_delay=ds_delay-1;
            ds_rsp_valid=ds_pending && ds_delay==0;ds_rsp_tag=ds_tag_q;ds_rsp_data=ds_data_q;
            if(ds_rsp_valid && STALL && !ds_injected)begin ds_rsp_tag=16'hffff;ds_rsp_data=~ds_data_q;end
            @(posedge clk);cycle=cycle+1;
            if(error_valid)$fatal(1,"supported program unexpectedly trapped case=%0d pc=%0d opcode=%0d",received,error_pc,error_opcode);
            if(held_read && (!sp_rd_valid || read_now!==read_payload))$fatal(1,"SP read changed under stall");
            if(held_write && (!sp_wr_valid || write_now!==write_payload))$fatal(1,"SP write changed under stall");
            if(held_prog && (!prog_valid || prog_now!==prog_payload))$fatal(1,"program request changed under stall");
            if(held_done && (!done_valid || done_now!==done_payload))$fatal(1,"integer retirement changed under stall");
            if(sp_rd_valid && sp_rd_ready && sp_wr_valid && sp_wr_ready)$fatal(1,"single-port collision");
            if(sp_rd_valid && !sp_rd_ready && !sp_pending)rd_stall=rd_stall+1;
            if(sp_wr_valid && !sp_wr_ready && !sp_pending)wr_stall=wr_stall+1;
            if(prog_valid && !prog_ready && !prog_pending)prog_stall=prog_stall+1;
            if(ds_req_valid && !ds_req_ready)ds_stall=ds_stall+1;
            if(done_valid && !done_ready)done_stall=done_stall+1;
            if(sp_rsp_valid && sp_rsp_ready)begin
                if(sp_rsp_tag==16'hffff)begin sp_injected=1;stale_sp=stale_sp+1;end
                else sp_pending=0;
            end
            if(sp_rd_valid && sp_rd_ready)begin
                if(sp_pending || sp_rd_addr[3:0]!=0 || sp_rd_tag!==16'h0100+received)$fatal(1,"SP read contract");
                if(!kernel_started)begin
                    expected_entry=fline[received]==rline[received]?4:8;
                    if(entry_reads>=expected_entry || sp_rd_addr!=={(entry_reads<4?fline[received]:rline[received]),entry_reads[1:0],4'b0})$fatal(1,"entry read address");
                    entry_reads=entry_reads+1;
                end else begin
                    if(event_index>=ev_start[received]+ev_count[received] || events[event_index][85] ||
                        sp_rd_addr!=={events[event_index][84:68],4'b0})$fatal(1,"actual RTL load address/order event=%0d",event_index);
                    if((events[event_index][67]?ram[sp_rd_addr>>4][127:64]:ram[sp_rd_addr>>4][63:0])!==events[event_index][63:0])$fatal(1,"actual memory operand differs from native");
                    event_index=event_index+1;
                end
                sp_data_q=ram[sp_rd_addr>>4];sp_tag_q=sp_rd_tag;sp_pending=1;sp_delay=STALL?3:1;sp_injected=0;
                total_reads=total_reads+1;rd_stall=0;
            end
            if(sp_wr_valid && sp_wr_ready)begin
                if(sp_wr_addr[3:0]!=0 || sp_wr_tag!==16'h0100+received)$fatal(1,"SP store contract");
                if(!dataset_taken)begin
                    if(!kernel_started || event_index>=ev_start[received]+ev_count[received] || !events[event_index][85] ||
                        sp_wr_addr!=={events[event_index][84:68],4'b0} || sp_wr_strb!==(events[event_index][67]?16'hff00:16'h00ff) ||
                        (events[event_index][67]?sp_wr_data[127:64]:sp_wr_data[63:0])!==events[event_index][63:0])
                        $fatal(1,"actual RTL store address/data/strobe/order event=%0d",event_index);
                    event_index=event_index+1;
                end else begin
                    if(tail_writes>=8 || sp_wr_strb!==16'hffff)$fatal(1,"tail store count/strobe");
                    if(tail_writes<4)begin
                        if(sp_wr_addr!=={rline[received],tail_writes[1:0],4'b0} || sp_wr_data!==outr[received][128*tail_writes+:128])$fatal(1,"hardware R dataset/tail store");
                    end else if(sp_wr_addr!=={fline[received],tail_writes[1:0],4'b0} || sp_wr_data!==outf[received][128*(tail_writes-4)+:128])$fatal(1,"hardware AES/store tail");
                    tail_writes=tail_writes+1;
                end
                for(b=0;b<16;b=b+1)if(sp_wr_strb[b])ram[sp_wr_addr>>4][8*b+:8]=sp_wr_data[8*b+:8];
                total_writes=total_writes+1;wr_stall=0;
            end
            if(commit_valid)begin
                if(commit_tag!==16'h0100+received || commit_pc!==pc_expected || commit_opcode!==programs[received*512+pc_expected][7:0] ||
                    commit_r!==gold_steps[received*512+pc_expected])$fatal(1,"actual RTL arithmetic retirement mismatch case=%0d pc=%0d opcode=%0d",received,pc_expected,commit_opcode);
                if(commit_pc==(versions[received]?383:255))kernel_total_cycles=kernel_total_cycles+cycle-kernel_begin_cycle+1;
                if(commit_opcode<16)iadd_commits=iadd_commits+1;
                pc_expected=pc_expected+1;total_commits=total_commits+1;
            end
            if(prog_rsp_valid && prog_rsp_ready)begin
                if(prog_rsp_tag==16'hffff)begin prog_injected=1;stale_prog=stale_prog+1;end
                else prog_pending=0;
            end
            if(prog_valid && prog_ready)begin
                program_length=versions[received]?384:256;pc_address=(prog_addr-(64'h10000000+received*4096))>>3;
                if(prog_pending || prog_addr[2:0]!=0 || prog_tag!==16'h0100+received || pc_address<0 || pc_address>=program_length || pc_address!=pc_expected)$fatal(1,"native program fetch address/tag/order");
                if(pc_address==0)kernel_begin_cycle=cycle;
                prog_data_q=programs[received*512+pc_address];prog_tag_q=prog_tag;prog_pending=1;prog_delay=STALL?3:1;prog_injected=0;
                total_fetches=total_fetches+1;kernel_started=1;prog_stall=0;
            end
            if(ds_rsp_valid && ds_rsp_ready)begin
                if(ds_rsp_tag==16'hffff)begin ds_injected=1;stale_ds=stale_ds+1;end
                else ds_pending=0;
            end
            if(ds_req_valid && ds_req_ready)begin
                if(dataset_taken || pc_expected!=(versions[received]?384:256) || event_index!=ev_start[received]+ev_count[received] ||
                    ds_req_tag!==16'h0100+received || ds_req_addr!==dsaddr[received] || !ds_prefetch_valid || ds_prefetch_addr!==pfaddr[received])$fatal(1,"hardware execute/dataset feedback");
                ds_data_q=dataset_line(ds_req_addr);if(ds_data_q!==dsdata[received])$fatal(1,"dataset model identity");
                ds_tag_q=ds_req_tag;ds_pending=1;ds_delay=STALL?3:1;ds_injected=0;dataset_taken=1;ds_stall=0;
            end
            held_read=sp_rd_valid && !sp_rd_ready;read_payload=read_now;
            held_write=sp_wr_valid && !sp_wr_ready;write_payload=write_now;
            held_prog=prog_valid && !prog_ready;prog_payload=prog_now;
            held_done=done_valid && !done_ready;done_payload=done_now;
            if(req_valid && req_ready)begin
                if(req_r!==rin[accepted] || req_mx!==mx[accepted] || req_ma!==ma[accepted] || req_round_mode!==round_in[accepted][1:0])$fatal(1,"hardware chain/input context");
                event_index=ev_start[accepted];accepted=accepted+1;
            end
            if(done_valid && done_ready)begin
                if(tail_writes!=8 || done_tag!==16'h0100+received || done_r!==outr[received] || done_f!==outf[received] || done_e!==oute[received] ||
                    done_mx!==outmx[received] || done_ma!==outma[received] || done_round_mode!==round_out[received][1:0] || done_spaddr0!==0 || done_spaddr1!==0)$fatal(1,"full hardware iteration result");
                for(j=0;j<4;j=j+1)if(ram[(fline[received]<<2)+j]!==fmem[received][128*j+:128] || ram[(rline[received]<<2)+j]!==rmem[received][128*j+:128])$fatal(1,"hardware scratchpad/alias result");
                if(fline[received]==rline[received])aliases=aliases+1;
                previous_r=done_r;previous_mx=done_mx;previous_ma=done_ma;previous_round=done_round_mode;
                received=received+1;entry_reads=0;tail_writes=0;kernel_started=0;dataset_taken=0;pc_expected=0;done_stall=0;
            end
            #1;
        end
        for(i=0;i<131072;i=i+1)if(ram[i]!==gold_ram[i])$fatal(1,"actual hardware full2MiB memory mismatch word=%0d",i);
        if(total_fetches!=2560 || total_commits!=2560 || total_writes!=64+BYTECODE_STORES || aliases!=4 || iadd_commits!=236)$fatal(1,"integer hardware coverage accounting");
        if(STALL && (stale_prog!=2560 || stale_sp==0 || stale_ds!=8))$fatal(1,"missing stale generation coverage");
        $display("PASS integer_hardware serial_iadd=%0d stall=%0d iterations=8 v2=4 v1=4 chains=4 aliases=4 fetched=2560 actual_RTL_retirements=2560 iadd_rs=236 native_reads=%0d native_stores=%0d tail_writes=64 full_memory_bytes=2097152 elapsed_cycles=%0d fetch_to_last_commit_cycles=%0d stale_program=%0d stale_sp=%0d stale_dataset=%0d",SERIAL_IADD,STALL,BYTECODE_READS,BYTECODE_STORES,cycle,kernel_total_cycles,stale_prog,stale_sp,stale_ds);
        $finish;
    end
endmodule
