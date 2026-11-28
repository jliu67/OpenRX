// SPDX-License-Identifier: BSD-3-Clause
// Experimental observers around verbatim pinned native execution bodies.
#include "dataset_lifecycle_native.hpp"
#include "bytecode_machine.hpp"
#include "virtual_machine.hpp"
#include "soft_aes.h"
#include <array>
#include <map>
#include <set>
#include <iostream>
using namespace randomx;
namespace P=prepared_lifecycle_native;
#include "locality.hpp"
#include "capacity.hpp"
#include "pinned_program_float_helpers.inc"

static std::string hx(const void* data,size_t n) {
 const auto* p=static_cast<const uint8_t*>(data);std::ostringstream o;
 for(size_t i=0;i<n;i++)o<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(p[i]);return o.str();
}
static std::string digest(const void* data,size_t n) {
 uint8_t h[32];P::require(!blake2b(h,32,data,n,nullptr,0),"observer digest");return hx(h,32);
}
static const std::array<const char*,29> names={"IADD_RS","IADD_M","ISUB_R","ISUB_M","IMUL_R","IMUL_M","IMULH_R","IMULH_M","ISMULH_R","ISMULH_M","IMUL_RCP","INEG_R","IXOR_R","IXOR_M","IROR_R","IROL_R","ISWAP_R","FSWAP_R","FADD_R","FADD_M","FSUB_R","FSUB_M","FSCAL_R","FMUL_R","FDIV_M","FSQRT_R","CBRANCH","CFROUND","ISTORE"};
static const std::array<unsigned,29> ceilings={16,23,39,46,62,66,70,71,75,76,84,86,101,106,114,116,120,124,140,145,161,166,172,204,208,214,239,240,256};
static unsigned family(unsigned raw){for(unsigned i=0;i<ceilings.size();i++)if(raw<ceilings[i])return i;throw std::runtime_error("opcode");}
struct Event {unsigned write,address,tier;uint64_t data;};
struct Boundary {uint64_t steps,route,ds,pf;unsigned round;std::string rf,sp_digest;std::vector<Event> events;};
class Census final:public randomx_vm,public BytecodeMachine {
public:
 static constexpr bool softAes=true;
 capacity66::Traffic traffic;
 uint64_t route=0,steps=0,read_address=0,prefetch_address=0;
 uint64_t opcode[29]{},fu[7]{},memcounts[3][2]{},regions[3][2]{},per_program[8]{};
 uint64_t branches_taken=0,cf_changed=0,active_rcp=0,nops=0,logical_order=0;
 uint64_t current_ready_matches=0,next_ready_matches=0,prefetch2_matches=0;
 uint32_t line0=0,line1=0;unsigned prog=0,iter=0;NativeRegisterFile* active=nullptr;
 std::set<uint64_t> dataset_lines;std::vector<Boundary> first;
 std::string program0,entropy0,a0,initial_hash;uint64_t initial_mx=0,initial_ma=0,initial_offset=0;
 std::vector<Event> saved_events;uint64_t ready_current=0,ready_next=0,prior_next=0,prefetch_ring[2]{};
 explicit Census(){datasetOffset=0;mem.mx=0;mem.ma=0;}
 void allocate()override{throw std::runtime_error("unused");}
 void getFinalResult(void*,size_t)override{throw std::runtime_error("unused");}
 void hashAndFill(void*,size_t,uint64_t*)override{throw std::runtime_error("unused");}
 void initScratchpad(void*)override{throw std::runtime_error("unused");}
 void run(void*)override{throw std::runtime_error("unused");}
 void prepare(uint8_t seed[64],uint8_t* memory){
  vmFlags=RANDOMX_FLAG_V2;scratchpad=memory;sequence_fixture::generate(seed,program);
#include "pinned_program_initialize.inc"
  if(prog==0){program0=hx(reinterpret_cast<const uint8_t*>(&program)+128,384*8);entropy0=hx(&program,128);a0=hx(reg.a,64);initial_mx=mem.mx;initial_ma=mem.ma;initial_offset=datasetOffset;}
 }
 void execute(){
  NativeRegisterFile nreg;
  for(unsigned i=0;i<RegisterCountFlt;i++)nreg.a[i]=rx_load_vec_f128(&reg.a[i].lo);
  compileProgram(program,bytecode,nreg,vmFlags);uint32_t spAddr0=mem.mx,spAddr1=mem.ma;
  for(iter=0;iter<2048;iter++){
   active=&nreg;route=UINT64_C(0xcbf29ce484222325);steps=0;saved_events.clear();
   ready_current=datasetOffset+(mem.ma&CacheLineAlignMask);ready_next=datasetOffset+(mem.mx&CacheLineAlignMask);
   if(iter)P::require(ready_current==prior_next,"next dataset source readiness");
   if(iter)++next_ready_matches;
   prior_next=ready_next;
   uint64_t mix=nreg.r[config.readReg0]^nreg.r[config.readReg1];
   line0=(spAddr0^uint32_t(mix))&ScratchpadL3Mask64;line1=(spAddr1^uint32_t(mix>>32))&ScratchpadL3Mask64;
   for(unsigned i=0;i<8;i++)traffic.event(locality37::ENTRY_R,false,line0+8*i,8,prog,iter);
   for(unsigned i=0;i<8;i++)traffic.event(locality37::ENTRY_FP,false,line1+8*i,8,prog,iter);
#include "pinned_iteration.inc"
   for(unsigned i=0;i<8;i++)traffic.event(locality37::TAIL_R,true,line1+8*i,8,prog,iter);
   for(unsigned i=0;i<4;i++)traffic.event(locality37::TAIL_F,true,line0+16*i,16,prog,iter);
   P::require(!spAddr0&&!spAddr1,"native cursor reset");per_program[prog]+=steps;
   if(prog==0&&iter<2){
    RegisterFile out{};std::memcpy(out.r,nreg.r,64);for(unsigned i=0;i<4;i++){rx_store_vec_f128(&out.f[i].lo,nreg.f[i]);rx_store_vec_f128(&out.e[i].lo,nreg.e[i]);rx_store_vec_f128(&out.a[i].lo,nreg.a[i]);}
    first.push_back({steps,route,read_address,prefetch_address,rx_get_rounding_mode(),hx(&out,sizeof(out)),digest(scratchpad,ScratchpadSize),saved_events});
   }
  }
  for(unsigned i=0;i<RegistersCount;i++)store64(&reg.r[i],nreg.r[i]);
  for(unsigned i=0;i<RegisterCountFlt;i++){rx_store_vec_f128(&reg.f[i].lo,nreg.f[i]);rx_store_vec_f128(&reg.e[i].lo,nreg.e[i]);}
 }
 void next_seed(uint8_t seed[64]){sequence_fixture::hash_registers(reg,seed);}
 void finish(uint8_t h[32]){hashAes1Rx4<true>(scratchpad,ScratchpadSize,&reg.a);P::require(!blake2b(h,32,&reg,sizeof(reg),nullptr,0),"final hash");}
private:
 void executeBytecode(InstructionByteCode bytecode[RANDOMX_PROGRAM_MAX_SIZE],uint8_t* scratchpad,ProgramConfiguration& config,randomx_flags flags){
#include "pinned_bytecode_loop.inc"
 }
 void observe(bool write,unsigned address,uint32_t mask){
  P::require(!(address&7)&&address+8<=ScratchpadSize,"native memory width/bounds");
  traffic.event(write?locality37::BC_WRITE:locality37::BC_READ,write,address,8,prog,iter);
  unsigned tier=mask==ScratchpadL1Mask?0:mask==ScratchpadL2Mask?1:mask==ScratchpadL3Mask?2:3;
  P::require(tier<3,"selected tier mask");++memcounts[tier][write];++regions[address<16384?0:address<262144?1:2][write];
  if(prog==0&&iter<2)saved_events.push_back({unsigned(write),address,tier,load64(scratchpad+address)});
 }
 void executeInstruction(RANDOMX_EXE_ARGS){
  unsigned before=unsigned(pc),address=0,unit=0;bool read=false,write=false;
  switch(ibc.type){
   case InstructionType::IADD_M:case InstructionType::ISUB_M:case InstructionType::IXOR_M:
   case InstructionType::IMUL_M:case InstructionType::IMULH_M:case InstructionType::ISMULH_M:
   case InstructionType::FADD_M:case InstructionType::FSUB_M:case InstructionType::FDIV_M:
    address=unsigned(static_cast<uint8_t*>(getScratchpadAddress(ibc,scratchpad))-scratchpad);read=true;break;
   case InstructionType::ISTORE:address=unsigned((*ibc.idst+ibc.imm)&ibc.memMask);write=true;break;
   default:break;
  }
  switch(ibc.type){
   case InstructionType::IMUL_R:case InstructionType::IMUL_M:case InstructionType::IMULH_R:case InstructionType::IMULH_M:case InstructionType::ISMULH_R:case InstructionType::ISMULH_M:unit=1;break;
   case InstructionType::FADD_R:case InstructionType::FADD_M:case InstructionType::FSUB_R:case InstructionType::FSUB_M:case InstructionType::FMUL_R:unit=2;break;
   case InstructionType::FDIV_M:case InstructionType::FSQRT_R:unit=3;break;
   case InstructionType::FSWAP_R:case InstructionType::FSCAL_R:unit=4;break;
   case InstructionType::CBRANCH:case InstructionType::CFROUND:unit=5;break;
   case InstructionType::NOP:unit=6;++nops;break;
   default:break;
  }
  // Native compileProgram converts active IMUL_RCP to IMUL_R, inactive to NOP.
  ++fu[unit];unsigned raw=program(before).opcode;++opcode[family(raw)];
  if(raw>=ceil_ISMULH_M&&raw<ceil_IMUL_RCP&&ibc.type!=InstructionType::NOP)++active_rcp;
  if(read)observe(false,address,ibc.memMask);
  unsigned old_round=rx_get_rounding_mode();BytecodeMachine::executeInstruction(ibc,pc,scratchpad,config,flags);
  if(ibc.type==InstructionType::CBRANCH&&unsigned(pc)!=before)++branches_taken;
  if(ibc.type==InstructionType::CFROUND&&rx_get_rounding_mode()!=old_round)++cf_changed;
  if(write)observe(true,address,ibc.memMask);
  uint64_t word=(uint64_t(before)<<17)|(uint64_t(raw)<<9)|unsigned(pc+1);route=(route^word)*UINT64_C(0x100000001b3);++steps;++logical_order;
 }
#include "pinned_scratchpad_address.inc"
 InstructionByteCode bytecode[RANDOMX_PROGRAM_MAX_SIZE];alignas(64) uint64_t fixture_line[8];
 void fixtureRead(uint64_t address,int_reg_t(&r)[RegistersCount]){
#include "pinned_dataset_read.inc"
 }
 void datasetRead(uint64_t address,int_reg_t(&r)[RegistersCount]){
  P::require(address==ready_current,"current dataset address available at entry");++current_ready_matches;
  if(iter>=2){P::require(address==prefetch_ring[iter%2],"two-iteration prefetch relation");++prefetch2_matches;}
  prefetch_ring[iter%2]=prefetch_address;read_address=address;dataset_lines.insert(address);
  provider().read(address,fixture_line);mem.memory=reinterpret_cast<uint8_t*>(fixture_line);fixtureRead(0,r);
 }
 void datasetPrefetch(uint64_t address){prefetch_address=address;}
public:
 static P::Dataset& provider(){static P::Dataset d;return d;}
};
int main(int argc,char**argv){try{
 if(argc==2&&std::string(argv[1])=="--self-test")return capacity66::selftest();
 P::require(argc==2,"exact immutable prefix argument");auto prefix=P::unhex(argv[1]);P::require(prefix.size()==52,"52-byte prefix");
 auto& provider=Census::provider();P::require(provider.item_requests==0&&!P::reference_role,"isolated counter collector");
 unsigned completed=0;std::clock_t cpu_start=std::clock(),cpu_prior=cpu_start;auto wall_start=P::Clock::now(),wall_prior=wall_start;
 for(uint64_t nonce:{UINT64_C(0),UINT64_C(2)}){
  auto input=prefix;for(unsigned b=0;b<8;b++)input.push_back(uint8_t(nonce>>(8*b)));
  std::vector<uint8_t> memory(ScratchpadSize);alignas(16) uint8_t seed[64];uint8_t actual[32],expected[32];
  double initial_s=0,program_s=0,execute_s=0,seed_s=0,final_s=0;auto start=P::Clock::now();
  P::initial(input,seed,memory);initial_s=P::seconds(start);Census vm;vm.traffic.scan(locality37::INIT,true);vm.traffic.snapshot(0);vm.initial_hash=digest(memory.data(),memory.size());rx_set_rounding_mode(0);
  auto old_requests=provider.item_requests;double old_seconds=provider.item_seconds;
  for(vm.prog=0;vm.prog<8;vm.prog++){
   start=P::Clock::now();vm.prepare(seed,memory.data());program_s+=P::seconds(start);
   start=P::Clock::now();vm.execute();execute_s+=P::seconds(start);
   if(vm.prog<7){start=P::Clock::now();vm.next_seed(seed);seed_s+=P::seconds(start);}
  }
  vm.traffic.snapshot(1);vm.traffic.scan(locality37::FINAL,false);
  start=P::Clock::now();vm.finish(actual);final_s=P::seconds(start);vm.traffic.finish();
  start=P::Clock::now();auto* reference=randomx_create_vm(RANDOMX_FLAG_V2,provider.cache,nullptr);P::require(reference,"canonical VM allocation");
  randomx_calculate_hash(reference,input.data(),input.size(),expected);randomx_destroy_vm(reference);double canonical_s=P::seconds(start);
  P::require(!std::memcmp(actual,expected,32),"canonical digest mismatch nonce="+std::to_string(nonce)+" actual="+hx(actual,32)+" expected="+hx(expected,32));P::require(provider.item_requests-old_requests==16384,"full dataset demand closure");
  uint64_t total=0,types=0,units=0;for(auto n:vm.per_program)total+=n;for(auto n:vm.opcode)types+=n;for(auto n:vm.fu)units+=n;P::require(total==types&&total==units,"counter closure");
  std::cout<<"{\"nonce\":"<<nonce<<",\"input_hex\":\""<<hx(input.data(),input.size())<<"\",\"digest_hex\":\""<<hx(actual,32)<<"\",\"canonical_digest_equal\":true,\"instruction_steps\":"<<total<<",\"opcode_counts\":{";
  for(unsigned i=0;i<29;i++)std::cout<<(i?",":"")<<'"'<<names[i]<<"\":"<<vm.opcode[i];
  std::cout<<"},\"FU_counts_compiled_type\":{";const char* unames[]={"integer","mul64","FP128","DIV128","bitwise128","control","NOP"};for(unsigned i=0;i<7;i++)std::cout<<(i?",":"")<<'"'<<unames[i]<<"\":"<<vm.fu[i];
  std::cout<<"},\"selected_mask_tiers\":[";for(unsigned i=0;i<3;i++)std::cout<<(i?",":"")<<"{\"capacity_bytes\":"<<(i==0?16384:i==1?262144:2097152)<<",\"read8\":"<<vm.memcounts[i][0]<<",\"write8\":"<<vm.memcounts[i][1]<<"}";
  std::cout<<"],\"address_regions_read8_write8\":[";for(unsigned i=0;i<3;i++)std::cout<<(i?",":"")<<'['<<vm.regions[i][0]<<','<<vm.regions[i][1]<<']';
  std::cout<<"],\"per_program_steps\":[";for(unsigned i=0;i<8;i++)std::cout<<(i?",":"")<<vm.per_program[i];
  std::cout<<"],\"dataset_requests\":16384,\"unique_dataset_lines\":"<<vm.dataset_lines.size()<<",\"entry_known_current_address_checks\":"<<vm.current_ready_matches<<",\"entry_known_next_address_checks\":"<<vm.next_ready_matches<<",\"prefetch_two_ahead_checks\":"<<vm.prefetch2_matches<<",\"branches_taken\":"<<vm.branches_taken<<",\"rounding_changes\":"<<vm.cf_changed<<",\"active_reciprocal_instructions\":"<<vm.active_rcp<<",\"compiled_NOPs\":"<<vm.nops;
  std::cout<<",\"host_seconds_not_hardware\":{\"input_and_fill\":"<<initial_s<<",\"program_generation\":"<<program_s<<",\"instrumented_execute_including_dataset\":"<<execute_s<<",\"dataset_nested\":"<<provider.item_seconds-old_seconds<<",\"seven_seed_hashes\":"<<seed_s<<",\"finalize\":"<<final_s<<",\"canonical_hash\":"<<canonical_s<<"}";
  std::cout<<",\"memory_service_census\":";vm.traffic.emit(std::cout);
  std::cout<<",\"first_program\":{\"word_bytes_hex\":\""<<vm.program0<<"\",\"entropy_bytes_hex\":\""<<vm.entropy0<<"\",\"A_bytes_hex\":\""<<vm.a0<<"\",\"initial_sp_blake2b256\":\""<<vm.initial_hash<<"\",\"initial_mx\":"<<vm.initial_mx<<",\"initial_ma\":"<<vm.initial_ma<<",\"dataset_offset\":"<<vm.initial_offset<<",\"first_two_iterations\":[";
  for(unsigned i=0;i<vm.first.size();i++){auto& b=vm.first[i];std::cout<<(i?",":"")<<"{\"steps\":"<<b.steps<<",\"route\":"<<b.route<<",\"round\":"<<b.round<<",\"dataset_address\":"<<b.ds<<",\"prefetch_address\":"<<b.pf<<",\"RF_bytes_hex\":\""<<b.rf<<"\",\"SP_blake2b256\":\""<<b.sp_digest<<"\",\"bytecode_events_write_address_tier_data\":[";for(unsigned e=0;e<b.events.size();e++){auto v=b.events[e];std::cout<<(e?",":"")<<'['<<v.write<<','<<v.address<<','<<v.tier<<",\""<<hx(&v.data,8)<<"\"]";}std::cout<<"]}";}
  std::cout<<"]}}\n";std::cout.flush();P::require(bool(std::cout),"summary output");
  ++completed;auto now_cpu=std::clock();auto now_wall=P::Clock::now();
  bool near_cpu=(now_cpu-cpu_start)+(now_cpu-cpu_prior)*6/5>55*CLOCKS_PER_SEC;
  bool near_wall=P::seconds(wall_start)+P::seconds(wall_prior)*1.2>60;
  cpu_prior=now_cpu;wall_prior=now_wall;
  if(nonce==0&&(near_cpu||near_wall))break;
 }
 P::require(provider.item_requests==completed*16384,"completed-input closure");
 std::cout<<"{\"kind\":\"completion\",\"requested_inputs\":2,\"completed_inputs\":"<<completed<<",\"bounded_subset\":"<<(completed<2?"true":"false")<<"}\n";return 0;
}catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
