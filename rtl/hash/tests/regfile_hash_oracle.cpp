// SPDX-License-Identifier: BSD-3-Clause
#include <cstddef>
#include "common.hpp"
#include "blake2/blake2.h"
#include <fstream>
#include <iomanip>
#include <string>
#include <cstdlib>
static_assert(sizeof(randomx::RegisterFile)==256,"native size");
static_assert(offsetof(randomx::RegisterFile,r)==0&&offsetof(randomx::RegisterFile,f)==64&&offsetof(randomx::RegisterFile,e)==128&&offsetof(randomx::RegisterFile,a)==192,"native byte layout");
static void hex(std::ostream& f,const uint8_t* p,unsigned n){for(unsigned i=n;i>0;--i)f<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(p[i-1]);}
int main(int argc,char**argv){if(argc!=4)return 2;std::ifstream input(argv[1]);std::ofstream f64(argv[2]),f32(argv[3]);std::string line;unsigned count=0;while(input>>line){if(line.size()!=512)return 3;uint8_t bytes[256],d64[64],d32[64]={};for(unsigned i=0;i<256;i++)bytes[i]=std::stoul(line.substr(510-2*i,2),nullptr,16);if(blake2b(d64,64,bytes,256,nullptr,0)||blake2b(d32,32,bytes,256,nullptr,0))return 4;hex(f64,bytes,256);f64<<' ';hex(f64,d64,64);f64<<'\n';hex(f32,bytes,256);f32<<' ';hex(f32,d32,64);f32<<'\n';count++;}if(!count||!f64||!f32)return 5;return 0;}
