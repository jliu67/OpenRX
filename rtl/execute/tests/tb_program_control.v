// SPDX-License-Identifier: BSD-3-Clause
`timescale 1ns/1ps
// Backend contract test; it validates control/initialization, not instruction arithmetic.
module tb_program_control #(parameter integer PROGRAMS=8,ITERATIONS=2048);
 reg  clk=0;
 reg  rst=0;
 reg  start_valid=0;
 wire  start_ready;
 reg [15:0] start_tag=0;
 reg  start_v2=0;
 wire  meta_req_valid;
 reg  meta_req_ready=0;
 wire [15:0] meta_req_tag;
 wire [2:0] meta_req_program;
 reg  meta_rsp_valid=0;
 wire  meta_rsp_ready;
 reg [15:0] meta_rsp_tag=0;
 reg [2:0] meta_rsp_program=0;
 reg [1023:0] meta_rsp_entropy=0;
 reg [63:0] meta_rsp_program_addr=0;
 wire  program_done_valid;
 reg  program_done_ready=0;
 wire [15:0] program_done_tag;
 wire [2:0] program_done_index;
 wire [11:0] program_done_iterations;
 wire [511:0] program_done_r;
 wire [511:0] program_done_f;
 wire [511:0] program_done_e;
 wire [511:0] program_done_a;
 wire [1:0] program_done_round_mode;
 wire  done_valid;
 reg  done_ready=0;
 wire [15:0] done_tag;
 wire [511:0] done_r;
 wire [511:0] done_f;
 wire [511:0] done_e;
 wire [511:0] done_a;
 wire [1:0] done_round_mode;
 wire [31:0] done_mx;
 wire [31:0] done_ma;
 wire [31:0] done_spaddr0;
 wire [31:0] done_spaddr1;
 wire  error_valid;
 reg  error_ready=0;
 wire [15:0] error_tag;
 wire [2:0] error_program;
 wire [1:0] error_code;
 wire [8:0] error_pc;
 wire [7:0] error_opcode;
 wire  iter_req_valid;
 reg  iter_req_ready=0;
 wire [15:0] iter_req_tag;
 wire  iter_req_v2;
 wire [1:0] iter_req_round_mode;
 wire [511:0] iter_req_r;
 wire [511:0] iter_req_a;
 wire [31:0] iter_req_spaddr0;
 wire [31:0] iter_req_spaddr1;
 wire [31:0] iter_req_mx;
 wire [31:0] iter_req_ma;
 wire [2:0] iter_req_read0;
 wire [2:0] iter_req_read1;
 wire [2:0] iter_req_read2;
 wire [2:0] iter_req_read3;
 wire [63:0] iter_req_emask0;
 wire [63:0] iter_req_emask1;
 wire [63:0] iter_req_dataset_offset;
 wire [63:0] iter_req_program_addr;
 reg  iter_done_valid=0;
 wire  iter_done_ready;
 reg [15:0] iter_done_tag=0;
 reg [511:0] iter_done_r=0;
 reg [511:0] iter_done_f=0;
 reg [511:0] iter_done_e=0;
 reg [1:0] iter_done_round_mode=0;
 reg [31:0] iter_done_mx=0;
 reg [31:0] iter_done_ma=0;
 reg [31:0] iter_done_spaddr0=0;
 reg [31:0] iter_done_spaddr1=0;
 reg  iter_error_valid=0;
 wire  iter_error_ready;
 reg [15:0] iter_error_tag=0;
 reg [8:0] iter_error_pc=0;
 reg [7:0] iter_error_opcode=0;
 wire  iteration_commit_valid;
 wire [15:0] iteration_commit_tag;
 wire [15:0] iteration_commit_backend_tag;
 wire [2:0] iteration_commit_program;
 wire [10:0] iteration_commit_index;
 wire [511:0] iteration_commit_r;
 wire [511:0] iteration_commit_f;
 wire [511:0] iteration_commit_e;
 wire [511:0] iteration_commit_a;
 wire [1:0] iteration_commit_round_mode;
 wire [31:0] iteration_commit_mx;
 wire [31:0] iteration_commit_ma;
 wire [31:0] iteration_commit_spaddr0;
 wire [31:0] iteration_commit_spaddr1;
 always #5 clk=~clk;
`ifdef PROGRAM_CONTROL_NETLIST
 randomx_program_control dut(
`else
 randomx_program_control #(.PROGRAMS(PROGRAMS),.ITERATIONS(ITERATIONS)) dut(
`endif
  .clk(clk),
  .rst(rst),
  .start_valid(start_valid),
  .start_ready(start_ready),
  .start_tag(start_tag),
  .start_v2(start_v2),
  .meta_req_valid(meta_req_valid),
  .meta_req_ready(meta_req_ready),
  .meta_req_tag(meta_req_tag),
  .meta_req_program(meta_req_program),
  .meta_rsp_valid(meta_rsp_valid),
  .meta_rsp_ready(meta_rsp_ready),
  .meta_rsp_tag(meta_rsp_tag),
  .meta_rsp_program(meta_rsp_program),
  .meta_rsp_entropy(meta_rsp_entropy),
  .meta_rsp_program_addr(meta_rsp_program_addr),
  .program_done_valid(program_done_valid),
  .program_done_ready(program_done_ready),
  .program_done_tag(program_done_tag),
  .program_done_index(program_done_index),
  .program_done_iterations(program_done_iterations),
  .program_done_r(program_done_r),
  .program_done_f(program_done_f),
  .program_done_e(program_done_e),
  .program_done_a(program_done_a),
  .program_done_round_mode(program_done_round_mode),
  .done_valid(done_valid),
  .done_ready(done_ready),
  .done_tag(done_tag),
  .done_r(done_r),
  .done_f(done_f),
  .done_e(done_e),
  .done_a(done_a),
  .done_round_mode(done_round_mode),
  .done_mx(done_mx),
  .done_ma(done_ma),
  .done_spaddr0(done_spaddr0),
  .done_spaddr1(done_spaddr1),
  .error_valid(error_valid),
  .error_ready(error_ready),
  .error_tag(error_tag),
  .error_program(error_program),
  .error_code(error_code),
  .error_pc(error_pc),
  .error_opcode(error_opcode),
  .iter_req_valid(iter_req_valid),
  .iter_req_ready(iter_req_ready),
  .iter_req_tag(iter_req_tag),
  .iter_req_v2(iter_req_v2),
  .iter_req_round_mode(iter_req_round_mode),
  .iter_req_r(iter_req_r),
  .iter_req_a(iter_req_a),
  .iter_req_spaddr0(iter_req_spaddr0),
  .iter_req_spaddr1(iter_req_spaddr1),
  .iter_req_mx(iter_req_mx),
  .iter_req_ma(iter_req_ma),
  .iter_req_read0(iter_req_read0),
  .iter_req_read1(iter_req_read1),
  .iter_req_read2(iter_req_read2),
  .iter_req_read3(iter_req_read3),
  .iter_req_emask0(iter_req_emask0),
  .iter_req_emask1(iter_req_emask1),
  .iter_req_dataset_offset(iter_req_dataset_offset),
  .iter_req_program_addr(iter_req_program_addr),
  .iter_done_valid(iter_done_valid),
  .iter_done_ready(iter_done_ready),
  .iter_done_tag(iter_done_tag),
  .iter_done_r(iter_done_r),
  .iter_done_f(iter_done_f),
  .iter_done_e(iter_done_e),
  .iter_done_round_mode(iter_done_round_mode),
  .iter_done_mx(iter_done_mx),
  .iter_done_ma(iter_done_ma),
  .iter_done_spaddr0(iter_done_spaddr0),
  .iter_done_spaddr1(iter_done_spaddr1),
  .iter_error_valid(iter_error_valid),
  .iter_error_ready(iter_error_ready),
  .iter_error_tag(iter_error_tag),
  .iter_error_pc(iter_error_pc),
  .iter_error_opcode(iter_error_opcode),
  .iteration_commit_valid(iteration_commit_valid),
  .iteration_commit_tag(iteration_commit_tag),
  .iteration_commit_backend_tag(iteration_commit_backend_tag),
  .iteration_commit_program(iteration_commit_program),
  .iteration_commit_index(iteration_commit_index),
  .iteration_commit_r(iteration_commit_r),
  .iteration_commit_f(iteration_commit_f),
  .iteration_commit_e(iteration_commit_e),
  .iteration_commit_a(iteration_commit_a),
  .iteration_commit_round_mode(iteration_commit_round_mode),
  .iteration_commit_mx(iteration_commit_mx),
  .iteration_commit_ma(iteration_commit_ma),
  .iteration_commit_spaddr0(iteration_commit_spaddr0),
  .iteration_commit_spaddr1(iteration_commit_spaddr1)
 );
 reg [1803:0] metadata[0:7];
 reg [511:0] expected_r,expected_f,expected_e;
 reg [1:0] expected_round;
 reg [31:0] expected_mx,expected_ma,expected_sp0,expected_sp1;
 reg [2499:0] held_request;
 reg [15:0] expected_tag,batch_tag;
 integer p,n,k,cycles=0,commits=0,resets=0,stale_meta=0,stale_backend=0;
 string directory;
 task tick;begin @(posedge clk);#1;cycles=cycles+1;end endtask
 task clean_inputs;begin
  start_valid=0;meta_req_ready=0;meta_rsp_valid=0;iter_req_ready=0;
  iter_done_valid=0;iter_error_valid=0;program_done_ready=0;done_ready=0;error_ready=0;
 end endtask
 task reset_control;begin
  clean_inputs;rst=1;tick;
  if(start_ready||meta_req_valid||iter_req_valid||program_done_valid||done_valid||error_valid||iteration_commit_valid)
   $fatal(1,"reset outputs");
  tick;rst=0;tick;resets=resets+1;
  if(!start_ready)$fatal(1,"reset idle");
 end endtask
 task start_batch;input [15:0] tag;input version;begin
  if(!start_ready)$fatal(1,"start not ready");
  batch_tag=tag;start_tag=tag;start_v2=version;start_valid=1;tick;start_valid=0;
  if(!meta_req_valid||meta_req_tag!==tag||meta_req_program!==0)$fatal(1,"first metadata request");
 end endtask
 task give_metadata;input integer index;input malformed;begin
  if(!meta_req_valid||meta_req_tag!==batch_tag||meta_req_program!==index)$fatal(1,"metadata identity");
  repeat(3)begin tick;if(!meta_req_valid||meta_req_tag!==batch_tag||meta_req_program!==index)$fatal(1,"held metadata request");end
  meta_req_ready=1;tick;meta_req_ready=0;
  meta_rsp_tag=batch_tag^16'h0001;meta_rsp_program=index;meta_rsp_entropy=~metadata[index][1023:0];
  meta_rsp_program_addr=64'hdead0003;meta_rsp_valid=1;
  if(!meta_rsp_ready)$fatal(1,"stale metadata readiness");
  tick;stale_meta=stale_meta+1;meta_rsp_valid=0;
  if(iter_req_valid||error_valid)$fatal(1,"stale metadata side effect");
  meta_rsp_tag=batch_tag;meta_rsp_program=(index+1)%8;meta_rsp_valid=1;#1;
  if(!meta_rsp_ready)$fatal(1,"stale program readiness");
  tick;stale_meta=stale_meta+1;meta_rsp_valid=0;
  if(iter_req_valid||error_valid)$fatal(1,"stale program side effect");
  meta_rsp_program=index;meta_rsp_entropy=metadata[index][1023:0];
  meta_rsp_program_addr=64'h200000+index*4096+(malformed?3:0);meta_rsp_valid=1;#1;
  if(!meta_rsp_ready)$fatal(1,"matching metadata readiness");
  tick;meta_rsp_valid=0;meta_rsp_entropy=~meta_rsp_entropy;meta_rsp_program_addr=64'hffffffffffffffff;
 end endtask
 task check_initialization;input integer index;begin
  if(!iter_req_valid||iter_req_r!==0||iter_req_a!==metadata[index][1535:1024]||
   iter_req_mx!==metadata[index][1567:1536]||iter_req_ma!==metadata[index][1599:1568]||
   iter_req_spaddr0!==metadata[index][1567:1536]||iter_req_spaddr1!==metadata[index][1599:1568]||
   iter_req_dataset_offset!==metadata[index][1663:1600]||iter_req_emask0!==metadata[index][1727:1664]||
   iter_req_emask1!==metadata[index][1791:1728]||iter_req_read0!==metadata[index][1794:1792]||
   iter_req_read1!==metadata[index][1797:1795]||iter_req_read2!==metadata[index][1800:1798]||
   iter_req_read3!==metadata[index][1803:1801]||iter_req_program_addr!==64'h200000+index*4096)
   $fatal(1,"native entropy initialization p=%0d",index);
 end endtask
 task request_hold;begin
  held_request={iter_req_tag,iter_req_v2,iter_req_round_mode,iter_req_r,iter_req_a,
   iter_req_mx,iter_req_ma,iter_req_spaddr0,iter_req_spaddr1,iter_req_read0,iter_req_read1,
   iter_req_read2,iter_req_read3,iter_req_emask0,iter_req_emask1,iter_req_dataset_offset,iter_req_program_addr};
  repeat(3)begin tick;
   if(!iter_req_valid||held_request!=={iter_req_tag,iter_req_v2,iter_req_round_mode,iter_req_r,iter_req_a,
    iter_req_mx,iter_req_ma,iter_req_spaddr0,iter_req_spaddr1,iter_req_read0,iter_req_read1,
    iter_req_read2,iter_req_read3,iter_req_emask0,iter_req_emask1,iter_req_dataset_offset,iter_req_program_addr})
    $fatal(1,"held iteration request");
  end
 end endtask
 task accept_iteration;begin iter_req_ready=1;tick;iter_req_ready=0;end endtask
 task stale_responses;begin
  iter_done_tag=expected_tag^16'h8000;iter_done_r=~expected_r;iter_done_valid=1;
  iter_error_tag=expected_tag^16'h8000;iter_error_pc=9'h123;iter_error_opcode=8'hfe;iter_error_valid=1;#1;
  if(!iter_done_ready||!iter_error_ready)$fatal(1,"stale backend readiness");
  tick;stale_backend=stale_backend+2;iter_done_valid=0;iter_error_valid=0;
  if(error_valid||iteration_commit_valid||iter_req_valid)$fatal(1,"stale backend side effect");
 end endtask
 task return_iteration;input integer program_index,iteration_index;begin
  iter_done_tag=expected_tag;
  for(k=0;k<8;k=k+1)begin
   iter_done_r[k*64+:64]=expected_r[k*64+:64]+expected_tag+k+1;
   iter_done_f[k*64+:64]={32'hf0000000,expected_tag,8'b0,k[7:0]};
   iter_done_e[k*64+:64]={32'he0000000,expected_tag,8'b0,k[7:0]};
  end
  iter_done_round_mode=(iteration_index==ITERATIONS-1)?expected_round+2'd3:expected_round;
  iter_done_mx=expected_mx+1;iter_done_ma=expected_ma^32'h00010000;iter_done_spaddr0=0;iter_done_spaddr1=0;
  expected_r=iter_done_r;expected_f=iter_done_f;expected_e=iter_done_e;expected_round=iter_done_round_mode;
  expected_mx=iter_done_mx;expected_ma=iter_done_ma;expected_sp0=0;expected_sp1=0;
  iter_done_valid=1;#1;if(!iter_done_ready)$fatal(1,"matching iteration readiness");tick;iter_done_valid=0;
  if(!iteration_commit_valid||iteration_commit_tag!==batch_tag||iteration_commit_backend_tag!==expected_tag||
   iteration_commit_program!==program_index||iteration_commit_index!==iteration_index||
   iteration_commit_r!==expected_r||iteration_commit_f!==expected_f||iteration_commit_e!==expected_e||
   iteration_commit_a!==metadata[program_index][1535:1024]||iteration_commit_round_mode!==expected_round||
   iteration_commit_mx!==expected_mx||iteration_commit_ma!==expected_ma||
   iteration_commit_spaddr0!==0||iteration_commit_spaddr1!==0)$fatal(1,"iteration commit %0d/%0d",program_index,iteration_index);
  commits=commits+1;expected_tag=expected_tag+1;
  iter_done_r=~iter_done_r;iter_done_f=~iter_done_f;iter_done_e=~iter_done_e;
 end endtask
 task check_program_return;input integer index;begin
  if(!program_done_valid||program_done_tag!==batch_tag||program_done_index!==index||program_done_iterations!==ITERATIONS||
   program_done_r!==expected_r||program_done_f!==expected_f||program_done_e!==expected_e||
   program_done_a!==metadata[index][1535:1024]||program_done_round_mode!==expected_round)
   $fatal(1,"program return %0d",index);
 end endtask
 task held_error;input [1:0] code;input [8:0] pc;input [7:0] opcode;begin
  repeat(4)begin
   if(!error_valid||error_tag!==batch_tag||error_program!==0||error_code!==code||error_pc!==pc||error_opcode!==opcode||
    iter_req_valid||program_done_valid||done_valid||iteration_commit_valid)$fatal(1,"held error");tick;
  end
  error_ready=1;tick;error_ready=0;if(!start_ready)$fatal(1,"error consume restart");
 end endtask
 initial begin
  if(!$value$plusargs("directory=%s",directory))$fatal(1,"directory missing");
  $readmemh({directory,"/metadata.mem"},metadata);
  reset_control;
  // Reset with metadata request held, then drain cancelled-generation responses.
  start_batch(16'h1000,0);reset_control;
  meta_rsp_valid=1;meta_rsp_tag=16'h1000;meta_rsp_program=0;iter_done_valid=1;iter_done_tag=16'h1000;
  tick;if(!start_ready||iteration_commit_valid||error_valid||iter_req_valid)$fatal(1,"late cancelled responses");clean_inputs;
  // Malformed program storage is a held error, with no backend launch.
  start_batch(16'h2000,1);give_metadata(0,1);held_error(1,0,0);
  // Matching backend error wins over a simultaneous successful response.
  start_batch(16'h2100,0);give_metadata(0,0);check_initialization(0);expected_tag=16'h2100;
  accept_iteration;expected_r=0;stale_responses;
  iter_error_tag=expected_tag;iter_error_pc=9'h12a;iter_error_opcode=8'h9c;iter_error_valid=1;
  iter_done_tag=expected_tag;iter_done_valid=1;#1;if(iter_done_ready)$fatal(1,"error priority readiness");
  tick;iter_error_valid=0;iter_done_valid=0;held_error(2,9'h12a,8'h9c);
  // Reset while an accepted backend request has not returned.
  start_batch(16'h2200,1);give_metadata(0,0);accept_iteration;reset_control;
  iter_done_valid=1;iter_done_tag=16'h2200;tick;iter_done_valid=0;
  if(!start_ready||iteration_commit_valid||program_done_valid)$fatal(1,"late cancelled backend");
  // Full parameter counts, native initialization and round-mode carry at every boundary.
  start_batch(16'h4000,1);expected_tag=16'h4000;expected_round=0;
  for(p=0;p<PROGRAMS;p=p+1)begin
   give_metadata(p,0);check_initialization(p);expected_r=0;
   expected_mx=metadata[p][1567:1536];expected_ma=metadata[p][1599:1568];
   expected_sp0=expected_mx;expected_sp1=expected_ma;
   for(n=0;n<ITERATIONS;n=n+1)begin
    if(!iter_req_valid||iter_req_tag!==expected_tag||iter_req_v2!==1||iter_req_round_mode!==expected_round||
     iter_req_r!==expected_r||iter_req_mx!==expected_mx||iter_req_ma!==expected_ma||
     iter_req_spaddr0!==expected_sp0||iter_req_spaddr1!==expected_sp1)$fatal(1,"feedback %0d/%0d",p,n);
    if(n%512==0)request_hold;
    accept_iteration;if(n==0)stale_responses;return_iteration(p,n);
   end
   repeat(4)begin check_program_return(p);tick;end
   program_done_ready=1;tick;program_done_ready=0;
  end
  repeat(5)begin
   if(!done_valid||done_tag!==batch_tag||done_r!==expected_r||done_f!==expected_f||done_e!==expected_e||
    done_a!==metadata[PROGRAMS-1][1535:1024]||done_round_mode!==expected_round||done_mx!==expected_mx||
    done_ma!==expected_ma||done_spaddr0!==0||done_spaddr1!==0||meta_req_valid||iter_req_valid||program_done_valid||iteration_commit_valid)
    $fatal(1,"held batch return");tick;
  end
  reset_control; // Cancellation of a held final response.
  // Cancellation of a held per-program response, using a completed mock backend.
  start_batch(16'ha000,0);give_metadata(0,0);expected_tag=16'ha000;expected_round=0;expected_r=0;
  expected_mx=metadata[0][1567:1536];expected_ma=metadata[0][1599:1568];
  for(n=0;n<ITERATIONS;n=n+1)begin accept_iteration;return_iteration(0,n);end
  check_program_return(0);reset_control;
  if(commits!==PROGRAMS*ITERATIONS+ITERATIONS)$fatal(1,"count mismatch");
  $display("PASS program_control programs=%0d iterations_per_program=%0d contract_commits=%0d native_entropy_records=8 resets=%0d held_error_codes=2 stale_meta=%0d stale_backend=%0d cycles=%0d arithmetic_backend=contract_stub",PROGRAMS,ITERATIONS,commits,resets,stale_meta,stale_backend,cycles);
  $finish;
 end
 initial begin #10000000;$fatal(1,"control timeout");end
endmodule
