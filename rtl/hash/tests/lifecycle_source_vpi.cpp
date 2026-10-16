// SPDX-License-Identifier: BSD-3-Clause
// External program/scratchpad provider consumes DUT outputs, never golden values.
#include <vpi_user.h>
#include "lifecycle_native.hpp"
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
static double initial_seconds=0,input_hash_seconds=0,generation_seconds=0,assertion_seconds=0,assertion_generation_seconds=0,assertion_input_hash_seconds=0;
static unsigned generations=0,input_hash_calls=0,software_fill_calls=0,assertion_generations=0,assertion_input_hash_calls=0;
static PLI_INT32 initial(PLI_BYTE8*){try{
 auto a=arguments();if(a.size()!=4)throw std::runtime_error("rx_life_initial arguments");
 uint8_t bytes[80];read_bytes(a[0],bytes,80);s_vpi_value n{};n.format=vpiIntVal;vpi_get_value(a[1],&n);
 if(n.value.integer<0||n.value.integer>80)throw std::runtime_error("input length");
 lifecycle_native::dataset();auto started=lifecycle_native::Clock::now();
 std::vector<uint8_t> input(bytes,bytes+n.value.integer),mem(randomx::ScratchpadSize);alignas(16) uint8_t seed[64];
 lifecycle_native::initial(input,seed,mem);sequence_fixture::image(string_value(a[2]),mem);write_bytes(a[3],seed,64);
 initial_seconds+=lifecycle_native::seconds(started);++software_fill_calls;
 }catch(const std::exception& e){vpi_printf("FAIL native source initial: %s\n",e.what());vpi_control(vpiFinish,1);}return 0;}
static PLI_INT32 input_hash_value(bool assertion_only){try{
 auto a=arguments();if(a.size()!=3)throw std::runtime_error("rx_life_input_hash arguments");
 uint8_t bytes[80];read_bytes(a[0],bytes,80);s_vpi_value n{};n.format=vpiIntVal;vpi_get_value(a[1],&n);
 if(n.value.integer<0||n.value.integer>80)throw std::runtime_error("input length");
 lifecycle_native::dataset();auto started=lifecycle_native::Clock::now();
 std::vector<uint8_t> input(bytes,bytes+n.value.integer);alignas(16) uint8_t seed[64];
 lifecycle_native::input_hash(input,seed);write_bytes(a[2],seed,64);
 if(assertion_only){assertion_input_hash_seconds+=lifecycle_native::seconds(started);++assertion_input_hash_calls;}
 else {input_hash_seconds+=lifecycle_native::seconds(started);++input_hash_calls;}
 }catch(const std::exception& e){vpi_printf("FAIL native source input hash: %s\n",e.what());vpi_control(vpiFinish,1);}return 0;}
static PLI_INT32 input_hash(PLI_BYTE8*){return input_hash_value(false);}
static PLI_INT32 input_hash_assertion(PLI_BYTE8*){return input_hash_value(true);}
static PLI_INT32 generate_image(bool assertion_only){try{
 auto a=arguments();if(a.size()!=3)throw std::runtime_error("rx_generate arguments");alignas(16) uint8_t seed[64];read_bytes(a[0],seed,64);
 auto started=lifecycle_native::Clock::now();randomx::Program p;sequence_fixture::generate(seed,p);sequence_fixture::words(string_value(a[1]),p);write_bytes(a[2],&p,128);
 if(assertion_only){assertion_generation_seconds+=lifecycle_native::seconds(started);++assertion_generations;}
 else {generation_seconds+=lifecycle_native::seconds(started);++generations;}
 }catch(const std::exception& e){vpi_printf("FAIL native source generate: %s\n",e.what());vpi_control(vpiFinish,1);}return 0;}
