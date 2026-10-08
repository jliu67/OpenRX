/*
 * OpenRX same-process measurement harness. No RandomX algorithm changes.
 * The block template below is from RandomX src/tests/benchmark.cpp:
 * Copyright (c) 2018-2019, tevador <tevador@gmail.com>
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *  * Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *  * Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *  * Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */
#include "randomx.h"
#include <algorithm>
#include <array>
#include <cfenv>
#include <cmath>
#include <condition_variable>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
#include <time.h>
#include <unistd.h>

using Digest = std::array<uint8_t, RANDOMX_HASH_SIZE>;
static const uint8_t block[] = {
    0x07,0x07,0xf7,0xa4,0xf0,0xd6,0x05,0xb3,0x03,0x26,0x08,0x16,0xba,0x3f,0x10,0x90,0x2e,0x1a,0x14,
    0x5a,0xc5,0xfa,0xd3,0xaa,0x3a,0xf6,0xea,0x44,0xc1,0x18,0x69,0xdc,0x4f,0x85,0x3f,0x00,0x2b,0x2e,
    0xea,0x00,0x00,0x00,0x00,0x77,0xb2,0x06,0xa0,0x2c,0xa5,0xb1,0xd4,0xce,0x6b,0xbf,0xdf,0x0a,0xca,
    0xc3,0x8b,0xde,0xd3,0x4d,0x2d,0xcd,0xee,0xf9,0x5c,0xd2,0x0c,0xef,0xc1,0x2f,0x61,0xd5,0x61,0x09
};
static const char* reference[] = {
    "10b649a3f15c7c7f88277812f2e74b337a0f20ce909af09199cccb960771cfa1",
    "b85d79e080b10b6ad28c2e6c993601a1361917dba979e03a0a8f7248aaf4ba52"
};

struct Options {
    uint32_t threads=1, init=2, nonces=1000, warmup=1000, repeats=4;
    double minimum=1;
    bool hardware=true;
    std::vector<unsigned> versions{0,1};
};
uint32_t integer(const std::string& s, uint32_t low, uint32_t high) {
    if (s.empty() || s.find_first_not_of("0123456789") != std::string::npos)
        throw std::runtime_error("integer options require decimal digits");
    auto n = std::stoull(s);
    if (n < low || n > high) throw std::runtime_error("integer option out of range");
    return static_cast<uint32_t>(n);
}
Options parse(int argc, char** argv) {
    Options o;
    std::map<std::string,std::string> values;
    for (int i=1; i<argc; i+=2) {
        if (i+1 >= argc || !values.emplace(argv[i],argv[i+1]).second)
            throw std::runtime_error("missing value or duplicate option");
    }
    for (const auto& kv: values) {
        const auto& k=kv.first; const auto& v=kv.second;
        if (k=="--threads") o.threads=integer(v,1,256);
        else if (k=="--init-threads") o.init=integer(v,1,256);
        else if (k=="--nonces") o.nonces=integer(v,1,2147483647);
        else if (k=="--warmup-nonces") o.warmup=integer(v,0,2147483647);
        else if (k=="--repeats") o.repeats=integer(v,1,10000);
        else if (k=="--min-seconds") {
            size_t used=0; o.minimum=std::stod(v,&used);
            if (used!=v.size() || !std::isfinite(o.minimum) || o.minimum<0)
                throw std::runtime_error("invalid minimum duration");
        }
        else if (k=="--aes" && (v=="hardware" || v=="software")) o.hardware=(v=="hardware");
        else if (k=="--versions" && v=="v1") o.versions={0};
        else if (k=="--versions" && v=="v2") o.versions={1};
        else if (k=="--versions" && v=="v1,v2") o.versions={0,1};
        else if (k=="--versions" && v=="v2,v1") o.versions={1,0};
        else throw std::runtime_error("unknown option or unsupported value: "+k);
    }
    if (o.threads>o.nonces || (o.warmup && o.threads>o.warmup))
        throw std::runtime_error("nonce counts must cover all workers");
    return o;
}
int64_t clock_ns(clockid_t id) {
    timespec t{};
    if (clock_gettime(id,&t)) throw std::runtime_error("clock_gettime failed");
    return int64_t(t.tv_sec)*1000000000 + t.tv_nsec;
}
int64_t resolution_ns(clockid_t id) {
    timespec t{};
    if (clock_getres(id,&t)) throw std::runtime_error("clock_getres failed");
    return int64_t(t.tv_sec)*1000000000 + t.tv_nsec;
}
struct Stamp { int64_t before, unix_ns, after; };
Stamp stamp() {
    auto before=clock_ns(CLOCK_MONOTONIC);
    auto wall=clock_ns(CLOCK_REALTIME);
    return {before,wall,clock_ns(CLOCK_MONOTONIC)};
}
void print_stamp(const Stamp& s) {
    std::cout << "{\"mono_before_ns\":"<<s.before<<",\"unix_ns\":"<<s.unix_ns
              <<",\"mono_after_ns\":"<<s.after<<"}";
}
std::string hex(const Digest& d) {
    std::string out; static const char* digits="0123456789abcdef";
    for (auto b: d) { out+=digits[b>>4]; out+=digits[b&15]; }
    return out;
}
void xor_digest(Digest& a, const Digest& b) {
    for (size_t i=0; i<a.size(); ++i) a[i]^=b[i];
}

