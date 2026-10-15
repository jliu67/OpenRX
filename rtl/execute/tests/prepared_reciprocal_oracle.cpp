// SPDX-License-Identifier: BSD-3-Clause
// Assertion-only gold: unchanged pinned compilation, instructions and iteration.
// One compilation per immutable admission; no prepared data supplies DUT inputs.
#include "bytecode_machine.hpp"
#include "virtual_machine.hpp"
#include "soft_aes.h"
#include <array>
#include <chrono>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <vector>
#include "pinned_destructor.inc"
using namespace randomx;
#include "pinned_float_masks.inc"

static constexpr unsigned Admissions=12,Iterations=4;
static constexpr uint32_t ActiveDivisors[]={3,5,6,7,9,10,0x7ffffffeU,0x7fffffffU,
    0x80000001U,0x80000003U,0x80000008U,0xfffffffdU,0xfffffffeU,0xffffffffU,0x10001U,0x40000001U};
static constexpr unsigned Schedule[]={0,0,1,2,3,0};
static constexpr uint64_t Addresses[]={0x1000,0x1000,0x1000,0x4000,0x4000,0x1000};
static unsigned current_case=0,current_admission=0,total_steps=0,total_events=0;
static unsigned branch_steps=0,branch_taken=0,rcp_steps=0,active_rcp_steps=0,nop_rcp_steps=0;
static unsigned low64_wraps=0,fp_steps=0,cf_steps=0,div_steps=0,sqrt_steps=0;
static std::ofstream steps,events,words,targets,plans,rcp_events,admissions;

static void hex(std::ostream& out,const void* pointer,size_t size) {
    const auto* bytes=static_cast<const uint8_t*>(pointer);
    for(size_t i=size;i>0;--i)out<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(bytes[i-1]);
}
static void image(const std::string& path,const std::vector<uint8_t>& memory) {
    std::ofstream out(path);if(!out)throw std::runtime_error("memory image open");
    for(size_t i=0;i<memory.size();i+=16){hex(out,memory.data()+i,16);out<<'\n';}
    out.close();if(!out)throw std::runtime_error("memory image write");
}
static bool raw_rcp(uint8_t raw){return raw>=ceil_ISMULH_M&&raw<ceil_IMUL_RCP;}
static void instruction(Instruction& op,uint8_t raw,unsigned dst,unsigned src,unsigned mod,uint32_t imm){
    op.opcode=raw;op.dst=uint8_t(dst);op.src=uint8_t(src);op.mod=uint8_t(mod);op.setImm32(imm);
}
static uint32_t nop_divisor(unsigned index){return index==0?0U:uint32_t(1)<<unsigned(index-1);}

