// SPDX-License-Identifier: BSD-3-Clause
#include <cstddef>
#include "blake2/blake2.h"
#include <fstream>
#include <iomanip>
#include <cstdint>
static void hex(std::ostream& f,const uint8_t* p,unsigned n){for(unsigned i=n;i>0;--i)f<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(p[i-1]);}
int main(int argc,char**argv){if(argc!=2)return 2;uint8_t input[256],d64[64],d32[64]={};for(unsigned i=0;i<256;i++)input[i]=i;if(blake2b(d64,64,input,256,nullptr,0)||blake2b(d32,32,input,256,nullptr,0))return 3;std::ofstream f(argv[1]);hex(f,input,256);f<<' ';hex(f,d64,64);f<<' ';hex(f,d32,64);f<<'\n';return !f;}
