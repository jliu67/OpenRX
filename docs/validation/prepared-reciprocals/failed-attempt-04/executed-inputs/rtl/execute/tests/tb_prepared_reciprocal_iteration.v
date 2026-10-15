// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
module tb_prepared_reciprocal_iteration #(parameter integer PREPARED_RCP=1,STALL=0);
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
    wire prog_ready;
    wire [63:0] prog_addr;
    wire [15:0] prog_tag;
    wire prog_rsp_valid;
    wire  prog_rsp_ready;
    wire [15:0] prog_rsp_tag;
    wire [63:0] prog_rsp_instruction;
    wire  error_valid;
    reg  error_ready=0;
    wire [15:0] error_tag;
    wire [8:0] error_pc;
    wire [7:0] error_opcode;
    wire  commit_valid;
    wire [15:0] commit_tag;
    wire [8:0] commit_pc;
    wire [7:0] commit_opcode;
    wire [511:0] commit_r,commit_f,commit_e;wire [1:0] commit_round_mode;
    wire [8:0] commit_next_pc,commit_branch_target;
    reg cancel=0,exec_cancel=0,prep_valid=0,prep_rsp_ready=0,prep_v2=0;
    reg [15:0] prep_epoch=0,req_program_epoch=0;reg [63:0] prep_program_addr=0;
    wire prep_ready,prep_rsp_valid,prep_rsp_error,image_valid,image_v2;
    wire [15:0] prep_rsp_epoch,image_epoch;wire [63:0] image_program_addr;
    wire load_req_valid,load_rsp_ready;reg load_req_ready=0,load_rsp_valid=0,load_rsp_error=0;
    wire [63:0] load_req_addr;wire [24:0] load_req_tag;
    reg [24:0] load_rsp_tag=0;reg [63:0] load_rsp_instruction=0;wire [1:0] error_reason;
    always #5 clk=~clk;
    randomx_prepared_integer_iteration #(.PREPARED_RCP(PREPARED_RCP),.SERIAL_IADD(0),.FP_LANES(2),.DIVSQRT_LANES(2)) dut(
        .cancel(cancel),.exec_cancel(exec_cancel),.req_program_epoch(req_program_epoch),
        .prep_valid(prep_valid),.prep_ready(prep_ready),.prep_epoch(prep_epoch),.prep_v2(prep_v2),.prep_program_addr(prep_program_addr),
        .load_req_valid(load_req_valid),.load_req_ready(load_req_ready),.load_req_addr(load_req_addr),.load_req_tag(load_req_tag),
        .load_rsp_valid(load_rsp_valid),.load_rsp_ready(load_rsp_ready),.load_rsp_tag(load_rsp_tag),
        .load_rsp_instruction(load_rsp_instruction),.load_rsp_error(load_rsp_error),
        .prep_rsp_valid(prep_rsp_valid),.prep_rsp_ready(prep_rsp_ready),.prep_rsp_epoch(prep_rsp_epoch),.prep_rsp_error(prep_rsp_error),
        .image_valid(image_valid),.image_epoch(image_epoch),.image_v2(image_v2),.image_program_addr(image_program_addr),.error_reason(error_reason),
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
        .error_valid(error_valid),
        .error_ready(error_ready),
        .error_tag(error_tag),
        .error_pc(error_pc),
        .error_opcode(error_opcode),
        .commit_valid(commit_valid),
        .commit_tag(commit_tag),
        .commit_pc(commit_pc),
        .commit_opcode(commit_opcode),
        .commit_r(commit_r),.commit_f(commit_f),.commit_e(commit_e),.commit_round_mode(commit_round_mode),.commit_next_pc(commit_next_pc),.commit_branch_target(commit_branch_target)
    );
    // Observe the real cache/execute packets; expected plans never feed them.
    assign prog_valid=dut.prog_valid;assign prog_ready=dut.prog_ready;
    assign prog_addr=dut.prog_addr;assign prog_tag=dut.prog_tag;
    assign prog_rsp_valid=dut.prog_rsp_valid;assign prog_rsp_ready=dut.prog_rsp_ready;
    assign prog_rsp_tag=dut.prog_rsp_tag;assign prog_rsp_instruction=dut.prog_rsp_instruction;
