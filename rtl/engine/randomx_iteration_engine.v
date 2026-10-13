// SPDX-License-Identifier: BSD-3-Clause
// Actual iteration memory/control around an external bytecode execution stage.
`default_nettype none
module randomx_iteration_engine #(
    parameter integer LANES=4, SERIAL_CONVERT=0, COALESCE_LINES=1
) (
    input wire clk,rst,
    input wire req_valid,output wire req_ready,
    input wire [15:0] req_tag,input wire req_v2,
    input wire [1:0] req_round_mode,
    input wire [511:0] req_r,req_a,
    input wire [31:0] req_spaddr0,req_spaddr1,req_mx,req_ma,
    input wire [2:0] req_read0,req_read1,req_read2,req_read3,
    input wire [63:0] req_emask0,req_emask1,req_dataset_offset,req_program_addr,

    // One outstanding ordered128-bit scratchpad read; at least one cycle latency.
    output wire sp_rd_valid,input wire sp_rd_ready,
    output wire [20:0] sp_rd_addr,output wire [15:0] sp_rd_tag,
    input wire sp_rsp_valid,output wire sp_rsp_ready,
    input wire [127:0] sp_rsp_data,input wire [15:0] sp_rsp_tag,
    output wire sp_wr_valid,input wire sp_wr_ready,
    output wire [20:0] sp_wr_addr,output wire [127:0] sp_wr_data,
    output wire [15:0] sp_wr_strb,sp_wr_tag,

    output wire ex_req_valid,input wire ex_req_ready,
    output wire [15:0] ex_req_tag,output wire ex_req_v2,
    output wire [1:0] ex_req_round_mode,
    output wire [511:0] ex_req_r,ex_req_f,ex_req_e,ex_req_a,
    output wire [63:0] ex_req_emask0,ex_req_emask1,ex_req_program_addr,
    input wire ex_ret_valid,output wire ex_ret_ready,
    input wire [15:0] ex_ret_tag,input wire [511:0] ex_ret_r,ex_ret_f,ex_ret_e,
    input wire [1:0] ex_ret_round_mode,
    // Execution-stage memory operations share the same ordered scratchpad port.
    input wire [15:0] ex_mem_tag,
    input wire ex_rd_valid,output wire ex_rd_ready,input wire [20:0] ex_rd_addr,
    output wire ex_rsp_valid,input wire ex_rsp_ready,output wire [127:0] ex_rsp_data,
    output wire [15:0] ex_rsp_tag,
    input wire ex_wr_valid,output wire ex_wr_ready,input wire [20:0] ex_wr_addr,
    input wire [127:0] ex_wr_data,input wire [15:0] ex_wr_strb,

    // Dataset cache-line read; the prefetch is a nonblocking advisory hint.
    output wire ds_req_valid,input wire ds_req_ready,
    output wire [63:0] ds_req_addr,ds_prefetch_addr,
    output wire [15:0] ds_req_tag,output wire ds_prefetch_valid,
    input wire ds_rsp_valid,output wire ds_rsp_ready,
    input wire [15:0] ds_rsp_tag,input wire [511:0] ds_rsp_data,

    output wire done_valid,input wire done_ready,output wire [15:0] done_tag,
    output wire [1:0] done_round_mode,
    output wire [511:0] done_r,done_f,done_e,
    output wire [31:0] done_mx,done_ma,done_spaddr0,done_spaddr1
);
    localparam [3:0] IDLE=0,R0_REQ=1,R0_RSP=2,R1_REQ=3,R1_RSP=4,
        CONVERT=5,EX_REQ=6,EX_WAIT=7,DS_REQ=8,DS_RSP=9,TAIL_REQ=10,TAIL_WAIT=11;
    reg [3:0] phase_q,convert_q;
    reg [1:0] beat_q;
    reg [15:0] tag_q;
    reg v2_q,ex_read_busy,ex_read_grant_q;
    reg [1:0] round_q;
    reg [511:0] input_r_q,a_q,line0_q,line1_q,f_convert_q,e_convert_q;
    reg [511:0] result_r_q,result_f_q,result_e_q;
    reg [14:0] line0_addr_q,line1_addr_q;
    reg [2:0] read2_q,read3_q;
    reg [63:0] emask0_q,emask1_q,offset_q,ds_addr_q,prefetch_q,program_q;
    reg [31:0] mx_q,ma_q;
    wire [63:0] address_mix=req_r[64*req_read0+:64]^req_r[64*req_read1+:64];
    wire [31:0] initial0=(req_spaddr0^address_mix[31:0])&32'h001fffc0;
    wire [31:0] initial1=(req_spaddr1^address_mix[63:32])&32'h001fffc0;
    wire [63:0] dataset_mix=ex_ret_r[64*read2_q+:64]^ex_ret_r[64*read3_q+:64];
    wire [31:0] changed_mp=(v2_q ? ma_q : mx_q)^dataset_mix[31:0];
    wire [63:0] fp_word[0:15];wire [511:0] parallel_f,parallel_e;
    wire [63:0] serial_word;
    generate
        if(SERIAL_CONVERT==0)begin: parallel_conversion
            genvar k;
            for(k=0;k<16;k=k+1)begin: word
                randomx_i32_to_f64 convert(.word_i(line1_q[32*k+:32]),.bits_o(fp_word[k]));
            end
            for(k=0;k<8;k=k+1)begin: lane
                assign parallel_f[64*k+:64]=fp_word[k];
                assign parallel_e[64*k+:64]=(fp_word[k+8]&64'h00ffffffffffffff)|
                    (k%2==0 ? emask0_q : emask1_q);
            end
            assign serial_word=0;
        end else begin: shared_conversion
            randomx_i32_to_f64 convert(.word_i(line1_q[32*convert_q+:32]),.bits_o(serial_word));
            assign parallel_f=0;assign parallel_e=0;
        end
        if((SERIAL_CONVERT!=0 && SERIAL_CONVERT!=1) || (COALESCE_LINES!=0 && COALESCE_LINES!=1))begin: invalid_config
            iteration_engine_requires_boolean_parameters invalid();
        end
    endgenerate

    wire tail_req_ready,tail_done_valid,tail_wr_valid;
    wire [127:0] tail_wr_data;wire [20:0] tail_wr_addr;
    wire [15:0] tail_wr_strb;wire [511:0] tail_f;
    wire [31:0] tail_next0,tail_next1;
    wire stale_sp=sp_rsp_tag!=tag_q,stale_ex=ex_ret_tag!=tag_q,stale_ds=ds_rsp_tag!=tag_q;
    wire ex_current=ex_mem_tag==tag_q;
    wire active_ex=!rst && phase_q==EX_WAIT;
    // A fresh write wins arbitration, but cannot preempt a read already held.
    wire current_write=active_ex && ex_current && ex_wr_valid && !ex_read_busy && !ex_read_grant_q;
    wire current_read=active_ex && ex_current && ex_rd_valid && !ex_read_busy &&
        (ex_read_grant_q || !ex_wr_valid);
    assign sp_rd_valid=!rst && (phase_q==R0_REQ || phase_q==R1_REQ || current_read);
    assign sp_rd_addr=phase_q==R0_REQ ? {line0_addr_q,beat_q,4'b0} :
        phase_q==R1_REQ ? {line1_addr_q,beat_q,4'b0} : ex_rd_addr;
    assign sp_rd_tag=tag_q;
    assign sp_rsp_ready=!rst && (stale_sp || phase_q==IDLE || phase_q==R0_RSP ||
        phase_q==R1_RSP || (phase_q==EX_WAIT && ex_read_busy && ex_rsp_ready));
    assign ex_rd_ready=!rst && (!ex_current || (current_read && sp_rd_ready));
    assign ex_rsp_valid=active_ex && ex_read_busy && sp_rsp_valid && !stale_sp;
    assign ex_rsp_data=sp_rsp_data;assign ex_rsp_tag=tag_q;
    assign sp_wr_valid=!rst && (current_write || (phase_q==TAIL_WAIT && tail_wr_valid));
    assign sp_wr_addr=phase_q==EX_WAIT ? ex_wr_addr : tail_wr_addr;
    assign sp_wr_data=phase_q==EX_WAIT ? ex_wr_data : tail_wr_data;
    assign sp_wr_strb=phase_q==EX_WAIT ? ex_wr_strb : tail_wr_strb;
    assign sp_wr_tag=tag_q;
    assign ex_wr_ready=!rst && (!ex_current || (current_write && sp_wr_ready));

    assign ex_req_valid=!rst && phase_q==EX_REQ;
    assign ex_req_tag=tag_q;assign ex_req_v2=v2_q;
    assign ex_req_round_mode=round_q;
    assign ex_req_r=input_r_q^line0_q;
    assign ex_req_f=SERIAL_CONVERT!=0 ? f_convert_q : parallel_f;
    assign ex_req_e=SERIAL_CONVERT!=0 ? e_convert_q : parallel_e;
    assign ex_req_a=a_q;
    assign ex_req_emask0=emask0_q;assign ex_req_emask1=emask1_q;
    assign ex_req_program_addr=program_q;
    assign ex_ret_ready=!rst && (stale_ex || (phase_q==EX_WAIT && !ex_read_busy && !ex_read_grant_q &&
        !(ex_current && (ex_rd_valid || ex_wr_valid))));
    assign ds_req_valid=!rst && phase_q==DS_REQ;
    assign ds_req_tag=tag_q;assign ds_req_addr=ds_addr_q;
    assign ds_prefetch_valid=ds_req_valid && ds_req_ready;
    assign ds_prefetch_addr=prefetch_q;
    assign ds_rsp_ready=!rst && (stale_ds || phase_q==IDLE || phase_q==DS_RSP);
    assign done_valid=!rst && phase_q==TAIL_WAIT && tail_done_valid;
    assign req_ready=!rst && (phase_q==IDLE || (done_valid && done_ready));
    assign done_tag=tag_q;assign done_r=result_r_q;assign done_f=tail_f;
    assign done_round_mode=round_q;
    assign done_e=result_e_q;assign done_mx=mx_q;assign done_ma=ma_q;
    assign done_spaddr0=tail_next0;assign done_spaddr1=tail_next1;

    randomx_iteration_store #(.LANES(LANES),.OVERLAP_R(1)) tail(
        .clk(clk),.rst(rst),.req_valid(!rst && phase_q==TAIL_REQ),.req_ready(tail_req_ready),
        .req_v2(v2_q),.req_r(result_r_q),.req_f(result_f_q),.req_e(result_e_q),
        .req_f_line(line0_addr_q),.req_r_line(line1_addr_q),
        .wr_valid(tail_wr_valid),.wr_ready(sp_wr_ready && phase_q==TAIL_WAIT),
        .wr_addr(tail_wr_addr),.wr_data(tail_wr_data),.wr_strb(tail_wr_strb),
        .done_valid(tail_done_valid),.done_ready(done_ready && phase_q==TAIL_WAIT),
        .done_f(tail_f),.done_spaddr0(tail_next0),.done_spaddr1(tail_next1));

    always @(posedge clk)begin
        if(rst)begin
            phase_q<=IDLE;beat_q<=0;convert_q<=0;tag_q<=0;v2_q<=0;round_q<=0;ex_read_busy<=0;ex_read_grant_q<=0;
            input_r_q<=0;a_q<=0;line0_q<=0;line1_q<=0;f_convert_q<=0;e_convert_q<=0;
            result_r_q<=0;result_f_q<=0;result_e_q<=0;
            line0_addr_q<=0;line1_addr_q<=0;read2_q<=0;read3_q<=0;
            emask0_q<=0;emask1_q<=0;offset_q<=0;ds_addr_q<=0;prefetch_q<=0;program_q<=0;mx_q<=0;ma_q<=0;
        end else if(req_valid && req_ready)begin
            phase_q<=R0_REQ;beat_q<=0;convert_q<=0;tag_q<=req_tag;v2_q<=req_v2;round_q<=req_round_mode;
            input_r_q<=req_r;a_q<=req_a;line0_addr_q<=initial0[20:6];line1_addr_q<=initial1[20:6];
            read2_q<=req_read2;read3_q<=req_read3;emask0_q<=req_emask0;emask1_q<=req_emask1;
            offset_q<=req_dataset_offset;program_q<=req_program_addr;mx_q<=req_mx;ma_q<=req_ma;ex_read_busy<=0;ex_read_grant_q<=0;
        end else begin
            case(phase_q)
                R0_REQ:if(sp_rd_valid && sp_rd_ready)phase_q<=R0_RSP;
                R1_REQ:if(sp_rd_valid && sp_rd_ready)phase_q<=R1_RSP;
                R0_RSP:if(sp_rsp_valid && sp_rsp_ready && !stale_sp)begin
                    line0_q[128*beat_q+:128]<=sp_rsp_data;
                    if(beat_q==3)begin
                        beat_q<=0;
                        if(COALESCE_LINES!=0 && line0_addr_q==line1_addr_q)begin
                            line1_q<={sp_rsp_data,line0_q[383:0]};convert_q<=0;
                            phase_q<=SERIAL_CONVERT!=0 ? CONVERT : EX_REQ;
                        end else phase_q<=R1_REQ;
                    end else begin beat_q<=beat_q+1'b1;phase_q<=R0_REQ;end
                end
                R1_RSP:if(sp_rsp_valid && sp_rsp_ready && !stale_sp)begin
                    line1_q[128*beat_q+:128]<=sp_rsp_data;
                    if(beat_q==3)begin
                        beat_q<=0;convert_q<=0;phase_q<=SERIAL_CONVERT!=0 ? CONVERT : EX_REQ;
                    end else begin beat_q<=beat_q+1'b1;phase_q<=R1_REQ;end
                end
                CONVERT:begin
                    if(convert_q<8)f_convert_q[64*convert_q+:64]<=serial_word;
                    else e_convert_q[64*(convert_q-8)+:64]<=
                        (serial_word&64'h00ffffffffffffff)|(convert_q[0] ? emask1_q : emask0_q);
                    if(convert_q==15)phase_q<=EX_REQ;
                    else convert_q<=convert_q+1'b1;
                end
                EX_REQ:if(ex_req_valid && ex_req_ready)phase_q<=EX_WAIT;
                EX_WAIT:begin
                    if(current_read)begin
                        ex_read_grant_q<=!sp_rd_ready;
                        if(sp_rd_ready)ex_read_busy<=1;
                    end
                    if(ex_rsp_valid && ex_rsp_ready)ex_read_busy<=0;
                    if(ex_ret_valid && ex_ret_ready && !stale_ex)begin
                        result_r_q<=ex_ret_r;result_f_q<=ex_ret_f;result_e_q<=ex_ret_e;
                        round_q<=ex_ret_round_mode;
                        ds_addr_q<=offset_q+{32'b0,(ma_q&32'h7fffffc0)};
                        prefetch_q<=offset_q+{32'b0,(changed_mp&32'h7fffffc0)};
                        mx_q<=v2_q ? changed_mp : ma_q;
                        ma_q<=v2_q ? mx_q : changed_mp;
                        phase_q<=DS_REQ;
                    end
                end
                DS_REQ:if(ds_req_valid && ds_req_ready)phase_q<=DS_RSP;
                DS_RSP:if(ds_rsp_valid && ds_rsp_ready && !stale_ds)begin
                    result_r_q<=result_r_q^ds_rsp_data;phase_q<=TAIL_REQ;
                end
                TAIL_REQ:if(tail_req_ready)phase_q<=TAIL_WAIT;
                TAIL_WAIT:if(done_valid && done_ready)phase_q<=IDLE;
                default:phase_q<=IDLE;
            endcase
        end
    end
endmodule
`default_nettype wire
