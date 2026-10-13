// SPDX-License-Identifier: BSD-3-Clause
// External fixture preparation only: pinned AES/BLAKE2b consumes actual input/state.
#pragma once
#include "common.hpp"
#include "program.hpp"
#include "aes_hash.hpp"
#include "blake2/blake2.h"
#include <cstring>
#include <fstream>
#include <iomanip>
#include <stdexcept>
#include <vector>
namespace sequence_fixture {
static const char message[]="OpenRX native program-sequence fixture 20261013";
static void hex(std::ostream& o,const void* pointer,size_t n){
 const auto* p=(const uint8_t*)pointer;
 for(size_t i=n;i>0;--i)o<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(p[i-1]);
}
static void image(const std::string& name,const std::vector<uint8_t>& mem){
 std::ofstream o(name);if(!o)throw std::runtime_error("image open");
 for(size_t i=0;i<mem.size();i+=16){hex(o,mem.data()+i,16);o<<'\n';}
 o.close();if(!o)throw std::runtime_error("image write");
}
static void initial(uint8_t seed[64],std::vector<uint8_t>& mem){
 if(blake2b(seed,64,message,sizeof(message)-1,nullptr,0))throw std::runtime_error("initial BLAKE2b");
 fillAes1Rx4<true>(seed,mem.size(),mem.data());
}
static void generate(uint8_t seed[64],randomx::Program& p){fillAes4Rx4<true>(seed,sizeof(p),&p);}
static void hash_registers(const randomx::RegisterFile& reg,uint8_t seed[64]){
 static_assert(sizeof(reg)==256,"native register layout");
 if(blake2b(seed,64,&reg,sizeof(reg),nullptr,0))throw std::runtime_error("program BLAKE2b");
}
static void words(const std::string& name,const randomx::Program& p){
 std::ofstream o(name);const uint8_t* bytes=(const uint8_t*)&p;
 for(unsigned i=0;i<RANDOMX_PROGRAM_MAX_SIZE;++i){hex(o,bytes+128+8*i,8);o<<'\n';}
 o.close();if(!o)throw std::runtime_error("program write");
}
}