// Every worker owns one VM per requested version, and survives every trial.
// Static striding avoids a shared per-hash atomic and covers [0,count) exactly.
class Pool {
    using VM=std::unique_ptr<randomx_vm,decltype(&randomx_destroy_vm)>;
    struct Slot { std::array<VM,2> vm{VM(nullptr,randomx_destroy_vm),VM(nullptr,randomx_destroy_vm)};
        Digest digest{}; uint32_t count=0; std::exception_ptr error; };
    std::vector<Slot> slots;
    std::vector<std::thread> workers;
    std::mutex mutex;
    std::condition_variable work, finished;
    unsigned ready=0, done=0;
    uint64_t generation=0;
    uint32_t count=0;
    unsigned version=0;
    bool stopping=false;
    void stop() noexcept {
        { std::lock_guard<std::mutex> lock(mutex); stopping=true; }
        work.notify_all();
        for (auto& t: workers) if (t.joinable()) t.join();
    }
    void worker(unsigned id) {
        uint64_t seen=0;
        std::unique_lock<std::mutex> lock(mutex);
        ++ready; finished.notify_one();
        while (true) {
            work.wait(lock,[&]{return stopping || generation!=seen;});
            if (stopping) return;
            seen=generation; auto n=count; auto v=version;
            lock.unlock();
            auto& slot=slots[id]; slot.digest.fill(0); slot.count=0; slot.error=nullptr;
            fenv_t saved{}; bool saved_ok=(fegetenv(&saved)==0);
            try {
                if (!saved_ok) throw std::runtime_error("cannot save worker floating-point environment");
                if (id<n) {
                    std::array<uint8_t,sizeof(block)> input{};
                    std::copy(std::begin(block),std::end(block),input.begin());
                    auto set_nonce=[&](uint32_t nonce){
                        for (unsigned b=0;b<4;++b) input[39+b]=uint8_t(nonce>>(8*b));
                    };
                    Digest hash{}; auto* vm=slot.vm[v].get();
                    set_nonce(id); randomx_calculate_hash_first(vm,input.data(),input.size());
                    for (uint64_t nonce=uint64_t(id)+slots.size();nonce<n;nonce+=slots.size()) {
                        set_nonce(static_cast<uint32_t>(nonce));
                        randomx_calculate_hash_next(vm,input.data(),input.size(),hash.data());
                        xor_digest(slot.digest,hash); ++slot.count;
                    }
                    randomx_calculate_hash_last(vm,hash.data());
                    xor_digest(slot.digest,hash); ++slot.count;
                }
            } catch (...) { slot.error=std::current_exception(); }
            // Batch API changes rounding; do not leak it between jobs.
            if (saved_ok && fesetenv(&saved)!=0)
                slot.error=std::make_exception_ptr(std::runtime_error("cannot restore worker FP environment"));
            lock.lock(); ++done; finished.notify_one();
        }
    }
public:
    struct Result { Digest digest{}; uint64_t hashes=0; Stamp start{},end{}; };
    Pool(const Options& o, randomx_dataset* dataset, randomx_flags flags):slots(o.threads) {
        for (auto& slot: slots) for (auto v: o.versions) {
            auto f=flags | (v ? RANDOMX_FLAG_V2 : RANDOMX_FLAG_DEFAULT);
            slot.vm[v].reset(randomx_create_vm(f,nullptr,dataset));
            if (!slot.vm[v]) throw std::runtime_error("VM allocation/ISA support failed; no silent fallback");
        }
        try {
            for (unsigned i=0;i<slots.size();++i) workers.emplace_back(&Pool::worker,this,i);
            std::unique_lock<std::mutex> lock(mutex);
            finished.wait(lock,[&]{return ready==slots.size();});
        } catch (...) { stop(); throw; }
    }
    ~Pool(){stop();}
    Result run(unsigned v, uint32_t n) {
        Result r;
        {
            std::unique_lock<std::mutex> lock(mutex);
            count=n; version=v; done=0;
            r.start=stamp(); ++generation; work.notify_all();
            finished.wait(lock,[&]{return done==slots.size();});
            r.end=stamp();
        }
        for (const auto& slot: slots) {
            if (slot.error) std::rethrow_exception(slot.error);
            xor_digest(r.digest,slot.digest); r.hashes+=slot.count;
        }
        if (r.hashes!=n) throw std::runtime_error("completed hash count mismatch");
        return r;
    }
};

