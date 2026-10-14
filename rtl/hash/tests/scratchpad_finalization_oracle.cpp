// SPDX-License-Identifier: BSD-3-Clause
// Expected results use unchanged pinned RandomX AES/BLAKE2b implementations.
#include "aes_hash.hpp"
#include "blake2/blake2.h"
#include "common.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static_assert(sizeof(randomx::RegisterFile) == 256, "native RegisterFile size");
static_assert(offsetof(randomx::RegisterFile, r) == 0 &&
              offsetof(randomx::RegisterFile, f) == 64 &&
              offsetof(randomx::RegisterFile, e) == 128 &&
              offsetof(randomx::RegisterFile, a) == 192, "native bank offsets");

static size_t input_size(const std::string& path) {
    std::ifstream input(path.c_str(), std::ios::binary | std::ios::ate);
    if (!input) throw std::runtime_error("cannot open input: " + path);
    const std::streampos end = input.tellg();
    if (end < std::streampos(0)) throw std::runtime_error("cannot size input: " + path);
    return static_cast<size_t>(end);
}

static void read_exact(const std::string& path, uint8_t* destination, size_t size) {
    std::ifstream input(path.c_str(), std::ios::binary);
    if (!input || !input.read(reinterpret_cast<char*>(destination),
                              static_cast<std::streamsize>(size)))
        throw std::runtime_error("short/unreadable input: " + path);
    if (input.peek() != std::char_traits<char>::eof())
        throw std::runtime_error("input grew while reading: " + path);
}

static void reverse_hex(std::ostream& output, const uint8_t* bytes, size_t size) {
    for (size_t i = size; i > 0; --i)
        output << std::hex << std::setfill('0') << std::setw(2)
               << static_cast<unsigned>(bytes[i - 1]);
    output << '\n';
}

static void write_rows(const std::string& path, const uint8_t* bytes,
                       size_t size, size_t row_bytes) {
    if (std::ifstream(path.c_str()).good())
        throw std::runtime_error("refusing to replace output: " + path);
    std::ofstream output(path.c_str(), std::ios::binary);
    if (!output) throw std::runtime_error("cannot create output: " + path);
    for (size_t offset = 0; offset < size; offset += row_bytes)
        reverse_hex(output, bytes + offset, row_bytes);
    output.close();
    if (!output) throw std::runtime_error("output write failed: " + path);
}

int main(int argc, char** argv) {
    if (argc != 4) {
        std::cerr << "usage: scratchpad-finalization-oracle SCRATCHPAD.bin REGISTER-FILE.bin OUTPUT_DIRECTORY\n";
        return 2;
    }
    try {
        const size_t size = input_size(argv[1]);
        if (size == 0 || size % 64 != 0 || size > randomx::ScratchpadSize)
            throw std::runtime_error("scratchpad length must be a positive multiple of64 up to the pinned ScratchpadSize");
        if (input_size(argv[2]) != sizeof(randomx::RegisterFile))
            throw std::runtime_error("RegisterFile input must be exactly256 bytes");

        // rx_load_vec_i128 may require16-byte alignment. Do not rely on the
        // alignment supplied by vector<uint8_t>'s allocator.
        std::vector<uint8_t> storage(size + 15);
        const uintptr_t aligned = (reinterpret_cast<uintptr_t>(storage.data()) + 15) & ~uintptr_t(15);
        uint8_t* const scratchpad = reinterpret_cast<uint8_t*>(aligned);
        read_exact(argv[1], scratchpad, size);
        std::array<uint8_t, 256> original;
        read_exact(argv[2], original.data(), original.size());
        alignas(64) randomx::RegisterFile registers;
        std::memcpy(&registers, original.data(), original.size());

        // Exactly VmBase::getFinalResult: replace only the raw A bank with
        // hashAes1Rx4, then unkeyed BLAKE2b over the native256-byte structure.
        // No AES constants, rounds, byte shuffles or alternate AES are copied here.
        hashAes1Rx4<true>(scratchpad, size, &registers.a);
        const uint8_t* const final_bytes = reinterpret_cast<const uint8_t*>(&registers);
        if (std::memcmp(final_bytes, original.data(), 192) != 0)
            throw std::runtime_error("native finalization changed R/F/E");
        std::array<uint8_t, 32> digest32;
        std::array<uint8_t, 64> digest64;
        if (blake2b(digest32.data(), digest32.size(), &registers, sizeof(registers), nullptr, 0) ||
            blake2b(digest64.data(), digest64.size(), &registers, sizeof(registers), nullptr, 0))
            throw std::runtime_error("native BLAKE2b failed");
        if (std::memcmp(digest32.data(), digest64.data(), digest32.size()) == 0)
            throw std::runtime_error("fixture must distinguish digest32 from truncated digest64");

        const std::string output(argv[3]);
        write_rows(output + "/scratchpad.hex", scratchpad, size, 16);
        write_rows(output + "/rf-in.hex", original.data(), original.size(), original.size());
        write_rows(output + "/aes-hash.hex", final_bytes + 192, 64, 64);
        write_rows(output + "/rf-final.hex", final_bytes, sizeof(registers), sizeof(registers));
        write_rows(output + "/digest32.hex", digest32.data(), digest32.size(), digest32.size());
        write_rows(output + "/digest64.hex", digest64.data(), digest64.size(), digest64.size());
        const std::string metadata_path = output + "/native-inputs.json";
        if (std::ifstream(metadata_path.c_str()).good())
            throw std::runtime_error("refusing to replace output: " + metadata_path);
        std::ofstream metadata(metadata_path.c_str());
        metadata << "{\n  \"scratchpad_bytes\": " << size
                 << ",\n  \"scratchpad_128bit_rows\": " << size / 16
                 << ",\n  \"aes_64byte_groups\": " << size / 64
                 << ",\n  \"register_file_bytes\": 256,\n"
                    "  \"a_bank_offset_bytes\": 192,\n"
                    "  \"r_f_e_preserved\": true,\n"
                    "  \"native_digest_bytes\": [32, 64],\n"
                    "  \"digest32_differs_from_truncated64\": true,\n"
                    "  \"hex_layout\": \"byte0 is bits7:0; each row prints highest byte first\",\n"
                    "  \"oracle\": \"unchanged pinned hashAes1Rx4<true> then native unkeyed blake2b\"\n}\n";
        metadata.close();
        if (!metadata) throw std::runtime_error("native metadata write failed");
        std::cout << "PASS native-finalization scratchpad_bytes=" << size
                  << " groups=" << size / 64
                  << " register_bytes=256 digest32=32 digest64=64 RFE_preserved=1\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
