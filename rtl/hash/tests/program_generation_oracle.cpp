// SPDX-License-Identifier: BSD-3-Clause
// Native fixtures call unchanged pinned fillAes4Rx4<true>, not a second AES.
#include "aes_hash.hpp"
#include "program.hpp"
#include <array>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

using Seed = std::array<uint8_t, 64>;
static void hex(std::ostream& out, const uint8_t* data, size_t size) {
    for (size_t i = size; i; --i)
        out << std::hex << std::setw(2) << std::setfill('0') << unsigned(data[i - 1]);
    out << '\n';
}
static void hex_file(const std::string& name, const uint8_t* data, size_t size, size_t word) {
    std::ofstream out(name);
    for (size_t i = 0; i < size; i += word) hex(out, data + i, word);
    out.close();
    if (!out) throw std::runtime_error("hex fixture write failed");
}
static void binary_file(const std::string& name, const uint8_t* data, size_t size) {
    std::ofstream out(name, std::ios::binary);
    out.write(reinterpret_cast<const char*>(data), size);
    out.close();
    if (!out) throw std::runtime_error("binary fixture write failed");
}
static Seed seed_for(const std::string& kind, const char* postfill_file) {
    Seed result{};
    if (kind == "postfill") {
        if (!postfill_file) throw std::runtime_error("postfill seed requires its pinned binary fixture");
        std::ifstream input(postfill_file, std::ios::binary);
        input.read(reinterpret_cast<char*>(result.data()), result.size());
        if (!input || input.peek() != std::char_traits<char>::eof())
            throw std::runtime_error("postfill seed must be exactly 64 bytes");
        return result;
    }
    if (postfill_file) throw std::runtime_error("external seed only accepted for postfill case");
    uint64_t rng = UINT64_C(0x4f70656e52584734);
    for (size_t i = 0; i < result.size(); ++i) {
        if (kind == "zero") result[i] = 0;
        else if (kind == "ones") result[i] = 255;
        else if (kind == "incrementing") result[i] = uint8_t(i);
        else if (kind == "prng") {
            rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
            result[i] = uint8_t(rng);
        } else throw std::runtime_error("seed kind must be zero, ones, incrementing, prng or postfill");
    }
    return result;
}
int main(int argc, char** argv) {
    try {
        if (argc != 4 && argc != 5)
            throw std::runtime_error("usage: oracle OUTPUT_DIRECTORY BYTES SEED_KIND [POSTFILL_SEED]");
        static_assert(sizeof(randomx::Program) == 3200, "native max384 Program layout");
        const std::string directory = argv[1], kind = argv[3];
        size_t parsed = 0;
        const auto size = std::stoull(argv[2], &parsed, 10);
        if (parsed != std::strlen(argv[2]) || size < 64 || size > sizeof(randomx::Program) || size % 64)
            throw std::runtime_error("generation length must be a multiple of 64 between 64 and 3200");
        alignas(16) Seed initial = seed_for(kind, argc == 5 ? argv[4] : nullptr), state = initial;
        using Allocation = std::unique_ptr<uint8_t, decltype(&std::free)>;
        Allocation image(static_cast<uint8_t*>(std::aligned_alloc(16, size)), &std::free);
        Allocation repeated(static_cast<uint8_t*>(std::aligned_alloc(16, size)), &std::free);
        if (!image || !repeated) throw std::runtime_error("aligned native fixture allocation");
        fillAes4Rx4<true>(state.data(), size, image.get());
        if (state != initial) throw std::runtime_error("native fillAes4Rx4 mutated its input seed");
        fillAes4Rx4<true>(state.data(), size, repeated.get());
        if (state != initial || std::memcmp(image.get(), repeated.get(), size))
            throw std::runtime_error("native repeated call must restart from unchanged seed");
        alignas(16) randomx::Program program;
        fillAes4Rx4<true>(state.data(), sizeof(program), &program);
        if (state != initial || std::memcmp(image.get(), &program, size))
            throw std::runtime_error("native program prefix/layout or unchanged-seed mismatch");
        hex_file(directory + "/seed-in.hex", initial.data(), 64, 64);
        hex_file(directory + "/image.hex", image.get(), size, 16);
        binary_file(directory + "/seed-in.bin", initial.data(), 64);
        binary_file(directory + "/image.bin", image.get(), size);
        std::ofstream summary(directory + "/native-summary.json");
        summary << "{\"bytes\":" << std::dec << size << ",\"seed_kind\":\"" << kind
                << "\",\"oracle\":\"unchanged pinned fillAes4Rx4<true>\","
                << "\"native_program_bytes\":3200,\"entropy_bytes\":128,\"maximum_instruction_words\":384,"
                << "\"input_seed_unchanged\":true,\"repeated_call_restarts\":true,\"native_program_prefix_verified\":true}\n";
        summary.close();
        if (!summary) throw std::runtime_error("native summary write failed");
        std::cout << "PASS native_program_generation bytes=" << size << " seed=" << kind
                  << " unchanged_seed=1 repeated_call_restarts=1 native_program_prefix=1\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL native_program_generation: " << error.what() << '\n';
        return 1;
    }
}
