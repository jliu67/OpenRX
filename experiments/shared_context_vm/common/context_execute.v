// SPDX-License-Identifier: BSD-3-Clause
// Native RandomX instruction execution, including iterative division/square root.
`default_nettype none
module openrx_context_execute #(parameter integer SERIAL_IADD=0,MUL_RADIX4=0,FP_LANES=2,DIVSQRT_LANES=2,PREPARED_RCP=0) (

    input wire fetch_enable,input wire[3:0]fetch_dispatch,
    input wire[31:0]prog_rsp_transport_tag,output wire[31:0]prog_transport_tag,
    output wire[1:0]prog_context,output wire[15:0]prog_req_epoch,
    input wire interleave,input wire [3:0] starts,program_available,memory_available,program_credit,memory_credit,
    input wire [3:0][5:0] epochs,input wire cancel_valid,input wire [1:0] cancel_context,
    input wire [2:0] hold_cycles,input wire [31:0] cycle,
    output wire [1:0] context_index,output wire context_valid,
    input wire clk,rst,
    input wire req_valid,output wire req_ready,input wire [15:0] req_tag,
    input wire req_v2,input wire [1:0] req_round_mode,
    input wire [511:0] req_r,req_f,req_e,req_a,
    input wire [63:0] req_emask0,req_emask1,req_program_addr,
    output wire prog_valid,input wire prog_ready,output wire [63:0] prog_addr,
    output wire [15:0] prog_tag,input wire prog_rsp_valid,output wire prog_rsp_ready,
    input wire [15:0] prog_rsp_tag,input wire [63:0] prog_rsp_instruction,
    input wire [15:0] req_program_epoch,prog_rsp_prepared_epoch,
    input wire [8:0] prog_rsp_prepared_pc,
    input wire prog_rsp_prepared_error,prog_rsp_rcp_valid,prog_rsp_rcp_nop,
    input wire [31:0] prog_rsp_rcp_divisor,input wire [63:0] prog_rsp_rcp_value,
    output wire [15:0] mem_tag,
    output wire rd_valid,input wire rd_ready,output wire [20:0] rd_addr,
    input wire rsp_valid,output wire rsp_ready,input wire [15:0] rsp_tag,
    input wire [127:0] rsp_data,
    output wire wr_valid,input wire wr_ready,output wire [20:0] wr_addr,
    output wire [127:0] wr_data,output wire [15:0] wr_strb,
    output wire ret_valid,input wire ret_ready,output wire [15:0] ret_tag,
    output wire [511:0] ret_r,ret_f,ret_e,output wire [1:0] ret_round_mode,
    output wire error_valid,input wire error_ready,output wire [15:0] error_tag,
    output wire [8:0] error_pc,output wire [7:0] error_opcode,
    output wire commit_valid,output wire [15:0] commit_tag,
    output wire [8:0] commit_pc,output wire [7:0] commit_opcode,output wire [511:0] commit_r,
    output wire [8:0] commit_next_pc,commit_branch_target,
    output wire [511:0] commit_f,commit_e,output wire [1:0] commit_round_mode
);
`include "randomx_opcode_ceils.vh"

    initial begin
     if(PREPARED_RCP!=1||SERIAL_IADD!=0||MUL_RADIX4!=0||FP_LANES!=2||DIVSQRT_LANES!=2)$fatal(1,"fixed validated component parameters");
    end


    reg [1:0] select_context,round_robin_q,serial_cursor_q;
    reg select_valid;reg [3:0] eligible;integer k,c;
    assign context_index=select_context;assign context_valid=select_valid;
    always @*begin
     eligible=0;
     for(k=0;k<4;k=k+1)begin
      case(state_q_bank[k])
       IDLE:eligible[k]=starts[k];
       FETCH_REQ:eligible[k]=fetch_enable?(queued_available[k]&&fetch_dispatch[k]):program_credit[k];
       FETCH_RSP:eligible[k]=!fetch_enable&&program_available[k];
       EXEC,IADD_SECOND,STORE_REQ,RETURN,ERROR:eligible[k]=1;
       MEM_REQ:eligible[k]=memory_credit[k];MEM_RSP:eligible[k]=memory_available[k];
       MUL_REQ:eligible[k]=mul_requests[k];MUL_WAIT:eligible[k]=mul_returns[k];
       FP_REQ:eligible[k]=fp_requests[k];FP_WAIT:eligible[k]=fp_returns[k];
       DIV_REQ:eligible[k]=div_requests[k];DIV_WAIT:eligible[k]=div_returns[k];
       default:eligible[k]=0;
      endcase
     end
     select_context=round_robin_q;select_valid=0;c=0;
     for(k=0;k<4;k=k+1)begin
      c=(integer'(round_robin_q)+k)&3;
      if(!select_valid&&eligible[c]&&(interleave||c==integer'(serial_cursor_q)))begin
       select_context=c[1:0];select_valid=!rst&&!cancel_valid;
      end
     end
    end
    always @(posedge clk)begin
     if(rst)begin round_robin_q<=0;serial_cursor_q<=0;end
     else if(select_valid)begin
      round_robin_q<=select_context+2'd1;
      if(ret_valid&&ret_ready&&serial_cursor_q!=3)serial_cursor_q<=serial_cursor_q+2'd1;
     end
    end

    localparam [4:0] IDLE=0,FETCH_REQ=1,FETCH_RSP=2,EXEC=3,MEM_REQ=4,MEM_RSP=5,
        STORE_REQ=6,IADD_SECOND=7,RETURN=8,ERROR=9,MUL_REQ=10,MUL_WAIT=11,RCP_REQ=12,RCP_WAIT=13,FP_REQ=14,FP_WAIT=15,DIV_REQ=16,DIV_WAIT=17;
    localparam [4:0] ADD_RS=0,ADD_M=1,SUB_R=2,SUB_M=3,NEG_R=4,XOR_R=5,XOR_M=6,
        ROR_R=7,ROL_R=8,SWAP_R=9,STORE=10,MUL_R=11,MUL_M=12,HIGH_R=13,HIGH_M=14,
        SIGNED_HIGH_R=15,SIGNED_HIGH_M=16,RCP=17,BRANCH=18,
        FSWAP=19,FADD_R=20,FADD_M=21,FSUB_R=22,FSUB_M=23,FSCAL=24,FMUL=25,ROUND=26,FDIV=27,FSQRT=28,BAD=31;
    reg [4:0] state_q_bank[0:3];
    wire [4:0] state_q=state_q_bank[select_context];
    reg [8:0] pc_q_bank[0:3];
    wire [8:0] pc_q=pc_q_bank[select_context];
    reg [15:0] tag_q_bank[0:3];
    wire [15:0] tag_q=tag_q_bank[select_context];
    reg [15:0] program_epoch_q_bank[0:3];
    wire [15:0] program_epoch_q=program_epoch_q_bank[select_context];
    reg [63:0] prepared_rcp_q_bank[0:3];
    wire [63:0] prepared_rcp_q=prepared_rcp_q_bank[select_context];
    wire prepared_packet_valid;wire [63:0] prepared_packet_value;
    generate if(PREPARED_RCP==1)begin: prepared_guard
        randomx_prepared_rcp_guard guard(
            .expected_epoch(program_epoch_q),.packet_epoch(effective_epoch),
            .expected_pc(pc_q),.packet_pc(effective_pc),
            .instruction(effective_word),.packet_value(effective_value),
            .packet_error(effective_error),.packet_rcp_valid(effective_rcp),
            .packet_nop(effective_nop),.packet_divisor(effective_divisor),
            .valid(prepared_packet_valid),.value(prepared_packet_value));
    end else if(PREPARED_RCP==0)begin: unprepared_guard
        assign prepared_packet_valid=1;assign prepared_packet_value=0;
    end else begin: invalid_prepared_parameter
        integer_execute_requires_PREPARED_RCP_0_or_1 invalid();
    end endgenerate
    reg v2_q_bank[0:3];
    wire v2_q=v2_q_bank[select_context];
    reg [1:0] round_q_bank[0:3];
    wire [1:0] round_q=round_q_bank[select_context];
    reg [63:0] program_q_bank[0:3];
    wire [63:0] program_q=program_q_bank[select_context];
    reg [63:0] instruction_q_bank[0:3];
    wire [63:0] instruction_q=instruction_q_bank[select_context];
    reg [63:0] tmp_q_bank[0:3];
    wire [63:0] tmp_q=tmp_q_bank[select_context];
    reg [63:0] emask0_q_bank[0:3];
    wire [63:0] emask0_q=emask0_q_bank[select_context];
    reg [63:0] emask1_q_bank[0:3];
    wire [63:0] emask1_q=emask1_q_bank[select_context];
    reg [511:0] r_q_bank[0:3];
    wire [511:0] r_q=r_q_bank[select_context];
    reg [511:0] f_q_bank[0:3];
    wire [511:0] f_q=f_q_bank[select_context];
    reg [511:0] e_q_bank[0:3];
    wire [511:0] e_q=e_q_bank[select_context];
    reg [511:0] a_q_bank[0:3];
    wire [511:0] a_q=a_q_bank[select_context];
    reg [20:0] address_q_bank[0:3];
    wire [20:0] address_q=address_q_bank[select_context];
    reg commit_q_bank[0:3];
    wire commit_q=commit_q_bank[select_context];
    reg [8:0] commit_pc_q_bank[0:3];
    wire [8:0] commit_pc_q=commit_pc_q_bank[select_context];
    reg [8:0] commit_next_q_bank[0:3];
    wire [8:0] commit_next_q=commit_next_q_bank[select_context];
    reg [8:0] commit_target_q_bank[0:3];
    wire [8:0] commit_target_q=commit_target_q_bank[select_context];
    reg [7:0] commit_opcode_q_bank[0:3];
    wire [7:0] commit_opcode_q=commit_opcode_q_bank[select_context];
    wire [2:0] dst=instruction_q[10:8],src=instruction_q[18:16];
    wire [63:0] rd=r_q[64*dst+:64],rs=r_q[64*src+:64];
    wire [63:0] immediate={{32{instruction_q[63]}},instruction_q[63:32]};
    wire [63:0] register_operand=dst==src ? immediate : rs;
    wire [63:0] displacement=dst==3'd5 ? immediate : 64'b0;
    wire [63:0] shifted=rs<<instruction_q[27:26];
    wire [5:0] rotate=dst==src ? instruction_q[37:32] : rs[5:0];
    function [4:0] decode;
        input [7:0] opcode;
        begin
            if(opcode<CEIL_IADD_RS)decode=ADD_RS;
            else if(opcode<CEIL_IADD_M)decode=ADD_M;
            else if(opcode<CEIL_ISUB_R)decode=SUB_R;
            else if(opcode<CEIL_ISUB_M)decode=SUB_M;
            else if(opcode<CEIL_IMUL_R)decode=MUL_R;
            else if(opcode<CEIL_IMUL_M)decode=MUL_M;
            else if(opcode<CEIL_IMULH_R)decode=HIGH_R;
            else if(opcode<CEIL_IMULH_M)decode=HIGH_M;
            else if(opcode<CEIL_ISMULH_R)decode=SIGNED_HIGH_R;
            else if(opcode<CEIL_ISMULH_M)decode=SIGNED_HIGH_M;
            else if(opcode<CEIL_IMUL_RCP)decode=RCP;
            else if(opcode<CEIL_INEG_R)decode=NEG_R;
            else if(opcode<CEIL_IXOR_R)decode=XOR_R;
            else if(opcode<CEIL_IXOR_M)decode=XOR_M;
            else if(opcode<CEIL_IROR_R)decode=ROR_R;
            else if(opcode<CEIL_IROL_R)decode=ROL_R;
            else if(opcode<CEIL_ISWAP_R)decode=SWAP_R;
            else if(opcode<CEIL_FSWAP_R)decode=FSWAP;
            else if(opcode<CEIL_FADD_R)decode=FADD_R;
            else if(opcode<CEIL_FADD_M)decode=FADD_M;
            else if(opcode<CEIL_FSUB_R)decode=FSUB_R;
            else if(opcode<CEIL_FSUB_M)decode=FSUB_M;
            else if(opcode<CEIL_FSCAL_R)decode=FSCAL;
            else if(opcode<CEIL_FMUL_R)decode=FMUL;
            else if(opcode<CEIL_FDIV_M)decode=FDIV;
            else if(opcode<CEIL_FSQRT_R)decode=FSQRT;
            else if(opcode<CEIL_CBRANCH)decode=BRANCH;
            else if(opcode<CEIL_CFROUND)decode=ROUND;
            else decode=STORE;
        end
    endfunction
    wire [4:0] kind=decode(instruction_q[7:0]);
    wire fp_memory=kind==FADD_M||kind==FSUB_M||kind==FDIV;
    wire [31:0] memory_mask=fp_memory ?
        (instruction_q[25:24]!=0 ? 32'h00003ff8 : 32'h0003fff8) : kind==STORE ?
        (instruction_q[31:28]>=14 ? 32'h001ffff8 :
            (instruction_q[25:24]!=0 ? 32'h00003ff8 : 32'h0003fff8)) :
        (dst==src ? 32'h001ffff8 :
            (instruction_q[25:24]!=0 ? 32'h00003ff8 : 32'h0003fff8));
    wire [31:0] memory_base=fp_memory ? rs[31:0] : kind==STORE ? rd[31:0] : (dst==src ? 32'b0 : rs[31:0]);
    // Address masks retain <=21 bits, so modulo32 addition equals native low64 bits.
    wire [31:0] memory_address=(memory_base+instruction_q[63:32])&memory_mask;
    wire [63:0] memory_value=address_q[3] ? rsp_data[127:64] : rsp_data[63:0];
    reg [63:0] mul_a_q_bank[0:3];
    wire [63:0] mul_a_q=mul_a_q_bank[select_context];
    reg [63:0] mul_b_q_bank[0:3];
    wire [63:0] mul_b_q=mul_b_q_bank[select_context];
    reg mul_high_q_bank[0:3];
    wire mul_high_q=mul_high_q_bank[select_context];
    reg mul_signed_q_bank[0:3];
    wire mul_signed_q=mul_signed_q_bank[select_context];
    wire mul_req_ready,mul_rsp_valid,rcp_req_ready,rcp_rsp_valid,rcp_rsp_nop;
    wire [15:0] mul_rsp_tag,rcp_rsp_tag;
    wire [63:0] mul_result,rcp_result;
    wire rcp_nop=instruction_q[63:32]==0 || (instruction_q[63:32]&(instruction_q[63:32]-32'd1))==0;
    wire [3:0] mul_requests,mul_returns,fp_requests,fp_returns,div_requests,div_returns;
    wire mul_busy,fp_busy,div_busy;wire[127:0]mul_result_wide;
    openrx_shared_fu #(.KIND(0)) multiplier(
     .clk(clk),.rst(rst),.cycle(cycle),.epochs(epochs),.cancel_valid(cancel_valid),.cancel_context(cancel_context),
     .context_index(select_context),.selected(select_valid),.req_valid(state_q==MUL_REQ),.req_ready(mul_req_ready),.core_owner(tag_q),
     .a({64'b0,mul_a_q}),.b({64'b0,mul_b_q}),.op(2'b0),.round_mode(2'b0),.high(mul_high_q),.signed_high(mul_signed_q),
     .rsp_valid(mul_rsp_valid),.rsp_ready(select_valid&&state_q==MUL_WAIT),.rsp_owner(mul_rsp_tag),.result(mul_result_wide),.flags(),
     .request_available(mul_requests),.return_available(mul_returns),.hold_cycles(hold_cycles),.busy(mul_busy),.accepted(),.returned(),.consumed(),.stale_dropped(),.held_cycles(),.peak_reserved());
    assign mul_result=mul_result_wide[63:0];
    randomx_reciprocal32 reciprocal(
        .clk(clk),.rst(rst),.req_valid(!rst && select_valid && PREPARED_RCP==0 && state_q==RCP_REQ),.req_ready(rcp_req_ready),
        .req_tag(tag_q),.req_divisor(instruction_q[63:32]),.rsp_valid(rcp_rsp_valid),
        .rsp_ready(!rst && select_valid && state_q==RCP_WAIT),.rsp_tag(rcp_rsp_tag),.rsp_result(rcp_result),.rsp_nop(rcp_rsp_nop));
    reg [127:0] fp_a_q_bank[0:3];
    wire [127:0] fp_a_q=fp_a_q_bank[select_context];
    reg [127:0] fp_b_q_bank[0:3];
    wire [127:0] fp_b_q=fp_b_q_bank[select_context];reg [1:0] fp_op_q_bank[0:3];
    wire [1:0] fp_op_q=fp_op_q_bank[select_context];
    wire fp_ready,fp_valid;wire [15:0] fp_tag;wire [127:0] fp_result;wire [4:0] fp_flags;
    wire [1:0] fdst=instruction_q[9:8],fsrc=instruction_q[17:16];
    wire [127:0] fr=f_q[128*fdst+:128],er=e_q[128*fdst+:128],ar=a_q[128*fsrc+:128];
    wire [63:0] packed_low,packed_high;
    randomx_i32_to_f64 fp_memory_low(memory_value[31:0],packed_low);
    randomx_i32_to_f64 fp_memory_high(memory_value[63:32],packed_high);
    openrx_shared_fu #(.KIND(1)) floating_unit(
     .clk(clk),.rst(rst),.cycle(cycle),.epochs(epochs),.cancel_valid(cancel_valid),.cancel_context(cancel_context),
     .context_index(select_context),.selected(select_valid),.req_valid(state_q==FP_REQ),.req_ready(fp_ready),.core_owner(tag_q),
     .a(fp_a_q),.b(fp_b_q),.op(fp_op_q),.round_mode(round_q),.high(1'b0),.signed_high(1'b0),
     .rsp_valid(fp_valid),.rsp_ready(select_valid&&state_q==FP_WAIT),.rsp_owner(fp_tag),.result(fp_result),.flags(fp_flags),
     .request_available(fp_requests),.return_available(fp_returns),.hold_cycles(hold_cycles),.busy(fp_busy),.accepted(),.returned(),.consumed(),.stale_dropped(),.held_cycles(),.peak_reserved());
    wire div_ready,div_valid;wire [15:0] div_tag;wire [127:0] div_result;wire [4:0] div_flags;
    openrx_shared_fu #(.KIND(2)) division_unit(
     .clk(clk),.rst(rst),.cycle(cycle),.epochs(epochs),.cancel_valid(cancel_valid),.cancel_context(cancel_context),
     .context_index(select_context),.selected(select_valid),.req_valid(state_q==DIV_REQ),.req_ready(div_ready),.core_owner(tag_q),
     .a(fp_a_q),.b(fp_b_q),.op({1'b0,kind==FSQRT}),.round_mode(round_q),.high(1'b0),.signed_high(1'b0),
     .rsp_valid(div_valid),.rsp_ready(select_valid&&state_q==DIV_WAIT),.rsp_owner(div_tag),.result(div_result),.flags(div_flags),
     .request_available(div_requests),.return_available(div_returns),.hold_cycles(hold_cycles),.busy(div_busy),.accepted(),.returned(),.consumed(),.stale_dropped(),.held_cycles(),.peak_reserved());
    // Native dynamicMantissaMask includes 52 fraction and four dynamic exponent bits.
    wire [63:0] denominator_low=(packed_low&64'h00ffffffffffffff)|emask0_q;
    wire [63:0] denominator_high=(packed_high&64'h00ffffffffffffff)|emask1_q;
    wire [5:0] cf_rotate=instruction_q[37:32];
    wire [63:0] cf_value=(rs>>cf_rotate)|(rs<<(64-cf_rotate));
    // Native compile-time usage is lexical, never updated by a replayed instruction.
    // Each CBRANCH marks all registers used, so later branches cannot replay an older branch.
    reg [8:0] usage_next_q_bank[0:3][0:7];
    wire [8:0] usage_next_q[0:7];genvar usage_next_q_k;generate for(usage_next_q_k=0;usage_next_q_k<8;usage_next_q_k=usage_next_q_k+1)begin: alias_usage_next_q assign usage_next_q[usage_next_q_k]=usage_next_q_bank[select_context][usage_next_q_k];end endgenerate
    reg [8:0] compile_next_q_bank[0:3];
    wire [8:0] compile_next_q=compile_next_q_bank[select_context];
    reg [8:0] branch_target_q_bank[0:3];
    wire [8:0] branch_target_q=branch_target_q_bank[select_context];
    reg [8:0] branch_pc_q_bank[0:3];
    wire [8:0] branch_pc_q=branch_pc_q_bank[select_context];
    integer usage_index,reset_context;
    wire [4:0] condition_shift={1'b0,instruction_q[31:28]}+CONDITION_OFFSET;
    wire [63:0] branch_immediate=(immediate|(64'd1<<condition_shift))&~(64'd1<<(condition_shift-1));
    wire [63:0] branch_result=rd+branch_immediate;
    wire branch_taken=(branch_result[31:0]&(CONDITION_MASK<<condition_shift))==0;
    wire [8:0] branch_target=pc_q==compile_next_q?usage_next_q[dst]:branch_target_q;
    wire [63:0] first_iadd;
    generate
        if(SERIAL_IADD==0)begin: two_adds
            assign first_iadd=shifted+displacement;
        end else begin: shared_add
            assign first_iadd=0;
        end
        if(SERIAL_IADD!=0 && SERIAL_IADD!=1)begin: invalid_parameter
            integer_execute_requires_SERIAL_IADD_0_or_1 invalid();
        end
    endgenerate
    wire [63:0] add_left=state_q==EXEC && kind==ADD_RS && SERIAL_IADD!=0 ? shifted : rd;
    wire [63:0] add_right=state_q==IADD_SECOND ? tmp_q :
        state_q==MEM_RSP ? memory_value : (SERIAL_IADD!=0 ? displacement : first_iadd);
    wire [63:0] add_result=add_left+add_right;
    wire old_program=prog_rsp_tag!=tag_q,old_memory=rsp_tag!=tag_q;
    assign req_ready=!rst && select_valid && state_q==IDLE;
    wire[3:0]fetch_need,queued_available;wire[35:0]fetch_pcs;wire[255:0]fetch_bases;
    wire[63:0]fetch_owners,fetch_epochs;
    wire[63:0]queued_word,queued_value;wire[31:0]queued_divisor;
    wire[15:0]queued_owner,queued_epoch;wire[8:0]queued_pc;wire queued_error,queued_rcp,queued_nop;
    wire queue_pop=fetch_enable&&select_valid&&state_q==FETCH_REQ&&queued_available[select_context];
    genvar f;
    generate for(f=0;f<4;f=f+1)begin: fetch_descriptors
     assign fetch_need[f]=state_q_bank[f]==FETCH_REQ;
     assign fetch_pcs[9*f+:9]=pc_q_bank[f];assign fetch_bases[64*f+:64]=program_q_bank[f];
     assign fetch_owners[16*f+:16]=tag_q_bank[f];assign fetch_epochs[16*f+:16]=program_epoch_q_bank[f];
    end endgenerate
    wire[63:0]effective_word=fetch_enable?queued_word:prog_rsp_instruction;
    wire[63:0]effective_value=fetch_enable?queued_value:prog_rsp_rcp_value;
    wire[31:0]effective_divisor=fetch_enable?queued_divisor:prog_rsp_rcp_divisor;
    wire[15:0]effective_epoch=fetch_enable?queued_epoch:prog_rsp_prepared_epoch;
    wire[8:0]effective_pc=fetch_enable?queued_pc:prog_rsp_prepared_pc;
    wire effective_error=fetch_enable?queued_error:prog_rsp_prepared_error;
    wire effective_rcp=fetch_enable?queued_rcp:prog_rsp_rcp_valid;
    wire effective_nop=fetch_enable?queued_nop:prog_rsp_rcp_nop;
    openrx_shared_fetch fetcher(
     .clk(clk),.rst(rst),.enable(fetch_enable),.cycle(cycle),.epochs(epochs),.cancel_valid(cancel_valid),.cancel_context(cancel_context),
     .need(fetch_need),.credit(program_credit),.pcs(fetch_pcs),.bases(fetch_bases),.owners(fetch_owners),.image_epochs(fetch_epochs),
     .bypass_valid(!rst&&select_valid&&state_q==FETCH_REQ),.bypass_context(select_context),
     .bypass_addr(program_q+{52'b0,pc_q,3'b0}),.bypass_owner(tag_q),.bypass_epoch(program_epoch_q),
     .bypass_rsp_ready(!rst&&select_valid&&(old_program||state_q==IDLE||state_q==FETCH_RSP)),
     .req_valid(prog_valid),.req_ready(prog_ready),.req_context(prog_context),.req_addr(prog_addr),.req_owner(prog_tag),.req_epoch(prog_req_epoch),.req_token(prog_transport_tag),
     .rsp_valid(prog_rsp_valid),.rsp_ready(prog_rsp_ready),.rsp_token(prog_rsp_transport_tag),.rsp_owner(prog_rsp_tag),.rsp_epoch(prog_rsp_prepared_epoch),.rsp_pc(prog_rsp_prepared_pc),
     .rsp_word(prog_rsp_instruction),.rsp_value(prog_rsp_rcp_value),.rsp_divisor(prog_rsp_rcp_divisor),.rsp_error(prog_rsp_prepared_error),.rsp_rcp(prog_rsp_rcp_valid),.rsp_nop(prog_rsp_rcp_nop),
     .pop_context(select_context),.pop(queue_pop),.available(queued_available),.head_word(queued_word),.head_value(queued_value),.head_divisor(queued_divisor),
     .head_owner(queued_owner),.head_epoch(queued_epoch),.head_pc(queued_pc),.head_error(queued_error),.head_rcp(queued_rcp),.head_nop(queued_nop),.fault());

    assign mem_tag=tag_q;
    assign rd_valid=!rst && select_valid && state_q==MEM_REQ;assign rd_addr={address_q[20:4],4'b0};
    assign rsp_ready=!rst && select_valid && (old_memory || state_q==IDLE || state_q==MEM_RSP);
    assign wr_valid=!rst && select_valid && state_q==STORE_REQ;assign wr_addr={address_q[20:4],4'b0};
    assign wr_data=address_q[3] ? {rs,64'b0} : {64'b0,rs};
    assign wr_strb=address_q[3] ? 16'hff00 : 16'h00ff;
    assign ret_valid=!rst && select_valid && state_q==RETURN;assign ret_tag=tag_q;
    assign ret_r=r_q;assign ret_f=f_q;assign ret_e=e_q;assign ret_round_mode=round_q;
    assign error_valid=!rst && select_valid && state_q==ERROR;assign error_tag=tag_q;
    assign error_pc=pc_q;assign error_opcode=instruction_q[7:0];
    assign commit_valid=!rst && select_valid && commit_q;assign commit_tag=tag_q;
    assign commit_next_pc=commit_next_q;assign commit_branch_target=commit_target_q;
    assign commit_f=f_q;assign commit_e=e_q;assign commit_round_mode=round_q;
    assign commit_pc=commit_pc_q;assign commit_opcode=commit_opcode_q;assign commit_r=r_q;
    task retire_at;
        input [8:0] next_pc;
        begin
            commit_q_bank[select_context]<=1;commit_pc_q_bank[select_context]<=pc_q;commit_opcode_q_bank[select_context]<=instruction_q[7:0];pc_q_bank[select_context]<=next_pc;
            commit_next_q_bank[select_context]<=next_pc;commit_target_q_bank[select_context]<=kind==BRANCH?branch_target:9'h1ff;
            if(next_pc==(v2_q ? 9'd384 : 9'd256))state_q_bank[select_context]<=RETURN;
            else state_q_bank[select_context]<=FETCH_REQ;
        end
    endtask
    task retire_instruction;
        begin retire_at(pc_q+9'd1);end
    endtask
    always @(posedge clk)begin
        if(rst||cancel_valid)begin
            for(reset_context=0;reset_context<4;reset_context=reset_context+1)begin
             if(rst||reset_context==integer'(cancel_context))begin
            state_q_bank[reset_context]<=IDLE;pc_q_bank[reset_context]<=0;tag_q_bank[reset_context]<=0;program_epoch_q_bank[reset_context]<=0;prepared_rcp_q_bank[reset_context]<=0;v2_q_bank[reset_context]<=0;round_q_bank[reset_context]<=0;program_q_bank[reset_context]<=0;
            instruction_q_bank[reset_context]<=0;tmp_q_bank[reset_context]<=0;r_q_bank[reset_context]<=0;f_q_bank[reset_context]<=0;e_q_bank[reset_context]<=0;a_q_bank[reset_context]<=0;address_q_bank[reset_context]<=0;
            fp_a_q_bank[reset_context]<=0;fp_b_q_bank[reset_context]<=0;fp_op_q_bank[reset_context]<=0;emask0_q_bank[reset_context]<=0;emask1_q_bank[reset_context]<=0;
            commit_q_bank[reset_context]<=0;commit_pc_q_bank[reset_context]<=0;commit_opcode_q_bank[reset_context]<=0;commit_next_q_bank[reset_context]<=0;commit_target_q_bank[reset_context]<=0;
            mul_a_q_bank[reset_context]<=0;mul_b_q_bank[reset_context]<=0;mul_high_q_bank[reset_context]<=0;mul_signed_q_bank[reset_context]<=0;
            compile_next_q_bank[reset_context]<=0;branch_target_q_bank[reset_context]<=0;branch_pc_q_bank[reset_context]<=0;
            for(usage_index=0;usage_index<8;usage_index=usage_index+1)usage_next_q_bank[reset_context][usage_index]<=0;
             end
            end
        end else if(select_valid)begin
            commit_q_bank[select_context]<=0;
            if(state_q==EXEC && pc_q==compile_next_q)begin
                compile_next_q_bank[select_context]<=pc_q+9'd1;
                if(kind==BRANCH)begin
                    branch_target_q_bank[select_context]<=usage_next_q[dst];branch_pc_q_bank[select_context]<=pc_q;
                    for(usage_index=0;usage_index<8;usage_index=usage_index+1)usage_next_q_bank[select_context][usage_index]<=pc_q+9'd1;
                end else if(kind==SWAP_R)begin
                    if(dst!=src)begin usage_next_q_bank[select_context][dst]<=pc_q+9'd1;usage_next_q_bank[select_context][src]<=pc_q+9'd1;end
                end else if(kind<BRANCH && kind!=STORE && !(kind==RCP && rcp_nop))usage_next_q_bank[select_context][dst]<=pc_q+9'd1;
            end
            case(state_q)
                IDLE:if(req_valid)begin
                    tag_q_bank[select_context]<=req_tag;program_epoch_q_bank[select_context]<=req_program_epoch;prepared_rcp_q_bank[select_context]<=0;v2_q_bank[select_context]<=req_v2;round_q_bank[select_context]<=req_round_mode;program_q_bank[select_context]<=req_program_addr;
                    r_q_bank[select_context]<=req_r;f_q_bank[select_context]<=req_f;e_q_bank[select_context]<=req_e;a_q_bank[select_context]<=req_a;emask0_q_bank[select_context]<=req_emask0;emask1_q_bank[select_context]<=req_emask1;pc_q_bank[select_context]<=0;state_q_bank[select_context]<=FETCH_REQ;
                    compile_next_q_bank[select_context]<=0;branch_target_q_bank[select_context]<=0;branch_pc_q_bank[select_context]<=0;
                    for(usage_index=0;usage_index<8;usage_index=usage_index+1)usage_next_q_bank[select_context][usage_index]<=0;
                end
                FETCH_REQ:if(fetch_enable)begin
                    if(queue_pop)begin
                        instruction_q_bank[select_context]<=effective_word;prepared_rcp_q_bank[select_context]<=prepared_packet_value;
                        state_q_bank[select_context]<=prepared_packet_valid?EXEC:ERROR;
                    end
                end else if(prog_ready)state_q_bank[select_context]<=FETCH_RSP;
                FETCH_RSP:if(prog_rsp_valid && !old_program)begin
                    instruction_q_bank[select_context]<=prog_rsp_instruction;prepared_rcp_q_bank[select_context]<=prepared_packet_value;
                    state_q_bank[select_context]<=prepared_packet_valid?EXEC:ERROR;
                end
                EXEC:case(kind)
                    ADD_RS:if(SERIAL_IADD!=0)begin tmp_q_bank[select_context]<=add_result;state_q_bank[select_context]<=IADD_SECOND;end
                        else begin r_q_bank[select_context][64*dst+:64]<=add_result;retire_instruction();end
                    SUB_R:begin r_q_bank[select_context][64*dst+:64]<=rd-register_operand;retire_instruction();end
                    NEG_R:begin r_q_bank[select_context][64*dst+:64]<=~rd+64'd1;retire_instruction();end
                    XOR_R:begin r_q_bank[select_context][64*dst+:64]<=rd^register_operand;retire_instruction();end
                    ROR_R:begin r_q_bank[select_context][64*dst+:64]<=(rd>>rotate)|(rd<<(64-rotate));retire_instruction();end
                    ROL_R:begin r_q_bank[select_context][64*dst+:64]<=(rd<<rotate)|(rd>>(64-rotate));retire_instruction();end
                    SWAP_R:begin
                        if(dst!=src)begin r_q_bank[select_context][64*dst+:64]<=rs;r_q_bank[select_context][64*src+:64]<=rd;end
                        retire_instruction();
                    end
                    ADD_M,SUB_M,XOR_M,MUL_M,HIGH_M,SIGNED_HIGH_M,FADD_M,FSUB_M,FDIV:begin address_q_bank[select_context]<=memory_address[20:0];state_q_bank[select_context]<=MEM_REQ;end
                    STORE:begin address_q_bank[select_context]<=memory_address[20:0];state_q_bank[select_context]<=STORE_REQ;end
                    MUL_R,HIGH_R,SIGNED_HIGH_R:begin
                        mul_a_q_bank[select_context]<=rd;mul_b_q_bank[select_context]<=kind==MUL_R?register_operand:rs;
                        mul_high_q_bank[select_context]<=kind!=MUL_R;mul_signed_q_bank[select_context]<=kind==SIGNED_HIGH_R;state_q_bank[select_context]<=MUL_REQ;
                    end
                    FSWAP:begin
                        if(dst<4)f_q_bank[select_context][128*fdst+:128]<={fr[63:0],fr[127:64]};
                        else e_q_bank[select_context][128*fdst+:128]<={er[63:0],er[127:64]};
                        retire_instruction();
                    end
                    FSCAL:begin f_q_bank[select_context][128*fdst+:128]<=fr^{2{64'h80f0000000000000}};retire_instruction();end
                    FADD_R,FSUB_R,FMUL:begin
                        fp_a_q_bank[select_context]<=kind==FMUL?er:fr;fp_b_q_bank[select_context]<=ar;
                        fp_op_q_bank[select_context]<=kind==FMUL?2'd2:kind==FSUB_R?2'd1:2'd0;state_q_bank[select_context]<=FP_REQ;
                    end
                    FSQRT:begin fp_a_q_bank[select_context]<=er;fp_b_q_bank[select_context]<=0;state_q_bank[select_context]<=DIV_REQ;end
                    ROUND:begin
                        if(!v2_q||cf_value[5:2]==0)round_q_bank[select_context]<=cf_value[1:0];
                        retire_instruction();
                    end
                    RCP:if(rcp_nop)retire_instruction();
                        else if(PREPARED_RCP==1)begin
                            mul_a_q_bank[select_context]<=rd;mul_b_q_bank[select_context]<=prepared_rcp_q;mul_high_q_bank[select_context]<=0;mul_signed_q_bank[select_context]<=0;state_q_bank[select_context]<=MUL_REQ;
                        end else state_q_bank[select_context]<=RCP_REQ;
                    BRANCH:begin
                        r_q_bank[select_context][64*dst+:64]<=branch_result;
                        retire_at(branch_taken?branch_target:pc_q+9'd1);
                    end
                    default:state_q_bank[select_context]<=ERROR;
                endcase
                FP_REQ:if(fp_ready)state_q_bank[select_context]<=FP_WAIT;
                FP_WAIT:if(fp_valid&&fp_tag==tag_q)begin
                    if(kind==FMUL)e_q_bank[select_context][128*fdst+:128]<=fp_result;
                    else f_q_bank[select_context][128*fdst+:128]<=fp_result;
                    retire_instruction();
                end
                DIV_REQ:if(div_ready)state_q_bank[select_context]<=DIV_WAIT;
                DIV_WAIT:if(div_valid&&div_tag==tag_q)begin e_q_bank[select_context][128*fdst+:128]<=div_result;retire_instruction();end
                IADD_SECOND:begin r_q_bank[select_context][64*dst+:64]<=add_result;retire_instruction();end
                MEM_REQ:if(rd_ready)state_q_bank[select_context]<=MEM_RSP;
                MEM_RSP:if(rsp_valid && !old_memory)begin
                    if(kind==FDIV)begin
                        fp_a_q_bank[select_context]<=er;fp_b_q_bank[select_context]<={denominator_high,denominator_low};state_q_bank[select_context]<=DIV_REQ;
                    end else if(fp_memory)begin
                        fp_a_q_bank[select_context]<=fr;fp_b_q_bank[select_context]<={packed_high,packed_low};fp_op_q_bank[select_context]<=kind==FSUB_M?2'd1:2'd0;state_q_bank[select_context]<=FP_REQ;
                    end else if(kind==MUL_M || kind==HIGH_M || kind==SIGNED_HIGH_M)begin
                        mul_a_q_bank[select_context]<=rd;mul_b_q_bank[select_context]<=memory_value;mul_high_q_bank[select_context]<=kind!=MUL_M;
                        mul_signed_q_bank[select_context]<=kind==SIGNED_HIGH_M;state_q_bank[select_context]<=MUL_REQ;
                    end else begin
                        if(kind==ADD_M)r_q_bank[select_context][64*dst+:64]<=add_result;
                        else if(kind==SUB_M)r_q_bank[select_context][64*dst+:64]<=rd-memory_value;
                        else r_q_bank[select_context][64*dst+:64]<=rd^memory_value;
                        retire_instruction();
                    end
                end
                STORE_REQ:if(wr_ready)retire_instruction();
                MUL_REQ:if(mul_req_ready)state_q_bank[select_context]<=MUL_WAIT;
                MUL_WAIT:if(mul_rsp_valid && mul_rsp_tag==tag_q)begin r_q_bank[select_context][64*dst+:64]<=mul_result;retire_instruction();end
                RCP_REQ:if(rcp_req_ready)state_q_bank[select_context]<=RCP_WAIT;
                RCP_WAIT:if(rcp_rsp_valid && rcp_rsp_tag==tag_q)begin
                    mul_a_q_bank[select_context]<=rd;mul_b_q_bank[select_context]<=rcp_result;mul_high_q_bank[select_context]<=0;mul_signed_q_bank[select_context]<=0;state_q_bank[select_context]<=MUL_REQ;
                end
                RETURN:if(ret_ready)state_q_bank[select_context]<=IDLE;
                ERROR:if(error_ready)state_q_bank[select_context]<=IDLE;
                default:state_q_bank[select_context]<=ERROR;
            endcase
        end
    end
endmodule
`default_nettype wire