int main(int argc, char** argv) {
    if (argc==2 && std::string(argv[1])=="--help") {
        std::cout<<"OpenRX steady adapter (Linux, full dataset, JIT, seed 0, small pages)\n"
            <<"--versions v1,v2 --aes hardware|software --threads 1 --init-threads 2\n"
            <<"--nonces 1000 --warmup-nonces 1000 --repeats 4 --min-seconds 1\n";
        return 0;
    }
    try {
        auto o=parse(argc,argv);
        auto supported=randomx_get_flags();
        if (!(supported & RANDOMX_FLAG_JIT) || (o.hardware && !(supported & RANDOMX_FLAG_HARD_AES)))
            throw std::runtime_error("requested JIT/hardware AES unavailable; no silent fallback");
        auto flags=RANDOMX_FLAG_JIT | RANDOMX_FLAG_FULL_MEM;
        if (o.hardware) flags|=RANDOMX_FLAG_HARD_AES;
        std::cout<<std::setprecision(17);
        std::cout<<"{\"type\":\"config\",\"schema_version\":1,\"pid\":"<<getpid()
                 <<",\"threads\":"<<o.threads<<",\"init_threads\":"<<o.init
                 <<",\"nonces\":"<<o.nonces<<",\"warmup_nonces\":"<<o.warmup
                 <<",\"repeats\":"<<o.repeats<<",\"min_seconds\":"<<o.minimum
                 <<",\"aes\":\""<<(o.hardware?"hardware":"software")<<"\",\"flags\":"<<int(flags)
                 <<",\"monotonic_resolution_ns\":"<<resolution_ns(CLOCK_MONOTONIC)
                 <<",\"realtime_resolution_ns\":"<<resolution_ns(CLOCK_REALTIME)
                 <<",\"seed\":0,\"versions\":[";
        for (size_t i=0;i<o.versions.size();++i) std::cout<<(i?",":"")<<"\"v"<<o.versions[i]+1<<"\"";
        std::cout<<"],\"scheduler\":\"static-stride-batch-first-next-last\",\"power_watts\":null}\n"<<std::flush;
        using Cache=std::unique_ptr<randomx_cache,decltype(&randomx_release_cache)>;
        using Dataset=std::unique_ptr<randomx_dataset,decltype(&randomx_release_dataset)>;
        Cache cache(randomx_alloc_cache(RANDOMX_FLAG_JIT),randomx_release_cache);
        if (!cache) throw std::runtime_error("cache allocation failed");
        const std::array<uint8_t,4> seed{};
        randomx_init_cache(cache.get(),seed.data(),seed.size());
        Dataset dataset(randomx_alloc_dataset(RANDOMX_FLAG_DEFAULT),randomx_release_dataset);
        if (!dataset) throw std::runtime_error("dataset allocation failed");
        std::vector<std::thread> initialization;
        std::vector<std::exception_ptr> errors(o.init);
        auto items=randomx_dataset_item_count();
        try {
            for (uint32_t i=0;i<o.init;++i) initialization.emplace_back([&,i]{
                try {
                    const auto begin=uint64_t(items)*i/o.init, end=uint64_t(items)*(i+1)/o.init;
                    randomx_init_dataset(dataset.get(),cache.get(),begin,end-begin);
                } catch (...) { errors[i]=std::current_exception(); }
            });
        } catch (...) { for(auto& t:initialization) t.join(); throw; }
        for (auto& t:initialization) t.join();
        for (auto& e:errors) if(e) std::rethrow_exception(e);
        cache.reset();
        Pool pool(o,dataset.get(),flags);
        uint64_t sequence=0, invalid=0;
        auto trial=[&](const char* phase,unsigned v,uint32_t n,uint32_t repeat){
            const auto r=pool.run(v,n);
            auto elapsed=r.end.before-r.start.after;
            if (elapsed<=0) throw std::runtime_error("non-positive monotonic interval");
            const auto digest=hex(r.digest);
            const bool known=(n==1000), correct=(!known || digest==reference[v]);
            const bool measured=(std::string(phase)=="measurement");
            const char* status=!correct?"hash-mismatch":
                (measured && double(elapsed)/1e9<o.minimum ? "too-short":"ok");
            if (std::string(status)!="ok") ++invalid;
            std::cout<<"{\"type\":\"interval\",\"sequence\":"<<++sequence
                <<",\"phase\":\""<<phase<<"\",\"version\":\"v"<<v+1<<"\",\"repeat\":"<<repeat
                <<",\"hashes\":"<<r.hashes<<",\"digest\":\""<<digest<<"\",\"reference_matches\":"
                <<(known?(correct?"true":"false"):"null")<<",\"status\":\""<<status<<"\",\"start\":";
            print_stamp(r.start); std::cout<<",\"end\":"; print_stamp(r.end);
            std::cout<<",\"elapsed_ns\":"<<elapsed<<"}\n"<<std::flush;
            if (!correct) throw std::runtime_error("known reference hash mismatch; aborting trials");
        };
        for (auto v:o.versions) trial("control",v,1000,0);
        for (uint32_t repeat=1;repeat<=o.repeats;++repeat) {
            auto order=o.versions;
            if (repeat%2==0) std::reverse(order.begin(),order.end());
            for(auto v:order) {
                if(o.warmup) trial("warmup",v,o.warmup,repeat);
                trial("measurement",v,o.nonces,repeat);
            }
        }
        std::cout<<"{\"type\":\"complete\",\"intervals\":"<<sequence
                 <<",\"invalid_intervals\":"<<invalid<<"}\n"<<std::flush;
        return invalid?2:0;
    } catch (const std::exception& e) {
        std::cerr<<"ERROR: "<<e.what()<<'\n'; return 1;
    }
}