static PLI_INT32 generate(PLI_BYTE8*){return generate_image(false);}
static PLI_INT32 generate_assertion(PLI_BYTE8*){return generate_image(true);}
static PLI_INT32 next_seed(PLI_BYTE8*){try{
 auto a=arguments();if(a.size()!=5)throw std::runtime_error("rx_next_seed arguments");randomx::RegisterFile reg;
 read_bytes(a[0],reg.r,64);read_bytes(a[1],reg.f,64);read_bytes(a[2],reg.e,64);read_bytes(a[3],reg.a,64);
 auto started=lifecycle_native::Clock::now();alignas(16) uint8_t seed[64];sequence_fixture::hash_registers(reg,seed);write_bytes(a[4],seed,64);assertion_seconds+=lifecycle_native::seconds(started);
 }catch(const std::exception& e){vpi_printf("FAIL native source next: %s\n",e.what());vpi_control(vpiFinish,1);}return 0;}
static PLI_INT32 dataset_read(PLI_BYTE8*){try{
 auto a=arguments();if(a.size()!=2)throw std::runtime_error("rx_dataset arguments");
 uint64_t address;read_bytes(a[0],&address,8);alignas(64) uint8_t line[64];lifecycle_native::dataset().read(address,line);write_bytes(a[1],line,64);
 }catch(const std::exception& e){vpi_printf("FAIL native dataset: %s\n",e.what());vpi_control(vpiFinish,1);}return 0;}
static PLI_INT32 statistics(PLI_BYTE8*){try{
 auto a=arguments();if(a.size()!=1)throw std::runtime_error("rx_provider_stats arguments");auto& d=lifecycle_native::dataset();
 std::ofstream out(string_value(a[0]));out<<std::setprecision(17)
  <<"{\"provider\":\"pinned randomx::initDatasetItem, native light cache; not a physical DRAM model\","
  <<"\"cache_bytes\":268435456,\"logical_dataset_bytes\":2181038016,\"materialized_dataset_bytes\":0,\"cache_key\":\""<<lifecycle_native::cache_key<<"\","
  <<"\"cache_initialization_host_seconds\":"<<d.initialization_seconds<<",\"initialization_host_seconds\":"<<initial_seconds
  <<",\"input_hash_host_seconds\":"<<input_hash_seconds<<",\"input_hash_calls\":"<<input_hash_calls
  <<",\"assertion_only_input_hash_host_seconds\":"<<assertion_input_hash_seconds<<",\"assertion_only_input_hash_calls\":"<<assertion_input_hash_calls
  <<",\"software_fill_provider_calls\":"<<software_fill_calls
  <<",\"program_generation_host_seconds\":"<<generation_seconds<<",\"program_generations\":"<<generations
  <<",\"assertion_only_program_generation_host_seconds\":"<<assertion_generation_seconds<<",\"assertion_only_program_generations\":"<<assertion_generations
  <<",\"dataset_provider_host_seconds\":"<<d.item_seconds<<",\"dataset_requests\":"<<d.item_requests
  <<",\"assertion_only_hash_host_seconds\":"<<assertion_seconds<<",\"provider_device_cycles\":null,\"provider_internal_physical_traffic_bytes\":null}\n";
 if(!out)throw std::runtime_error("provider statistics write");
 }catch(const std::exception& e){vpi_printf("FAIL native statistics: %s\n",e.what());vpi_control(vpiFinish,1);}return 0;}
static void register_tasks(){
 for(auto pair:std::vector<std::pair<const char*,PLI_INT32(*)(PLI_BYTE8*)>>{{"$rx_life_initial",initial},{"$rx_life_input_hash",input_hash},{"$rx_life_input_hash_assertion",input_hash_assertion},{"$rx_generate",generate},{"$rx_generate_assertion",generate_assertion},{"$rx_next_seed",next_seed},{"$rx_dataset",dataset_read},{"$rx_provider_stats",statistics}}){
  s_vpi_systf_data d{};d.type=vpiSysTask;d.tfname=(PLI_BYTE8*)pair.first;d.calltf=pair.second;vpi_register_systf(&d);
 }
}
extern "C" { void (*vlog_startup_routines[])()={register_tasks,nullptr}; }
