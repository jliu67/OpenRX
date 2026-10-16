// SPDX-License-Identifier: BSD-3-Clause
// Differential fixtures call unchanged pinned RandomX fillAes1Rx4<true>.
#include "aes_hash.hpp"
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
static Seed seed_for(const std::string& kind) {
    Seed result{};
    uint64_t rng = UINT64_C(0x4f70656e52584631);
    for (size_t i = 0; i < result.size(); ++i) {
        if (kind == "zero") result[i] = 0;
        else if (kind == "ones") result[i] = 255;
        else if (kind == "incrementing") result[i] = uint8_t(i);
        else if (kind == "prng") {
            rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
            result[i] = uint8_t(rng);
        } else throw std::runtime_error("seed kind must be zero, ones, incrementing or prng");
    }
    return result;
}
int main(int argc, char** argv) {
    try {
        if (argc != 4) throw std::runtime_error("usage: oracle OUTPUT_DIRECTORY BYTES SEED_KIND");
        const std::string directory = argv[1], kind = argv[3];
        size_t parsed = 0;
        const auto size = std::stoull(argv[2], &parsed, 10);
        if (parsed != std::strlen(argv[2]) || size < 64 || size > 2097152 || size % 64)
            throw std::runtime_error("fill length must be a multiple of 64 between 64 and 2097152");
        alignas(16) Seed initial = seed_for(kind), final = initial, split = initial;
        using Allocation = std::unique_ptr<uint8_t, decltype(&std::free)>;
        Allocation image(static_cast<uint8_t*>(std::aligned_alloc(16, size)), &std::free);
        Allocation split_image(static_cast<uint8_t*>(std::aligned_alloc(16, size)), &std::free);
        if (!image || !split_image) throw std::runtime_error("aligned native fixture allocation");
        fillAes1Rx4<true>(final.data(), size, image.get());
        // Native continuation must preserve exactly the same image and seed.
        // A zero-length second call is permitted by the unchanged native API.
        fillAes1Rx4<true>(split.data(), 64, split_image.get());
        fillAes1Rx4<true>(split.data(), size - 64, split_image.get() + 64);
        if (std::memcmp(image.get(), split_image.get(), size) || final != split)
            throw std::runtime_error("native split-call continuation disagreement");
        if (std::memcmp(final.data(), image.get() + size - 64, 64))
            throw std::runtime_error("native final seed differs from last 64 image bytes");
        hex_file(directory + "/seed-in.hex", initial.data(), 64, 64);
        hex_file(directory + "/seed-out.hex", final.data(), 64, 64);
        hex_file(directory + "/image.hex", image.get(), size, 16);
        binary_file(directory + "/seed-in.bin", initial.data(), 64);
        binary_file(directory + "/seed-out.bin", final.data(), 64);
        binary_file(directory + "/image.bin", image.get(), size);
        std::ofstream summary(directory + "/native-summary.json");
        summary << "{\"bytes\":" << std::dec << size << ",\"seed_kind\":\"" << kind
                << "\",\"oracle\":\"unchanged pinned fillAes1Rx4<true>\","
                << "\"split_call_continuation_verified\":true,\"final_seed_is_last_64_bytes\":true}\n";
        summary.close();
        if (!summary) throw std::runtime_error("native summary write failed");
        std::cout << "PASS native_initial_scratchpad_fill bytes=" << size << " seed=" << kind
                  << " continuation=1 postfill_seed=1\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL native_initial_scratchpad_fill: " << error.what() << '\n';
        return 1;
    }
}