`include "prepared_reciprocal_sizes.vh"
    reg [127:0] ram[0:131071],gold_ram[0:131071];
    reg [63:0] programs[0:TOTAL_PROGRAM_WORDS-1];
    reg [97:0] native_plan[0:TOTAL_PROGRAM_WORDS-1];
    reg [1563:0] gold_steps[0:TOTAL_STEPS-1];reg [8:0] compiled_targets[0:TOTAL_PROGRAM_WORDS-1];
    reg [85:0] events[0:TOTAL_EVENTS-1];
    integer versions[0:TOTAL_ITERATIONS-1],chains[0:TOTAL_ITERATIONS-1],ev_start[0:TOTAL_ITERATIONS-1],ev_count[0:TOTAL_ITERATIONS-1];
    integer read0[0:TOTAL_ITERATIONS-1],read1[0:TOTAL_ITERATIONS-1],read2[0:TOTAL_ITERATIONS-1],read3[0:TOTAL_ITERATIONS-1];
    integer round_in[0:TOTAL_ITERATIONS-1],round_out[0:TOTAL_ITERATIONS-1],step_start[0:TOTAL_ITERATIONS-1],step_count[0:TOTAL_ITERATIONS-1];
    integer program_index[0:TOTAL_ITERATIONS-1],admission_end[0:TOTAL_ITERATIONS-1];
    integer static_rcp_count[0:TOTAL_ITERATIONS-1],static_active_rcp_count[0:TOTAL_ITERATIONS-1];
    integer dynamic_rcp_count[0:TOTAL_ITERATIONS-1],dynamic_active_rcp_count[0:TOTAL_ITERATIONS-1];
    reg [63:0] program_addr[0:TOTAL_ITERATIONS-1];
    reg [31:0] sp0[0:TOTAL_ITERATIONS-1],sp1[0:TOTAL_ITERATIONS-1],mx[0:TOTAL_ITERATIONS-1],ma[0:TOTAL_ITERATIONS-1];
    reg [31:0] outmx[0:TOTAL_ITERATIONS-1],outma[0:TOTAL_ITERATIONS-1];
    reg [14:0] fline[0:TOTAL_ITERATIONS-1],rline[0:TOTAL_ITERATIONS-1];
    reg [63:0] em0[0:TOTAL_ITERATIONS-1],em1[0:TOTAL_ITERATIONS-1],offset[0:TOTAL_ITERATIONS-1];
    reg [63:0] dsaddr[0:TOTAL_ITERATIONS-1],pfaddr[0:TOTAL_ITERATIONS-1];
    reg [511:0] rin[0:TOTAL_ITERATIONS-1],ain[0:TOTAL_ITERATIONS-1],loadr[0:TOTAL_ITERATIONS-1];
    reg [511:0] loadf[0:TOTAL_ITERATIONS-1],loade[0:TOTAL_ITERATIONS-1],expr[0:TOTAL_ITERATIONS-1];
    reg [511:0] expf[0:TOTAL_ITERATIONS-1],expe[0:TOTAL_ITERATIONS-1],dsdata[0:TOTAL_ITERATIONS-1];
    reg [511:0] outr[0:TOTAL_ITERATIONS-1],outf[0:TOTAL_ITERATIONS-1],oute[0:TOTAL_ITERATIONS-1];
    reg [511:0] fmem[0:TOTAL_ITERATIONS-1],rmem[0:TOTAL_ITERATIONS-1];
    reg [511:0] previous_r;reg [31:0] previous_mx,previous_ma;reg [1:0] previous_round;
    string directory,path,metrics_path;
    reg [1023:0] metrics_error;
    integer cycles=0,received=0,admission=0,preparations=0,loaded_words=0,reloads=0;
    integer program_length=0,load_count=0,load_matches=0,load_pending=0,load_delay=0,load_stale_phase=0,load_stall=0;
    integer load_stale_errors=0,prep_begin=0,prep_response_clocks=0,prep_wall=0,exec_wall=0,control_wall=0;
    integer prep_phase[0:5],exec_phase[0:17],controller_phase[0:11];
    integer prep_rcp_requests=0,runtime_rcp_requests=0,prep_req_stall=0,prep_rsp_wait=0;
    integer launch_clocks=0,entry_clocks=0,kernel_clocks=0,dataset_clocks=0,tail_clocks=0,return_clocks=0;
    integer sp_req_wait=0,sp_reply_wait=0,sp_store_wait=0,ds_req_wait=0,ds_reply_wait=0,done_hold_wait=0;
    integer cache_fetch_req_wait=0,cache_fetch_reply_wait=0,tail_aes_wait=0;
    integer sp_pending=0,sp_delay=0,sp_injected=0,ds_pending=0,ds_delay=0,ds_injected=0;
    integer rd_stall=0,wr_stall=0,ds_stall=0,done_stall=0,stale_sp=0,stale_ds=0;
    integer event_index=0,step_index=0,pc_expected=0,pc_address=0,entry_reads=0,tail_writes=0;
    integer kernel_started=0,dataset_taken=0,total_reads=0,total_writes=0,total_fetches=0,total_commits=0;
    integer rcp_commits=0,rcp_active=0,rcp_nops=0,iteration_rcp=0,iteration_active_rcp=0;
    integer aliases=0,total_tail_writes=0,i,j,b,n,control_mode=0,local_guards=0,exec_cancels=0;
    integer load_state,core_state=0,phase,outside_clocks,metrics_fd=0,metrics_errno;
    integer ownership_exec_cancels=0,ownership_whole_cancels=0,ownership_resets=0;
    integer ownership_active=0,ownership_held=0,control_program_reads=0,control_commits=0,control_stores=0,control_late_replies=0;
    integer record_first=0,record_prep=0,record_prep_response=0,record_exec=0,record_entry=0,record_kernel=0,record_dataset=0,record_tail=0;
    integer record_launch=0,record_return=0,record_loads=0,record_commits=0,record_dynamic=0,record_active=0,record_nop=0;
    integer record_prep_s3=0,record_prep_s4=0,record_ex_s12=0,record_ex_s13=0,record_prep_rcp=0,record_runtime_rcp=0;
    integer admission_preparation[0:TOTAL_ADMISSIONS-1],admission_prep_response[0:TOTAL_ADMISSIONS-1],admission_execution[0:TOTAL_ADMISSIONS-1];
    integer admission_entry[0:TOTAL_ADMISSIONS-1],admission_kernel[0:TOTAL_ADMISSIONS-1],admission_dataset[0:TOTAL_ADMISSIONS-1];
    integer admission_tail[0:TOTAL_ADMISSIONS-1],admission_launch[0:TOTAL_ADMISSIONS-1],admission_return[0:TOTAL_ADMISSIONS-1];
    integer admission_reads[0:TOTAL_ADMISSIONS-1],admission_commits[0:TOTAL_ADMISSIONS-1],admission_static[0:TOTAL_ADMISSIONS-1],admission_static_active[0:TOTAL_ADMISSIONS-1];
    integer admission_dynamic[0:TOTAL_ADMISSIONS-1],admission_active[0:TOTAL_ADMISSIONS-1],admission_nop[0:TOTAL_ADMISSIONS-1];
    integer admission_prep_s3[0:TOTAL_ADMISSIONS-1],admission_prep_s4[0:TOTAL_ADMISSIONS-1],admission_ex_s12[0:TOTAL_ADMISSIONS-1],admission_ex_s13[0:TOTAL_ADMISSIONS-1];
    integer admission_prep_rcp[0:TOTAL_ADMISSIONS-1],admission_runtime_rcp[0:TOTAL_ADMISSIONS-1],admission_version[0:TOTAL_ADMISSIONS-1];
    reg [15:0] control_late_tag=0;
    reg [15:0] active_epoch=0,active_tag=0,sp_tag_q=0,ds_tag_q=0;
    reg [24:0] load_tag_q=0;reg [63:0] load_word_q=0;
    reg [127:0] sp_data_q=0;reg [511:0] ds_data_q=0;reg [97:0] expected_plan;
    reg held_read=0,held_write=0,held_prog=0,held_done=0,held_load=0,held_fetch_rsp=0;
    reg [255:0] read_payload,write_payload;reg [127:0] prog_payload;reg [4095:0] done_payload;
    reg [88:0] load_payload;reg [203:0] fetch_rsp_payload;
    wire [255:0] read_now={sp_rd_tag,sp_rd_addr};
    wire [255:0] write_now={sp_wr_tag,sp_wr_addr,sp_wr_strb,sp_wr_data};
    wire [127:0] prog_now={prog_tag,prog_addr};
    wire [4095:0] done_now={done_tag,done_round_mode,done_r,done_f,done_e,done_mx,done_ma,done_spaddr0,done_spaddr1};
    wire [88:0] load_now={load_req_tag,load_req_addr};
    wire [203:0] fetch_rsp_now={prog_rsp_tag,dut.prog_rsp_prepared_epoch,dut.prog_rsp_prepared_pc,
      prog_rsp_instruction,dut.prog_rsp_rcp_valid,dut.prog_rsp_rcp_nop,dut.prog_rsp_rcp_divisor,dut.prog_rsp_rcp_value,dut.prog_rsp_prepared_error};
    wire prep_rcp_accepted;
    generate if(PREPARED_RCP)begin: observed_preparation
      assign prep_rcp_accepted=dut.cache.prepared.reciprocal.req_valid&&dut.cache.prepared.reciprocal.req_ready;
    end else begin: observed_baseline
      assign prep_rcp_accepted=1'b0;
    end endgenerate
    always @(posedge clk)cycles=cycles+1;

    function [511:0] dataset_line;input [63:0] address;reg [63:0] x;integer word_index;begin
      x=address^64'hdabacafe13456789;
      for(word_index=0;word_index<8;word_index=word_index+1)begin x=x^(x<<13);x=x^(x>>7);x=x^(x<<17);dataset_line[64*word_index+:64]=x;end
    end endfunction

    // Outer phases are disjoint and sum to measured preparation/execution time.
    // FSM and transport counters below are nested observers, not extra clocks
    // to add on top of the outer ledger.
    task account;input preparing;begin
      if(preparing)begin
        prep_wall=prep_wall+1;load_state=dut.cache.state_q;
        if((^dut.cache.state_q)===1'bx||load_state<0||load_state>5)$fatal(1,"unknown cache phase");
        prep_phase[load_state]=prep_phase[load_state]+1;
        if(prep_rcp_accepted)prep_rcp_requests=prep_rcp_requests+1;
        if(load_req_valid&&!load_req_ready)prep_req_stall=prep_req_stall+1;
        if(load_state==2)prep_rsp_wait=prep_rsp_wait+1;
      end else begin
        exec_wall=exec_wall+1;phase=dut.iteration.controller.phase_q;
        if((^dut.iteration.controller.phase_q)===1'bx||phase<0||phase>11)$fatal(1,"unknown iteration phase");
        controller_phase[phase]=controller_phase[phase]+1;
        if(done_valid)return_clocks=return_clocks+1;
        else if(phase==0)launch_clocks=launch_clocks+1;
        else if(phase<=6)entry_clocks=entry_clocks+1;
        else if(phase==7)kernel_clocks=kernel_clocks+1;
        else if(phase<=9)dataset_clocks=dataset_clocks+1;
        else tail_clocks=tail_clocks+1;
        if(phase==7)begin
          core_state=dut.iteration.execute.state_q;
          if((^dut.iteration.execute.state_q)===1'bx||core_state<0||core_state>17)$fatal(1,"unknown execution phase");
          exec_phase[core_state]=exec_phase[core_state]+1;
        end
        if(dut.iteration.execute.reciprocal.req_valid&&dut.iteration.execute.reciprocal.req_ready)runtime_rcp_requests=runtime_rcp_requests+1;
        if(sp_rd_valid&&!sp_rd_ready)sp_req_wait=sp_req_wait+1;
        if(sp_pending)sp_reply_wait=sp_reply_wait+1;
        if(sp_wr_valid&&!sp_wr_ready)sp_store_wait=sp_store_wait+1;
        if(ds_req_valid&&!ds_req_ready)ds_req_wait=ds_req_wait+1;
        if(ds_pending)ds_reply_wait=ds_reply_wait+1;
        if(done_valid&&!done_ready)done_hold_wait=done_hold_wait+1;
        if(prog_valid&&!prog_ready)cache_fetch_req_wait=cache_fetch_req_wait+1;
        if(core_state==2&&phase==7)cache_fetch_reply_wait=cache_fetch_reply_wait+1;
        if(phase==11&&!done_valid&&!dut.iteration.controller.tail.core_valid)tail_aes_wait=tail_aes_wait+1;
      end
    end endtask

    task begin_record;begin
      record_first=received;record_prep=prep_wall;record_prep_response=prep_response_clocks;record_exec=exec_wall;
      record_launch=launch_clocks;record_entry=entry_clocks;record_kernel=kernel_clocks;record_dataset=dataset_clocks;
      record_tail=tail_clocks;record_return=return_clocks;record_loads=loaded_words;record_commits=total_commits;
      record_dynamic=rcp_commits;record_active=rcp_active;record_nop=rcp_nops;
      record_prep_s3=prep_phase[3];record_prep_s4=prep_phase[4];record_ex_s12=exec_phase[12];record_ex_s13=exec_phase[13];
      record_prep_rcp=prep_rcp_requests;record_runtime_rcp=runtime_rcp_requests;
    end endtask
    task finish_record;begin
      if(received-record_first+1!=ITERATIONS_PER_ADMISSION||program_index[record_first]!=admission)$fatal(1,"admission record boundary");
      admission_preparation[admission]=prep_wall-record_prep;admission_prep_response[admission]=prep_response_clocks-record_prep_response;
      admission_execution[admission]=exec_wall-record_exec;admission_launch[admission]=launch_clocks-record_launch;
      admission_entry[admission]=entry_clocks-record_entry;admission_kernel[admission]=kernel_clocks-record_kernel;
      admission_dataset[admission]=dataset_clocks-record_dataset;admission_tail[admission]=tail_clocks-record_tail;
      admission_return[admission]=return_clocks-record_return;admission_reads[admission]=loaded_words-record_loads;
      admission_commits[admission]=total_commits-record_commits;admission_static[admission]=static_rcp_count[record_first];
      admission_static_active[admission]=static_active_rcp_count[record_first];admission_version[admission]=versions[record_first];
      admission_dynamic[admission]=rcp_commits-record_dynamic;admission_active[admission]=rcp_active-record_active;admission_nop[admission]=rcp_nops-record_nop;
      admission_prep_s3[admission]=prep_phase[3]-record_prep_s3;admission_prep_s4[admission]=prep_phase[4]-record_prep_s4;
      admission_ex_s12[admission]=exec_phase[12]-record_ex_s12;admission_ex_s13[admission]=exec_phase[13]-record_ex_s13;
      admission_prep_rcp[admission]=prep_rcp_requests-record_prep_rcp;admission_runtime_rcp[admission]=runtime_rcp_requests-record_runtime_rcp;
      if(admission_execution[admission]!=admission_launch[admission]+admission_entry[admission]+admission_kernel[admission]+
         admission_dataset[admission]+admission_tail[admission]+admission_return[admission])$fatal(1,"per-admission outer execution ledger");
      if(admission_reads[admission]!=(versions[record_first]?384:256))$fatal(1,"per-admission complete program load count");
    end endtask

    // The driver supplies an output path; fixture DIR remains read-only.
    // Top-level integers intentionally match PASS fields. Wait observers are
    // nested in the outer clocks and must never be added to them a second time.
    task write_metrics;begin
      if(metrics_path!="")begin
        metrics_fd=$fopen(metrics_path,"w");if(metrics_fd==0)$fatal(1,"cannot create METRICS output");
        $fdisplay(metrics_fd,"{");
        $fdisplay(metrics_fd,"\"schema_version\":1,\"prepared\":%0d,\"stall\":%0d,\"control\":%0d,",PREPARED_RCP,STALL,control_mode);
        $fdisplay(metrics_fd,"\"admissions\":%0d,\"iterations\":%0d,\"reloads\":%0d,\"program_reads\":%0d,\"retirements\":%0d,",TOTAL_ADMISSIONS,TOTAL_ITERATIONS,reloads,loaded_words,total_commits);
        $fdisplay(metrics_fd,"\"static_rcp\":%0d,\"static_active_rcp\":%0d,\"dynamic_rcp\":%0d,\"dynamic_active_rcp\":%0d,\"dynamic_nop_rcp\":%0d,",TOTAL_STATIC_RCP,TOTAL_STATIC_ACTIVE_RCP,rcp_commits,rcp_active,rcp_nops);
        $fdisplay(metrics_fd,"\"preparation_rcp_requests\":%0d,\"runtime_rcp_requests\":%0d,",prep_rcp_requests,runtime_rcp_requests);
        $fdisplay(metrics_fd,"\"preparation_clocks\":%0d,\"preparation_response_clocks\":%0d,\"execution_clocks\":%0d,",prep_wall,prep_response_clocks,exec_wall);
        $fdisplay(metrics_fd,"\"launch_clocks\":%0d,\"entry_clocks\":%0d,\"kernel_clocks\":%0d,\"dataset_clocks\":%0d,\"tail_clocks\":%0d,\"return_clocks\":%0d,",launch_clocks,entry_clocks,kernel_clocks,dataset_clocks,tail_clocks,return_clocks);
        $fdisplay(metrics_fd,"\"control_clocks\":%0d,\"outside_clocks\":%0d,\"elapsed_cycles\":%0d,",control_wall,outside_clocks,cycles);
        for(j=0;j<6;j=j+1)$fdisplay(metrics_fd,"\"prep_s%0d\":%0d,",j,prep_phase[j]);
        for(j=0;j<18;j=j+1)$fdisplay(metrics_fd,"\"ex_s%0d\":%0d,",j,exec_phase[j]);
        $fdisplay(metrics_fd,"\"controller_phase_clocks\":[%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d],",controller_phase[0],controller_phase[1],controller_phase[2],controller_phase[3],controller_phase[4],controller_phase[5],controller_phase[6],controller_phase[7],controller_phase[8],controller_phase[9],controller_phase[10],controller_phase[11]);
        $fdisplay(metrics_fd,"\"prep_request_stall\":%0d,\"prep_reply_wait\":%0d,\"sp_request_stall\":%0d,\"sp_reply_wait\":%0d,\"sp_store_stall\":%0d,",prep_req_stall,prep_rsp_wait,sp_req_wait,sp_reply_wait,sp_store_wait);
        $fdisplay(metrics_fd,"\"dataset_request_stall\":%0d,\"dataset_reply_wait\":%0d,\"return_hold_wait\":%0d,\"fetch_request_stall\":%0d,\"fetch_reply_wait\":%0d,\"tail_aes_wait\":%0d,",ds_req_wait,ds_reply_wait,done_hold_wait,cache_fetch_req_wait,cache_fetch_reply_wait,tail_aes_wait);
        $fdisplay(metrics_fd,"\"scratchpad_reads\":%0d,\"scratchpad_writes\":%0d,\"tail_writes\":%0d,\"stale_load\":%0d,\"stale_sp\":%0d,\"stale_dataset\":%0d,",total_reads,total_writes,total_tail_writes,load_stale_errors,stale_sp,stale_ds);
        $fdisplay(metrics_fd,"\"local_metadata_errors\":%0d,\"exec_cancels\":%0d,\"ownership_exec_cancels\":%0d,\"ownership_whole_cancels\":%0d,\"ownership_resets\":%0d,",local_guards,exec_cancels,ownership_exec_cancels,ownership_whole_cancels,ownership_resets);
        $fdisplay(metrics_fd,"\"ownership_active\":%0d,\"ownership_held\":%0d,\"control_program_reads\":%0d,\"control_commits\":%0d,\"control_stores\":%0d,\"control_late_replies\":%0d,",ownership_active,ownership_held,control_program_reads,control_commits,control_stores,control_late_replies);
        $fdisplay(metrics_fd,"\"full_memory_bytes\":2097152,\"native_RFE_round_control\":1,\"immutable_metadata_assertions_only\":1,\"full_hash_measured\":0,\"wait_observers_are_nested\":true,");
        $fdisplay(metrics_fd,"\"admission_records\":[");
        for(j=0;j<TOTAL_ADMISSIONS;j=j+1)begin
          $fdisplay(metrics_fd,"{\"admission\":%0d,\"v2\":%0d,\"epoch\":%0d,\"iterations\":%0d,\"program_reads\":%0d,\"retirements\":%0d,",j,admission_version[j],16'h3000+j,ITERATIONS_PER_ADMISSION,admission_reads[j],admission_commits[j]);
          $fdisplay(metrics_fd,"\"static_rcp\":%0d,\"static_active_rcp\":%0d,\"dynamic_rcp\":%0d,\"dynamic_active_rcp\":%0d,\"dynamic_nop_rcp\":%0d,",admission_static[j],admission_static_active[j],admission_dynamic[j],admission_active[j],admission_nop[j]);
          $fdisplay(metrics_fd,"\"preparation_clocks\":%0d,\"preparation_response_clocks\":%0d,\"execution_clocks\":%0d,",admission_preparation[j],admission_prep_response[j],admission_execution[j]);
          $fdisplay(metrics_fd,"\"launch_clocks\":%0d,\"entry_clocks\":%0d,\"kernel_clocks\":%0d,\"dataset_clocks\":%0d,\"tail_clocks\":%0d,\"return_clocks\":%0d,",admission_launch[j],admission_entry[j],admission_kernel[j],admission_dataset[j],admission_tail[j],admission_return[j]);
          $fdisplay(metrics_fd,"\"prep_s3\":%0d,\"prep_s4\":%0d,\"ex_s12\":%0d,\"ex_s13\":%0d,\"preparation_rcp_requests\":%0d,\"runtime_rcp_requests\":%0d}%0s",admission_prep_s3[j],admission_prep_s4[j],admission_ex_s12[j],admission_ex_s13[j],admission_prep_rcp[j],admission_runtime_rcp[j],j==TOTAL_ADMISSIONS-1?"":",");
        end
        $fdisplay(metrics_fd,"]}");metrics_errno=$ferror(metrics_fd,metrics_error);
        if(metrics_errno!=0)$fatal(1,"METRICS output write failed: %0s",metrics_error);$fclose(metrics_fd);metrics_fd=0;
      end
    end endtask

    task load_step;begin
      @(negedge clk);load_req_ready=!load_pending&&(!STALL||load_stall>=2);
      load_rsp_valid=0;load_rsp_error=0;
      if(load_pending)begin
        if(load_delay>0)load_delay=load_delay-1;
        else begin
          load_rsp_valid=1;load_rsp_tag=load_tag_q;load_rsp_instruction=load_word_q;
          if(load_stale_phase==1)begin load_rsp_tag={active_epoch^16'h8000,load_tag_q[8:0]};load_rsp_instruction=~load_word_q;load_rsp_error=1;end
          else if(load_stale_phase==2)begin load_rsp_tag={active_epoch,load_tag_q[8:0]^9'd1};load_rsp_instruction=~load_word_q;load_rsp_error=1;end
        end
      end
      @(posedge clk);account(1);
      if(held_load&&(!load_req_valid||load_now!==load_payload))$fatal(1,"held admission load changed");
      held_load=load_req_valid&&!load_req_ready;load_payload=load_now;
      if(load_req_valid&&!load_req_ready)load_stall=load_stall+1;
      if(load_rsp_valid&&load_rsp_ready)begin
        if(!load_pending)$fatal(1,"admission adapter lost outstanding read");
        if(load_stale_phase!=0)begin load_stale_errors=load_stale_errors+1;load_stale_phase=load_stale_phase==1?2:0;load_delay=1;end
        else begin load_pending=0;load_matches=load_matches+1;end
      end
      if(load_req_valid&&load_req_ready)begin
        if(load_pending||load_count>=program_length||load_req_tag!=={active_epoch,load_count[8:0]}||load_req_addr!==program_addr[received]+load_count*8)$fatal(1,"admission word address/epoch/index");
        load_tag_q=load_req_tag;load_word_q=programs[admission*512+load_count];load_pending=1;
        load_delay=STALL?2+(load_count%2):0;load_stale_phase=STALL?(load_count==0?1:load_count==program_length-1?2:0):0;
        load_count=load_count+1;loaded_words=loaded_words+1;load_stall=0;
      end
      #1;if(image_valid&&(load_count!=program_length||load_matches!=program_length||load_pending))$fatal(1,"partial immutable admission visible");
      if(error_valid||commit_valid||sp_rd_valid||sp_wr_valid||ds_req_valid||done_valid)$fatal(1,"preparation leaked execution");
      if(cycles-prep_begin>100000)$fatal(1,"admission preparation timeout");
    end endtask

    task prepare_admission;begin
      admission=program_index[received];active_epoch=16'h3000+admission;program_length=versions[received]?384:256;
      load_count=0;load_matches=0;load_pending=0;load_delay=0;load_stale_phase=0;load_stall=0;held_load=0;
      @(negedge clk);prep_valid=1;prep_epoch=active_epoch;prep_v2=versions[received];prep_program_addr=program_addr[received];
      if(!prep_ready||req_valid)$fatal(1,"new immutable admission not reserved");
      @(posedge clk);account(1);#1;prep_begin=cycles;prep_valid=0;
      prep_epoch=~active_epoch;prep_v2=~versions[received][0];prep_program_addr=~program_addr[received];
      while(!prep_rsp_valid)load_step;
      prep_response_clocks=prep_response_clocks+cycles-prep_begin;
      if(prep_rsp_error||prep_rsp_epoch!==active_epoch||!image_valid||image_epoch!==active_epoch||
         image_v2!==versions[received][0]||image_program_addr!==program_addr[received]||load_count!=program_length||load_matches!=program_length)$fatal(1,"complete immutable admission metadata");
      repeat(4)begin @(negedge clk);load_rsp_valid=0;@(posedge clk);account(1);#1;if(!prep_rsp_valid||prep_rsp_error||prep_rsp_epoch!==active_epoch||req_ready)$fatal(1,"held admission acknowledgment");end
      @(negedge clk);prep_rsp_ready=1;@(posedge clk);account(1);#1;prep_rsp_ready=0;
      if(prep_rsp_valid||!prep_ready||!req_ready)$fatal(1,"admission acknowledgment release");
      preparations=preparations+1;reloads=reloads+1;
    end endtask

    task set_request;begin
      req_tag=active_tag;req_v2=versions[received];req_program_epoch=active_epoch;req_program_addr=program_addr[received];
      req_r=chains[received]?previous_r:rin[received];req_a=ain[received];
      req_mx=chains[received]?previous_mx:mx[received];req_ma=chains[received]?previous_ma:ma[received];
      req_round_mode=chains[received]?previous_round:round_in[received];
      req_spaddr0=sp0[received];req_spaddr1=sp1[received];req_read0=read0[received];req_read1=read1[received];
      req_read2=read2[received];req_read3=read3[received];req_emask0=em0[received];req_emask1=em1[received];req_dataset_offset=offset[received];
    end endtask
    task poison_request;begin
      req_tag=~active_tag;req_v2=~req_v2;req_program_epoch=~active_epoch;req_program_addr=~req_program_addr;
      req_r=~req_r;req_a=~req_a;req_mx=~req_mx;req_ma=~req_ma;req_round_mode=~req_round_mode;
      req_spaddr0=~req_spaddr0;req_spaddr1=~req_spaddr1;req_read0=~req_read0;req_read1=~req_read1;
      req_read2=~req_read2;req_read3=~req_read3;req_emask0=~req_emask0;req_emask1=~req_emask1;req_dataset_offset=~req_dataset_offset;
    end endtask

    task descriptor_guards;
      integer why,start;
      begin
        for(why=0;why<3;why=why+1)begin
          @(negedge clk);active_tag=16'he000+why;set_request;req_valid=1;start=cycles;
          case(why)0:req_program_epoch=active_epoch^16'd1;1:req_program_addr=program_addr[received]+8;2:req_v2=~versions[received][0];endcase
          if(!req_ready)$fatal(1,"metadata guard request not ready");
          @(posedge clk);#1;req_valid=0;poison_request;
          repeat(4)begin
            @(negedge clk);prep_valid=1;
            #1;if(!error_valid||error_reason!==1||error_tag!==active_tag||error_pc!==0||error_opcode!==0||prep_ready||req_ready||
              sp_rd_valid||sp_wr_valid||ds_req_valid||prog_valid||commit_valid||done_valid||load_req_valid)$fatal(1,"held local epoch/base/version error");
            @(posedge clk);#1;
          end
          @(negedge clk);prep_valid=0;error_ready=1;@(posedge clk);#1;error_ready=0;
          if(error_valid||!req_ready||!image_valid||image_epoch!==active_epoch)$fatal(1,"metadata error altered immutable reservation");
          control_wall=control_wall+cycles-start;local_guards=local_guards+1;
        end
        // Cancel before the first accepted entry load: no native store or
        // retirement may occur, and exec_cancel must retain the prepared image.
        @(negedge clk);active_tag=16'hf101;set_request;req_valid=1;start=cycles;
        @(posedge clk);#1;req_valid=0;poison_request;
        while(!sp_rd_valid)begin @(posedge clk);#1;if(commit_valid||sp_wr_valid||error_valid||done_valid)$fatal(1,"early cancel escaped entry phase");end
        repeat(3)begin @(negedge clk);prep_valid=1;#1;if(prep_ready||!sp_rd_valid||sp_rd_tag!==active_tag)$fatal(1,"active execution admitted replacement");@(posedge clk);#1;end
        @(negedge clk);exec_cancel=1;prep_valid=0;
        #1;if(sp_rd_valid||sp_wr_valid||prog_valid||commit_valid||done_valid||error_valid)$fatal(1,"execution cancel suppression");
        @(posedge clk);#1;@(negedge clk);exec_cancel=0;
        sp_rsp_valid=1;sp_rsp_tag=active_tag;sp_rsp_data=~128'b0;
        repeat(3)begin @(posedge clk);#1;if(!req_ready||!image_valid||image_epoch!==active_epoch||sp_rd_valid||sp_wr_valid||commit_valid||done_valid||error_valid)$fatal(1,"late canceled execution contaminated image");end
        @(negedge clk);sp_rsp_valid=0;control_wall=control_wall+cycles-start;exec_cancels=exec_cancels+1;
      end
    endtask

    // These control images run only after all native RAM comparisons. Their
    // separate zero-data memory provider never reads or writes native ram[];
    // preparation, retirement and clocks are explicitly control-only metrics.
    task control_image;input integer trial;
      integer start,count,matched_control_reads,pending;
      reg [24:0] pending_tag;
      begin
        start=cycles;count=0;matched_control_reads=0;pending=0;
        active_epoch=16'he100+trial;active_tag=16'hf200+trial;
        @(negedge clk);prep_valid=1;prep_epoch=active_epoch;prep_v2=0;prep_program_addr=64'h04000000+trial*4096;
        req_valid=0;sp_rd_ready=0;sp_wr_ready=0;ds_req_ready=0;sp_rsp_valid=0;ds_rsp_valid=0;done_ready=0;
        load_req_ready=0;load_rsp_valid=0;prep_rsp_ready=0;
        if(!prep_ready)$fatal(1,"ownership control image reservation");
        @(posedge clk);#1;prep_valid=0;prep_epoch=~active_epoch;prep_v2=1;prep_program_addr=3;
        while(!prep_rsp_valid)begin
          @(negedge clk);load_req_ready=!pending;load_rsp_valid=pending;load_rsp_tag=pending_tag;
          load_rsp_instruction={32'b0,8'b0,8'hf8,8'hf8,8'd76};load_rsp_error=0;
          @(posedge clk);
          if(load_rsp_valid&&load_rsp_ready)begin pending=0;matched_control_reads=matched_control_reads+1;end
          if(load_req_valid&&load_req_ready)begin
            if(pending||count>=256||load_req_addr!==64'h04000000+trial*4096+count*8||load_req_tag!=={active_epoch,count[8:0]})$fatal(1,"control image word identity");
            pending=1;pending_tag=load_req_tag;count=count+1;control_program_reads=control_program_reads+1;
          end
          #1;if(image_valid&&(count!=256||matched_control_reads!=256||pending))$fatal(1,"partial ownership control image");
          if(sp_rd_valid||sp_wr_valid||commit_valid||done_valid||error_valid||ds_req_valid)$fatal(1,"control image leaked execution");
          if(cycles-start>5000)$fatal(1,"ownership control preparation timeout");
        end
        if(prep_rsp_error||prep_rsp_epoch!==active_epoch||!image_valid||image_epoch!==active_epoch||image_v2||
           image_program_addr!==64'h04000000+trial*4096||count!=256||matched_control_reads!=256)$fatal(1,"ownership control image completion");
        @(negedge clk);load_rsp_valid=0;load_req_ready=0;prep_rsp_ready=1;
        @(posedge clk);#1;prep_rsp_ready=0;
        control_wall=control_wall+cycles-start;
      end
    endtask

    task control_execution;input held_completion;input integer stop_kind;
      integer start,reads,writes,committed,pending,ds_p,finished;
      reg [15:0] pending_tag,ds_pending_tag;
      reg [4095:0] saved_done;
      begin
        start=cycles;reads=0;writes=0;committed=0;pending=0;ds_p=0;finished=0;
        @(negedge clk);req_valid=1;req_tag=active_tag;req_program_epoch=active_epoch;req_program_addr=image_program_addr;
        req_v2=0;req_round_mode=3;req_r=0;req_a=0;req_mx=0;req_ma=0;req_spaddr0=0;req_spaddr1=0;
        req_read0=0;req_read1=0;req_read2=0;req_read3=0;req_emask0=0;req_emask1=0;req_dataset_offset=0;
        sp_rd_ready=0;sp_wr_ready=0;ds_req_ready=0;sp_rsp_valid=0;ds_rsp_valid=0;done_ready=0;
        if(!req_ready)$fatal(1,"ownership control execution reservation");
        @(posedge clk);#1;req_valid=0;poison_request;
        // Deliver an earlier canceled tag after fresh capture, before any
        // matching entry reply. A new generation is used for every image/tag.
        if(control_late_tag!=0)repeat(2)begin
          @(negedge clk);sp_rsp_valid=1;sp_rsp_tag=control_late_tag;sp_rsp_data=~128'b0;
          ds_rsp_valid=1;ds_rsp_tag=control_late_tag;ds_rsp_data=~512'b0;
          #1;if(!sp_rsp_ready||!ds_rsp_ready||commit_valid||done_valid||error_valid||sp_wr_valid)$fatal(1,"late canceled reply after fresh capture");
          @(posedge clk);control_late_replies=control_late_replies+2;#1;
        end
        while(!finished)begin
          @(negedge clk);prep_valid=1;prep_epoch=16'hffff;prep_v2=1;prep_program_addr=3;
          sp_rd_ready=!pending;sp_wr_ready=held_completion&&!pending;ds_req_ready=held_completion&&!ds_p;
          sp_rsp_valid=held_completion&&pending;sp_rsp_tag=pending_tag;sp_rsp_data=0;
          ds_rsp_valid=held_completion&&ds_p;ds_rsp_tag=ds_pending_tag;ds_rsp_data=0;
          @(posedge clk);
          if(prep_ready||load_req_valid||prep_rsp_valid||!image_valid||image_epoch!==active_epoch||error_valid)$fatal(1,"active control admitted image replacement");
          if(sp_rsp_valid&&sp_rsp_ready)pending=0;
          if(sp_rd_valid&&sp_rd_ready)begin
            if(pending||sp_rd_tag!==active_tag||sp_rd_addr[3:0]!=0||reads>=4)$fatal(1,"ownership control entry read");
            pending=1;pending_tag=sp_rd_tag;reads=reads+1;
          end
          if(ds_rsp_valid&&ds_rsp_ready)ds_p=0;
          if(ds_req_valid&&ds_req_ready)begin
            if(ds_p||ds_req_tag!==active_tag||committed!=256)$fatal(1,"ownership control dataset request");
            ds_p=1;ds_pending_tag=ds_req_tag;
          end
          if(sp_wr_valid&&sp_wr_ready)begin
            if(!held_completion||sp_wr_tag!==active_tag||sp_wr_strb!==16'hffff||writes>=8)$fatal(1,"ownership control tail store");
            writes=writes+1;control_stores=control_stores+1;
          end
          if(commit_valid)begin
            if(!held_completion||commit_tag!==active_tag||commit_pc!==committed||commit_opcode!==8'd76||
               commit_next_pc!==committed+1||{commit_round_mode,commit_e,commit_f,commit_r}!=={2'd3,1536'b0})$fatal(1,"ownership control exact RCP NOP retirement");
            committed=committed+1;control_commits=control_commits+1;
          end
          #1;
          if((held_completion&&done_valid)||(!held_completion&&reads==1))finished=1;
          if(cycles-start>5000)$fatal(1,"ownership control execution timeout");
        end
        if(held_completion)begin
          if(reads!=4||writes!=8||committed!=256||pending||ds_p||done_tag!==active_tag)$fatal(1,"ownership held completion setup");
          saved_done=done_now;
          repeat(4)begin
            @(negedge clk);sp_rsp_valid=0;ds_rsp_valid=0;
            #1;if(!done_valid||done_now!==saved_done||prep_ready||req_ready||commit_valid||load_req_valid)$fatal(1,"ownership held completion changed");
            @(posedge clk);#1;
          end
          ownership_held=ownership_held+1;
        end else begin
          repeat(2)begin @(negedge clk);sp_rd_ready=0;#1;if(done_valid||commit_valid||sp_wr_valid||prep_ready)$fatal(1,"ownership active cancellation boundary");@(posedge clk);#1;end
          ownership_active=ownership_active+1;
        end
        @(negedge clk);prep_valid=0;sp_rd_ready=0;sp_wr_ready=0;ds_req_ready=0;sp_rsp_valid=0;ds_rsp_valid=0;
        case(stop_kind)0:exec_cancel=1;1:cancel=1;2:rst=1;endcase
        #1;if(req_ready||prep_ready||sp_rd_valid||sp_wr_valid||ds_req_valid||prog_valid||commit_valid||done_valid||error_valid)$fatal(1,"ownership reset/cancel suppression");
        if(stop_kind==0)begin if(!image_valid||image_epoch!==active_epoch)$fatal(1,"exec_cancel invalidated reusable image");end
        else if(image_valid)$fatal(1,"whole reset/cancel retained image");
        @(posedge clk);#1;@(negedge clk);rst=0;cancel=0;exec_cancel=0;
        control_late_tag=active_tag;sp_rsp_valid=1;sp_rsp_tag=control_late_tag;sp_rsp_data=~128'b0;
        ds_rsp_valid=1;ds_rsp_tag=control_late_tag;ds_rsp_data=~512'b0;
        repeat(3)begin
          #1;if(!req_ready||!prep_ready||!sp_rsp_ready||!ds_rsp_ready||sp_rd_valid||sp_wr_valid||ds_req_valid||prog_valid||commit_valid||done_valid||error_valid)$fatal(1,"ownership late canceled response/release");
          if(image_valid!==(stop_kind==0))$fatal(1,"ownership logical image cancellation");
          @(posedge clk);control_late_replies=control_late_replies+2;#1;@(negedge clk);
        end
        sp_rsp_valid=0;ds_rsp_valid=0;
        case(stop_kind)0:ownership_exec_cancels=ownership_exec_cancels+1;1:ownership_whole_cancels=ownership_whole_cancels+1;2:ownership_resets=ownership_resets+1;endcase
        control_wall=control_wall+cycles-start;
      end
    endtask

    task ownership_controls;integer trial;begin
      control_late_tag=16'hf101;
      for(trial=0;trial<6;trial=trial+1)begin control_image(trial);control_execution(trial>=3,trial%3);end
      if(ownership_exec_cancels!=2||ownership_whole_cancels!=2||ownership_resets!=2||ownership_active!=3||ownership_held!=3||
         control_program_reads!=6*256||control_commits!=3*256||control_stores!=3*8||control_late_replies!=6*10)$fatal(1,"ownership cancellation coverage");
    end endtask

    task execute_iteration;
      integer finished;
      reg done_taken;
      begin
        active_tag=16'h0100+received;event_index=ev_start[received];step_index=step_start[received];pc_expected=0;
        entry_reads=0;tail_writes=0;kernel_started=0;dataset_taken=0;iteration_rcp=0;iteration_active_rcp=0;
        sp_pending=0;sp_delay=0;sp_injected=0;ds_pending=0;ds_delay=0;ds_injected=0;
        rd_stall=0;wr_stall=0;ds_stall=0;done_stall=0;held_read=0;held_write=0;held_prog=0;held_done=0;held_fetch_rsp=0;
        @(negedge clk);set_request;req_valid=1;done_ready=0;
        if(!req_ready||!image_valid||image_epoch!==active_epoch)$fatal(1,"native immutable iteration not ready");
        if(req_r!==rin[received]||req_mx!==mx[received]||req_ma!==ma[received]||req_round_mode!==round_in[received][1:0])$fatal(1,"DUT-derived iteration chain/input");
        @(posedge clk);account(0);#1;req_valid=0;poison_request;finished=0;
        while(!finished)begin
          @(negedge clk);
          // All stalls depend on request ordinals, not elapsed time. Faster RCP
          // execution cannot change the paired memory profile or dataset bytes.
          sp_rd_ready=!sp_pending&&(!STALL||rd_stall>=2);sp_wr_ready=!sp_pending&&(!STALL||wr_stall>=2);
          ds_req_ready=!ds_pending&&(!STALL||ds_stall>=2);done_ready=done_stall>=4;
          if(sp_delay>0)sp_delay=sp_delay-1;
          sp_rsp_valid=sp_pending&&sp_delay==0;sp_rsp_tag=sp_tag_q;sp_rsp_data=sp_data_q;
          if(sp_rsp_valid&&STALL&&!sp_injected)begin sp_rsp_tag=16'hffff;sp_rsp_data=~sp_data_q;end
          if(ds_delay>0)ds_delay=ds_delay-1;
          ds_rsp_valid=ds_pending&&ds_delay==0;ds_rsp_tag=ds_tag_q;ds_rsp_data=ds_data_q;
          if(ds_rsp_valid&&STALL&&!ds_injected)begin ds_rsp_tag=16'hffff;ds_rsp_data=~ds_data_q;end
          prep_valid=1;prep_epoch=16'hffff;prep_v2=~versions[received][0];prep_program_addr=3;
          @(posedge clk);account(0);done_taken=done_valid&&done_ready;
          if(error_valid)$fatal(1,"native prepared execution error case=%0d reason=%0d pc=%0d op=%0d",received,error_reason,error_pc,error_opcode);
          if(prep_ready||load_req_valid||prep_rsp_valid||!image_valid||image_epoch!==active_epoch||image_v2!==versions[received][0]||image_program_addr!==program_addr[received])$fatal(1,"active/held native execution lost immutable reservation");
          if(held_read&&(!sp_rd_valid||read_now!==read_payload))$fatal(1,"held scratchpad read changed");
          if(held_write&&(!sp_wr_valid||write_now!==write_payload))$fatal(1,"held scratchpad store changed");
          if(held_prog&&(!prog_valid||prog_now!==prog_payload))$fatal(1,"held immutable fetch changed");
          if(held_done&&(!done_valid||done_now!==done_payload))$fatal(1,"held native result changed");
          if(held_fetch_rsp&&(!prog_rsp_valid||fetch_rsp_now!==fetch_rsp_payload))$fatal(1,"held prepared packet changed");
          if(sp_rd_valid&&sp_rd_ready&&sp_wr_valid&&sp_wr_ready)$fatal(1,"single-port scratchpad collision");
          if(sp_rd_valid&&!sp_rd_ready&&!sp_pending)rd_stall=rd_stall+1;
          if(sp_wr_valid&&!sp_wr_ready&&!sp_pending)wr_stall=wr_stall+1;
          if(ds_req_valid&&!ds_req_ready)ds_stall=ds_stall+1;
          if(done_valid&&!done_ready)done_stall=done_stall+1;
          if(sp_rsp_valid&&sp_rsp_ready)begin if(sp_rsp_tag==16'hffff)begin sp_injected=1;stale_sp=stale_sp+1;end else sp_pending=0;end
          if(sp_rd_valid&&sp_rd_ready)begin
            if(sp_pending||sp_rd_addr[3:0]!=0||sp_rd_tag!==active_tag)$fatal(1,"native scratchpad read identity");
            if(!kernel_started)begin
              if(entry_reads>=(fline[received]==rline[received]?4:8)||sp_rd_addr!=={(entry_reads<4?fline[received]:rline[received]),entry_reads[1:0],4'b0})$fatal(1,"native entry read address");
              entry_reads=entry_reads+1;
            end else begin
              if(event_index>=ev_start[received]+ev_count[received]||events[event_index][85]||sp_rd_addr!=={events[event_index][84:68],4'b0}||
                (events[event_index][67]?ram[sp_rd_addr>>4][127:64]:ram[sp_rd_addr>>4][63:0])!==events[event_index][63:0])$fatal(1,"native bytecode read address/order/data");
              event_index=event_index+1;
            end
            sp_data_q=ram[sp_rd_addr>>4];sp_tag_q=sp_rd_tag;sp_pending=1;sp_delay=STALL?3:1;sp_injected=0;rd_stall=0;total_reads=total_reads+1;
          end
          if(sp_wr_valid&&sp_wr_ready)begin
            if(sp_wr_addr[3:0]!=0||sp_wr_tag!==active_tag)$fatal(1,"native store identity");
            if(!dataset_taken)begin
              if(!kernel_started||event_index>=ev_start[received]+ev_count[received]||!events[event_index][85]||sp_wr_addr!=={events[event_index][84:68],4'b0}||
                sp_wr_strb!==(events[event_index][67]?16'hff00:16'h00ff)||
                (events[event_index][67]?sp_wr_data[127:64]:sp_wr_data[63:0])!==events[event_index][63:0])$fatal(1,"native bytecode store address/order/data");
              event_index=event_index+1;
            end else begin
              if(tail_writes>=8||sp_wr_strb!==16'hffff)$fatal(1,"native tail store count");
              if(tail_writes<4)begin
                if(sp_wr_addr!=={rline[received],tail_writes[1:0],4'b0}||sp_wr_data!==outr[received][128*tail_writes+:128])$fatal(1,"native R tail");
              end else if(sp_wr_addr!=={fline[received],tail_writes[1:0],4'b0}||sp_wr_data!==outf[received][128*(tail_writes-4)+:128])$fatal(1,"native AES/F tail");
              tail_writes=tail_writes+1;total_tail_writes=total_tail_writes+1;
            end
            for(b=0;b<16;b=b+1)if(sp_wr_strb[b])ram[sp_wr_addr>>4][8*b+:8]=sp_wr_data[8*b+:8];
            total_writes=total_writes+1;wr_stall=0;
          end
          // A registered retirement pulse can share the next FETCH_REQ edge.
          // Advance the native PC before validating that next request/packet,
          // matching the accepted tb_divsqrt_iteration observer ordering.
          if(commit_valid)begin
            if(step_index>=step_start[received]+step_count[received]||commit_tag!==active_tag||commit_pc!==pc_expected||
              commit_pc!==gold_steps[step_index][1563:1555]||commit_next_pc!==gold_steps[step_index][1554:1546]||
              commit_opcode!==gold_steps[step_index][1545:1538]||{commit_round_mode,commit_e,commit_f,commit_r}!==gold_steps[step_index][1537:0]||
              commit_branch_target!==compiled_targets[admission*512+pc_expected])$fatal(1,"native exact retirement case=%0d step=%0d pc=%0d",received,step_index,pc_expected);
            if(commit_opcode>=76&&commit_opcode<84)begin
              rcp_commits=rcp_commits+1;iteration_rcp=iteration_rcp+1;
              if(native_plan[admission*512+pc_expected][96])rcp_nops=rcp_nops+1;
              else begin rcp_active=rcp_active+1;iteration_active_rcp=iteration_active_rcp+1;end
            end
            pc_expected=commit_next_pc;step_index=step_index+1;total_commits=total_commits+1;
          end
          if(prog_valid&&prog_ready)begin
            pc_address=(prog_addr-program_addr[received])>>3;
            if(prog_tag!==active_tag||prog_addr[2:0]!=0||pc_address<0||pc_address>=(versions[received]?384:256)||pc_address!=pc_expected)$fatal(1,"dynamic immutable fetch order case=%0d admission=%0d step=%0d expected_pc=%0d fetched_pc=%0d addr=%016h base=%016h tag=%04h expected_tag=%04h epoch=%04h core_state=%0d commit_valid=%0d commit_pc=%0d commit_next=%0d",received,admission,step_index,pc_expected,pc_address,prog_addr,program_addr[received],prog_tag,active_tag,active_epoch,dut.iteration.execute.state_q,commit_valid,commit_pc,commit_next_pc);
            total_fetches=total_fetches+1;kernel_started=1;
          end
          if(prog_rsp_valid&&prog_rsp_ready)begin
            expected_plan=PREPARED_RCP?native_plan[admission*512+pc_expected]:98'b0;
            if(prog_rsp_tag!==active_tag||prog_rsp_instruction!==programs[admission*512+pc_expected]||dut.prog_rsp_prepared_epoch!==active_epoch||
              dut.prog_rsp_prepared_pc!==pc_expected||dut.prog_rsp_prepared_error||
              {dut.prog_rsp_rcp_valid,dut.prog_rsp_rcp_nop,dut.prog_rsp_rcp_divisor,dut.prog_rsp_rcp_value}!==expected_plan)$fatal(1,"native prepared packet mismatch case=%0d admission=%0d step=%0d expected_pc=%0d packet_pc=%0d packet_epoch=%04h expected_epoch=%04h packet_tag=%04h expected_tag=%04h instruction=%016h expected_instruction=%016h metadata=%025h expected_metadata=%025h packet_error=%0d core_state=%0d",received,admission,step_index,pc_expected,dut.prog_rsp_prepared_pc,dut.prog_rsp_prepared_epoch,active_epoch,prog_rsp_tag,active_tag,prog_rsp_instruction,programs[admission*512+pc_expected],{dut.prog_rsp_rcp_valid,dut.prog_rsp_rcp_nop,dut.prog_rsp_rcp_divisor,dut.prog_rsp_rcp_value},expected_plan,dut.prog_rsp_prepared_error,dut.iteration.execute.state_q);
          end
          if(ds_rsp_valid&&ds_rsp_ready)begin if(ds_rsp_tag==16'hffff)begin ds_injected=1;stale_ds=stale_ds+1;end else ds_pending=0;end
          if(ds_req_valid&&ds_req_ready)begin
            if(dataset_taken||pc_expected!=(versions[received]?384:256)||event_index!=ev_start[received]+ev_count[received]||
              ds_req_tag!==active_tag||ds_req_addr!==dsaddr[received]||!ds_prefetch_valid||ds_prefetch_addr!==pfaddr[received])$fatal(1,"native dataset/control feedback");
            ds_data_q=dataset_line(ds_req_addr);if(ds_data_q!==dsdata[received])$fatal(1,"dataset fixture identity");
            ds_tag_q=ds_req_tag;ds_pending=1;ds_delay=STALL?3:1;ds_injected=0;dataset_taken=1;ds_stall=0;
          end
          held_read=sp_rd_valid&&!sp_rd_ready;read_payload=read_now;
          held_write=sp_wr_valid&&!sp_wr_ready;write_payload=write_now;
          held_prog=prog_valid&&!prog_ready;prog_payload=prog_now;
          held_done=done_valid&&!done_ready;done_payload=done_now;
          held_fetch_rsp=prog_rsp_valid&&!prog_rsp_ready;fetch_rsp_payload=fetch_rsp_now;
          if(done_taken)begin
            if(tail_writes!=8||done_tag!==active_tag||{done_e,done_f,done_r}!=={oute[received],outf[received],outr[received]}||
              done_mx!==outmx[received]||done_ma!==outma[received]||done_round_mode!==round_out[received][1:0]||done_spaddr0!==0||done_spaddr1!==0||
              step_index!=step_start[received]+step_count[received]||iteration_rcp!=dynamic_rcp_count[received]||iteration_active_rcp!=dynamic_active_rcp_count[received])$fatal(1,"native full iteration result/count");
            if(fline[received]==rline[received])aliases=aliases+1;
            previous_r=done_r;previous_mx=done_mx;previous_ma=done_ma;previous_round=done_round_mode;finished=1;
          end
          #1;prep_valid=0;
        end
        sp_rsp_valid=0;ds_rsp_valid=0;done_ready=0;
        if(!image_valid||image_epoch!==active_epoch||!prep_ready)$fatal(1,"iteration completion failed to release image ownership");
      end
    endtask

    initial begin
`include "case_vectors.vh"
      if(!$value$plusargs("DIR=%s",directory))$fatal(1,"DIR missing");
      if($value$plusargs("CONTROL=%d",control_mode))begin if(control_mode!=0&&control_mode!=1)$fatal(1,"CONTROL must be0or1");end
      metrics_path="";if($value$plusargs("METRICS=%s",metrics_path))begin if(metrics_path=="")$fatal(1,"METRICS path empty");end
      $sformat(path,"%0s/initial.hex",directory);$readmemh(path,ram);
      $sformat(path,"%0s/programs.mem",directory);$readmemh(path,programs);
      $sformat(path,"%0s/targets.mem",directory);$readmemh(path,compiled_targets);
      $sformat(path,"%0s/reciprocal_plan.mem",directory);$readmemh(path,native_plan);
      $sformat(path,"%0s/steps.mem",directory);$readmemh(path,gold_steps);
      $sformat(path,"%0s/events.mem",directory);$readmemh(path,events);
      for(i=0;i<131072;i=i+1)if((^ram[i])===1'bx)$fatal(1,"missing native initial memory word=%0d",i);
      for(i=0;i<TOTAL_PROGRAM_WORDS;i=i+1)if((^programs[i])===1'bx||(^native_plan[i])===1'bx||(^compiled_targets[i])===1'bx)$fatal(1,"missing native immutable word/plan/target");
      for(i=0;i<TOTAL_STEPS;i=i+1)if((^gold_steps[i])===1'bx)$fatal(1,"missing native retirement record");
      for(i=0;i<TOTAL_EVENTS;i=i+1)if((^events[i])===1'bx)$fatal(1,"missing native scratchpad event record");
      for(i=0;i<6;i=i+1)prep_phase[i]=0;
      for(i=0;i<18;i=i+1)exec_phase[i]=0;
      for(i=0;i<12;i=i+1)controller_phase[i]=0;
      rst=1;repeat(2)begin @(posedge clk);#1;end @(negedge clk);rst=0;
      while(received<TOTAL_ITERATIONS)begin
        if(received%ITERATIONS_PER_ADMISSION==0)begin begin_record;prepare_admission;if(control_mode&&received==0)descriptor_guards;end
        execute_iteration;
        if(admission_end[received])begin
          $sformat(path,"%0s/final-%0d.hex",directory,program_index[received]);$readmemh(path,gold_ram);
          for(i=0;i<131072;i=i+1)if((^gold_ram[i])===1'bx||ram[i]!==gold_ram[i])$fatal(1,"native all2MiB admission memory mismatch admission=%0d word=%0d",program_index[received],i);
          finish_record;
        end
        received=received+1;
      end
      if(total_fetches!=TOTAL_STEPS||total_commits!=TOTAL_STEPS||event_index!=TOTAL_EVENTS||total_writes!=8*TOTAL_ITERATIONS+BYTECODE_STORES||
        total_tail_writes!=8*TOTAL_ITERATIONS||preparations!=TOTAL_ADMISSIONS||reloads!=TOTAL_ADMISSIONS||loaded_words!=6*384+6*256||
        rcp_commits!=TOTAL_DYNAMIC_RCP||rcp_active!=TOTAL_DYNAMIC_ACTIVE_RCP||rcp_nops!=TOTAL_DYNAMIC_NOP_RCP)$fatal(1,"paired native coverage accounting");
      if(prep_rcp_requests!=(PREPARED_RCP?TOTAL_STATIC_ACTIVE_RCP:0)||runtime_rcp_requests!=(PREPARED_RCP?0:TOTAL_DYNAMIC_ACTIVE_RCP))$fatal(1,"actual reciprocal request ledger");
      if(exec_wall!=launch_clocks+entry_clocks+kernel_clocks+dataset_clocks+tail_clocks+return_clocks)$fatal(1,"outer execution phase ledger does not close");
      n=0;for(i=0;i<18;i=i+1)n=n+exec_phase[i];if(n!=kernel_clocks)$fatal(1,"nested execution FSM ledger does not close");
      n=0;for(i=0;i<6;i=i+1)n=n+prep_phase[i];if(n!=prep_wall)$fatal(1,"preparation FSM ledger does not close");
      if(STALL&&(stale_sp==0||stale_ds!=TOTAL_ITERATIONS||load_stale_errors!=3*TOTAL_ADMISSIONS))$fatal(1,"paired stale traffic coverage");
      if(control_mode&&(local_guards!=3||exec_cancels!=1))$fatal(1,"wrapper ownership controls");
      if(control_mode)ownership_controls;
      outside_clocks=cycles-prep_wall-exec_wall-control_wall;if(outside_clocks<0)$fatal(1,"clock ledger overlap");
      write_metrics;
      $display("PASS prepared_reciprocal_iteration prepared=%0d stall=%0d control=%0d admissions=%0d iterations=%0d reloads=%0d program_reads=%0d retirements=%0d static_rcp=%0d static_active_rcp=%0d dynamic_rcp=%0d dynamic_active_rcp=%0d dynamic_nop_rcp=%0d preparation_rcp_requests=%0d runtime_rcp_requests=%0d preparation_clocks=%0d preparation_response_clocks=%0d execution_clocks=%0d launch_clocks=%0d entry_clocks=%0d kernel_clocks=%0d dataset_clocks=%0d tail_clocks=%0d return_clocks=%0d control_clocks=%0d outside_clocks=%0d elapsed_cycles=%0d prep_s0=%0d prep_s1=%0d prep_s2=%0d prep_s3=%0d prep_s4=%0d prep_s5=%0d ex_s0=%0d ex_s1=%0d ex_s2=%0d ex_s3=%0d ex_s4=%0d ex_s5=%0d ex_s6=%0d ex_s7=%0d ex_s8=%0d ex_s9=%0d ex_s10=%0d ex_s11=%0d ex_s12=%0d ex_s13=%0d ex_s14=%0d ex_s15=%0d ex_s16=%0d ex_s17=%0d prep_request_stall=%0d prep_reply_wait=%0d sp_request_stall=%0d sp_reply_wait=%0d sp_store_stall=%0d dataset_request_stall=%0d dataset_reply_wait=%0d return_hold_wait=%0d fetch_request_stall=%0d fetch_reply_wait=%0d tail_aes_wait=%0d scratchpad_reads=%0d scratchpad_writes=%0d tail_writes=%0d stale_load=%0d stale_sp=%0d stale_dataset=%0d local_metadata_errors=%0d exec_cancels=%0d ownership_exec_cancels=%0d ownership_whole_cancels=%0d ownership_resets=%0d ownership_active=%0d ownership_held=%0d control_program_reads=%0d control_commits=%0d control_stores=%0d control_late_replies=%0d full_memory_bytes=2097152 native_RFE_round_control=1 immutable_metadata_assertions_only=1 full_hash_measured=0",PREPARED_RCP,STALL,control_mode,TOTAL_ADMISSIONS,TOTAL_ITERATIONS,reloads,loaded_words,total_commits,TOTAL_STATIC_RCP,TOTAL_STATIC_ACTIVE_RCP,rcp_commits,rcp_active,rcp_nops,prep_rcp_requests,runtime_rcp_requests,prep_wall,prep_response_clocks,exec_wall,launch_clocks,entry_clocks,kernel_clocks,dataset_clocks,tail_clocks,return_clocks,control_wall,outside_clocks,cycles,prep_phase[0],prep_phase[1],prep_phase[2],prep_phase[3],prep_phase[4],prep_phase[5],exec_phase[0],exec_phase[1],exec_phase[2],exec_phase[3],exec_phase[4],exec_phase[5],exec_phase[6],exec_phase[7],exec_phase[8],exec_phase[9],exec_phase[10],exec_phase[11],exec_phase[12],exec_phase[13],exec_phase[14],exec_phase[15],exec_phase[16],exec_phase[17],prep_req_stall,prep_rsp_wait,sp_req_wait,sp_reply_wait,sp_store_wait,ds_req_wait,ds_reply_wait,done_hold_wait,cache_fetch_req_wait,cache_fetch_reply_wait,tail_aes_wait,total_reads,total_writes,total_tail_writes,load_stale_errors,stale_sp,stale_ds,local_guards,exec_cancels,ownership_exec_cancels,ownership_whole_cancels,ownership_resets,ownership_active,ownership_held,control_program_reads,control_commits,control_stores,control_late_replies);
      $finish;
    end
    initial begin #2000000000;$fatal(1,"paired prepared iteration deadlock");end
endmodule