// Controlled mixed family selection follows the accepted divsqrt fixture; source
// compilation/execution remains the native pin, including native branch targets.
static void mixed(Program& program,unsigned first,unsigned count,unsigned context){
    const uint8_t ops[]={uint8_t(ceil_IADD_RS-RANDOMX_FREQ_IADD_RS),uint8_t(ceil_IADD_M-RANDOMX_FREQ_IADD_M),
        uint8_t(ceil_ISUB_R-RANDOMX_FREQ_ISUB_R),uint8_t(ceil_ISUB_M-RANDOMX_FREQ_ISUB_M),
        uint8_t(ceil_INEG_R-RANDOMX_FREQ_INEG_R),uint8_t(ceil_IXOR_R-RANDOMX_FREQ_IXOR_R),
        uint8_t(ceil_IXOR_M-RANDOMX_FREQ_IXOR_M),uint8_t(ceil_IROR_R-RANDOMX_FREQ_IROR_R),
        uint8_t(ceil_IROL_R-RANDOMX_FREQ_IROL_R),uint8_t(ceil_ISWAP_R-RANDOMX_FREQ_ISWAP_R),
        uint8_t(ceil_ISTORE-RANDOMX_FREQ_ISTORE),uint8_t(ceil_IMUL_R-RANDOMX_FREQ_IMUL_R),
        uint8_t(ceil_IMUL_M-RANDOMX_FREQ_IMUL_M),uint8_t(ceil_IMULH_R-RANDOMX_FREQ_IMULH_R),
        uint8_t(ceil_IMULH_M-RANDOMX_FREQ_IMULH_M),uint8_t(ceil_ISMULH_R-RANDOMX_FREQ_ISMULH_R),
        uint8_t(ceil_ISMULH_M-RANDOMX_FREQ_ISMULH_M),uint8_t(ceil_IMUL_RCP-RANDOMX_FREQ_IMUL_RCP),
        uint8_t(ceil_FSWAP_R-RANDOMX_FREQ_FSWAP_R),uint8_t(ceil_FADD_R-RANDOMX_FREQ_FADD_R),
        uint8_t(ceil_FADD_M-RANDOMX_FREQ_FADD_M),uint8_t(ceil_FSUB_R-RANDOMX_FREQ_FSUB_R),
        uint8_t(ceil_FSUB_M-RANDOMX_FREQ_FSUB_M),uint8_t(ceil_FSCAL_R-RANDOMX_FREQ_FSCAL_R),
        uint8_t(ceil_FMUL_R-RANDOMX_FREQ_FMUL_R),uint8_t(ceil_FDIV_M-RANDOMX_FREQ_FDIV_M),
        uint8_t(ceil_FSQRT_R-RANDOMX_FREQ_FSQRT_R),uint8_t(ceil_CFROUND-RANDOMX_FREQ_CFROUND),
        uint8_t(ceil_CBRANCH-RANDOMX_FREQ_CBRANCH)};
    const unsigned freq[]={RANDOMX_FREQ_IADD_RS,RANDOMX_FREQ_IADD_M,RANDOMX_FREQ_ISUB_R,RANDOMX_FREQ_ISUB_M,
        RANDOMX_FREQ_INEG_R,RANDOMX_FREQ_IXOR_R,RANDOMX_FREQ_IXOR_M,RANDOMX_FREQ_IROR_R,RANDOMX_FREQ_IROL_R,
        RANDOMX_FREQ_ISWAP_R,RANDOMX_FREQ_ISTORE,RANDOMX_FREQ_IMUL_R,RANDOMX_FREQ_IMUL_M,RANDOMX_FREQ_IMULH_R,
        RANDOMX_FREQ_IMULH_M,RANDOMX_FREQ_ISMULH_R,RANDOMX_FREQ_ISMULH_M,RANDOMX_FREQ_IMUL_RCP,
        RANDOMX_FREQ_FSWAP_R,RANDOMX_FREQ_FADD_R,RANDOMX_FREQ_FADD_M,RANDOMX_FREQ_FSUB_R,RANDOMX_FREQ_FSUB_M,
        RANDOMX_FREQ_FSCAL_R,RANDOMX_FREQ_FMUL_R,RANDOMX_FREQ_FDIV_M,RANDOMX_FREQ_FSQRT_R,
        RANDOMX_FREQ_CFROUND,RANDOMX_FREQ_CBRANCH};
    const uint32_t immediate[]={0,1,0xffffffffU,0x80000000U,0x7fffffffU,8,0xfffffff8U,63,64,65,0x12345678U,0x80000008U};
    for(unsigned k=0;k<count;++k){
        const unsigned family=k%29,group=k/29,pc=first+k;
        const unsigned dst=pc,src=group%3==0?dst:pc*3+group*2+1;
        const unsigned mod=(((group+context*3)%16)<<4)|((group%4)<<2)|((group/4)%4);
        instruction(program(pc),uint8_t(ops[family]+(group+context*7)%freq[family]),dst,src,mod,
            family==17?ActiveDivisors[(group+context)%16]:immediate[group%12]);
    }
}
static void make_program(Program& program,unsigned kind,bool v2){
    const unsigned size=Program::getSize(v2?RANDOMX_FLAG_V2:RANDOMX_FLAG_DEFAULT);
    // Fill the maximum buffer deterministically; only native version-sized slots execute.
    for(unsigned i=0;i<RANDOMX_PROGRAM_MAX_SIZE;++i)
        instruction(program(i),uint8_t(ceil_IMUL_RCP-RANDOMX_FREQ_IMUL_RCP),i,i,0,0);
    if(kind==0){
        for(unsigned i=0;i<256;++i)instruction(program(i),uint8_t(ceil_ISMULH_M+i%8),
            0xa0U|(i/8)%8,0xf8U|i%8,i,nop_divisor(i/8));
        if(v2)mixed(program,256,size-256,0);
    }else if(kind==1){
        for(unsigned i=0;i<8;++i)instruction(program(i),uint8_t(ceil_ISMULH_M+i),0xe0U|i,0xf8U|i,i,0x80000000U);
        mixed(program,8,size-8,1);
        // Last lexical integer write is at b+1. Both RCP NOPs must leave its
        // branch target at b+2; the native branch replays NOPs and an actual store.
        const unsigned b=size-16;
        instruction(program(b),uint8_t(ceil_ISUB_M),6,6,0,0); // IMUL_R immediate zero
        instruction(program(b+1),uint8_t(ceil_IADD_M),6,6,0,0U-384U); // ISUB_R sets384
        instruction(program(b+2),uint8_t(ceil_ISMULH_M),0xfe,0xf9,0xff,0);
        instruction(program(b+3),uint8_t(ceil_ISMULH_M+7),0x86,0xfe,0x80,0x80000000U);
        instruction(program(b+4),uint8_t(ceil_CFROUND),1,2,0xf0,64);
        instruction(program(b+5),uint8_t(ceil_FSQRT_R),6,0,0,0xffffffffU);
        instruction(program(b+6),uint8_t(ceil_FSQRT_R+1),7,0,0,0);
        instruction(program(b+7),uint8_t(ceil_ISMULH_M+2),7,7,0,3);
        instruction(program(b+8),uint8_t(ceil_FSQRT_R+2),7,0,0,0);
        // Remaining mixed suffix retains floating, load/store and CFROUND coverage.
        mixed(program,b+9,7,3);
    }else if(kind==2||kind==3){
        for(unsigned i=0;i<256;++i){
            unsigned alias=(kind-2)*256+i,encoding=alias/64,dst=(alias/8)%8,src=alias%8;
            instruction(program(i),uint8_t(ceil_ISMULH_M+encoding),((encoding*32)&0xf8)|dst,
                0xf8U|src,alias,ActiveDivisors[(alias/8+src)%16]);
        }
        if(v2)mixed(program,256,size-256,kind);
    }else if(kind==4){
        for(unsigned i=0;i<96;++i)instruction(program(i),uint8_t(ceil_ISMULH_M+i%8),
            0xf8U|(i%8),0x80U|((i/8)%8),i,nop_divisor(i%33));
        for(unsigned i=0;i<128;++i)instruction(program(96+i),uint8_t(ceil_ISMULH_M+i%8),
            0x80U|((i/8)%8),0xf8U|(i%8),i,ActiveDivisors[i/8]);
        for(unsigned i=224;i<size;++i)instruction(program(i),uint8_t(ceil_INEG_R),i,i,0,0); // IXOR_R
    }else throw std::runtime_error("unknown template");
}

