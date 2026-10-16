// SPDX-License-Identifier: BSD-3-Clause
// Same native callback boundary as VPI; no golden state drives this provider.
#include <svdpi.h>
#include "lifecycle_native.hpp"
#include <cstdlib>
#include <iostream>

static double initial_seconds=0,input_hash_seconds=0,generation_seconds=0,assertion_seconds=0,assertion_generation_seconds=0,assertion_input_hash_seconds=0;
static unsigned generations=0,input_hash_calls=0,software_fill_calls=0,assertion_generations=0,assertion_input_hash_calls=0;
template<class Function> static void checked(Function fn) {
 try { fn(); }
 catch(const std::exception& error) {
  std::cerr << "FAIL native DPI source: " << error.what() << '\n';
  std::exit(1);
 }
}
extern "C" void rx_life_initial(const svBitVecVal* value,int length,const char* filename,svBitVecVal* result) {
 checked([&] {
  if(length<0||length>80)throw std::runtime_error("input length");
  lifecycle_native::dataset();auto started=lifecycle_native::Clock::now();
  auto* bytes=reinterpret_cast<const uint8_t*>(value);
  std::vector<uint8_t> input(bytes,bytes+length),memory(randomx::ScratchpadSize);
  alignas(16) uint8_t seed[64];lifecycle_native::initial(input,seed,memory);
  sequence_fixture::image(filename,memory);std::memcpy(result,seed,64);
  initial_seconds+=lifecycle_native::seconds(started);++software_fill_calls;
 });
}
static void input_hash(const svBitVecVal* value,int length,svBitVecVal* result,bool assertion_only) {
 checked([&] {
  if(length<0||length>80)throw std::runtime_error("input length");
  lifecycle_native::dataset();auto started=lifecycle_native::Clock::now();
  auto* bytes=reinterpret_cast<const uint8_t*>(value);
  std::vector<uint8_t> input(bytes,bytes+length);alignas(16) uint8_t seed[64];
  lifecycle_native::input_hash(input,seed);std::memcpy(result,seed,64);
  if(assertion_only){assertion_input_hash_seconds+=lifecycle_native::seconds(started);++assertion_input_hash_calls;}
  else {input_hash_seconds+=lifecycle_native::seconds(started);++input_hash_calls;}
 });
}
extern "C" void rx_life_input_hash(const svBitVecVal* value,int length,svBitVecVal* result) {input_hash(value,length,result,false);}
extern "C" void rx_life_input_hash_assertion(const svBitVecVal* value,int length,svBitVecVal* result) {input_hash(value,length,result,true);}
static void generate(const svBitVecVal* value,const char* filename,svBitVecVal* entropy,bool assertion_only) {
 checked([&] {
  alignas(16) uint8_t seed[64];std::memcpy(seed,value,64);auto started=lifecycle_native::Clock::now();
  randomx::Program program;sequence_fixture::generate(seed,program);sequence_fixture::words(filename,program);
  std::memcpy(entropy,&program,128);
  if(assertion_only){assertion_generation_seconds+=lifecycle_native::seconds(started);++assertion_generations;}
  else {generation_seconds+=lifecycle_native::seconds(started);++generations;}
 });
}
extern "C" void rx_generate(const svBitVecVal* value,const char* filename,svBitVecVal* entropy) {generate(value,filename,entropy,false);}
extern "C" void rx_generate_assertion(const svBitVecVal* value,const char* filename,svBitVecVal* entropy) {generate(value,filename,entropy,true);}
extern "C" void rx_next_seed(const svBitVecVal* r,const svBitVecVal* f,const svBitVecVal* e,const svBitVecVal* a,svBitVecVal* result) {
 checked([&] {
  randomx::RegisterFile reg;std::memcpy(reg.r,r,64);std::memcpy(reg.f,f,64);std::memcpy(reg.e,e,64);std::memcpy(reg.a,a,64);
  auto started=lifecycle_native::Clock::now();alignas(16) uint8_t seed[64];sequence_fixture::hash_registers(reg,seed);
  std::memcpy(result,seed,64);assertion_seconds+=lifecycle_native::seconds(started);
 });
}
extern "C" void rx_dataset(const svBitVecVal* address,svBitVecVal* result) {
 checked([&] {
  uint64_t value;std::memcpy(&value,address,8);alignas(64) uint8_t line[64];
  lifecycle_native::dataset().read(value,line);std::memcpy(result,line,64);
 });
}
extern "C" void rx_provider_stats(const char* filename) {
 checked([&] {
  auto& d=lifecycle_native::dataset();std::ofstream out(filename);out<<std::setprecision(17)
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
 });
}
