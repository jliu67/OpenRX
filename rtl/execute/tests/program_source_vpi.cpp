// SPDX-License-Identifier: BSD-3-Clause
// External program/scratchpad provider consumes DUT outputs, never golden values.
#include <vpi_user.h>
#include "program_native_helpers.hpp"
#include <array>
#include <string>
static std::vector<vpiHandle> arguments(){
 std::vector<vpiHandle> a;auto i=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,nullptr));
 while(auto h=vpi_scan(i))a.push_back(h);return a;
}
static std::string string_value(vpiHandle h){s_vpi_value v{};v.format=vpiStringVal;vpi_get_value(h,&v);return v.value.str;}
static void read_bytes(vpiHandle h,void* output,size_t size){
 if(vpi_get(vpiSize,h)!=int(size*8))throw std::runtime_error("VPI vector width");
 s_vpi_value v{};v.format=vpiVectorVal;vpi_get_value(h,&v);auto* bytes=(uint8_t*)output;
 for(size_t i=0;i<size/4;++i){if(v.value.vector[i].bval)throw std::runtime_error("unknown DUT state reaches native source");uint32_t x=v.value.vector[i].aval;std::memcpy(bytes+4*i,&x,4);}
}
static void write_bytes(vpiHandle h,const void* input,size_t size){
 if(vpi_get(vpiSize,h)!=int(size*8))throw std::runtime_error("VPI output width");
 std::vector<s_vpi_vecval> bits(size/4);auto* bytes=(const uint8_t*)input;
 for(size_t i=0;i<size/4;++i){std::memcpy(&bits[i].aval,bytes+4*i,4);bits[i].bval=0;}
 s_vpi_value v{};v.format=vpiVectorVal;v.value.vector=bits.data();vpi_put_value(h,&v,nullptr,vpiNoDelay);
}
static PLI_INT32 initial(PLI_BYTE8*){try{
 auto a=arguments();if(a.size()!=2)throw std::runtime_error("rx_initial arguments");
 std::vector<uint8_t> mem(randomx::ScratchpadSize);alignas(16) uint8_t seed[64];sequence_fixture::initial(seed,mem);
 sequence_fixture::image(string_value(a[0]),mem);write_bytes(a[1],seed,64);
 }catch(const std::exception& e){vpi_printf("FAIL native source initial: %s\n",e.what());vpi_control(vpiFinish,1);}return 0;}
static PLI_INT32 generate(PLI_BYTE8*){try{
 auto a=arguments();if(a.size()!=3)throw std::runtime_error("rx_generate arguments");alignas(16) uint8_t seed[64];read_bytes(a[0],seed,64);
 randomx::Program p;sequence_fixture::generate(seed,p);sequence_fixture::words(string_value(a[1]),p);write_bytes(a[2],&p,128);
 }catch(const std::exception& e){vpi_printf("FAIL native source generate: %s\n",e.what());vpi_control(vpiFinish,1);}return 0;}
static PLI_INT32 next_seed(PLI_BYTE8*){try{
 auto a=arguments();if(a.size()!=5)throw std::runtime_error("rx_next_seed arguments");randomx::RegisterFile reg;
 read_bytes(a[0],reg.r,64);read_bytes(a[1],reg.f,64);read_bytes(a[2],reg.e,64);read_bytes(a[3],reg.a,64);
 alignas(16) uint8_t seed[64];sequence_fixture::hash_registers(reg,seed);write_bytes(a[4],seed,64);
 }catch(const std::exception& e){vpi_printf("FAIL native source next: %s\n",e.what());vpi_control(vpiFinish,1);}return 0;}
static void register_tasks(){
 for(auto pair:std::vector<std::pair<const char*,PLI_INT32(*)(PLI_BYTE8*)>>{{"$rx_initial",initial},{"$rx_generate",generate},{"$rx_next_seed",next_seed}}){
  s_vpi_systf_data d{};d.type=vpiSysTask;d.tfname=(PLI_BYTE8*)pair.first;d.calltf=pair.second;vpi_register_systf(&d);
 }
}
extern "C" { void (*vlog_startup_routines[])()={register_tasks,nullptr}; }