class Fixture final:public randomx_vm,public BytecodeMachine {
public:
    static constexpr bool softAes=true;
    NativeRegisterFile boundary{},loaded{},executed{};
    unsigned static_rcp=0,static_active=0,dynamic_rcp=0,dynamic_active=0;
    uint32_t boundary0=0,boundary1=0;
    uint64_t read_address=0,prefetch_address=0;
    Fixture(){datasetOffset=0;mem.mx=0;mem.ma=0;}
    void allocate()override{throw std::runtime_error("unused allocate");}
    void getFinalResult(void*,size_t)override{throw std::runtime_error("hash outside component");}
    void hashAndFill(void*,size_t,uint64_t*)override{throw std::runtime_error("hash outside component");}
    void initScratchpad(void*)override{throw std::runtime_error("fixture initialization is external");}
    void run(void*)override{throw std::runtime_error("bounded iterations use unchanged native body");}
    uint32_t mx()const{return mem.mx;}uint32_t ma()const{return mem.ma;}
    uint64_t offset()const{return datasetOffset;}
    ProgramConfiguration cfg()const{return config;}
    const uint64_t* dataset_line()const{return fixture_line;}
    uint64_t prepare(bool v2,unsigned kind,NativeRegisterFile& nreg,uint8_t* memory){
        vmFlags=v2?RANDOMX_FLAG_V2:RANDOMX_FLAG_DEFAULT;scratchpad=memory;
        mem.mx=mem.ma=0;datasetOffset=64*uint64_t(17+current_admission);
        config.readReg0=0;config.readReg1=2;config.readReg2=4;config.readReg3=6;
        config.eMask[0]=getFloatMask(UINT64_C(0x123456789abcdef0));
        config.eMask[1]=getFloatMask(UINT64_C(0xfedcba9876543210));
        const uint64_t lo[]={0x3ff0000000000001ULL,0x3ff8000000000001ULL,0x3ff4000000000003ULL,0x3fffffffffffffffULL};
        const uint64_t hi[]={0x3ff2000000000005ULL,0x3ff1000000000001ULL,0x3ff7000000000003ULL,0x3ffe000000000001ULL};
        for(unsigned i=0;i<4;++i)nreg.a[i]=rx_set_vec_f128(hi[i],lo[i]);
        make_program(program,kind,v2);static_rcp=static_active=0;
        auto begin=std::chrono::steady_clock::now();
        compileProgram(program,bytecode,nreg,vmFlags);
        uint64_t nanos=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-begin).count();
        for(unsigned pc=0;pc<Program::getSize(vmFlags);++pc){
            auto& op=program(pc);const auto& ibc=bytecode[pc];bool valid=raw_rcp(op.opcode),nop=valid&&ibc.type==InstructionType::NOP;
            uint64_t reciprocal=valid&&!nop?ibc.imm:0;
            if(valid&&!nop&&(ibc.type!=InstructionType::IMUL_R||ibc.isrc!=&ibc.imm))throw std::runtime_error("native RCP binding");
            words<<std::dec<<current_admission<<' '<<pc<<' ';hex(words,&op,8);words<<'\n';
            targets<<std::dec<<current_admission<<' '<<pc<<' '<<unsigned(op.opcode)<<' '
                <<(ibc.type==InstructionType::CBRANCH?ibc.target+1:-1)<<'\n';
            plans<<std::dec<<current_admission<<' '<<pc<<' '<<unsigned(valid)<<' '<<unsigned(nop)<<' '
                <<std::hex<<(valid?op.getImm32():0)<<' '<<reciprocal<<'\n';
            static_rcp+=valid;static_active+=valid&&!nop;
        }
        return nanos;
    }
    void primitive(const std::string& out){
        std::ofstream p(out+"/primitive-programs.hex"),m(out+"/primitive-metadata.hex");
        if(!p||!m)throw std::runtime_error("primitive outputs");
        NativeRegisterFile nreg{};
        for(unsigned version=0;version<2;++version){
            bool v2=version!=0;randomx_flags flags=v2?RANDOMX_FLAG_V2:RANDOMX_FLAG_DEFAULT;
            make_program(program,4,v2);compileProgram(program,bytecode,nreg,flags);
            for(unsigned pc=0;pc<Program::getSize(flags);++pc){
                auto& op=program(pc);auto& ibc=bytecode[pc];bool valid=raw_rcp(op.opcode),nop=valid&&ibc.type==InstructionType::NOP;
                p<<std::dec<<version<<' '<<pc<<' ';hex(p,&op,8);p<<'\n';
                m<<std::dec<<version<<' '<<pc<<' '<<unsigned(valid)<<' '<<unsigned(nop)<<' '
                    <<std::hex<<(valid?op.getImm32():0)<<' '<<(valid&&!nop?ibc.imm:0)<<'\n';
            }
        }
        p.close();m.close();if(!p||!m)throw std::runtime_error("primitive write");
    }
    void iteration(NativeRegisterFile& nreg,uint32_t& spAddr0,uint32_t& spAddr1){
        active=&nreg;addr0=&spAddr0;addr1=&spAddr1;dynamic_rcp=dynamic_active=0;
#include "pinned_iteration.inc"
        if(spAddr0||spAddr1)throw std::runtime_error("native cursor reset");
    }
