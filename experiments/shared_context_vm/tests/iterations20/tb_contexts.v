`timescale 1ns/1ps
module tb_contexts;
 `include "fixture.vh"
 reg clk=0,rst=1;always #5 clk=~clk;
 reg[31:0]cycle=0;always @(negedge clk)cycle<=cycle+1;
 integer policy,read_latency,fetch_setting;
 wire[1:0]selected,prog_context;wire selected_valid,req_ready,pv,pr,psready,rd,rr,rsready,wr,wrready,ret,err,commit;
 wire[63:0]pa;wire[15:0]pt,mt,ret_tag,et,ct,prog_req_epoch;wire[31:0]prog_transport_tag;
 wire[20:0]ra,wa;wire[127:0]wd;wire[15:0]strb;wire[511:0]ret_r,ret_f,ret_e,commit_r,commit_f,commit_e;
 wire[1:0]ret_round,commit_round;wire[8:0]ep,cp,cn,cb;wire[7:0]eo,co;
 reg[127:0]ram[0:524287];reg[63:0]rom[0:1535],reciprocals[0:1535];reg[85:0]events[0:342];
 reg[3:0]ip=0,mp=0,dp=0;reg[31:0]i_token[0:3],i_due[0:3],m_token[0:3],m_due[0:3],d_due[0:3];
 reg[15:0]i_owner[0:3],i_epoch[0:3],m_owner[0:3],d_owner[0:3];reg[8:0]i_pc[0:3];
 reg[127:0]m_data[0:3];reg[1:0]m_kind[0:3];reg[511:0]d_data[0:3];
 integer i_sequence[0:3],m_sequence[0:3],event_index[0:3],steps[0:3],writes[0:3],entry_reads[0:3],tail_writes[0:3];
 reg[63:0]route[0:3];reg[31:0]begin_cycle[0:3];
 wire[3:0]program_available,program_credit,memory_available,memory_credit,raw_memory_available,raw_memory_credit,starts,completed;
 wire[511:0]entry_r,entry_f,entry_e,entry_a;wire[63:0]entry_em0,entry_em1,program_base;
 wire[15:0]owner={6'd1,selected,8'b0};wire[3:0][5:0]epochs={4{6'd1}};
 genvar g;
 generate for(g=0;g<4;g=g+1)begin: availability
  assign program_available[g]=ip[g]&&cycle>=i_due[g];assign program_credit[g]=!ip[g];
  assign raw_memory_available[g]=mp[g]&&cycle>=m_due[g];assign raw_memory_credit[g]=!mp[g];
 end endgenerate
 reg[1:0]response_rr=0,response_context=0;reg service_valid;integer scan,rc;
 always @*begin
  response_context=selected;service_valid=program_available[selected];rc=0;
  if(fetch_setting!=0)begin
   response_context=response_rr;service_valid=0;
   for(scan=0;scan<4;scan=scan+1)begin
    rc=(integer'(response_rr)+scan)&3;
    if(!service_valid&&program_available[rc])begin response_context=rc[1:0];service_valid=1;end
   end
  end
 end
 always @(posedge clk)if(rst)response_rr<=0;else if(service_valid&&psready)response_rr<=response_context+2'd1;
 assign pr=program_credit[prog_context];
 wire[63:0]instruction=rom[integer'(response_context)*384+integer'(i_pc[response_context])];
 wire is_rcp=instruction[7:0]>=76&&instruction[7:0]<84;wire[31:0]divisor=instruction[63:32];wire nop=divisor==0||(divisor&(divisor-1'b1))==0;
 wire core_rsp_valid;wire[127:0]core_rsp_data;wire[15:0]core_rsp_tag;
 openrx_context_execute #(.PREPARED_RCP(1)) core(
  .fetch_enable(fetch_setting!=0),.fetch_dispatch(4'b1111),.prog_rsp_transport_tag(i_token[response_context]),.prog_transport_tag(prog_transport_tag),.prog_context(prog_context),.prog_req_epoch(prog_req_epoch),
  .interleave(policy!=0),.starts(starts),.program_available(program_available),.memory_available(memory_available),.program_credit(program_credit),.memory_credit(memory_credit),.epochs(epochs),.cancel_valid(1'b0),.cancel_context(2'b0),.hold_cycles(3'b0),.cycle(cycle),.context_index(selected),.context_valid(selected_valid),
  .clk(clk),.rst(rst),.req_valid(starts[selected]),.req_ready(req_ready),.req_tag(owner),.req_v2(1'b1),.req_round_mode(INIT_ROUND[selected]),
  .req_r(entry_r),.req_f(entry_f),.req_e(entry_e),.req_a(entry_a),.req_emask0(entry_em0),.req_emask1(entry_em1),.req_program_addr(program_base),
  .prog_valid(pv),.prog_ready(pr),.prog_addr(pa),.prog_tag(pt),.prog_rsp_valid(service_valid),.prog_rsp_ready(psready),.prog_rsp_tag(i_owner[response_context]),.prog_rsp_instruction(instruction),
  .req_program_epoch(owner),.prog_rsp_prepared_epoch(i_epoch[response_context]),.prog_rsp_prepared_pc(i_pc[response_context]),.prog_rsp_prepared_error(1'b0),.prog_rsp_rcp_valid(is_rcp),.prog_rsp_rcp_nop(is_rcp&&nop),.prog_rsp_rcp_divisor(is_rcp?divisor:32'b0),.prog_rsp_rcp_value(is_rcp?reciprocals[integer'(response_context)*384+integer'(i_pc[response_context])]:64'b0),
  .mem_tag(mt),.rd_valid(rd),.rd_ready(rr),.rd_addr(ra),.rsp_valid(core_rsp_valid),.rsp_ready(rsready),.rsp_tag(core_rsp_tag),.rsp_data(core_rsp_data),.wr_valid(wr),.wr_ready(wrready),.wr_addr(wa),.wr_data(wd),.wr_strb(strb),
  .ret_valid(ret),.ret_ready(1'b1),.ret_tag(ret_tag),.ret_r(ret_r),.ret_f(ret_f),.ret_e(ret_e),.ret_round_mode(ret_round),.error_valid(err),.error_ready(1'b1),.error_tag(et),.error_pc(ep),.error_opcode(eo),
  .commit_valid(commit),.commit_tag(ct),.commit_pc(cp),.commit_opcode(co),.commit_r(commit_r),.commit_next_pc(cn),.commit_branch_target(cb),.commit_f(commit_f),.commit_e(commit_e),.commit_round_mode(commit_round));
 wire mv,mwrite,mrvalid,mrready;wire[1:0]mc,mkind,mrc;wire[20:0]maddr;wire[127:0]mwd;wire[15:0]mstrb;
 reg[1:0]memory_rr=0,memory_context=0;reg memory_valid;integer mscan,mctx;
 always @*begin
  memory_valid=0;memory_context=memory_rr;mctx=0;
  for(mscan=0;mscan<4;mscan=mscan+1)begin
   mctx=(integer'(memory_rr)+mscan)&3;
   if(!memory_valid&&raw_memory_available[mctx]&&
    (shell.phase[mctx]!=5||(selected_valid&&selected==mctx&&rsready)))begin memory_valid=1;memory_context=mctx[1:0];end
  end
 end
 assign mrvalid=memory_valid;assign mrc=memory_context;
 reg[1:0]dataset_rr=0,dataset_context=0;reg dataset_valid;integer dscan,dctx;
 always @*begin
  dataset_valid=0;dataset_context=dataset_rr;dctx=0;
  for(dscan=0;dscan<4;dscan=dscan+1)begin dctx=(integer'(dataset_rr)+dscan)&3;if(!dataset_valid&&dp[dctx]&&cycle>=d_due[dctx])begin dataset_valid=1;dataset_context=dctx[1:0];end end
 end
 wire dv,dr,drready;wire[1:0]dc;wire[63:0]da,pref;wire[15:0]dt;
 assign dr=!dp[dc];
 openrx_iteration_shell shell(
  .clk(clk),.rst(rst),.interleave(policy!=0),.cycle(cycle),.core_context(selected),.core_selected(selected_valid),.core_start(selected_valid&&starts[selected]&&req_ready),.core_return(ret),
  .starts(starts),.core_memory_available(memory_available),.core_memory_credit(memory_credit),.entry_r(entry_r),.entry_f(entry_f),.entry_e(entry_e),.entry_a(entry_a),.entry_em0(entry_em0),.entry_em1(entry_em1),.program_base(program_base),
  .kernel_r(ret_r),.kernel_f(ret_f),.kernel_e(ret_e),.kernel_round(ret_round),.core_rd(rd),.core_wr(wr),.core_rsp_ready(rsready),.core_ra(ra),.core_wa(wa),.core_wd(wd),.core_strb(strb),.core_rd_ready(rr),.core_wr_ready(wrready),.core_rsp_valid(core_rsp_valid),.core_rsp_data(core_rsp_data),.core_rsp_tag(core_rsp_tag),
  .mem_valid(mv),.mem_write(mwrite),.mem_context(mc),.mem_addr(maddr),.mem_data(mwd),.mem_strb(mstrb),.mem_kind(mkind),.mem_credit(raw_memory_credit),.mem_available(raw_memory_available),.mem_rsp_valid(mrvalid),.mem_rsp_ready(mrready),.mem_rsp_context(mrc),.mem_rsp_data(m_data[mrc]),.mem_rsp_tag(m_owner[mrc]),
  .ds_valid(dv),.ds_context(dc),.ds_addr(da),.ds_prefetch(pref),.ds_tag(dt),.ds_ready(dr),.ds_rsp_valid(dataset_valid),.ds_rsp_ready(drready),.ds_rsp_context(dataset_context),.ds_rsp_tag(d_owner[dataset_context]),.ds_data(d_data[dataset_context]),.completed(completed));
 reg[4095:0]p0,p1,p2,p3,program_path,rcp_path,event_path;integer i,j,k,index,beat,n,earliest=-1,last_cycle=0,idle=0,read_min=100000,read_max=0;
 reg[85:0]event_word;reg[63:0]check_fnv;reg[127:0]expected_tail;
 initial begin
  if(!$value$plusargs("POLICY=%d",policy)||!$value$plusargs("READ=%d",read_latency)||!$value$plusargs("FETCH=%d",fetch_setting)||!$value$plusargs("INITIAL0=%s",p0)||!$value$plusargs("INITIAL1=%s",p1)||!$value$plusargs("INITIAL2=%s",p2)||!$value$plusargs("INITIAL3=%s",p3)||!$value$plusargs("PROGRAM=%s",program_path)||!$value$plusargs("RCP=%s",rcp_path)||!$value$plusargs("EVENTS=%s",event_path))$fatal(1,"exact iteration fixtures");
  if(policy<0||policy>1||fetch_setting<0||fetch_setting>1||(read_latency!=1&&read_latency!=10))$fatal(1,"bounded iteration cases");
  $readmemh(p0,ram,0,131071);$readmemh(p1,ram,131072,262143);$readmemh(p2,ram,262144,393215);$readmemh(p3,ram,393216,524287);
  $readmemh(program_path,rom);$readmemh(rcp_path,reciprocals);$readmemh(event_path,events);
  for(i=0;i<4;i=i+1)begin i_sequence[i]=0;m_sequence[i]=0;event_index[i]=0;steps[i]=0;writes[i]=0;entry_reads[i]=0;tail_writes[i]=0;route[i]=64'hcbf29ce484222325;begin_cycle[i]=0;i_owner[i]=0;i_epoch[i]=0;i_pc[i]=0;i_token[i]=0;i_due[i]=0;m_token[i]=0;m_due[i]=0;m_owner[i]=0;m_data[i]=0;m_kind[i]=0;d_due[i]=0;d_owner[i]=0;d_data[i]=0;end
  $display("HEADER programs=0,1,2,3 private_SP_bytes=8388608 mul64=1 FP128=1 DIV128=1 AES128=1 converter32to64=16 SP_ports=1/1 dataset_ports=1/1 DS_latency=1 POLICY=%0d READ=%0d FETCH=%0d",policy,read_latency,fetch_setting);
  repeat(2)@(negedge clk);rst=0;
  wait(completed==15);@(negedge clk);
  if(ip!=0||mp!=0||dp!=0||shell.tail_busy||core.fetcher.reserved!=0||core.fetcher.valid!=0||core.fetcher.held||core.mul_busy||core.fp_busy||core.div_busy||core.multiplier.reserved!=0||core.floating_unit.reserved!=0||core.division_unit.reserved!=0)$fatal(1,"iteration credits did not drain");
  for(i=0;i<4;i=i+1)begin
   if(steps[i]!=STEPS[i]||event_index[i]!=COUNT[i]||writes[i]!=WRITES[i]||entry_reads[i]!=8||tail_writes[i]!=8)$fatal(1,"full iteration traffic closure");
   check_fnv=64'hcbf29ce484222325;
   for(j=0;j<131072;j=j+1)for(k=0;k<16;k=k+1)check_fnv=(check_fnv^{56'b0,ram[i*131072+j][8*k+:8]})*64'h100000001b3;
   if(check_fnv!==SP_FNV[i])$fatal(1,"full private scratchpad FNV mismatch");
   $display("SP_FINAL %0h %0h",i,check_fnv);
  end
  $display("STATS batch_cycles=%0d first=%0d last=%0d idle=%0d read_min=%0d read_max=%0d",last_cycle-earliest+1,earliest,last_cycle,idle,read_min,read_max);
  $display("FETCH_STATS req=%0d rsp=%0d pop=%0d peak_reserved=%0d peak_valid=%0d reserved_cycles=%0d valid_cycles=%0d fairness_age=%0d",core.fetcher.requests,core.fetcher.responses,core.fetcher.pops,core.fetcher.peak_reserved,core.fetcher.peak_valid,core.fetcher.reserved_cycles,core.fetcher.valid_cycles,core.fetcher.peak_age);
  $display("ITERATIONS_NATIVE_PASS contexts=4 programs=0,1,2,3 steps=384,384,393,384 events=80,90,82,91 full_iteration_entry_dataset_XOR_AES_tail=1 shared_pool=1 credits_drained=1 complete_hash=0");$finish;
 end
 always @(posedge clk)if(!rst)begin
  if(cycle>70000)$fatal(1,"bounded iteration watchdog");
  if(err||core.fetcher.fault!=0)$fatal(1,"iteration execution protocol error context=%0d pc=%0d opcode=%0h",selected,ep,eo);
  if(earliest>=0&&completed!=15&&!selected_valid)idle=idle+1;
  if(service_valid&&psready)begin
   if(i_token[response_context][25:24]!==response_context)$fatal(1,"instruction response owner");
   ip[response_context]<=0;$display("PR %0h %0h %0h %0h",cycle,response_context,i_token[response_context],i_pc[response_context]);
  end
  if(pv&&pr)begin
   index=(pa-(64'h10000000+{50'b0,prog_context,12'b0}))>>3;
   if(ip[prog_context]||pt!=={6'd1,prog_context,8'b0}||prog_req_epoch!==pt||index<0||index>=384||pa[2:0]!=0||i_sequence[prog_context]>=1024||prog_transport_tag!=={6'd1,prog_context,24'(i_sequence[prog_context])})$fatal(1,"instruction request owner/image/credit");
   ip[prog_context]<=1;i_owner[prog_context]<=pt;i_epoch[prog_context]<=prog_req_epoch;i_pc[prog_context]<=index[8:0];i_due[prog_context]<=cycle+1;i_token[prog_context]<=prog_transport_tag;
   $display("PQ %0h %0h %0h %0h %0h",cycle,prog_context,6'd1,i_sequence[prog_context],index);i_sequence[prog_context]=i_sequence[prog_context]+1;
  end
  if(mv)begin
   if(mp[mc]||maddr[3:0]!=0||maddr>=2097152)$fatal(1,"one SP credit and native aligned private range");
   if(earliest<0)earliest=cycle;beat=integer'(mc)*131072+integer'(maddr>>4);
   if(mkind==0)begin
    index=entry_reads[mc];if(mwrite||index>=8||maddr!==((index<4?L0[mc]:L1[mc])+21'((index%4)*16)))$fatal(1,"native entry read order/address");entry_reads[mc]=index+1;
   end else if(mkind==1)begin
    index=event_index[mc];if(index>=COUNT[mc]||mt!=={6'd1,mc,8'b0})$fatal(1,"native event count/owner");event_word=events[EVENT_BASE[mc]+index];
    if(maddr!=={event_word[84:68],4'b0}||mwrite!==event_word[85])$fatal(1,"native bytecode SP address/order/type");
    if(mwrite)begin
     if(mstrb!==(event_word[67]?16'hff00:16'h00ff)||(event_word[67]?mwd[127:64]:mwd[63:0])!==event_word[63:0])$fatal(1,"native store data/strobes");writes[mc]=writes[mc]+1;
    end else if((event_word[67]?ram[beat][127:64]:ram[beat][63:0])!==event_word[63:0])$fatal(1,"native read data");event_index[mc]=index+1;
   end else if(mkind==2)begin
    index=tail_writes[mc];expected_tail=index<4?GR[mc][128*(index%4)+:128]:GF[mc][128*(index%4)+:128];
    if(!mwrite||index>=8||maddr!==((index<4?L1[mc]:L0[mc])+21'((index%4)*16))||mstrb!==16'hffff||mwd!==expected_tail)$fatal(1,"native R then F tail order/data/address/strobe");tail_writes[mc]=index+1;
   end else $fatal(1,"invalid SP owner phase");
   if(mwrite)begin
    for(j=0;j<16;j=j+1)if(mstrb[j])ram[beat][8*j+:8]=mwd[8*j+:8];
    $display("MW %0h %0h %0h %0h %0h %0h %0h",cycle,mc,m_sequence[mc],mkind,maddr,mstrb,mwd);
   end else begin
    mp[mc]<=1;m_owner[mc]<={6'd1,mc,8'b0};m_data[mc]<=ram[beat];m_due[mc]<=cycle+32'(read_latency);m_token[mc]<={6'd1,mc,24'(m_sequence[mc])};m_kind[mc]<=mkind;
    $display("MQ %0h %0h %0h %0h %0h %0h",cycle,mc,m_sequence[mc],mkind,maddr,ram[beat]);
   end
   m_sequence[mc]=m_sequence[mc]+1;
  end
  if(mrvalid&&mrready)begin
   if(!mp[mrc]||m_owner[mrc]!=={6'd1,mrc,8'b0})$fatal(1,"SP response ownership");
   n=integer'(cycle-(m_due[mrc]-32'(read_latency)));if(n<read_min)read_min=n;if(n>read_max)read_max=n;
   mp[mrc]<=0;memory_rr<=mrc+2'd1;$display("MR %0h %0h %0h %0h %0h",cycle,mrc,m_token[mrc],m_kind[mrc],m_data[mrc]);
  end
  if(dv&&dr)begin
   if(da!==DSADDR[dc]||pref!==PREFETCH[dc]||dt!=={6'd1,dc,8'b0})$fatal(1,"native dataset address/prefetch/owner");
   dp[dc]<=1;d_owner[dc]<=dt;d_data[dc]<=DSDATA[dc];d_due[dc]<=cycle+1;$display("DQ %0h %0h %0h %0h %0h",cycle,dc,dt,da,pref);
  end
  if(dataset_valid&&drready)begin
   if(!dp[dataset_context])$fatal(1,"dataset response credit");dp[dataset_context]<=0;dataset_rr<=dataset_context+2'd1;
   $display("DR %0h %0h %0h %0h",cycle,dataset_context,d_owner[dataset_context],d_data[dataset_context]);
  end
  if(selected_valid)begin
   if(starts[selected]&&req_ready)begin begin_cycle[selected]=cycle;$display("START %0h %0h 1 %0h",cycle,selected,owner);$display("ADMIT_ROUND %0h %0h %0h",cycle,selected,INIT_ROUND[selected]);end
   if(commit)begin
    if(ct!==owner||cp>=384||co!==rom[integer'(selected)*384+integer'(cp)][7:0]||steps[selected]>=STEPS[selected])$fatal(1,"native dynamic retirement ownership/opcode");
    route[selected]=(route[selected]^(({55'b0,cp}<<17)|({56'b0,co}<<9)|{55'b0,cn}))*64'h100000001b3;steps[selected]=steps[selected]+1;
    $display("C %0h %0h 1 %0h %0h %0h",cycle,selected,cp,cn,route[selected]);
   end
   if(ret)begin
    if(ret_tag!==owner||ret_r!==(GR[selected]^DSDATA[selected])||ret_e!==GE[selected]||ret_round!==ROUND[selected]||steps[selected]!=STEPS[selected]||route[selected]!==ROUTE[selected]||event_index[selected]!=COUNT[selected]||writes[selected]!=WRITES[selected])$fatal(1,"native dynamic kernel RF/route/event closure context=%0d",selected);
    $display("KERNEL_DONE %0h %0h %0h %0h %0h %0h %0h",cycle,selected,cycle-begin_cycle[selected]+1,ret_round,ret_r,ret_f,ret_e);
   end
  end
  if(shell.tail_done&&shell.tail_busy)last_cycle=cycle;
 end
endmodule
