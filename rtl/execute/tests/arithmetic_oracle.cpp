// SPDX-License-Identifier: BSD-3-Clause
#include "intrin_portable.h"
#include "reciprocal.h"
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <set>
#include <stdexcept>
static uint64_t random_state=UINT64_C(0x6d756c2d65786563);
static uint64_t next(){random_state^=random_state<<13;random_state^=random_state>>7;random_state^=random_state<<17;return random_state;}
static int64_t signed_bits(uint64_t value){int64_t result;std::memcpy(&result,&value,8);return result;}
int main(int argc,char**argv){
    if(argc!=2)return 2;
    std::string out=argv[1];std::ofstream mul(out+"/multiply.hex"),rcp(out+"/reciprocal.hex");
    if(!mul||!rcp)throw std::runtime_error("arithmetic fixture output");
    const uint64_t edges[]={0,1,2,3,UINT64_MAX,UINT64_MAX-1,UINT64_C(0x8000000000000000),
        UINT64_C(0x7fffffffffffffff),UINT64_C(0x8000000000000001),UINT64_C(0xaaaaaaaaaaaaaaaa),
        UINT64_C(0x5555555555555555),UINT64_C(0x00000000ffffffff),UINT64_C(0xffffffff00000000),
        UINT64_C(0x0000000100000000),UINT64_C(0x0000000080000000),UINT64_C(0x0101010101010101)};
    unsigned count=0;
    auto emit=[&](uint64_t a,uint64_t b){for(unsigned mode=0;mode<3;++mode){
        uint64_t expected=mode==0?a*b:mode==1?mulh(a,b):uint64_t(smulh(signed_bits(a),signed_bits(b)));
        mul<<std::hex<<a<<' '<<b<<' '<<unsigned(mode!=0)<<' '<<unsigned(mode==2)<<' '<<expected<<'\n';++count;
    }};
    for(auto a:edges)for(auto b:edges)emit(a,b);
    for(unsigned i=0;i<512;++i){uint64_t a=next(),b=next();emit(a,b);}
    std::set<uint32_t> divisors={0,3,5,6,7,9,10,0xffffffffU,0xfffffffeU,0x80000001U,0x7fffffffU};
    for(unsigned k=0;k<32;++k){uint32_t value=uint32_t(1)<<k;divisors.insert(value);divisors.insert(value-1);divisors.insert(value+1);}
    for(unsigned i=0;i<512;++i)divisors.insert(uint32_t(next()));
    unsigned rcount=0,nops=0;
    for(auto d:divisors){bool nop=d==0||(d&(d-1))==0;uint64_t result=nop?0:randomx_reciprocal(d);
        rcp<<std::hex<<d<<' '<<unsigned(nop)<<' '<<result<<'\n';++rcount;nops+=nop;
    }
    mul.close();rcp.close();if(!mul||!rcp)throw std::runtime_error("arithmetic fixture write");
    std::cout<<"PASS native arithmetic products="<<count<<" reciprocal="<<rcount<<" nop_divisors="<<nops<<" seed=6d756c2d65786563\n";
}
