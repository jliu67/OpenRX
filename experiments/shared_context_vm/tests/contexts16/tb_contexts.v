`timescale 1ns/1ps
module tb_contexts;
 `include "fixture.vh"
 reg clk=0,rst=1;always #5 clk=~clk;
 reg[31:0]cycle=0;always @(negedge clk)cycle<=cycle+1;
 integer policy=0,read_latency=1,cancel_test=0,hold_setting=0;
 reg[3:0][5:0]epochs={4{6'd1}};reg[3:0]started=0,completed=0;wire[3:0]starts=~started;
 reg cancel_valid=0;wire[1:0]cancel_context=0;
 wire[1:0]selected;wire selected_valid;
 wire req_ready,pv,pr,psready,rd,rr,rsready,wr,ret,err,commit;
 wire[63:0]pa;wire[15:0]pt,mt,ret_tag,et,ct;
 wire[20:0]ra,wa;wire[127:0]wd;wire[15:0]strb;
 wire[511:0]ret_r,ret_f,ret_e,commit_r,commit_f,commit_e;
 wire[1:0]ret_round,commit_round;wire[8:0]ep,cp,cn,cb;wire[7:0]eo,co;
 reg[127:0]ram[0:524287]; // exactly4*2MiB private mutable backing store
 reg[63:0]rom[0:383],reciprocals[0:383];reg[85:0]events[0:79];
 reg[3:0]ip=0,mp=0;
 reg[15:0]i_owner[0:3],m_owner[0:3];reg[31:0]i_token[0:3],m_token[0:3],i_due[0:3],m_due[0:3];
 reg[8:0]i_pc[0:3];reg[127:0]m_data[0:3];
 integer i_sequence[0:3],m_sequence[0:3],event_index[0:3],steps[0:3],writes[0:3];
 reg[63:0]route[0:3];reg[31:0]begin_cycle[0:3],end_cycle[0:3];
 reg[511:0]final_f[0:3],final_e[0:3];
 integer grants[0:3],idle_clocks=0,peak_live=0,stale_program=0,stale_memory=0;
 integer earliest=-1,last_cycle=0,i,j,k,n,index,beat,events_checked=0;
 integer read_min=100000,read_max=0;
 reg[31:0]last_write_address[0:3];reg[127:0]last_write_value[0:3];
 wire[15:0]owner={epochs[selected],selected,8'b0};
 wire[3:0]program_available,memory_available,program_credit,memory_credit;
 genvar g;
 generate for(g=0;g<4;g=g+1)begin: availability
  assign program_credit[g]=!ip[g];assign memory_credit[g]=!mp[g];
  assign program_available[g]=ip[g]&&cycle>=i_due[g]&&i_token[g][31:26]==epochs[g];
  assign memory_available[g]=mp[g]&&cycle>=m_due[g]&&m_token[g][31:26]==epochs[g];
 end endgenerate
 assign pr=program_credit[selected];assign rr=memory_credit[selected];
 wire[63:0]instruction=rom[i_pc[selected]];
 wire is_rcp=instruction[7:0]>=76&&instruction[7:0]<84;
 wire[31:0]divisor=instruction[63:32];
 wire nop=divisor==0||(divisor&(divisor-1'b1))==0;
 openrx_context_execute #(.PREPARED_RCP(1)) core(
  .interleave(policy!=0),.starts(starts),.program_available(program_available),.memory_available(memory_available),
  .program_credit(program_credit),.memory_credit(memory_credit),.epochs(epochs),.cancel_valid(cancel_valid),.cancel_context(cancel_context),
  .hold_cycles(hold_setting[2:0]),.cycle(cycle),.context_index(selected),.context_valid(selected_valid),
  .clk(clk),.rst(rst),.req_valid(starts[selected]),.req_ready(req_ready),.req_tag(owner),.req_v2(1'b1),.req_round_mode(2'b0),
  .req_r(START_R),.req_f(START_F),.req_e(START_E),.req_a(START_A),.req_emask0(EMASK0),.req_emask1(EMASK1),.req_program_addr(64'h10000000),
  .prog_valid(pv),.prog_ready(pr),.prog_addr(pa),.prog_tag(pt),.prog_rsp_valid(program_available[selected]),.prog_rsp_ready(psready),
  .prog_rsp_tag(i_owner[selected]),.prog_rsp_instruction(instruction),.req_program_epoch(owner),.prog_rsp_prepared_epoch(i_owner[selected]),
  .prog_rsp_prepared_pc(i_pc[selected]),.prog_rsp_prepared_error(1'b0),.prog_rsp_rcp_valid(is_rcp),.prog_rsp_rcp_nop(is_rcp&&nop),
  .prog_rsp_rcp_divisor(is_rcp?divisor:32'b0),.prog_rsp_rcp_value(is_rcp?reciprocals[i_pc[selected]]:64'b0),
  .mem_tag(mt),.rd_valid(rd),.rd_ready(rr),.rd_addr(ra),.rsp_valid(memory_available[selected]),.rsp_ready(rsready),
  .rsp_tag(m_owner[selected]),.rsp_data(m_data[selected]),.wr_valid(wr),.wr_ready(1'b1),.wr_addr(wa),.wr_data(wd),.wr_strb(strb),
  .ret_valid(ret),.ret_ready(1'b1),.ret_tag(ret_tag),.ret_r(ret_r),.ret_f(ret_f),.ret_e(ret_e),.ret_round_mode(ret_round),
  .error_valid(err),.error_ready(1'b1),.error_tag(et),.error_pc(ep),.error_opcode(eo),
  .commit_valid(commit),.commit_tag(ct),.commit_pc(cp),.commit_opcode(co),.commit_r(commit_r),.commit_next_pc(cn),.commit_branch_target(cb),
  .commit_f(commit_f),.commit_e(commit_e),.commit_round_mode(commit_round)
 );
 // One physical AES lane checks native post-kernelF after timed work has ended.
 reg aes_request=0;wire aes_ready,aes_valid;reg[511:0]aes_f=0,aes_e=0;wire[511:0]aes_result;
 randomx_v2_aes_mix #(.LANES(1)) native_postcheck(clk,rst,aes_request,aes_ready,aes_f,aes_e,aes_valid,1'b1,aes_result);
 reg[4095:0]initial_path,program_path,rcp_path,event_path;
 initial begin
  if(!$value$plusargs("POLICY=%d",policy)||!$value$plusargs("READ=%d",read_latency)||
     !$value$plusargs("CANCEL=%d",cancel_test)||!$value$plusargs("HOLD=%d",hold_setting)||
     !$value$plusargs("INITIAL=%s",initial_path)||!$value$plusargs("PROGRAM=%s",program_path)||
     !$value$plusargs("RCP=%s",rcp_path)||!$value$plusargs("EVENTS=%s",event_path))$fatal(1,"explicit component operands");
  if(policy<0||policy>1||(read_latency!=1&&read_latency!=10)||cancel_test<0||cancel_test>1||hold_setting<0||hold_setting>2)$fatal(1,"closed bounded component cases");
  if(cancel_test&&policy!=1)$fatal(1,"cancel fixture requires interleaving");
  $readmemh(initial_path,ram,0,131071);
  for(i=1;i<4;i=i+1)for(j=0;j<131072;j=j+1)ram[i*131072+j]=ram[j];
  $readmemh(program_path,rom);$readmemh(rcp_path,reciprocals);$readmemh(event_path,events);
  for(i=0;i<4;i=i+1)begin
   i_sequence[i]=0;m_sequence[i]=0;event_index[i]=0;steps[i]=0;writes[i]=0;grants[i]=0;route[i]=64'hcbf29ce484222325;
   i_owner[i]<=0;m_owner[i]<=0;i_pc[i]<=0;i_token[i]<=0;m_token[i]<=0;i_due[i]<=0;m_due[i]<=0;m_data[i]<=0;
   begin_cycle[i]=0;end_cycle[i]=0;last_write_address[i]=0;last_write_value[i]=0;
  end
  $display("HEADER contexts=4 private_SP_bytes=8388608 integer_datapaths=1 mul64=1 FP128=1 DIV128=1 POLICY=%0d READ=%0d CANCEL=%0d HOLD=%0d",policy,read_latency,cancel_test,hold_setting);
  repeat(2)@(negedge clk);rst=0;
  wait(completed==4'b1111);@(negedge clk);
  if(ip!=0||mp!=0||core.mul_busy||core.fp_busy||core.div_busy||core.multiplier.reserved!=0||core.floating_unit.reserved!=0||core.division_unit.reserved!=0)$fatal(1,"component did not drain all return credits");
  for(i=0;i<4;i=i+1)begin
   aes_f=final_f[i];aes_e=final_e[i];aes_request=1;
   @(posedge clk);if(!aes_ready)$fatal(1,"shared AES checker admission");
   @(negedge clk);aes_request=0;wait(aes_valid);@(posedge clk);
   if(aes_result!==EXPECTED_POST_AES_F)$fatal(1,"native post-AESF mismatch context=%0d",i);
   $display("AES %0h %0h %0h",cycle,i,aes_result);@(negedge clk);
  end
  if(cancel_test&&core.division_unit.stale_dropped==0)$fatal(1,"cancel fixture lacked stale FU drain");
  if(hold_setting!=0&&(core.multiplier.held_cycles==0||core.floating_unit.held_cycles==0||core.division_unit.held_cycles==0))$fatal(1,"held-return fixture incomplete");
  $display("STATS batch_cycles=%0d first=%0d last=%0d idle=%0d peak_live=%0d read_min=%0d read_max=%0d stale_program=%0d stale_memory=%0d",last_cycle-earliest+1,earliest,last_cycle,idle_clocks,peak_live,read_min,read_max,stale_program,stale_memory);
  $display("FU_STATS mul=%0d/%0d/%0d/%0d FP=%0d/%0d/%0d/%0d DIV=%0d/%0d/%0d/%0d peak=%0d,%0d,%0d held=%0d,%0d,%0d",core.multiplier.accepted,core.multiplier.returned,core.multiplier.consumed,core.multiplier.stale_dropped,
   core.floating_unit.accepted,core.floating_unit.returned,core.floating_unit.consumed,core.floating_unit.stale_dropped,
   core.division_unit.accepted,core.division_unit.returned,core.division_unit.consumed,core.division_unit.stale_dropped,
   core.multiplier.peak_reserved,core.floating_unit.peak_reserved,core.division_unit.peak_reserved,core.multiplier.held_cycles,core.floating_unit.held_cycles,core.division_unit.held_cycles);
  $display("CONTEXTS_NATIVE_PASS contexts=4 steps_each=384 events_each=80 native_R_E_round_route_and_AES_F=1 shared_pool=1 credits_drained=1 complete_hash=0");$finish;
 end
 always @(posedge clk)begin
  if(rst)started<=0;
  else if(cancel_valid)started[cancel_context]<=0;
  else if(selected_valid&&starts[selected]&&req_ready)started[selected]<=1;
 end
 always @(posedge clk)if(!rst)begin
  if(cycle>50000)$fatal(1,"bounded component watchdog");
  if(err)$fatal(1,"native component error ctx=%0d pc=%0d op=%0d owner=%0h",selected,ep,eo,et);
  if(rd&&wr)$fatal(1,"global memory request port exceeded");
  if(earliest>=0&&completed!=15)begin
   if(!selected_valid)idle_clocks=idle_clocks+1;
   n=0;for(k=0;k<4;k=k+1)if(core.state_q_bank[k]!=0)n=n+1;
   if(n>peak_live)peak_live=n;
  end
  for(k=0;k<4;k=k+1)begin
   if(core.state_q_bank[k]==12||core.state_q_bank[k]==13)$fatal(1,"runtime reciprocal is outside prepared component");
   if(ip[k]&&i_token[k][31:26]!=epochs[k]&&cycle>=i_due[k])begin ip[k]<=0;stale_program=stale_program+1;$display("PI_DROP %0h %0h %0h",cycle,k,i_token[k]);end
   if(mp[k]&&m_token[k][31:26]!=epochs[k]&&cycle>=m_due[k])begin mp[k]<=0;stale_memory=stale_memory+1;$display("MI_DROP %0h %0h %0h",cycle,k,m_token[k]);end
   if((core.multiplier.reserved[k]?1:0)+(core.floating_unit.reserved[k]?1:0)+(core.division_unit.reserved[k]?1:0)>1)$fatal(1,"blocking context has multiple FU credits");
  end
  if(selected_valid)begin
   grants[selected]=grants[selected]+1;
   if(starts[selected]&&req_ready)begin
    begin_cycle[selected]=cycle;if(earliest<0)earliest=cycle;
    $display("START %0h %0h %0h %0h",cycle,selected,epochs[selected],owner);
   end
   if(program_available[selected]&&psready)begin
    if(i_owner[selected]!==owner||i_token[selected][25:24]!==selected)$fatal(1,"instruction recipient ownership");
    ip[selected]<=0;$display("PR %0h %0h %0h %0h",cycle,selected,i_token[selected],i_pc[selected]);
   end
   if(pv&&pr)begin
    index=(pa-64'h10000000)>>3;
    if(ip[selected]||pt!==owner||index<0||index>=384||pa[2:0]!=0||i_sequence[selected]>=1024)$fatal(1,"instruction request binding/credit");
    ip[selected]<=1;i_owner[selected]<=pt;i_pc[selected]<=index[8:0];i_due[selected]<=cycle+1;
    i_token[selected]<={epochs[selected],selected,24'(i_sequence[selected])};i_sequence[selected]=i_sequence[selected]+1;
    $display("PQ %0h %0h %0h %0h %0h",cycle,selected,epochs[selected],i_sequence[selected]-1,index);
   end
   if(memory_available[selected]&&rsready)begin
    if(m_owner[selected]!==owner||m_token[selected][25:24]!==selected)$fatal(1,"memory recipient ownership");
    mp[selected]<=0;n=integer'(cycle-(m_due[selected]-read_latency));if(n<read_min)read_min=n;if(n>read_max)read_max=n;
    $display("MR %0h %0h %0h %0h",cycle,selected,m_token[selected],m_data[selected]);
   end
   if(rd&&rr)begin
    index=event_index[selected];beat=integer'(selected)*131072+integer'(ra>>4);
    if(index>=80||events[index][85]||ra[3:0]!=0||ra!=={events[index][84:68],4'b0}||mt!==owner||mp[selected])$fatal(1,"native read address/order/owner");
    if((events[index][67]?ram[beat][127:64]:ram[beat][63:0])!==events[index][63:0])$fatal(1,"native read value context=%0d event=%0d",selected,index);
    mp[selected]<=1;m_owner[selected]<=mt;m_data[selected]<=ram[beat];m_due[selected]<=cycle+32'(read_latency);
    m_token[selected]<={epochs[selected],selected,24'(m_sequence[selected])};m_sequence[selected]=m_sequence[selected]+1;
    event_index[selected]=index+1;events_checked=events_checked+1;
    $display("MQ %0h %0h %0h %0h %0h %0h",cycle,selected,epochs[selected],m_sequence[selected]-1,ra,ram[beat]);
   end
   if(wr)begin
    index=event_index[selected];beat=integer'(selected)*131072+integer'(wa>>4);
    if(index>=80||!events[index][85]||wa!=={events[index][84:68],4'b0}||strb!==(events[index][67]?16'hff00:16'h00ff)||mt!==owner)$fatal(1,"native write address/order/strobe/owner");
    if((events[index][67]?wd[127:64]:wd[63:0])!==events[index][63:0])$fatal(1,"native write value");
    for(j=0;j<16;j=j+1)if(strb[j])ram[beat][8*j+:8]=wd[8*j+:8];
    last_write_address[selected]=wa;last_write_value[selected]=ram[beat];writes[selected]=writes[selected]+1;
    event_index[selected]=index+1;m_sequence[selected]=m_sequence[selected]+1;events_checked=events_checked+1;
    $display("MW %0h %0h %0h %0h %0h %0h %0h",cycle,selected,epochs[selected],m_sequence[selected]-1,wa,strb,wd);
   end
   if(commit)begin
    if(ct!==owner||cp>=384||co!==rom[cp][7:0])$fatal(1,"native ordered retirement ownership/opcode");
    route[selected]=(route[selected]^(({55'b0,cp}<<17)|({56'b0,co}<<9)|{55'b0,cn}))*64'h100000001b3;
    steps[selected]=steps[selected]+1;
    $display("C %0h %0h %0h %0h %0h %0h",cycle,selected,epochs[selected],cp,cn,route[selected]);
   end
   if(ret)begin
    if(ret_tag!==owner||ret_r!==EXPECTED_R||ret_e!==EXPECTED_E||ret_round!==EXPECTED_ROUND||steps[selected]!=EXPECTED_STEPS||route[selected]!==EXPECTED_ROUTE||event_index[selected]!=80||writes[selected]!=19)$fatal(1,"native kernel final state/route/event closure context=%0d steps=%0d events=%0d",selected,steps[selected],event_index[selected]);
    if(completed[selected])$fatal(1,"duplicate kernel completion");
    completed[selected]<=1;end_cycle[selected]=cycle;last_cycle=cycle;final_f[selected]=ret_f;final_e[selected]=ret_e;
    $display("DONE %0h %0h %0h %0h %0h %0h %0h %0h",cycle,selected,epochs[selected],cycle-begin_cycle[selected]+1,ret_round,ret_r,ret_f,ret_e);
   end
  end
 end
 reg[127:0]saved_canceled_write;integer saved_canceled_address;
 initial begin
  wait(!rst);
  if(cancel_test)begin
   wait(core.div_busy&&core.division_unit.inflight_token[9:8]==0&&writes[0]>0);
   @(negedge clk);saved_canceled_address=last_write_address[0]>>4;saved_canceled_write=ram[saved_canceled_address];cancel_valid=1;
   $display("CANCEL %0h ctx=0 old_epoch=%0h writes=%0d steps=%0d",cycle,epochs[0],writes[0],steps[0]);
   @(negedge clk);cancel_valid=0;if(epochs[0]==63)$fatal(1,"epoch exhaustion");epochs[0]=epochs[0]+1'b1;
   if(ram[saved_canceled_address]!==saved_canceled_write)$fatal(1,"cancel rolled back accepted store");
   // Explicit fresh initialization, not cancellation rollback; excluded from
   // all performance comparisons. Other context RAM/state is undisturbed.
   $readmemh(initial_path,ram,0,131071);
   event_index[0]=0;steps[0]=0;writes[0]=0;route[0]=64'hcbf29ce484222325;i_sequence[0]=0;m_sequence[0]=0;
   $display("REINIT %0h ctx=0 new_epoch=%0h private_bytes=2097152",cycle,epochs[0]);
  end
 end
endmodule
