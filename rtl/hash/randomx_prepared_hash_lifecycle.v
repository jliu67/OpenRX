// SPDX-License-Identifier: BSD-3-Clause
// Connected v2 hash ownership. Native initialization/program generation/dataset
// callbacks have explicit optional hardware replacements. Input BLAKE2b and
// dataset service remain host boundaries in both hardware AES modes.
`default_nettype none
module randomx_prepared_hash_lifecycle #(
 parameter integer PROGRAMS=8,ITERATIONS=2048,PREPARED_RCP=1,SCRATCHPAD_BYTES=2097152,HARDWARE_FILL=0,HARDWARE_PROGRAM=0
)(
 input wire clk,rst,cancel,
 input wire req_valid,output wire req_ready,input wire [15:0] req_tag,
 input wire [639:0] req_input,input wire [6:0] req_input_bytes,
 output wire init_req_valid,input wire init_req_ready,output wire [15:0] init_req_tag,
 output wire [639:0] init_req_input,output wire [6:0] init_req_input_bytes,
 input wire init_wr_valid,output wire init_wr_ready,input wire [15:0] init_wr_tag,
 input wire [20:0] init_wr_addr,input wire [127:0] init_wr_data,input wire [15:0] init_wr_strb,
 input wire init_rsp_valid,output wire init_rsp_ready,input wire [15:0] init_rsp_tag,
 input wire [511:0] init_rsp_seed,input wire init_rsp_error,
 output wire [511:0] meta_req_seed,input wire meta_rsp_error,
 input wire sp_rsp_error,input wire ds_rsp_error,
 output wire rsp_valid,input wire rsp_ready,output wire [15:0] rsp_tag,
 output wire [511:0] rsp_r,rsp_f,rsp_e,rsp_a,output wire [1:0] rsp_round_mode,
 output wire [255:0] rsp_digest,output wire rsp_error,
 output wire error_valid,output wire [15:0] error_tag,output wire [2:0] error_program,
 output wire [1:0] error_code,output wire [8:0] error_pc,output wire [7:0] error_opcode,
 output wire [3:0] phase,output wire [1:0] init_fill_phase,output wire [1:0] program_gen_phase,output wire [1:0] scratchpad_owner,output wire generation_exhausted,
 output wire  prep_commit_valid,
 output wire [15:0] prep_commit_epoch,
 output wire [2:0] prep_commit_program,
 output wire  meta_req_valid,
 input wire  meta_req_ready,
 output wire [15:0] meta_req_tag,
 output wire [2:0] meta_req_program,
 input wire  meta_rsp_valid,
 output wire  meta_rsp_ready,
 input wire [15:0] meta_rsp_tag,
 input wire [2:0] meta_rsp_program,
 input wire [1023:0] meta_rsp_entropy,
 input wire [63:0] meta_rsp_program_addr,
 output wire  program_done_valid,
 input wire  program_done_ready,
 output wire [15:0] program_done_tag,
 output wire [2:0] program_done_index,
 output wire [11:0] program_done_iterations,
 output wire [511:0] program_done_r,
 output wire [511:0] program_done_f,
 output wire [511:0] program_done_e,
 output wire [511:0] program_done_a,
 output wire [1:0] program_done_round_mode,
 output wire  program_done_seed_valid,
 output wire [511:0] program_done_seed,
 output wire  iteration_commit_valid,
 output wire [15:0] iteration_commit_tag,
 output wire [15:0] iteration_commit_backend_tag,
 output wire [2:0] iteration_commit_program,
 output wire [10:0] iteration_commit_index,
 output wire [511:0] iteration_commit_r,
 output wire [511:0] iteration_commit_f,
 output wire [511:0] iteration_commit_e,
 output wire [511:0] iteration_commit_a,
 output wire [1:0] iteration_commit_round_mode,
 output wire [31:0] iteration_commit_mx,
 output wire [31:0] iteration_commit_ma,
 output wire [31:0] iteration_commit_spaddr0,
 output wire [31:0] iteration_commit_spaddr1,
 output wire  sp_rd_valid,
 input wire  sp_rd_ready,
 output wire [20:0] sp_rd_addr,
 output wire [50:0] sp_rd_tag,
 input wire  sp_rsp_valid,
 output wire  sp_rsp_ready,
 input wire [127:0] sp_rsp_data,
 input wire [50:0] sp_rsp_tag,
 output wire  sp_wr_valid,
 input wire  sp_wr_ready,
 output wire [20:0] sp_wr_addr,
 output wire [127:0] sp_wr_data,
 output wire [15:0] sp_wr_strb,
 output wire [50:0] sp_wr_tag,
 output wire  ds_req_valid,
 input wire  ds_req_ready,
 output wire [63:0] ds_req_addr,
 output wire [63:0] ds_prefetch_addr,
 output wire [31:0] ds_req_tag,
 output wire  ds_prefetch_valid,
 input wire  ds_rsp_valid,
 output wire  ds_rsp_ready,
 input wire [31:0] ds_rsp_tag,
 input wire [511:0] ds_rsp_data,
 output wire  prog_valid,
 input wire  prog_ready,
 output wire [63:0] prog_addr,
 output wire [40:0] prog_tag,
 input wire  prog_rsp_valid,
 output wire  prog_rsp_ready,
 input wire [40:0] prog_rsp_tag,
 input wire [63:0] prog_rsp_instruction,
 input wire  prog_rsp_error,
 output wire  commit_valid,
 output wire [15:0] commit_tag,
 output wire [8:0] commit_pc,
 output wire [7:0] commit_opcode,
 output wire [511:0] commit_r,
 output wire [8:0] commit_next_pc,
 output wire [8:0] commit_branch_target,
 output wire [511:0] commit_f,
 output wire [511:0] commit_e,
 output wire [1:0] commit_round_mode
);
 localparam [3:0] IDLE=0,INIT_REQUEST=1,INIT_STREAM=2,CHAIN_START=3,RUN=4,FIN_START=5,FIN_WAIT=6,RETURN=7,ERROR=8,FILL_START=9,FILL_RUN=10;
 localparam [1:0] OWNER_INIT=0,OWNER_EXEC=1,OWNER_FINAL=2,OWNER_NONE=3;
 localparam [21:0] FINAL_CAPACITY=SCRATCHPAD_BYTES;
 reg [3:0] state_q;reg [15:0] generation_counter_q,generation_q,user_tag_q;
 reg [639:0] input_q;reg [6:0] input_bytes_q;reg [17:0] init_beats_q;
 reg [511:0] seed_q,r_q,f_q,e_q,a_q;reg [1:0] round_q;
 reg [255:0] digest_q;reg [2:0] error_program_q;reg [1:0] error_code_q;
 reg [8:0] error_pc_q;reg [7:0] error_opcode_q;
 // Provider faults belong only to the exact outstanding transfer. A stale
 // same-generation reply must not abort a later iteration/program.
 reg sp_wait_q,ds_wait_q,meta_wait_q;
 reg [50:0] expected_sp_q;reg [31:0] expected_ds_q;
 reg [2:0] expected_meta_program_q;
 wire [3:0] chain_phase;
 wire chain_epoch_capacity_exhausted;
 wire  chain_start_valid;
 wire  chain_start_ready;
 wire [15:0] chain_start_tag;
 wire  chain_start_v2;
 wire  chain_meta_req_valid;
 wire  chain_meta_req_ready;
 wire [15:0] chain_meta_req_tag;
 wire [2:0] chain_meta_req_program;
 wire  chain_meta_rsp_valid;
 wire  chain_meta_rsp_ready;
 wire [15:0] chain_meta_rsp_tag;
 wire [2:0] chain_meta_rsp_program;
 wire [1023:0] chain_meta_rsp_entropy;
 wire [63:0] chain_meta_rsp_program_addr;
 wire  chain_program_done_ready;
 wire  chain_done_valid;
 wire  chain_done_ready;
 wire [15:0] chain_done_tag;
 wire [511:0] chain_done_r;
 wire [511:0] chain_done_f;
 wire [511:0] chain_done_e;
 wire [511:0] chain_done_a;
 wire [1:0] chain_done_round_mode;
 wire [31:0] chain_done_mx;
 wire [31:0] chain_done_ma;
 wire [31:0] chain_done_spaddr0;
 wire [31:0] chain_done_spaddr1;
 wire  chain_error_valid;
 wire  chain_error_ready;
 wire [15:0] chain_error_tag;
 wire [2:0] chain_error_program;
 wire [1:0] chain_error_code;
 wire [8:0] chain_error_pc;
 wire [7:0] chain_error_opcode;
 wire  chain_sp_rd_valid;
 wire  chain_sp_rd_ready;
 wire [20:0] chain_sp_rd_addr;
 wire [15:0] chain_sp_rd_tag;
 wire  chain_sp_rsp_valid;
 wire  chain_sp_rsp_ready;
 wire [127:0] chain_sp_rsp_data;
 wire [15:0] chain_sp_rsp_tag;
 wire  chain_sp_wr_valid;
 wire  chain_sp_wr_ready;
 wire [20:0] chain_sp_wr_addr;
 wire [127:0] chain_sp_wr_data;
 wire [15:0] chain_sp_wr_strb;
 wire [15:0] chain_sp_wr_tag;
 wire  chain_ds_req_valid;
 wire  chain_ds_req_ready;
 wire [63:0] chain_ds_req_addr;
 wire [63:0] chain_ds_prefetch_addr;
 wire [15:0] chain_ds_req_tag;
 wire  chain_ds_prefetch_valid;
 wire  chain_ds_rsp_valid;
 wire  chain_ds_rsp_ready;
 wire [15:0] chain_ds_rsp_tag;
 wire [511:0] chain_ds_rsp_data;
 wire  chain_prog_valid;
 wire  chain_prog_ready;
 wire [63:0] chain_prog_addr;
 wire [24:0] chain_prog_tag;
 wire  chain_prog_rsp_valid;
 wire  chain_prog_rsp_ready;
 wire [24:0] chain_prog_rsp_tag;
 wire [63:0] chain_prog_rsp_instruction;
 wire  chain_prog_rsp_error;
 wire final_req_ready,final_rsp_valid,final_rsp_error;
 wire [15:0] final_rsp_tag;wire [1:0] final_rsp_round;
 wire [511:0] final_rsp_r,final_rsp_f,final_rsp_e,final_rsp_a;
 wire [255:0] final_rsp_digest;
 wire final_sp_rd_valid,final_sp_rsp_ready;wire [20:0] final_sp_rd_addr;wire [32:0] final_sp_rd_tag;
 wire fill_req_ready,fill_wr_valid,fill_rsp_valid;
 wire [20:0] fill_wr_addr;wire [127:0] fill_wr_data;wire [15:0] fill_wr_strb,fill_wr_tag,fill_rsp_tag;
 wire [511:0] fill_rsp_seed;wire [1:0] fill_phase;
 // A generated image is private until all 3,200 bytes and the generator return
 // have been accepted. Reset/cancel invalidates ownership without clearing RAM.
 localparam [2:0] PG_IDLE=0,PG_START=1,PG_FILL=2,PG_META=3,PG_READY=4;
 reg [2:0] pg_state_q,pg_program_q;reg [15:0] pg_tag_q;reg [511:0] pg_seed_q;
 reg [7:0] pg_beats_q;reg [1023:0] pg_entropy_q;reg [127:0] pg_words_q[0:191];
 reg pg_fetch_pending_q,pg_fetch_error_q;reg [24:0] pg_fetch_tag_q;reg [63:0] pg_fetch_data_q;
 wire pg_req_ready,pg_out_valid,pg_out_ready,pg_rsp_valid,pg_rsp_ready;
 wire [11:0] pg_out_addr;wire [127:0] pg_out_data;wire [15:0] pg_out_tag,pg_rsp_tag;wire [1:0] pg_phase;
 wire [63:0] pg_base=64'h10000000+{49'b0,pg_program_q,12'b0};
 wire [63:0] pg_fetch_index=(chain_prog_addr-pg_base)>>3;
 wire pg_fetch_bad=chain_prog_addr[2:0]!=0||chain_prog_addr<pg_base||pg_fetch_index>=384||chain_prog_tag[8:0]!=pg_fetch_index[8:0];
 wire pg_out_bad=pg_out_tag!=pg_tag_q||pg_beats_q>=200||pg_out_addr!={pg_beats_q,4'b0};
 wire pg_bad=HARDWARE_PROGRAM&&state_q==RUN&&pg_state_q==PG_FILL&&
             ((pg_out_valid&&pg_out_ready&&pg_out_bad)||(pg_rsp_valid&&pg_rsp_ready&&(pg_rsp_tag!=pg_tag_q||pg_beats_q!=200)));
 wire active=!rst&&!cancel;
 wire init_stale=init_wr_tag!=generation_q;
 wire init_bad=init_beats_q>=SCRATCHPAD_BYTES/16||init_wr_addr!={init_beats_q[16:0],4'b0}||init_wr_strb!=16'hffff;
 wire hardware_init_fault=HARDWARE_FILL&&init_wr_valid&&!init_stale&&
                          (state_q==INIT_STREAM||state_q==FILL_START||state_q==FILL_RUN);
 wire exec_reply=sp_rsp_tag[50:35]==generation_q&&sp_rsp_tag[34:33]==OWNER_EXEC&&state_q==RUN;
 wire final_reply=sp_rsp_tag[50:35]==generation_q&&sp_rsp_tag[34:33]==OWNER_FINAL&&state_q==FIN_WAIT;
 wire dataset_reply=ds_rsp_tag[31:16]==generation_q&&state_q==RUN;
 wire program_reply=!HARDWARE_PROGRAM&&prog_rsp_tag[40:25]==generation_q&&state_q==RUN;
 wire metadata_reply=!HARDWARE_PROGRAM&&meta_rsp_tag==generation_q&&state_q==RUN;
 wire current_sp_error=sp_wait_q&&sp_rsp_tag==expected_sp_q;
 wire current_ds_error=ds_wait_q&&ds_rsp_tag==expected_ds_q;
 wire current_meta_error=meta_wait_q&&meta_rsp_program==expected_meta_program_q;
 assign generation_exhausted=generation_counter_q==16'hffff||chain_epoch_capacity_exhausted;
 assign req_ready=active&&state_q==IDLE&&!generation_exhausted;
 assign init_req_valid=active&&state_q==INIT_REQUEST;
 assign init_req_tag=generation_q;assign init_req_input=input_q;assign init_req_input_bytes=input_bytes_q;
 // In hardware mode stale external writes are drained. A matching host write
 // after the initialization request was accepted is a protocol error and never
 // reaches memory. INIT_REQUEST drains writes without interpreting them.
 assign init_wr_ready=active&&(HARDWARE_FILL||init_stale||state_q!=INIT_STREAM||init_bad||sp_wr_ready);
 // A matching hardware-mode seed offered together with the request must wait
 // for INIT_STREAM, the state that consumes it. Stale responses may still drain.
 assign init_rsp_ready=active&&(HARDWARE_FILL?(init_rsp_tag!=generation_q||state_q!=INIT_REQUEST):
                              (init_rsp_tag!=generation_q||state_q!=INIT_STREAM||init_rsp_error||init_beats_q==SCRATCHPAD_BYTES/16));
 assign rsp_valid=active&&(state_q==RETURN||state_q==ERROR);assign rsp_error=state_q==ERROR;
 assign rsp_tag=user_tag_q;assign rsp_r=r_q;assign rsp_f=f_q;assign rsp_e=e_q;assign rsp_a=a_q;
 assign rsp_round_mode=round_q;assign rsp_digest=digest_q;
 assign error_valid=active&&state_q==ERROR;assign error_tag=user_tag_q;
 assign error_program=error_program_q;assign error_code=error_code_q;assign error_pc=error_pc_q;assign error_opcode=error_opcode_q;
 assign scratchpad_owner=(state_q==INIT_REQUEST||state_q==INIT_STREAM||state_q==FILL_START||state_q==FILL_RUN)?OWNER_INIT:state_q==RUN?OWNER_EXEC:
                         (state_q==FIN_START||state_q==FIN_WAIT)?OWNER_FINAL:OWNER_NONE;
 // Exactly one outer phase per admitted clock. Stall counters are nested observers.
 assign phase=cancel?4'd9:(state_q==INIT_REQUEST||state_q==INIT_STREAM||state_q==FILL_START||state_q==FILL_RUN)?4'd1:
              state_q==RUN?(HARDWARE_PROGRAM&&(pg_state_q==PG_START||pg_state_q==PG_FILL||pg_state_q==PG_META)?4'd7:chain_phase):(state_q==FIN_START||state_q==FIN_WAIT)?
              4'd6:
              (state_q==RETURN||state_q==ERROR)?4'd8:4'd2;
 assign init_fill_phase=HARDWARE_FILL&&(state_q==FILL_START||state_q==FILL_RUN)?fill_phase:2'd0;
 assign program_gen_phase=HARDWARE_PROGRAM&&active&&state_q==RUN?pg_phase:2'd0;
 assign chain_start_valid=active&&state_q==CHAIN_START;assign chain_start_tag=generation_q;assign chain_start_v2=1'b1;
 assign meta_req_valid=!HARDWARE_PROGRAM&&active&&state_q==RUN&&chain_meta_req_valid;
 assign chain_meta_req_ready=active&&state_q==RUN&&(HARDWARE_PROGRAM?
                             ((pg_state_q==PG_IDLE||pg_state_q==PG_READY)&&!pg_fetch_pending_q):meta_req_ready);
 assign meta_req_tag=chain_meta_req_tag;assign meta_req_program=chain_meta_req_program;assign meta_req_seed=seed_q;
 assign chain_meta_rsp_valid=HARDWARE_PROGRAM?(active&&state_q==RUN&&pg_state_q==PG_META):(meta_rsp_valid&&metadata_reply&&!meta_rsp_error);
 assign meta_rsp_ready=active&&(HARDWARE_PROGRAM||!metadata_reply||meta_rsp_error||chain_meta_rsp_ready);
 assign chain_meta_rsp_tag=HARDWARE_PROGRAM?pg_tag_q:meta_rsp_tag;assign chain_meta_rsp_program=HARDWARE_PROGRAM?pg_program_q:meta_rsp_program;
 assign chain_meta_rsp_entropy=HARDWARE_PROGRAM?pg_entropy_q:meta_rsp_entropy;
 assign chain_meta_rsp_program_addr=HARDWARE_PROGRAM?pg_base:meta_rsp_program_addr;
 assign chain_program_done_ready=active&&state_q==RUN&&program_done_ready;
 assign chain_done_ready=active&&state_q==RUN;assign chain_error_ready=active&&state_q==RUN;
 assign prog_valid=!HARDWARE_PROGRAM&&active&&state_q==RUN&&chain_prog_valid;
 assign chain_prog_ready=active&&state_q==RUN&&(HARDWARE_PROGRAM?
                         (pg_state_q==PG_READY&&pg_tag_q==generation_q&&!pg_fetch_pending_q&&!chain_meta_req_valid):prog_ready);
 assign prog_addr=chain_prog_addr;assign prog_tag={generation_q,chain_prog_tag};
 assign chain_prog_rsp_valid=HARDWARE_PROGRAM?(active&&state_q==RUN&&pg_fetch_pending_q):(prog_rsp_valid&&program_reply);
 assign prog_rsp_ready=active&&(HARDWARE_PROGRAM||!program_reply||chain_prog_rsp_ready);
 assign chain_prog_rsp_tag=HARDWARE_PROGRAM?pg_fetch_tag_q:prog_rsp_tag[24:0];
 assign chain_prog_rsp_instruction=HARDWARE_PROGRAM?pg_fetch_data_q:prog_rsp_instruction;
 assign chain_prog_rsp_error=HARDWARE_PROGRAM?pg_fetch_error_q:prog_rsp_error;
 assign ds_req_valid=active&&state_q==RUN&&chain_ds_req_valid;assign chain_ds_req_ready=ds_req_ready&&active&&state_q==RUN;
 assign ds_req_addr=chain_ds_req_addr;assign ds_req_tag={generation_q,chain_ds_req_tag};
 assign ds_prefetch_addr=chain_ds_prefetch_addr;assign ds_prefetch_valid=active&&state_q==RUN&&chain_ds_prefetch_valid;
 assign chain_ds_rsp_valid=ds_rsp_valid&&dataset_reply&&!ds_rsp_error;
 assign ds_rsp_ready=active&&(!dataset_reply||ds_rsp_error||chain_ds_rsp_ready);
 assign chain_ds_rsp_tag=ds_rsp_tag[15:0];assign chain_ds_rsp_data=ds_rsp_data;
 assign sp_rd_valid=active&&((state_q==RUN&&chain_sp_rd_valid)||(state_q==FIN_WAIT&&final_sp_rd_valid));
 assign sp_rd_addr=state_q==RUN?chain_sp_rd_addr:final_sp_rd_addr;
 assign sp_rd_tag=state_q==RUN?{generation_q,OWNER_EXEC,17'b0,chain_sp_rd_tag}:{generation_q,OWNER_FINAL,final_sp_rd_tag};
 assign chain_sp_rd_ready=active&&state_q==RUN&&sp_rd_ready;
 assign chain_sp_rsp_valid=sp_rsp_valid&&exec_reply&&!sp_rsp_error;
 assign chain_sp_rsp_data=sp_rsp_data;assign chain_sp_rsp_tag=sp_rsp_tag[15:0];
 assign sp_rsp_ready=active&&(exec_reply?(sp_rsp_error||chain_sp_rsp_ready):final_reply?final_sp_rsp_ready:1'b1);
 assign sp_wr_valid=active&&((!HARDWARE_FILL&&state_q==INIT_STREAM&&init_wr_valid&&!init_stale&&!init_bad)||
                    (HARDWARE_FILL&&state_q==FILL_RUN&&fill_wr_valid&&!hardware_init_fault)||(state_q==RUN&&chain_sp_wr_valid));
 assign sp_wr_addr=HARDWARE_FILL&&state_q==FILL_RUN?fill_wr_addr:state_q==INIT_STREAM?init_wr_addr:chain_sp_wr_addr;
 assign sp_wr_data=HARDWARE_FILL&&state_q==FILL_RUN?fill_wr_data:state_q==INIT_STREAM?init_wr_data:chain_sp_wr_data;
 assign sp_wr_strb=HARDWARE_FILL&&state_q==FILL_RUN?fill_wr_strb:state_q==INIT_STREAM?init_wr_strb:chain_sp_wr_strb;
 assign sp_wr_tag=HARDWARE_FILL&&state_q==FILL_RUN?{fill_wr_tag,OWNER_INIT,15'b0,init_beats_q}:
                  state_q==INIT_STREAM?{generation_q,OWNER_INIT,15'b0,init_beats_q}:{generation_q,OWNER_EXEC,17'b0,chain_sp_wr_tag};
 assign chain_sp_wr_ready=active&&state_q==RUN&&sp_wr_ready;
 generate if(HARDWARE_FILL)begin: hardware_initial_fill
  randomx_initial_scratchpad_fill #(.SCRATCHPAD_BYTES(SCRATCHPAD_BYTES)) filler(
   .clk(clk),.rst(rst),.cancel(cancel||state_q==ERROR),
   .req_valid(active&&state_q==FILL_START&&!hardware_init_fault),.req_ready(fill_req_ready),.req_tag(generation_q),.req_seed(seed_q),
   .sp_wr_valid(fill_wr_valid),.sp_wr_ready(active&&state_q==FILL_RUN&&sp_wr_ready&&!hardware_init_fault),
   .sp_wr_addr(fill_wr_addr),.sp_wr_data(fill_wr_data),.sp_wr_strb(fill_wr_strb),.sp_wr_tag(fill_wr_tag),
   .rsp_valid(fill_rsp_valid),.rsp_ready(active&&state_q==FILL_RUN),.rsp_tag(fill_rsp_tag),.rsp_seed(fill_rsp_seed),.phase(fill_phase)
  );
 end else begin: software_initial_fill
  assign fill_req_ready=0;assign fill_wr_valid=0;assign fill_wr_addr=0;assign fill_wr_data=0;assign fill_wr_strb=0;assign fill_wr_tag=0;
  assign fill_rsp_valid=0;assign fill_rsp_tag=0;assign fill_rsp_seed=0;assign fill_phase=0;
 end endgenerate
 assign pg_out_ready=HARDWARE_PROGRAM&&active&&state_q==RUN&&pg_state_q==PG_FILL;
 assign pg_rsp_ready=HARDWARE_PROGRAM&&active&&state_q==RUN&&pg_state_q==PG_FILL;
 generate if(HARDWARE_PROGRAM)begin: hardware_program_generation
  randomx_program_generation #(.OUTPUT_BYTES(3200)) generator(
   .clk(clk),.rst(rst),.cancel(cancel||state_q==ERROR),
   .req_valid(active&&state_q==RUN&&pg_state_q==PG_START),.req_ready(pg_req_ready),.req_tag(pg_tag_q),.req_seed(pg_seed_q),
   .out_valid(pg_out_valid),.out_ready(pg_out_ready),.out_addr(pg_out_addr),.out_data(pg_out_data),.out_tag(pg_out_tag),
   .rsp_valid(pg_rsp_valid),.rsp_ready(pg_rsp_ready),.rsp_tag(pg_rsp_tag),.phase(pg_phase));
 end else begin: software_program_generation
  assign pg_req_ready=0;assign pg_out_valid=0;assign pg_out_addr=0;assign pg_out_data=0;assign pg_out_tag=0;
  assign pg_rsp_valid=0;assign pg_rsp_tag=0;assign pg_phase=0;
 end endgenerate
 randomx_prepared_program_hash_sequence #(.PROGRAMS(PROGRAMS),.ITERATIONS(ITERATIONS),.PREPARED_RCP(PREPARED_RCP)) chain(
  .clk(clk),
  .rst(rst),
  .cancel(cancel||state_q==ERROR),
  .phase(chain_phase),
  .prep_commit_valid(prep_commit_valid),
  .prep_commit_epoch(prep_commit_epoch),
  .prep_commit_program(prep_commit_program),
  .epoch_capacity_exhausted(chain_epoch_capacity_exhausted),
  .start_valid(chain_start_valid),
  .start_ready(chain_start_ready),
  .start_tag(chain_start_tag),
  .start_v2(chain_start_v2),
  .meta_req_valid(chain_meta_req_valid),
  .meta_req_ready(chain_meta_req_ready),
  .meta_req_tag(chain_meta_req_tag),
  .meta_req_program(chain_meta_req_program),
  .meta_rsp_valid(chain_meta_rsp_valid),
  .meta_rsp_ready(chain_meta_rsp_ready),
  .meta_rsp_tag(chain_meta_rsp_tag),
  .meta_rsp_program(chain_meta_rsp_program),
  .meta_rsp_entropy(chain_meta_rsp_entropy),
  .meta_rsp_program_addr(chain_meta_rsp_program_addr),
  .program_done_valid(program_done_valid),
  .program_done_ready(chain_program_done_ready),
  .program_done_tag(program_done_tag),
  .program_done_index(program_done_index),
  .program_done_iterations(program_done_iterations),
  .program_done_r(program_done_r),
  .program_done_f(program_done_f),
  .program_done_e(program_done_e),
  .program_done_a(program_done_a),
  .program_done_round_mode(program_done_round_mode),
  .program_done_seed_valid(program_done_seed_valid),
  .program_done_seed(program_done_seed),
  .done_valid(chain_done_valid),
  .done_ready(chain_done_ready),
  .done_tag(chain_done_tag),
  .done_r(chain_done_r),
  .done_f(chain_done_f),
  .done_e(chain_done_e),
  .done_a(chain_done_a),
  .done_round_mode(chain_done_round_mode),
  .done_mx(chain_done_mx),
  .done_ma(chain_done_ma),
  .done_spaddr0(chain_done_spaddr0),
  .done_spaddr1(chain_done_spaddr1),
  .error_valid(chain_error_valid),
  .error_ready(chain_error_ready),
  .error_tag(chain_error_tag),
  .error_program(chain_error_program),
  .error_code(chain_error_code),
  .error_pc(chain_error_pc),
  .error_opcode(chain_error_opcode),
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
  .iteration_commit_spaddr1(iteration_commit_spaddr1),
  .sp_rd_valid(chain_sp_rd_valid),
  .sp_rd_ready(chain_sp_rd_ready),
  .sp_rd_addr(chain_sp_rd_addr),
  .sp_rd_tag(chain_sp_rd_tag),
  .sp_rsp_valid(chain_sp_rsp_valid),
  .sp_rsp_ready(chain_sp_rsp_ready),
  .sp_rsp_data(chain_sp_rsp_data),
  .sp_rsp_tag(chain_sp_rsp_tag),
  .sp_wr_valid(chain_sp_wr_valid),
  .sp_wr_ready(chain_sp_wr_ready),
  .sp_wr_addr(chain_sp_wr_addr),
  .sp_wr_data(chain_sp_wr_data),
  .sp_wr_strb(chain_sp_wr_strb),
  .sp_wr_tag(chain_sp_wr_tag),
  .ds_req_valid(chain_ds_req_valid),
  .ds_req_ready(chain_ds_req_ready),
  .ds_req_addr(chain_ds_req_addr),
  .ds_prefetch_addr(chain_ds_prefetch_addr),
  .ds_req_tag(chain_ds_req_tag),
  .ds_prefetch_valid(chain_ds_prefetch_valid),
  .ds_rsp_valid(chain_ds_rsp_valid),
  .ds_rsp_ready(chain_ds_rsp_ready),
  .ds_rsp_tag(chain_ds_rsp_tag),
  .ds_rsp_data(chain_ds_rsp_data),
  .prog_valid(chain_prog_valid),
  .prog_ready(chain_prog_ready),
  .prog_addr(chain_prog_addr),
  .prog_tag(chain_prog_tag),
  .prog_rsp_valid(chain_prog_rsp_valid),
  .prog_rsp_ready(chain_prog_rsp_ready),
  .prog_rsp_tag(chain_prog_rsp_tag),
  .prog_rsp_instruction(chain_prog_rsp_instruction),
  .prog_rsp_error(chain_prog_rsp_error),
  .commit_valid(commit_valid),
  .commit_tag(commit_tag),
  .commit_pc(commit_pc),
  .commit_opcode(commit_opcode),
  .commit_r(commit_r),
  .commit_next_pc(commit_next_pc),
  .commit_branch_target(commit_branch_target),
  .commit_f(commit_f),
  .commit_e(commit_e),
  .commit_round_mode(commit_round_mode)
 );
 randomx_scratchpad_finalizer #(.SCRATCHPAD_BYTES(SCRATCHPAD_BYTES)) finalizer(
  .clk(clk),.rst(rst||cancel||state_q==ERROR),.req_valid(active&&state_q==FIN_START),.req_ready(final_req_ready),
  .req_tag(generation_q),.req_scratchpad_bytes(FINAL_CAPACITY),.req_round_mode(round_q),.req_r(r_q),.req_f(f_q),.req_e(e_q),.req_a(a_q),
  .sp_rd_valid(final_sp_rd_valid),.sp_rd_ready(active&&state_q==FIN_WAIT&&sp_rd_ready),.sp_rd_addr(final_sp_rd_addr),.sp_rd_tag(final_sp_rd_tag),
  .sp_rsp_valid(sp_rsp_valid&&final_reply),.sp_rsp_ready(final_sp_rsp_ready),.sp_rsp_data(sp_rsp_data),.sp_rsp_tag(sp_rsp_tag[32:0]),.sp_rsp_error(sp_rsp_error),
  .rsp_valid(final_rsp_valid),.rsp_ready(active&&state_q==FIN_WAIT),.rsp_tag(final_rsp_tag),.rsp_round_mode(final_rsp_round),
  .rsp_r(final_rsp_r),.rsp_f(final_rsp_f),.rsp_e(final_rsp_e),.rsp_a(final_rsp_a),.rsp_digest(final_rsp_digest),.rsp_error(final_rsp_error)
 );
 generate if(SCRATCHPAD_BYTES<64||SCRATCHPAD_BYTES>2097152||SCRATCHPAD_BYTES%64!=0)begin: invalid_capacity
  lifecycle_requires_64_to_2097152_bytes_in_64_byte_groups invalid();end endgenerate
 generate if(HARDWARE_FILL!=0&&HARDWARE_FILL!=1)begin: invalid_fill_mode
  lifecycle_hardware_fill_requires_boolean_0_or_1 invalid();end endgenerate
 generate if(HARDWARE_PROGRAM!=0&&HARDWARE_PROGRAM!=1)begin: invalid_program_mode
  lifecycle_hardware_program_requires_boolean_0_or_1 invalid();end endgenerate
 always @(posedge clk)begin
  if(rst||cancel||state_q==ERROR||state_q==IDLE)begin
   pg_state_q<=PG_IDLE;pg_tag_q<=0;pg_program_q<=0;pg_seed_q<=0;pg_beats_q<=0;pg_entropy_q<=0;
   pg_fetch_pending_q<=0;pg_fetch_error_q<=0;pg_fetch_tag_q<=0;pg_fetch_data_q<=0;
  end else if(HARDWARE_PROGRAM)begin
   if(chain_prog_rsp_valid&&chain_prog_rsp_ready)pg_fetch_pending_q<=0;
   if(chain_prog_valid&&chain_prog_ready)begin
    pg_fetch_pending_q<=1;pg_fetch_tag_q<=chain_prog_tag;pg_fetch_error_q<=pg_fetch_bad;
    if(pg_fetch_bad)pg_fetch_data_q<=0;
    else pg_fetch_data_q<=pg_fetch_index[0]?pg_words_q[pg_fetch_index[8:1]][127:64]:pg_words_q[pg_fetch_index[8:1]][63:0];
   end
   case(pg_state_q)
    PG_IDLE,PG_READY:if(chain_meta_req_valid&&chain_meta_req_ready)begin
     pg_tag_q<=chain_meta_req_tag;pg_program_q<=chain_meta_req_program;pg_seed_q<=seed_q;
     pg_beats_q<=0;pg_entropy_q<=0;pg_state_q<=PG_START;
    end
    PG_START:if(pg_req_ready)pg_state_q<=PG_FILL;
    PG_FILL:begin
     if(pg_out_valid&&pg_out_ready&&!pg_out_bad)begin
      if(pg_beats_q<8)pg_entropy_q[128*pg_beats_q[2:0]+:128]<=pg_out_data;
      else pg_words_q[pg_beats_q-8]<=pg_out_data;
      pg_beats_q<=pg_beats_q+8'd1;
     end
     if(pg_rsp_valid&&pg_rsp_ready&&!pg_bad)pg_state_q<=PG_META;
    end
    PG_META:if(chain_meta_rsp_valid&&chain_meta_rsp_ready)pg_state_q<=PG_READY;
    default:pg_state_q<=PG_IDLE;
   endcase
  end
 end
 always @(posedge clk)begin
  if(rst||cancel||state_q==IDLE||state_q==ERROR)begin
   sp_wait_q<=0;ds_wait_q<=0;meta_wait_q<=0;
   expected_sp_q<=0;expected_ds_q<=0;expected_meta_program_q<=0;
  end else begin
   if(sp_rsp_valid&&sp_rsp_ready&&current_sp_error)sp_wait_q<=0;
   if(ds_rsp_valid&&ds_rsp_ready&&current_ds_error)ds_wait_q<=0;
   if(meta_rsp_valid&&meta_rsp_ready&&metadata_reply&&current_meta_error)meta_wait_q<=0;
   if(sp_rd_valid&&sp_rd_ready)begin sp_wait_q<=1;expected_sp_q<=sp_rd_tag;end
   if(ds_req_valid&&ds_req_ready)begin ds_wait_q<=1;expected_ds_q<=ds_req_tag;end
   if(meta_req_valid&&meta_req_ready)begin meta_wait_q<=1;expected_meta_program_q<=meta_req_program;end
  end
  if(rst)generation_counter_q<=0;
  else if(req_valid&&req_ready)generation_counter_q<=generation_counter_q+16'd1;
  if(rst||cancel)begin
   state_q<=IDLE;generation_q<=0;user_tag_q<=0;input_q<=0;input_bytes_q<=0;init_beats_q<=0;seed_q<=0;
   r_q<=0;f_q<=0;e_q<=0;a_q<=0;round_q<=0;digest_q<=0;error_program_q<=0;error_code_q<=0;error_pc_q<=0;error_opcode_q<=0;
  end else begin
   case(state_q)
    IDLE:if(req_valid&&req_ready)begin
     generation_q<=generation_counter_q+16'd1;user_tag_q<=req_tag;input_q<=req_input;input_bytes_q<=req_input_bytes;
     init_beats_q<=0;seed_q<=0;digest_q<=0;error_program_q<=0;error_code_q<=req_input_bytes>80?2'd1:2'd0;error_pc_q<=0;error_opcode_q<=0;
     state_q<=req_input_bytes>80?ERROR:INIT_REQUEST;
    end
    INIT_REQUEST:if(init_req_ready)state_q<=INIT_STREAM;
    INIT_STREAM:begin
     if(init_wr_valid&&init_wr_ready&&!init_stale&&(HARDWARE_FILL||init_bad))begin error_code_q<=1;state_q<=ERROR;end
     else begin
      if(init_wr_valid&&init_wr_ready&&!init_stale)init_beats_q<=init_beats_q+18'd1;
      if(init_rsp_valid&&init_rsp_ready&&init_rsp_tag==generation_q)begin
       if(init_rsp_error)begin error_code_q<=1;state_q<=ERROR;end
       else begin seed_q<=init_rsp_seed;state_q<=HARDWARE_FILL?FILL_START:CHAIN_START;end
      end
     end
    end
    FILL_START:begin
     if(init_wr_valid&&init_wr_ready&&!init_stale)begin error_code_q<=1;state_q<=ERROR;end
     else if(fill_req_ready)state_q<=FILL_RUN;
    end
    FILL_RUN:begin
     if(sp_wr_valid&&sp_wr_ready)init_beats_q<=init_beats_q+18'd1;
     if(init_wr_valid&&init_wr_ready&&!init_stale)begin error_code_q<=1;state_q<=ERROR;end
     else if(fill_rsp_valid)begin
      if(fill_rsp_tag!=generation_q||init_beats_q!=SCRATCHPAD_BYTES/16)begin error_code_q<=3;state_q<=ERROR;end
      else begin seed_q<=fill_rsp_seed;state_q<=CHAIN_START;end
     end
    end
    CHAIN_START:if(chain_start_ready)state_q<=RUN;
    RUN:begin
     if(program_done_valid&&chain_program_done_ready&&program_done_seed_valid)seed_q<=program_done_seed;
     if(pg_bad)begin error_program_q<=pg_program_q;error_code_q<=3;state_q<=ERROR;end
     else if(chain_error_valid)begin
      error_program_q<=chain_error_program;error_code_q<=chain_error_code;error_pc_q<=chain_error_pc;error_opcode_q<=chain_error_opcode;state_q<=ERROR;
     end else if((meta_rsp_valid&&metadata_reply&&current_meta_error&&meta_rsp_error)||
                 (ds_rsp_valid&&dataset_reply&&current_ds_error&&ds_rsp_error)||
                 (sp_rsp_valid&&exec_reply&&current_sp_error&&sp_rsp_error))begin error_code_q<=3;state_q<=ERROR;end
     else if(chain_done_valid)begin
      r_q<=chain_done_r;f_q<=chain_done_f;e_q<=chain_done_e;a_q<=chain_done_a;round_q<=chain_done_round_mode;state_q<=FIN_START;
     end
    end
    FIN_START:if(final_req_ready)state_q<=FIN_WAIT;
    FIN_WAIT:if(final_rsp_valid)begin
     r_q<=final_rsp_r;f_q<=final_rsp_f;e_q<=final_rsp_e;a_q<=final_rsp_a;round_q<=final_rsp_round;
     if(final_rsp_error||final_rsp_tag!=generation_q)begin digest_q<=0;error_code_q<=3;state_q<=ERROR;end
     else begin digest_q<=final_rsp_digest;state_q<=RETURN;end
    end
    RETURN,ERROR:if(rsp_ready)state_q<=IDLE;
    default:begin error_code_q<=3;state_q<=ERROR;end
   endcase
  end
 end
endmodule
`default_nettype wire
