// SPDX-License-Identifier: BSD-3-Clause
// Reference vectors call unchanged pinned RandomX software, not a second AES.
#include "soft_aes.h"
#include "blake2/endian.h"
#include <array>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>

using Block = std::array<uint8_t, 16>;
using Registers = std::array<Block, 4>;
static uint64_t rng_state = UINT64_C(0x4f70656e52587632);
static uint8_t next_byte() {
    rng_state ^= rng_state << 13;
    rng_state ^= rng_state >> 7;
    rng_state ^= rng_state << 17;
    return uint8_t(rng_state);
}
static Block random_block() {
    Block b;
    for (auto& x : b) x = next_byte();
    return b;
}
static rx_vec_i128 load(const Block& b) {
    return rx_set_int_vec_i128(
        unsigned32ToSigned2sCompl(load32(b.data()+12)),
        unsigned32ToSigned2sCompl(load32(b.data()+8)),
        unsigned32ToSigned2sCompl(load32(b.data()+4)),
        unsigned32ToSigned2sCompl(load32(b.data())));
}
static Block store(rx_vec_i128 y) {
    Block out;
    store32(out.data(), uint32_t(rx_vec_i128_x(y)));
    store32(out.data()+4, uint32_t(rx_vec_i128_y(y)));
    store32(out.data()+8, uint32_t(rx_vec_i128_z(y)));
    store32(out.data()+12, uint32_t(rx_vec_i128_w(y)));
    return out;
}
static Block round(const Block& b, const Block& k, bool dec) {
    return store(dec ? soft_aesdec(load(b),load(k)) : soft_aesenc(load(b),load(k)));
}
static void hex(std::ostream& s, const Block& b) {
    for (auto i=b.rbegin();i!=b.rend();++i)
        s << std::hex << std::setfill('0') << std::setw(2) << unsigned(*i);
}
static void hex(std::ostream& s, const Registers& regs) {
    for (auto i=regs.rbegin();i!=regs.rend();++i) hex(s,*i);
}
int main(int argc, char** argv) {
    if (argc!=2) { std::cerr << "usage: oracle OUTPUT_DIRECTORY\n"; return 2; }
    std::ofstream rounds(std::string(argv[1])+"/rounds.hex");
    std::ofstream mixes(std::string(argv[1])+"/mixes.hex");
    std::ofstream v1(std::string(argv[1])+"/v1.hex");
    if (!rounds || !mixes || !v1) throw std::runtime_error("cannot open vector outputs");
    // Every byte value at every position, both directions, plus random blocks.
    for (unsigned i=0;i<512;++i) {
        Block b=random_block(),k=random_block();
        if (i<256) b.fill(uint8_t(i));
        for (unsigned dec=0;dec<2;++dec) {
            rounds << dec << ' '; hex(rounds,b); rounds << ' '; hex(rounds,k);
            rounds << ' '; hex(rounds,round(b,k,dec!=0)); rounds << '\n';
        }
    }
    for (unsigned i=0;i<256;++i) {
        Registers f,e;
        for (unsigned j=0;j<4;++j) { f[j]=random_block();e[j]=random_block(); }
        if (i==0) { for (auto& b:f) b.fill(0);for (auto& b:e) b.fill(0); }
        if (i==1) { for (auto& b:f) b.fill(255);for (auto& b:e) b.fill(255); }
        if (i==2) {
            for (unsigned j=0;j<4;++j) for(unsigned k=0;k<16;++k) {
                f[j][k]=uint8_t(16*j+k);e[j][k]=uint8_t(255-16*j-k);
            }
        }
        if (i==3) {
            // Raw IEEE NaN/infinity/sign payloads: no floating-point conversion.
            for (unsigned j=0;j<4;++j) {
                store64(f[j].data(),UINT64_C(0x7ff8000000000001)+j);
                store64(f[j].data()+8,UINT64_C(0xfff0000000000000)+j);
                store64(e[j].data(),UINT64_C(0x8000000000000000)+j);
                store64(e[j].data()+8,UINT64_C(0x7ff0000000000000)+j);
            }
        }
        Registers out=f;
        for(unsigned key=0;key<4;++key) for(unsigned lane=0;lane<4;++lane)
            out[lane]=round(out[lane],e[key],lane%2==1);
        hex(mixes,f);mixes << ' ';hex(mixes,e);mixes << ' ';hex(mixes,out);mixes << '\n';
        // vm_interpreted.cpp v1 post-VM boundary: F[i] ^= E[i].
        Registers v1_out;
        for(unsigned lane=0;lane<4;++lane)
            v1_out[lane]=store(rx_xor_vec_i128(load(f[lane]),load(e[lane])));
        hex(v1,v1_out);v1 << '\n';
    }
    rounds.close(); mixes.close(); v1.close();
    if (!rounds || !mixes || !v1) throw std::runtime_error("vector output write failed");
    std::cout << "oracle: rounds=1024 mixes=256 v1=256 seed=0x4f70656e52587632\n";
}