private:
    void executeBytecode(InstructionByteCode bytecode[RANDOMX_PROGRAM_MAX_SIZE],uint8_t* scratchpad,ProgramConfiguration& config,randomx_flags flags){
        loaded=*active;
#include "pinned_bytecode_loop.inc"
        executed=*active;
    }
    void executeInstruction(RANDOMX_EXE_ARGS){
        const int before_pc=pc;const uint8_t raw=program(pc).opcode;
        unsigned address=0;bool read=false,write=false,rcp=raw_rcp(raw),nop=rcp&&ibc.type==InstructionType::NOP;
        switch(ibc.type){
            case InstructionType::IADD_M:case InstructionType::ISUB_M:case InstructionType::IXOR_M:
            case InstructionType::IMUL_M:case InstructionType::IMULH_M:case InstructionType::ISMULH_M:
            case InstructionType::FADD_M:case InstructionType::FSUB_M:case InstructionType::FDIV_M:
                address=unsigned((uint8_t*)getScratchpadAddress(ibc,scratchpad)-scratchpad);read=true;break;
            case InstructionType::ISTORE:address=unsigned((*ibc.idst+ibc.imm)&ibc.memMask);write=true;break;
            default:break;
        }
        if(read||write)if(address%8||address+8>ScratchpadSize)throw std::runtime_error("native access bounds");
        if(read)event(unsigned(before_pc),false,address,load64(scratchpad+address));
        uint64_t before_rcp=rcp?active->r[program(pc).dst%8]:0;
        BytecodeMachine::executeInstruction(ibc,pc,scratchpad,config,flags);
        steps<<std::dec<<current_case<<' '<<before_pc<<' '<<unsigned(raw)<<' ';hex(steps,active->r,64);steps<<' ';
        hex(steps,active->f,64);steps<<' ';hex(steps,active->e,64);steps<<' '<<std::dec<<rx_get_rounding_mode()<<' '<<pc+1<<'\n';
        ++total_steps;
        if(rcp){
            uint64_t value=nop?0:ibc.imm,after_rcp=active->r[program(before_pc).dst%8];
            bool wrapped=!nop&&((__uint128_t(before_rcp)*value)>>64)!=0;
            rcp_events<<std::dec<<current_case<<' '<<before_pc<<' '<<unsigned(raw)<<' '<<unsigned(nop)<<' '
                <<std::hex<<program(before_pc).getImm32()<<' '<<before_rcp<<' '<<value<<' '<<after_rcp<<' '<<unsigned(wrapped)<<'\n';
            ++rcp_steps;++dynamic_rcp;if(nop)++nop_rcp_steps;else{++active_rcp_steps;++dynamic_active;low64_wraps+=wrapped;}
        }
        if(ibc.type==InstructionType::CBRANCH){++branch_steps;branch_taken+=pc!=before_pc;}
        if(raw>=ceil_ISWAP_R&&raw<ceil_FSQRT_R)++fp_steps;
        if(ibc.type==InstructionType::CFROUND)++cf_steps;
        if(ibc.type==InstructionType::FDIV_M)++div_steps;
        if(ibc.type==InstructionType::FSQRT_R)++sqrt_steps;
        if(write)event(unsigned(before_pc),true,address,load64(scratchpad+address));
    }
    void event(unsigned pc,bool write,unsigned address,uint64_t value){
        events<<std::dec<<current_case<<' '<<pc<<' '<<unsigned(write)<<' '<<std::hex<<address<<' '<<value<<'\n';++total_events;
    }
