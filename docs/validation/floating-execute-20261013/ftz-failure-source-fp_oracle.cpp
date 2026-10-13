// SPDX-License-Identifier: BSD-3-Clause
// Native pinned RandomX vector operations; MXCSR state is local to this process.
#include "intrin_portable.h"
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <xmmintrin.h>
static uint64_t seed=UINT64_C(0x66702d6e61746976);
static uint64_t next(){seed^=seed<<13;seed^=seed>>7;seed^=seed<<17;return seed;}
__attribute__((noinline)) static rx_vec_f128 calculate(unsigned op,rx_vec_f128 a,rx_vec_f128 b){
 if(op==0)return rx_add_vec_f128(a,b);
 if(op==1)return rx_sub_vec_f128(a,b);
 return rx_mul_vec_f128(a,b);
}
int main(int argc,char**argv){
 if(argc!=2)return 2;std::ofstream s(argv[1]);if(!s)return 3;
 const uint64_t edges[]={0,UINT64_C(0x8000000000000000),1,UINT64_C(0x8000000000000001),
  UINT64_C(0x000fffffffffffff),UINT64_C(0x800fffffffffffff),UINT64_C(0x0010000000000000),
  UINT64_C(0x0010000000000001),UINT64_C(0x3ff0000000000000),UINT64_C(0xbff0000000000000),
  UINT64_C(0x3fefffffffffffff),UINT64_C(0x3ff0000000000001),UINT64_C(0x3ca0000000000000),
  UINT64_C(0x3fe0000000000000),UINT64_C(0x7fefffffffffffff),UINT64_C(0xffefffffffffffff),
  UINT64_C(0x7ff0000000000000),UINT64_C(0xfff0000000000000),UINT64_C(0x7ff8000000001234),
  UINT64_C(0xfff8000000005678),UINT64_C(0x7ff0000000001234),UINT64_C(0xfff0000000005678),
  UINT64_C(0x001fffffffffffff),UINT64_C(0x8010000000000000)};
 unsigned count=0;
 auto emit=[&](uint64_t a,uint64_t b){for(unsigned ftz=0;ftz<2;++ftz)for(unsigned rm=0;rm<4;++rm)for(unsigned op=0;op<3;++op){
  _mm_setcsr((ftz?rx_mxcsr_default:0x1f80)|(rm<<13));
  auto result=calculate(op,rx_set_vec_f128(a,a),rx_set_vec_f128(b,b));
  alignas(16) uint64_t values[2];rx_store_vec_f128((double*)values,result);unsigned csr=_mm_getcsr();
  unsigned flags=((csr&1)?16:0)|((csr&4)?8:0)|((csr&8)?4:0)|((csr&16)?2:0)|((csr&32)?1:0);
  s<<std::hex<<a<<' '<<b<<' '<<op<<' '<<rm<<' '<<ftz<<' '<<values[0]<<' '<<flags<<' '<<csr<<'\n';++count;
 }};
 for(auto a:edges)for(auto b:edges)emit(a,b);
 for(unsigned i=0;i<256;++i){uint64_t a=next(),b=next();emit(a,b);}
 _mm_setcsr(rx_mxcsr_default);s.close();if(!s)return 4;
 std::cout<<"PASS native FP vectors="<<count<<" operations=3 rounding_modes=4 DAZ_FTZ_models=2 seed=66702d6e61746976\n";
}
