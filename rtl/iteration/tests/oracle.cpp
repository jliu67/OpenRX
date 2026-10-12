// SPDX-License-Identifier: BSD-3-Clause
// Executes the verbatim pinned iteration in a fixture with real bytecode and
// a deterministic dataset-line provider. No full dataset or hash is claimed.
#include "bytecode_machine.hpp"
#include "virtual_machine.hpp"
#include "soft_aes.h"
#include <array>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <vector>

#include "pinned_destructor.inc"
using namespace randomx;
using Bytes64=std::array<uint8_t,64>;
static uint64_t rng=UINT64_C(0x697465722d746169);
static uint64_t next() {rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return rng;}
static void hex(std::ostream& s,const uint8_t* p,size_t n) {
    for(size_t i=n;i>0;--i)s<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(p[i-1]);
}
static void image(const std::string& name,const std::vector<uint8_t>& mem) {
    std::ofstream s(name);
    if(!s)throw std::runtime_error("image open failed");
    for(size_t i=0;i<mem.size();i+=16){hex(s,mem.data()+i,16);s<<'\n';}
    s.close();if(!s)throw std::runtime_error("image write failed");
}

class Fixture final:public randomx_vm,public BytecodeMachine {
public:
    static constexpr bool softAes=true;
    NativeRegisterFile boundary;
    uint32_t boundary0=0,boundary1=0;
    uint64_t read_address=0,prefetch_address=0;
    Fixture() {datasetOffset=0;mem.mx=0;mem.ma=0;}
    void allocate() override {throw std::runtime_error("unused allocate");}
    void getFinalResult(void*,size_t) override {throw std::runtime_error("unused hash");}
    void hashAndFill(void*,size_t,uint64_t*) override {throw std::runtime_error("unused hash");}
    void initScratchpad(void*) override {throw std::runtime_error("unused init");}
    void run(void*) override {throw std::runtime_error("unused full VM");}
    void prepare(bool v2,NativeRegisterFile& nreg,uint8_t* memory) {
        vmFlags=v2?RANDOMX_FLAG_V2:RANDOMX_FLAG_DEFAULT;scratchpad=memory;
        config.readReg0=0;config.readReg1=2;config.readReg2=4;config.readReg3=6;
        config.eMask[0]=config.eMask[1]=UINT64_C(0x3000000000000000);
        // A full-size controlled program, using unchanged compile/execute code.
        const uint8_t ops[]={uint8_t(ceil_IADD_RS-1),uint8_t(ceil_IXOR_R-1),
            uint8_t(ceil_IMUL_R-1),uint8_t(ceil_INEG_R-1),uint8_t(ceil_FADD_R-1),
            uint8_t(ceil_FSUB_R-1),uint8_t(ceil_FMUL_R-1),uint8_t(ceil_FSWAP_R-1)};
        for(unsigned i=0;i<Program::getSize(vmFlags);++i) {
            auto& op=program(i);op.opcode=ops[i%8];op.dst=i%8;op.src=(i+3)%8;
            op.mod=uint8_t(i*13);op.setImm32(uint32_t(i*0x9e3779b9U));
        }
        for(unsigned i=0;i<4;++i) {
            // Finite positive A constants, serialized as raw IEEE64 bits.
            nreg.a[i]=rx_set_vec_f128(UINT64_C(0x3fec000000000000),UINT64_C(0x3fe8000000000000));
        }
        compileProgram(program,bytecode,nreg,vmFlags);
    }
    void iteration(NativeRegisterFile& nreg,uint32_t& spAddr0,uint32_t& spAddr1) {
        active=&nreg;addr0=&spAddr0;addr1=&spAddr1;
#include "pinned_iteration.inc"
        if(spAddr0!=0 || spAddr1!=0)throw std::runtime_error("cursor reset mismatch");
    }
private:
    InstructionByteCode bytecode[RANDOMX_PROGRAM_MAX_SIZE];
    NativeRegisterFile* active=nullptr;
    uint32_t *addr0=nullptr,*addr1=nullptr;
    alignas(64) uint64_t fixture_line[8];
    void fixtureRead(uint64_t address,int_reg_t(&r)[RegistersCount]) {
#include "pinned_dataset_read.inc"
    }
    void datasetRead(uint64_t address,int_reg_t(&r)[RegistersCount]) {
        read_address=address;
        uint64_t x=address^UINT64_C(0xdabacafe13456789);
        for(auto& word:fixture_line){x^=x<<13;x^=x>>7;x^=x<<17;word=x;}
        // Dataset addresses map to deterministic64-byte fixture lines.
        mem.memory=reinterpret_cast<uint8_t*>(fixture_line);fixtureRead(0,r);
        boundary=*active;boundary0=*addr0;boundary1=*addr1;
    }
    void datasetPrefetch(uint64_t address) {prefetch_address=address;}
};

int main(int argc,char** argv) {
    if(argc!=2)return 2;
    static_assert(ScratchpadSize==2097152,"fixture assumes pinned2MiB scratchpad");
    std::string out=argv[1];std::vector<uint8_t> mem(ScratchpadSize);
    for(size_t i=0;i<mem.size();++i)mem[i]=uint8_t(i*37+(i>>11)+0x5a);
    image(out+"/initial.hex",mem);
    std::ofstream trace(out+"/iterations.hex");if(!trace)throw std::runtime_error("trace open");
    Fixture vm;NativeRegisterFile nreg;
    for(unsigned test=0;test<128;++test) {
        const bool v2=test<64;
        for(auto& r:nreg.r)r=next();
        vm.prepare(v2,nreg,mem.data());
        const uint64_t mix=nreg.r[0]^nreg.r[2];
        uint32_t faddr=uint32_t(next())&ScratchpadL3Mask64;
        uint32_t raddr=uint32_t(next())&ScratchpadL3Mask64;
        if(test%8==0)faddr=raddr=0;
        if(test%8==1)faddr=raddr=ScratchpadL3Mask64;
        if(test%8==2){faddr=0;raddr=ScratchpadL3Mask64;}
        if(test%8==3){faddr=ScratchpadL3Mask64;raddr=0;}
        uint32_t spAddr0=faddr^uint32_t(mix),spAddr1=raddr^uint32_t(mix>>32);
        vm.iteration(nreg,spAddr0,spAddr1);
        if(vm.boundary0!=faddr || vm.boundary1!=raddr)throw std::runtime_error("address fixture mismatch");
        trace<<std::dec<<unsigned(v2)<<' '<<std::hex<<(faddr>>6)<<' '<<(raddr>>6)<<' ';
        hex(trace,reinterpret_cast<uint8_t*>(vm.boundary.r),64);trace<<' ';
        hex(trace,reinterpret_cast<uint8_t*>(vm.boundary.f),64);trace<<' ';
        hex(trace,reinterpret_cast<uint8_t*>(vm.boundary.e),64);trace<<' ';
        hex(trace,reinterpret_cast<uint8_t*>(nreg.f),64);trace<<' ';
        hex(trace,mem.data()+raddr,64);trace<<' ';hex(trace,mem.data()+faddr,64);trace<<'\n';
    }
    trace.close();if(!trace)throw std::runtime_error("trace write failed");image(out+"/final.hex",mem);
    std::cout<<"PASS software iterations=128 v2=64 v1=64 aliases=32 scratchpad_bytes=2097152 seed=0x697465722d746169\n";
}
