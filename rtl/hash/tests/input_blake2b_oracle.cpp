// SPDX-License-Identifier: BSD-3-Clause
// Native expected digests call unchanged pinned blake2b.c only.
#include "blake2/blake2.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <initializer_list>
#include <iostream>
#include <stdexcept>
#include <string>

using Input = std::array<uint8_t,80>;
static uint64_t rng=UINT64_C(0x4f70656e52584948);
static uint8_t next_byte(){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return uint8_t(rng);}
static void hex(std::ostream& out,const uint8_t* bytes,size_t count){
    for(size_t i=count;i;i--)out<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(bytes[i-1]);
}
static void vector(std::ostream& out,unsigned length,const Input& input){
    uint8_t digest[64];
    if(length>80||blake2b(digest,64,input.data(),length,nullptr,0))throw std::runtime_error("native input BLAKE2b");
    out<<std::dec<<length<<' ';hex(out,input.data(),input.size());out<<' ';hex(out,digest,64);out<<'\n';
}
static bool boundary(unsigned length){
    for(unsigned value:{0U,1U,7U,8U,15U,16U,31U,32U,63U,64U,65U,79U,80U})if(value==length)return true;
    return false;
}
int main(int argc,char** argv){
    try{
        if(argc!=2)throw std::runtime_error("usage: oracle OUTPUT_DIRECTORY");
        const std::string dir=argv[1];
        std::ofstream all(dir+"/vectors.hex"),mapped(dir+"/mapped-vectors.hex"),control(dir+"/control.hex");
        if(!all||!mapped||!control)throw std::runtime_error("native vector output open");
        unsigned total=0,mapped_count=0;
        for(unsigned length=0;length<=80;length++){
            for(unsigned pattern=0;pattern<4;pattern++){
                Input input{};
                for(unsigned i=0;i<80;i++)input[i]=pattern==0?0:pattern==1?255:pattern==2?uint8_t(i):next_byte();
                vector(all,length,input);total++;
                if(pattern==2&&boundary(length)){vector(mapped,length,input);mapped_count++;}
            }
            // Equal prefixes and opposite unused tails must produce equal digests.
            for(unsigned poison=0;poison<2;poison++){
                Input input{};for(unsigned i=0;i<80;i++)input[i]=i<length?uint8_t(i):uint8_t(poison?255:0);
                vector(all,length,input);total++;
                if(poison&&boundary(length)){vector(mapped,length,input);mapped_count++;}
            }
        }
        for(unsigned n=0;n<128;n++){
            Input input{};for(auto& byte:input)byte=next_byte();
            vector(all,unsigned(next_byte())%81,input);total++;
        }
        Input first{},restart{};for(unsigned i=0;i<80;i++){first[i]=uint8_t(i);restart[i]=255;}
        vector(control,80,first);vector(control,0,restart);
        // Pinned native explicitly accepts nullptr for an empty message.
        uint8_t empty_null[64],empty_buffer[64];
        if(blake2b(empty_null,64,nullptr,0,nullptr,0)||blake2b(empty_buffer,64,restart.data(),0,nullptr,0))
            throw std::runtime_error("native empty input");
        for(unsigned i=0;i<64;i++)if(empty_null[i]!=empty_buffer[i])throw std::runtime_error("empty input pointer semantics");
        all.close();mapped.close();control.close();
        if(!all||!mapped||!control||total!=614||mapped_count!=26)throw std::runtime_error("native corpus write/count");
        std::ofstream summary(dir+"/native-summary.json");
        summary<<"{\"native_vectors\":"<<total<<",\"mapped_vectors\":"<<mapped_count
               <<",\"valid_lengths\":81,\"patterns_per_length\":4,\"tail_poison_cases\":162,\"arbitrary_cases\":128,"
               <<"\"control_vectors\":2,\"empty_null_input_verified\":true,\"digest_bytes\":64,"
               <<"\"oracle\":\"unchanged pinned blake2b.c unkeyed64\"}\n";
        summary.close();if(!summary)throw std::runtime_error("native summary write");
        std::cout<<"PASS native_input_blake2b native_vectors=614 mapped_vectors=26 valid_lengths=81 tail_poison=162 empty_null=1\n";
        return 0;
    }catch(const std::exception& error){std::cerr<<"FAIL native_input_blake2b: "<<error.what()<<'\n';return 1;}
}
