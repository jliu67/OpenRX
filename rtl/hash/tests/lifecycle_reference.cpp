// SPDX-License-Identifier: BSD-3-Clause
// Native-generated programs; unchanged pinned instruction/iteration bodies provide gold.
#include "bytecode_machine.hpp"
#include "virtual_machine.hpp"
#include "soft_aes.h"
#include "program_native_helpers.hpp"
#include <array>
#include <iostream>
#include <cstdlib>
#include "lifecycle_native.hpp"
using namespace randomx;
using sequence_fixture::hex;
#include "pinned_program_float_helpers.inc"
static std::ofstream events,iterations,metadata,finalregs;
static uint64_t event_count=0,total_steps=0,total_branches=0,total_fp=0,total_cf=0;
static uint64_t static_active_rcp=0,dynamic_active_rcp=0;
static unsigned current_program=0,current_iteration=0;
class Fixture final:public randomx_vm,public BytecodeMachine {
public:
 static constexpr bool softAes=true;
 uint64_t route=0,steps=0,read_address=0,prefetch_address=0;
 uint32_t line0=0,line1=0;
 NativeRegisterFile* active=nullptr;
 Fixture(){datasetOffset=0;mem.mx=0;mem.ma=0;}
 void allocate()override{throw std::runtime_error("unused allocate");}
 void getFinalResult(void*,size_t)override{throw std::runtime_error("software providers separately timed; hardware seed/finalizer connected by lifecycle");}
 void hashAndFill(void*,size_t,uint64_t*)override{throw std::runtime_error("outside component");}
 void initScratchpad(void*)override{throw std::runtime_error("external scratchpad initializer");}
 void run(void*)override{throw std::runtime_error("fixture run uses bounded iteration count");}
 void prepare(uint8_t seed[64],bool v2,uint8_t* memory){
  vmFlags=v2?RANDOMX_FLAG_V2:RANDOMX_FLAG_DEFAULT;scratchpad=memory;
  sequence_fixture::generate(seed,program);
  for(unsigned pc=0;pc<384;++pc){
   const auto& op=program(pc);uint32_t divisor=op.getImm32();
   if(op.opcode>=ceil_ISMULH_M&&op.opcode<ceil_IMUL_RCP&&divisor&&(divisor&(divisor-1)))++static_active_rcp;
  }
#include "pinned_program_initialize.inc"
 }
 void write_metadata(){
  metadata<<std::dec<<current_program<<' ';hex(metadata,&program,128);metadata<<' ';
  hex(metadata,reg.a,64);metadata<<' '<<std::hex<<mem.mx<<' '<<mem.ma<<' '<<datasetOffset<<' '
   <<config.eMask[0]<<' '<<config.eMask[1]<<' '<<config.readReg0<<' '<<config.readReg1<<' '<<config.readReg2<<' '<<config.readReg3<<'\n';
 }
 void execute(unsigned count,std::ofstream& trace){
  NativeRegisterFile nreg;
  for(unsigned i=0;i<RegisterCountFlt;++i)nreg.a[i]=rx_load_vec_f128(&reg.a[i].lo);
  compileProgram(program,bytecode,nreg,vmFlags);
  uint32_t spAddr0=mem.mx,spAddr1=mem.ma;
  for(unsigned ic=0;ic<count;++ic){
   current_iteration=ic;active=&nreg;uint64_t start=event_count;route=UINT64_C(0xcbf29ce484222325);steps=0;
   uint64_t mix=nreg.r[config.readReg0]^nreg.r[config.readReg1];
   line0=(spAddr0^uint32_t(mix))&ScratchpadL3Mask64;line1=(spAddr1^uint32_t(mix>>32))&ScratchpadL3Mask64;
#include "pinned_iteration.inc"
   if(spAddr0||spAddr1)throw std::runtime_error("native cursor reset");
   trace<<std::dec<<current_program<<' '<<ic<<' '<<start<<' '<<event_count-start<<' '<<steps<<' ';
   hex(trace,nreg.r,64);trace<<' ';hex(trace,nreg.f,64);trace<<' ';hex(trace,nreg.e,64);trace<<' ';hex(trace,nreg.a,64);
   trace<<' '<<std::hex<<rx_get_rounding_mode()<<' '<<mem.mx<<' '<<mem.ma<<' '<<spAddr0<<' '<<spAddr1<<' '
    <<line0<<' '<<line1<<' '<<read_address<<' '<<prefetch_address<<' '<<route<<'\n';
  }
  for(unsigned i=0;i<RegistersCount;++i)store64(&reg.r[i],nreg.r[i]);
  for(unsigned i=0;i<RegisterCountFlt;++i){rx_store_vec_f128(&reg.f[i].lo,nreg.f[i]);rx_store_vec_f128(&reg.e[i].lo,nreg.e[i]);}
 }
 void hash_next(uint8_t seed[64]){sequence_fixture::hash_registers(reg,seed);}
 void finalize(const std::string& out,uint8_t digest[32]){
  hashAes1Rx4<true>(scratchpad,ScratchpadSize,&reg.a);
  if(blake2b(digest,32,&reg,sizeof(reg),nullptr,0))throw std::runtime_error("native final BLAKE2b256");
  std::ofstream a(out+"/final-a.hex"),rf(out+"/final-rf.hex"),d(out+"/final-digest32.hex");
  hex(a,reg.a,64);a<<'\n';hex(rf,&reg,sizeof(reg));rf<<'\n';hex(d,digest,32);d<<'\n';
  if(!a||!rf||!d)throw std::runtime_error("final assertion write");
 }
 void write_registers(){finalregs<<std::dec<<current_program<<' ';hex(finalregs,&reg,sizeof(reg));finalregs<<' '<<std::hex<<rx_get_rounding_mode()<<'\n';}
private:
 void executeBytecode(InstructionByteCode bytecode[RANDOMX_PROGRAM_MAX_SIZE],uint8_t* scratchpad,ProgramConfiguration& config,randomx_flags flags){
#include "pinned_bytecode_loop.inc"
 }
 void executeInstruction(RANDOMX_EXE_ARGS){
  const unsigned before=unsigned(pc);unsigned address=0;bool read=false,write=false;
  switch(ibc.type){
   case InstructionType::IADD_M:case InstructionType::ISUB_M:case InstructionType::IXOR_M:
   case InstructionType::IMUL_M:case InstructionType::IMULH_M:case InstructionType::ISMULH_M:
   case InstructionType::FADD_M:case InstructionType::FSUB_M:case InstructionType::FDIV_M:
    address=unsigned((uint8_t*)getScratchpadAddress(ibc,scratchpad)-scratchpad);read=true;break;
   case InstructionType::ISTORE:address=unsigned((*ibc.idst+ibc.imm)&ibc.memMask);write=true;break;
   default:break;
  }
  if(read)event(false,address,load64(scratchpad+address));
  BytecodeMachine::executeInstruction(ibc,pc,scratchpad,config,flags);
  unsigned raw=program(before).opcode;uint64_t word=(uint64_t(before)<<17)|(uint64_t(raw)<<9)|unsigned(pc+1);
  uint32_t divisor=program(before).getImm32();
  if(raw>=ceil_ISMULH_M&&raw<ceil_IMUL_RCP&&divisor&&(divisor&(divisor-1)))++dynamic_active_rcp;
  route=(route^word)*UINT64_C(0x100000001b3);++steps;++total_steps;
  if(ibc.type==InstructionType::CBRANCH)++total_branches;
  if(raw>=124&&raw<214)++total_fp;
  if(ibc.type==InstructionType::CFROUND)++total_cf;
  if(write)event(true,address,load64(scratchpad+address));
 }
 void event(bool write,unsigned address,uint64_t data){
  if(address%8||address+8>ScratchpadSize)throw std::runtime_error("native access bounds");
  events<<std::hex<<((uint64_t(write)<<21)|address)<<' '<<data<<'\n';++event_count;
 }
#include "pinned_scratchpad_address.inc"
 InstructionByteCode bytecode[RANDOMX_PROGRAM_MAX_SIZE];alignas(64) uint64_t fixture_line[8];
 void fixtureRead(uint64_t address,int_reg_t(&r)[RegistersCount]){
#include "pinned_dataset_read.inc"
 }
 void datasetRead(uint64_t address,int_reg_t(&r)[RegistersCount]){
  read_address=address;lifecycle_native::dataset().read(address,fixture_line);
  mem.memory=(uint8_t*)fixture_line;fixtureRead(0,r);
 }
 void datasetPrefetch(uint64_t address){prefetch_address=address;}
};
int main(int argc,char**argv){
 if(argc!=6)return 2;std::string out=argv[1];unsigned programs=std::strtoul(argv[2],nullptr,10),count=std::strtoul(argv[3],nullptr,10);bool v2=std::strtoul(argv[4],nullptr,10)!=0;
 if(!programs||programs>8||!count||count>2048)return 3;
 std::vector<uint8_t> memory(ScratchpadSize);alignas(16) uint8_t seed[64];auto input=lifecycle_native::unhex(argv[5]);lifecycle_native::dataset();lifecycle_native::initial(input,seed,memory);
 sequence_fixture::image(out+"/initial.hex",memory);events.open(out+"/accesses.hex");iterations.open(out+"/iterations.hex");metadata.open(out+"/metadata.hex");finalregs.open(out+"/program-registers.hex");
 if(!events||!iterations||!metadata||!finalregs)throw std::runtime_error("trace open");
 rx_set_rounding_mode(0);Fixture vm;
 for(unsigned p=0;p<programs;++p){current_program=p;vm.prepare(seed,v2,memory.data());vm.write_metadata();sequence_fixture::words(out+"/program-"+std::to_string(p)+".mem",vm.getProgram());vm.execute(count,iterations);vm.write_registers();sequence_fixture::image(out+"/final-"+std::to_string(p)+".hex",memory);if(p+1<programs)vm.hash_next(seed);}
 uint8_t final_digest[32];vm.finalize(out,final_digest);bool canonical=false;double canonical_seconds=0;
 if(programs==8&&count==2048&&v2){
  auto started=lifecycle_native::Clock::now();auto* reference=randomx_create_vm(RANDOMX_FLAG_V2,lifecycle_native::dataset().cache,nullptr);
  if(!reference)throw std::runtime_error("canonical native VM allocation");uint8_t expected[32];randomx_calculate_hash(reference,input.data(),input.size(),expected);
  canonical_seconds=lifecycle_native::seconds(started);randomx_destroy_vm(reference);
  if(std::memcmp(expected,final_digest,32))throw std::runtime_error("unchanged full native RandomX hash mismatch");canonical=true;
 }
 std::ofstream complete(out+"/full-reference.json");complete<<"{\"canonical_randomx_calculate_hash_verified\":"<<(canonical?"true":"false")
  <<",\"canonical_host_seconds\":"<<canonical_seconds<<",\"dataset\":\"pinned initDatasetItem native light mode\",\"cache_key\":\""<<lifecycle_native::cache_key
  <<"\",\"input_hex\":\""<<argv[5]<<"\",\"bounded_iteration_profile\":"<<(count!=2048?"true":"false")<<"}\n";
 events.close();iterations.close();metadata.close();finalregs.close();if(!events||!iterations||!metadata||!finalregs)throw std::runtime_error("trace write");
 std::ofstream summary(out+"/oracle-summary.json");summary<<"{\"programs\":"<<programs<<",\"iterations_per_program\":"<<count<<",\"total_iterations\":"<<programs*count<<",\"v2\":"<<unsigned(v2)<<",\"instruction_steps\":"<<total_steps<<",\"bytecode_events\":"<<event_count<<",\"branches\":"<<total_branches<<",\"fp\":"<<total_fp<<",\"cfround\":"<<total_cf<<",\"static_active_reciprocals\":"<<static_active_rcp<<",\"dynamic_active_reciprocals\":"<<dynamic_active_rcp<<",\"dataset\":\"pinned initDatasetItem actual native dataset, light mode\",\"native_default_programs\":8,\"native_default_iterations\":2048,\"initialization_program_generation_interprogram_BLAKE2b_final_hash\":\"software providers separately timed; hardware seed/finalizer connected by lifecycle\"}\n";
 std::cout<<"PASS native_lifecycle_reference programs="<<programs<<" iterations_per_program="<<count<<" v2="<<v2<<" total_iterations="<<programs*count<<" instruction_steps="<<total_steps<<" bytecode_events="<<event_count<<"\n";
}