#include "pinned_scratchpad_address.inc"
    InstructionByteCode bytecode[RANDOMX_PROGRAM_MAX_SIZE];
    NativeRegisterFile* active=nullptr;uint32_t *addr0=nullptr,*addr1=nullptr;
    alignas(64) uint64_t fixture_line[8];
    void fixtureRead(uint64_t address,int_reg_t(&r)[RegistersCount]){
#include "pinned_dataset_read.inc"
    }
    void datasetRead(uint64_t address,int_reg_t(&r)[RegistersCount]){
        read_address=address;uint64_t x=address^UINT64_C(0xdabacafe13456789);
        for(auto& value:fixture_line){x^=x<<13;x^=x>>7;x^=x<<17;value=x;}
        mem.memory=(uint8_t*)fixture_line;fixtureRead(0,r);
        boundary=*active;boundary0=*addr0;boundary1=*addr1;
    }
    void datasetPrefetch(uint64_t address){prefetch_address=address;}
};

int main(int argc,char** argv){
    if(argc!=2)return 2;static_assert(ScratchpadSize==2097152,"pinned scratchpad size");
    static_assert(RANDOMX_FREQ_IMUL_RCP==8,"all eight native encodings");
    std::string out=argv[1];std::vector<uint8_t> memory(ScratchpadSize);
    for(size_t i=0;i<memory.size();++i)memory[i]=uint8_t(i*37+(i>>11)+0x5a);
    const uint64_t edges[]={UINT64_MAX,UINT64_C(0x8000000000000000),UINT64_C(0x7fffffffffffffff),
        UINT64_C(0xaaaaaaaaaaaaaaaa),UINT64_C(0x5555555555555555),UINT64_MAX-1,3,UINT64_C(0xffffffff00000000)};
    for(unsigned i=0;i<8;++i){store64(memory.data()+8*i,edges[i]);store64(memory.data()+ScratchpadSize-64+8*i,edges[7-i]);}
    image(out+"/initial.hex",memory);
    std::ofstream trace(out+"/iterations.hex");
    steps.open(out+"/instruction-steps.hex");events.open(out+"/accesses.hex");words.open(out+"/programs.hex");
    targets.open(out+"/compiled-targets.hex");plans.open(out+"/reciprocal-plan.hex");
    rcp_events.open(out+"/reciprocal-events.hex");admissions.open(out+"/admissions.hex");
    if(!trace||!steps||!events||!words||!targets||!plans||!rcp_events||!admissions)throw std::runtime_error("trace open");
    Fixture vm;vm.primitive(out);NativeRegisterFile nreg{};unsigned reads=0,writes=0;
    for(unsigned admission=0;admission<Admissions;++admission){
        current_admission=admission;bool v2=admission<6;unsigned local=admission%6,kind=Schedule[local];
        nreg=NativeRegisterFile{};rx_set_rounding_mode(admission%4);
        uint64_t nanos=vm.prepare(v2,kind,nreg,memory.data());uint32_t sp0=vm.mx(),sp1=vm.ma();auto cfg=vm.cfg();
        admissions<<std::dec<<admission<<' '<<unsigned(v2)<<' '<<kind<<' '<<admission*Iterations<<' '<<Iterations<<' '
            <<vm.static_rcp<<' '<<vm.static_active<<' '<<nanos<<' '<<std::hex<<Addresses[local]<<'\n';
        for(unsigned iteration=0;iteration<Iterations;++iteration){
            current_case=admission*Iterations+iteration;auto input=nreg;unsigned oldround=rx_get_rounding_mode();
            unsigned start=total_events;uint32_t old0=sp0,old1=sp1,oldmx=vm.mx(),oldma=vm.ma();
            vm.iteration(nreg,sp0,sp1);
            trace<<std::dec<<current_case<<' '<<unsigned(v2)<<' '<<unsigned(iteration!=0)<<' '<<start<<' '<<total_events-start<<' '
                <<cfg.readReg0<<' '<<cfg.readReg1<<' '<<cfg.readReg2<<' '<<cfg.readReg3<<' '<<oldround<<' '<<rx_get_rounding_mode()<<' '
                <<std::hex<<old0<<' '<<old1<<' '<<oldmx<<' '<<oldma<<' '<<cfg.eMask[0]<<' '<<cfg.eMask[1]<<' '<<vm.offset()<<' ';
            hex(trace,input.r,64);trace<<' ';hex(trace,input.a,64);trace<<' ';hex(trace,vm.loaded.r,64);trace<<' ';
            hex(trace,vm.loaded.f,64);trace<<' ';hex(trace,vm.loaded.e,64);trace<<' ';hex(trace,vm.executed.r,64);trace<<' ';
            hex(trace,vm.executed.f,64);trace<<' ';hex(trace,vm.executed.e,64);trace<<' '<<vm.read_address<<' '<<vm.prefetch_address<<' ';
            hex(trace,vm.dataset_line(),64);trace<<' ';hex(trace,nreg.r,64);trace<<' ';hex(trace,nreg.f,64);trace<<' ';hex(trace,nreg.e,64);
            trace<<' '<<vm.mx()<<' '<<vm.ma()<<' '<<(vm.boundary0>>6)<<' '<<(vm.boundary1>>6)<<' ';
            hex(trace,memory.data()+vm.boundary0,64);trace<<' ';hex(trace,memory.data()+vm.boundary1,64);trace<<'\n';
        }
        image(out+"/final-"+std::to_string(admission)+".hex",memory);
    }
    trace.close();steps.close();events.close();words.close();targets.close();plans.close();rcp_events.close();admissions.close();
    if(!trace||!steps||!events||!words||!targets||!plans||!rcp_events||!admissions)throw std::runtime_error("trace write");
    std::ifstream input_events(out+"/accesses.hex");unsigned c,pc,w,addr;uint64_t data;
    while(input_events>>std::dec>>c>>pc>>w>>std::hex>>addr>>data){w?++writes:++reads;}
    if(!input_events.eof())throw std::runtime_error("event reread");
    std::ofstream summary(out+"/oracle-summary.json");
    summary<<"{\"admissions\":12,\"iterations\":48,\"iterations_per_admission\":4,\"v2\":24,\"v1\":24,"
        <<"\"instruction_steps\":"<<total_steps<<",\"branches\":"<<branch_steps<<",\"branch_taken\":"<<branch_taken
        <<",\"dynamic_rcp\":"<<rcp_steps<<",\"dynamic_active_rcp\":"<<active_rcp_steps<<",\"dynamic_nop_rcp\":"<<nop_rcp_steps
        <<",\"low64_wraps\":"<<low64_wraps<<",\"fp_steps\":"<<fp_steps<<",\"cf_steps\":"<<cf_steps
        <<",\"div_steps\":"<<div_steps<<",\"sqrt_steps\":"<<sqrt_steps<<",\"bytecode_read64\":"<<reads
        <<",\"bytecode_store64\":"<<writes<<",\"full_memory_snapshots\":12,\"scratchpad_bytes\":2097152,"
        <<"\"native_program_compilations\":12,\"native_primitive_compilations\":2,\"iteration_body\":\"verbatim pinned vm_interpreted\","
        <<"\"dataset\":\"deterministic addressed fixture, not full dataset\",\"full_hash\":false}\n";
    summary.close();if(!summary)throw std::runtime_error("summary write");
    std::cout<<"PASS prepared_reciprocal_native admissions=12 iterations=48 instruction_steps="<<total_steps
        <<" dynamic_rcp="<<rcp_steps<<" dynamic_active_rcp="<<active_rcp_steps<<" dynamic_nop_rcp="<<nop_rcp_steps
        <<" branches="<<branch_steps<<" taken="<<branch_taken<<" low64_wraps="<<low64_wraps
        <<" bytecode_reads="<<reads<<" stores="<<writes<<" full_memory_snapshots=12 full_memory_bytes=2097152\n";
}
