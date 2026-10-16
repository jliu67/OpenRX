// SPDX-License-Identifier: BSD-3-Clause
// Untimed host providers using unchanged pinned RandomX code.
#pragma once
#include "program_native_helpers.hpp"
#include "randomx.h"
#include "dataset.hpp"
#include <chrono>
#include <memory>

namespace lifecycle_native {
using Clock = std::chrono::steady_clock;
inline double seconds(Clock::time_point start) {
    return std::chrono::duration<double>(Clock::now() - start).count();
}
static constexpr char cache_key[] = "OpenRX connected lifecycle dataset key 20261016";
struct Dataset {
    randomx_cache* cache;
    double initialization_seconds = 0, item_seconds = 0;
    uint64_t item_requests = 0;
    Dataset() {
        auto start = Clock::now();
        cache = randomx_alloc_cache(RANDOMX_FLAG_DEFAULT);
        if (!cache) throw std::runtime_error("native256MiB cache allocation failed");
        randomx_init_cache(cache, cache_key, sizeof(cache_key) - 1);
        initialization_seconds = seconds(start);
    }
    ~Dataset() { randomx_release_cache(cache); }
    Dataset(const Dataset&) = delete;
    void read(uint64_t address, void* output) {
        if ((address & 63) || address > randomx::DatasetSize - 64)
            throw std::runtime_error("actual native dataset address/alignment");
        auto start = Clock::now();
        // Exactly the unchanged InterpretedLightVm provider; no xorshift fixture.
        randomx::initDatasetItem(cache, static_cast<uint8_t*>(output), address / 64);
        item_seconds += seconds(start);
        ++item_requests;
    }
};
inline Dataset& dataset() { static Dataset result; return result; }
inline void initial(const std::vector<uint8_t>& input, uint8_t seed[64], std::vector<uint8_t>& memory) {
    if (blake2b(seed, 64, input.data(), input.size(), nullptr, 0))
        throw std::runtime_error("native input BLAKE2b");
    // fill updates seed in place; program0 must consume this post-fill seed.
    fillAes1Rx4<true>(seed, memory.size(), memory.data());
}
inline std::vector<uint8_t> unhex(const std::string& text) {
    if (text.size() % 2 || text.size() > 160) throw std::runtime_error("input hex length");
    std::vector<uint8_t> output;
    for (size_t i = 0; i < text.size(); i += 2) {
        auto digit=[](char c) { if(c>='0'&&c<='9')return c-'0'; if(c>='a'&&c<='f')return c-'a'+10;
            if(c>='A'&&c<='F')return c-'A'+10; throw std::runtime_error("input hex digit"); };
        output.push_back(uint8_t(16*digit(text[i])+digit(text[i+1])));
    }
    return output;
}
}
