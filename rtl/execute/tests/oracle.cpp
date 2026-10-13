// SPDX-License-Identifier: BSD-3-Clause
// Golden-only native execution; hardware independently fetches/executes these instructions.
// Executes the verbatim pinned iteration in a fixture with real bytecode and
// a deterministic dataset-line provider. No full dataset or hash is claimed.
#include "bytecode_machine.hpp"
#include "virtual_machine.hpp"
#include "soft_aes.h"
#include <array>
#include <cstring>
#include <climits>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <vector>

#include "pinned_destructor.inc"
using namespace randomx;
using Bytes64=std::array<uint8_t,64>;
static uint64_t rng=UINT64_C(0x656e67696e652d35);
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

struct Access {unsigned test,pc,write,addr;uint64_t data;};
static std::vector<Access> accesses;
static unsigned current_test=0;
static std::ofstream instruction_steps;
static std::ofstream program_words;
#include "pinned_float_masks.inc"
class Fixture final:public randomx_vm,public BytecodeMachine {
public:
    static constexpr bool softAes=true;
    NativeRegisterFile boundary,loaded,executed;
    uint32_t boundary0=0,boundary1=0;
    uint64_t read_address=0,prefetch_address=0;
    uint32_t mx()const{return mem.mx;}uint32_t ma()const{return mem.ma;}
    uint64_t offset()const{return datasetOffset;}
    ProgramConfiguration cfg()const{return config;}
    const uint64_t* dataset_line()const{return fixture_line;}
    void cold(uint32_t mx,uint32_t ma) {
        mem.mx=mx;mem.ma=ma;datasetOffset=(next()%(DatasetExtraItems+1))*64;
        config.readReg0=next()%2;config.readReg1=2+next()%2;
        config.readReg2=4+next()%2;config.readReg3=6+next()%2;
        config.eMask[0]=getFloatMask(next());config.eMask[1]=getFloatMask(next());
    }
    Fixture() {datasetOffset=0;mem.mx=0;mem.ma=0;}
    void allocate() override {throw std::runtime_error("unused allocate");}
    void getFinalResult(void*,size_t) override {throw std::runtime_error("unused hash");}
    void hashAndFill(void*,size_t,uint64_t*) override {throw std::runtime_error("unused hash");}
    void initScratchpad(void*) override {throw std::runtime_error("unused init");}
    void run(void*) override {throw std::runtime_error("unused full VM");}
    void prepare(bool v2,NativeRegisterFile& nreg,uint8_t* memory) {
        vmFlags=v2?RANDOMX_FLAG_V2:RANDOMX_FLAG_DEFAULT;scratchpad=memory;
        // A full-size controlled program, using unchanged compile/execute code.
        const uint8_t ops[]={uint8_t(ceil_IADD_RS-RANDOMX_FREQ_IADD_RS),uint8_t(ceil_IADD_M-RANDOMX_FREQ_IADD_M),
            uint8_t(ceil_ISUB_R-RANDOMX_FREQ_ISUB_R),uint8_t(ceil_ISUB_M-RANDOMX_FREQ_ISUB_M),uint8_t(ceil_INEG_R-RANDOMX_FREQ_INEG_R),
            uint8_t(ceil_IXOR_R-RANDOMX_FREQ_IXOR_R),uint8_t(ceil_IXOR_M-RANDOMX_FREQ_IXOR_M),uint8_t(ceil_IROR_R-RANDOMX_FREQ_IROR_R),
            uint8_t(ceil_IROL_R-RANDOMX_FREQ_IROL_R),uint8_t(ceil_ISWAP_R-RANDOMX_FREQ_ISWAP_R),uint8_t(ceil_ISTORE-RANDOMX_FREQ_ISTORE)};
        const unsigned freq[]={RANDOMX_FREQ_IADD_RS,RANDOMX_FREQ_IADD_M,RANDOMX_FREQ_ISUB_R,RANDOMX_FREQ_ISUB_M,RANDOMX_FREQ_INEG_R,
            RANDOMX_FREQ_IXOR_R,RANDOMX_FREQ_IXOR_M,RANDOMX_FREQ_IROR_R,RANDOMX_FREQ_IROL_R,RANDOMX_FREQ_ISWAP_R,RANDOMX_FREQ_ISTORE};
        const uint32_t imm[]={0,1,0xffffffffU,0x80000000U,0x7fffffffU,8,0xfffffff8U,63,64,65,0x12345678U,0x80000008U};
        for(unsigned i=0;i<Program::getSize(vmFlags);++i) {
            unsigned family=i%11,group=i/11;
            auto& op=program(i);op.opcode=uint8_t(ops[family]+group%freq[family]);op.dst=uint8_t(i);
            op.src=group%3==0?op.dst:uint8_t(i*3+group*2+1);
            unsigned cond=group%4==0?15:group%16;
            op.mod=uint8_t((cond<<4)|((group%4)<<2)|((group/4)%4));
            op.setImm32(imm[group%12]^uint32_t((group/12)*0x9e3779b9U));
            program_words<<std::dec<<current_test<<' '<<i<<' ';hex(program_words,reinterpret_cast<const uint8_t*>(&op),8);program_words<<'\n';
        }
        for(unsigned i=0;i<4;++i) {
            // Finite positive A constants, serialized as raw IEEE64 bits.
            nreg.a[i]=rx_set_vec_f128(UINT64_C(0x3ff8000000000000),UINT64_C(0x3ff4000000000000));
        }
        compileProgram(program,bytecode,nreg,vmFlags);
    }
    void iteration(NativeRegisterFile& nreg,uint32_t& spAddr0,uint32_t& spAddr1) {
        active=&nreg;addr0=&spAddr0;addr1=&spAddr1;
#include "pinned_iteration.inc"
        if(spAddr0!=0 || spAddr1!=0)throw std::runtime_error("cursor reset mismatch");
    }
private:
    void executeBytecode(InstructionByteCode bytecode[RANDOMX_PROGRAM_MAX_SIZE],uint8_t* scratchpad,ProgramConfiguration& config,randomx_flags flags) {
        loaded=*active;
#include "pinned_bytecode_loop.inc"
        executed=*active;
    }
    void executeInstruction(RANDOMX_EXE_ARGS) {
        unsigned address=0;bool read=false,write=false;
        switch(ibc.type) {
            case InstructionType::IADD_M:case InstructionType::ISUB_M:case InstructionType::IXOR_M:
                address=unsigned(static_cast<uint8_t*>(getScratchpadAddress(ibc,scratchpad))-scratchpad);read=true;break;
            case InstructionType::ISTORE:
                // Observational address exactly matches the unchanged pinned exe_ISTORE.
                address=unsigned((*ibc.idst+ibc.imm)&ibc.memMask);write=true;break;
            default:break;
        }
        if((read||write) && (address%8 || address+8>ScratchpadSize))throw std::runtime_error("bad access");
        if(read)accesses.push_back({current_test,unsigned(pc),0,address,load64(scratchpad+address)});
        BytecodeMachine::executeInstruction(ibc,pc,scratchpad,config,flags);
        instruction_steps<<std::dec<<current_test<<' '<<pc<<' '<<unsigned(program(pc).opcode)<<' ';
        hex(instruction_steps,reinterpret_cast<const uint8_t*>(active->r),64);instruction_steps<<'\n';
        if(write)accesses.push_back({current_test,unsigned(pc),1,address,load64(scratchpad+address)});
    }
#include "pinned_scratchpad_address.inc"
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
    const int32_t edges[16]={0,1,-1,INT32_MIN,INT32_MAX,2,-2,0x1000000,-0x1000000,
        0x1000001,-0x1000001,0x40000000,-0x40000000,0x3fffffff,-0x3fffffff,17};
    memcpy(mem.data(),edges,64);memcpy(mem.data()+ScratchpadSize-64,edges,64);
    image(out+"/initial.hex",mem);
    instruction_steps.open(out+"/instruction-steps.hex");program_words.open(out+"/programs.hex");
    if(!instruction_steps || !program_words)throw std::runtime_error("instruction output open");
    Fixture vm;NativeRegisterFile nreg{};uint32_t sp0=0,sp1=0;unsigned aliases=0,reads=0,writes=0;
    for(unsigned test=0;test<8;++test) {
        current_test=test;bool v2=test<4;bool chained=test%4>=2;
        if(!chained) {
            nreg=NativeRegisterFile{};
            uint32_t faddr=uint32_t(next())&ScratchpadL3Mask64,raddr=uint32_t(next())&ScratchpadL3Mask64;
            switch(test%4) {
                case 0:faddr=raddr=0;break;
                case 1:faddr=raddr=ScratchpadL3Mask64;break;
                case 2:faddr=0;raddr=ScratchpadL3Mask64;break;
                case 3:faddr=ScratchpadL3Mask64;raddr=0;break;
                case 4:case 5:raddr=faddr;break;
            }
            vm.cold(faddr,raddr);sp0=faddr;sp1=raddr;rx_set_rounding_mode(test%4);
        }
        vm.prepare(v2,nreg,mem.data());auto cfg=vm.cfg();auto input=nreg;
        unsigned oldround=rx_get_rounding_mode();unsigned start=accesses.size();uint32_t old0=sp0,old1=sp1,oldmx=vm.mx(),oldma=vm.ma();
        vm.iteration(nreg,sp0,sp1);unsigned count=accesses.size()-start;
        if(vm.boundary0==vm.boundary1)++aliases;
        trace<<std::dec<<test<<' '<<unsigned(v2)<<' '<<unsigned(chained)<<' '<<start<<' '<<count<<' '
            <<unsigned(cfg.readReg0)<<' '<<unsigned(cfg.readReg1)<<' '<<unsigned(cfg.readReg2)<<' '<<unsigned(cfg.readReg3)<<' '<<oldround<<' '<<rx_get_rounding_mode()<<' '
            <<std::hex<<old0<<' '<<old1<<' '<<oldmx<<' '<<oldma<<' '<<cfg.eMask[0]<<' '<<cfg.eMask[1]<<' '<<vm.offset()<<' ';
        hex(trace,reinterpret_cast<uint8_t*>(input.r),64);trace<<' ';hex(trace,reinterpret_cast<uint8_t*>(input.a),64);trace<<' ';
        hex(trace,reinterpret_cast<uint8_t*>(vm.loaded.r),64);trace<<' ';
        hex(trace,reinterpret_cast<uint8_t*>(vm.loaded.f),64);trace<<' ';hex(trace,reinterpret_cast<uint8_t*>(vm.loaded.e),64);trace<<' ';
        hex(trace,reinterpret_cast<uint8_t*>(vm.executed.r),64);trace<<' ';hex(trace,reinterpret_cast<uint8_t*>(vm.executed.f),64);trace<<' ';hex(trace,reinterpret_cast<uint8_t*>(vm.executed.e),64);trace<<' ';
        trace<<vm.read_address<<' '<<vm.prefetch_address<<' ';hex(trace,reinterpret_cast<const uint8_t*>(vm.dataset_line()),64);trace<<' ';
        hex(trace,reinterpret_cast<uint8_t*>(nreg.r),64);trace<<' ';hex(trace,reinterpret_cast<uint8_t*>(nreg.f),64);trace<<' ';hex(trace,reinterpret_cast<uint8_t*>(nreg.e),64);trace<<' ';
        trace<<vm.mx()<<' '<<vm.ma()<<' '<<(vm.boundary0>>6)<<' '<<(vm.boundary1>>6)<<' ';
        hex(trace,mem.data()+vm.boundary0,64);trace<<' ';hex(trace,mem.data()+vm.boundary1,64);trace<<'\n';
    }
    instruction_steps.close();program_words.close();if(!instruction_steps || !program_words)throw std::runtime_error("instruction output write");
    trace.close();if(!trace)throw std::runtime_error("trace write");image(out+"/final.hex",mem);
    std::ofstream access(out+"/accesses.hex");
    for(auto e:accesses){access<<std::dec<<e.test<<' '<<e.pc<<' '<<e.write<<' '<<std::hex<<e.addr<<' '<<e.data<<'\n';e.write?++writes:++reads;}
    access.close();if(!access)throw std::runtime_error("access write");
    std::ofstream convert(out+"/i32-vectors.hex");
    for(unsigned mode=0;mode<4;++mode) {
        rx_set_rounding_mode(mode);
        for(unsigned i=0;i<1024;++i) {
            uint32_t bits=uint32_t(next());
            if(i<16)bits=uint32_t(edges[i]);
            else if(i<112) {
                unsigned k=(i-16)/3;
                bits=(uint32_t(1)<<k)+int((i-16)%3)-1;
            }
            alignas(16) uint32_t inputs[2]={bits,~bits};
            alignas(16) uint64_t expected[2];
            auto native=rx_cvt_packed_int_vec_f128(inputs);
            rx_store_vec_f128(reinterpret_cast<double*>(expected),native);
            convert<<std::hex<<bits<<' '<<expected[0]<<'\n';
        }
    }
    convert.close();if(!convert)throw std::runtime_error("conversion vectors write");
    std::ofstream summary(out+"/oracle-summary.json");summary<<"{\"iterations\":8,\"v2\":4,\"v1\":4,\"chained_iterations\":4,\"aliases\":"<<aliases
        <<",\"bytecode_read64\":"<<reads<<",\"bytecode_store64\":"<<writes<<",\"seed\":\"0x656e67696e652d35\"}\n";
    std::cout<<"PASS native integer iterations=8 aliases="<<aliases<<" actual_bytecode_reads="<<reads<<" stores="<<writes<<" full_memory_bytes=2097152\n";
}
