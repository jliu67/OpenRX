// SPDX-License-Identifier: BSD-3-Clause
// Retained PR80 cache0 context for NEW bounded lifecycle validation only.
// The driver must receipt-bind the actual fixture bytes before execution.
// This loader checks their representation; it does not replace SHA provenance.
#pragma once
#include "lifecycle_native.hpp"
#include "reciprocal.h"
#include <algorithm>
#include <array>
#include <cstdlib>
#include <filesystem>
#include <limits>
#include <regex>
#include <sstream>

namespace prepared_lifecycle_native {
using lifecycle_native::Clock;
using lifecycle_native::seconds;
using lifecycle_native::input_hash;
using lifecycle_native::initial;
using lifecycle_native::unhex;
inline constexpr char cache_key[] = "test key 000";
inline constexpr char cache_key_hex[] = "74657374206b657920303030";
// Enabled only by the separate reference translation unit, before its original
// main runs. VPI/DPI providers leave this false and never export oracle inputs.
inline bool reference_role = false;
namespace fs = std::filesystem;
inline void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error("prepared cache: " + message);
}
inline std::string text(const fs::path& path) {
    require(fs::is_regular_file(path) && !fs::is_symlink(path), "regular input " + path.string());
    std::ifstream in(path, std::ios::binary);
    require(bool(in), "open " + path.string());
    std::ostringstream out; out << in.rdbuf();
    require(!in.bad(), "read " + path.string());
    return out.str();
}
inline uint64_t number(const std::string& token, unsigned base, size_t digits = 0) {
    require(!token.empty() && (!digits || token.size() == digits), "numeric width");
    require(std::regex_match(token, std::regex(base == 16 ? "[0-9a-fA-F]+" : "[0-9]+")), "numeric syntax");
    size_t used = 0; uint64_t value = std::stoull(token, &used, base);
    require(used == token.size(), "numeric suffix"); return value;
}
inline uint64_t json_number(const std::string& value, const char* key) {
    std::regex pattern(std::string("\"") + key + "\"\\s*:\\s*([0-9]+)\\s*[,}]");
    std::sregex_iterator it(value.begin(), value.end(), pattern), end;
    require(it != end, std::string("missing JSON number ") + key);
    uint64_t result = number((*it)[1], 10); ++it;
    require(it == end, std::string("duplicate JSON number ") + key); return result;
}
inline std::string json_string(const std::string& value, const char* key) {
    std::regex pattern(std::string("\"") + key + "\"\\s*:\\s*\"([^\"]*)\"");
    std::sregex_iterator it(value.begin(), value.end(), pattern), end;
    require(it != end, std::string("missing JSON string ") + key);
    std::string result = (*it)[1]; ++it;
    require(it == end, std::string("duplicate JSON string ") + key); return result;
}
inline void json_true(const std::string& value, const char* key) {
    std::regex pattern(std::string("\"") + key + "\"\\s*:\\s*true\\s*[,}]");
    require(std::regex_search(value, pattern), std::string("JSON true ") + key);
}
inline std::vector<uint64_t> words(const fs::path& path, size_t expected) {
    std::istringstream in(text(path)); std::vector<uint64_t> result; std::string line;
    while (std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        result.push_back(number(line, 16, 16));
    }
    require(result.size() == expected, "word count " + path.string()); return result;
}
inline uint64_t packed_bits(const std::string& value, unsigned low, unsigned count) {
    require(value.size() == 20 && count <= 64 && low + count <= 80, "packed descriptor bounds");
    number(value.substr(0, 4), 16, 4); number(value.substr(4), 16, 16);
    uint64_t result = 0;
    for (unsigned bit = 0; bit < count; ++bit) {
        unsigned position = low + bit;
        unsigned nibble = unsigned(number(value.substr(19 - position / 4, 1), 16, 1));
        result |= uint64_t((nibble >> (position % 4)) & 1u) << bit;
    }
    return result;
}
inline std::string quote(const std::string& value) {
    std::ostringstream out; out << '"';
    for (unsigned char c : value) {
        if (c == '"' || c == '\\') out << '\\' << c;
        else if (c < 32) out << "\\u00" << std::hex << std::setw(2) << std::setfill('0') << unsigned(c);
        else out << c;
    }
    out << '"'; return out.str();
}
struct ProviderCounters {
    double initial_seconds = 0, input_hash_seconds = 0, generation_seconds = 0;
    double assertion_seconds = 0, assertion_generation_seconds = 0, assertion_input_hash_seconds = 0;
    unsigned generations = 0, input_hash_calls = 0, software_fill_calls = 0;
    unsigned assertion_generations = 0, assertion_input_hash_calls = 0;
};
struct Dataset {
    randomx_cache* cache = nullptr;
    std::unique_ptr<randomx_cache, decltype(&randomx_release_cache)> owned_cache{nullptr, randomx_release_cache};
    // Compatibility with unchanged provider bodies: no native cache init occurs.
    double initialization_seconds = 0, item_seconds = 0, assertion_item_seconds = 0;
    double asset_load_seconds = 0, gold_export_seconds = 0;
    uint64_t item_requests = 0, assertion_item_requests = 0, gold_export_rows = 0;
    fs::path root;
    fs::path reference_output;
    std::ofstream gold;
    Dataset() {
        static_assert(RANDOMX_CACHE_ACCESSES == 8 && randomx::CacheSize == 268435456 &&
                      randomx::CacheLineSize == 64 && randomx::SuperscalarMaxSize == 512,
                      "pinned dataset configuration");
        uint64_t endian = 1;
        require(*reinterpret_cast<uint8_t*>(&endian) == 1, "native retained image requires little-endian host");
        const char* value = std::getenv("RX_PREPARED_CACHE_ROOT");
        require(value && *value, "RX_PREPARED_CACHE_ROOT is mandatory"); root = fs::path(value);
        require(fs::is_directory(root) && !fs::is_symlink(root), "fixture root directory");
        auto started = Clock::now();
        std::string metadata = text(root / "cache-0-metadata.json");
        require(json_number(metadata, "cache_id") == 0 && json_string(metadata, "key_hex") == cache_key_hex &&
                json_number(metadata, "key_bytes") == sizeof(cache_key) - 1, "cache0 key identity");
        require(json_number(metadata, "cache_bytes") == randomx::CacheSize &&
                json_number(metadata, "cache_lines") == 4194304 && json_number(metadata, "native_flags") == 0 &&
                json_number(metadata, "argon_initializations") == 1 && json_number(metadata, "prepared_programs") == 8,
                "retained cache metadata");
        json_true(metadata, "prepared_replay_identity_checked");
        uint64_t table_count = json_number(metadata, "reciprocal_count");
        require(table_count == 239, "accepted cache0 global reciprocal count");
        auto table = words(root / "cache-0-reciprocals.mem", size_t(table_count));
        auto prepared = words(root / "cache-0-prepared-programs.mem", 4096);
        auto original = words(root / "cache-0-original-programs.mem", 4096);
        std::array<unsigned, 8> counts{}, addresses{}; bool descriptors = false;
        std::array<bool, 16> seen{};
        std::istringstream cases(text(root / "cases-real.hex")); std::string line;
        while (std::getline(cases, line)) {
            std::istringstream row(line); std::string id_s, cache_s, item_s, rcp_s, counts_s, addresses_s, final_s, extra;
            require(bool(row >> id_s >> cache_s >> item_s >> rcp_s >> counts_s >> addresses_s >> final_s) && !(row >> extra), "real case row");
            uint64_t id = number(id_s, 10), cache_id = number(cache_s, 10);
            require(id < 16 && !seen[size_t(id)] && cache_id == (id < 8 ? 0u : 1u), "real case inventory"); seen[size_t(id)] = true;
            number(item_s, 16, 16); require(final_s.size() == 128 && std::regex_match(final_s, std::regex("[0-9a-fA-F]+")), "real final representation");
            uint64_t rcp = number(rcp_s, 16, 8), packed_addresses = number(addresses_s, 16, 16);
            if (cache_id != 0) continue;
            require(rcp == table_count, "real reciprocal descriptor");
            for (unsigned stage = 0; stage < 8; ++stage) {
                unsigned count = unsigned(packed_bits(counts_s, stage * 10, 10));
                unsigned address = unsigned((packed_addresses >> (8 * stage)) & 255);
                require(count > 0 && count <= 512 && address < 8, "native descriptor bounds");
                if (descriptors) require(count == counts[stage] && address == addresses[stage], "native context descriptor changed between items");
                else { counts[stage] = count; addresses[stage] = address; }
            }
            descriptors = true;
        }
        require(descriptors && std::all_of(seen.begin(), seen.end(), [](bool b) { return b; }), "complete real case list");
        randomx::SuperscalarProgramList programs{}; size_t reciprocal_index = 0;
        std::vector<uint32_t> divisors;
        for (unsigned stage = 0; stage < 8; ++stage) {
            auto& p = programs[stage]; p.setSize(counts[stage]); p.setAddressRegister(int(addresses[stage]));
            for (unsigned pc = 0; pc < 512; ++pc) {
                uint64_t raw = prepared[stage * 512 + pc], source = original[stage * 512 + pc];
                if (pc >= counts[stage]) { require(raw == 0 && source == 0, "unused program padding"); continue; }
                unsigned op = unsigned(raw & 255), dst = unsigned(raw >> 8 & 255), src = unsigned(raw >> 16 & 255);
                uint32_t imm = uint32_t(raw >> 32);
                bool register_source = op <= 3 || op == 11 || op == 12;
                require(op < 14 && dst < 8 && (!register_source || src < 8) && (op != 4 || imm <= 63), "prepared instruction representation");
                if (op == 13) {
                    require(imm == reciprocal_index && imm < table.size() && uint32_t(raw) == uint32_t(source), "global reciprocal index/order");
                    uint32_t divisor = uint32_t(source >> 32);
                    require(divisor && (divisor & (divisor - 1)) && randomx_reciprocal(divisor) == table[imm], "original divisor/reciprocal identity");
                    divisors.push_back(divisor);
                    ++reciprocal_index;
                } else require(raw == source, "nonreciprocal prepared identity");
                auto& instruction = p(int(pc)); instruction = {};
                instruction.opcode = uint8_t(op); instruction.dst = uint8_t(dst); instruction.src = uint8_t(src);
                instruction.mod = uint8_t(raw >> 24); instruction.setImm32(imm);
            }
        }
        require(reciprocal_index == table.size(), "complete global reciprocal table consumed");
        std::string rcp_metadata = text(root / "cache-0-reciprocal-metadata.json");
        json_true(rcp_metadata, "global_indices");
        require(std::regex_search(rcp_metadata, std::regex("\"deduplicated\"\\s*:\\s*false")), "non-deduplicated table metadata");
        std::regex entry("\\{\\s*\"index\"\\s*:\\s*([0-9]+)\\s*,\\s*\"divisor\"\\s*:\\s*([0-9]+)\\s*,\\s*\"value_hex\"\\s*:\\s*\"([0-9a-fA-F]{16})\"\\s*\\}");
        size_t entries = 0;
        for (std::sregex_iterator it(rcp_metadata.begin(), rcp_metadata.end(), entry), end; it != end; ++it) {
            require(number((*it)[1], 10) == entries && entries < table.size() && number((*it)[3], 16, 16) == table[entries], "full reciprocal metadata");
            require(number((*it)[2], 10) == divisors[entries], "reciprocal metadata original divisor");
            ++entries;
        }
        require(entries == table.size(), "reciprocal metadata entry count");
        fs::path image = root / "cache-0.bin";
        require(fs::is_regular_file(image) && !fs::is_symlink(image) && fs::file_size(image) == randomx::CacheSize, "actual cache image size/type");
        std::unique_ptr<randomx_cache, decltype(&randomx_release_cache)> loaded(randomx_alloc_cache(RANDOMX_FLAG_DEFAULT), randomx_release_cache);
        require(bool(loaded), "256MiB retained cache allocation");
        std::ifstream memory(image, std::ios::binary);
        require(bool(memory.read(reinterpret_cast<char*>(loaded->memory), randomx::CacheSize)) &&
                memory.gcount() == std::streamsize(randomx::CacheSize) && memory.peek() == std::char_traits<char>::eof(), "exact cache image read");
        loaded->programs = programs; loaded->reciprocalCache = std::move(table); loaded->cacheKey = cache_key;
        require(loaded->isInitialized(), "native prepared context readiness");
        owned_cache = std::move(loaded); cache = owned_cache.get(); asset_load_seconds = seconds(started);
        if (reference_role) {
            const char* destination = std::getenv("RX_PREPARED_REFERENCE_OUTPUT");
            require(destination && *destination, "RX_PREPARED_REFERENCE_OUTPUT is mandatory for reference");
            reference_output = fs::path(destination);
            require(fs::is_directory(reference_output) && !fs::is_symlink(reference_output), "fresh reference output directory");
            enable_gold_export(reference_output / "dataset-items.hex");
        }
    }
    ~Dataset() = default;
    Dataset(const Dataset&) = delete;
    Dataset& operator=(const Dataset&) = delete;
    void enable_gold_export(const fs::path& path) {
        require(!gold.is_open() && !fs::exists(path), "fresh native dataset gold export");
        gold.open(path, std::ios::binary); require(bool(gold), "gold export open");
    }
    void close_gold_export() {
        if (gold.is_open()) { gold.close(); require(bool(gold), "gold export close"); }
    }
    void calculate(uint64_t address, void* output, bool assertion_only) {
        require(!(address & 63) && address <= randomx::DatasetSize - 64, "dataset byte address/alignment");
        if (reference_role) require(!assertion_only && item_requests < 2, "reference bounded to two native item calls");
        auto started = Clock::now();
        randomx::initDatasetItem(cache, static_cast<uint8_t*>(output), address / 64);
        double elapsed = seconds(started);
        if (assertion_only) { assertion_item_seconds += elapsed; ++assertion_item_requests; }
        else { item_seconds += elapsed; ++item_requests; }
        if (gold.is_open()) {
            started = Clock::now(); gold << std::hex << std::setw(16) << std::setfill('0') << address << ' ';
            sequence_fixture::hex(gold, output, 64); gold << '\n'; require(bool(gold), "native gold row write");
            gold.flush(); require(bool(gold), "native gold row flush");
            gold_export_seconds += seconds(started); ++gold_export_rows;
            statistics((reference_output / "dataset-native-host-time.json").string(), {}, "native-reference");
        }
    }
    void read(uint64_t address, void* output) { calculate(address, output, false); }
    void read_assertion(uint64_t address, void* output) { calculate(address, output, true); }
    void statistics(const std::string& filename, const ProviderCounters& p, const char* role) const {
        std::ofstream out(filename); require(bool(out), "statistics open"); out << std::setprecision(17)
          << "{\"provider\":\"pinned initDatasetItem on retained PR80 prepared cache0; no Argon/cache export\",\"role\":" << quote(role)
          << ",\"cache_key\":" << quote(cache_key) << ",\"cache_key_hex\":" << quote(cache_key_hex)
          << ",\"prepared_fixture_root\":" << quote(root.string())
          << ",\"provider_callback_counter_scope\":\"Input/fill/program/hash counters describe explicit provider or assertion callbacks only; direct unchanged reference initial/fill/program/interprogram/finalization work is outside those counters and is not timed by this file\""
          << ",\"native_item_counter_scope\":\"dataset_requests counts direct reference items when role=native-reference, otherwise live software provider calls; assertion_only_dataset_requests is separate\""
          << ",\"asset_identity_requires_external_receipt_binding\":true,\"cache_bytes\":268435456,\"logical_dataset_bytes\":2181038016,\"materialized_dataset_bytes\":0"
          << ",\"retained_cache_images_loaded\":1,\"retained_cache_bytes_loaded\":268435456,\"prepared_programs_loaded\":8,\"global_reciprocal_entries\":239"
          << ",\"argon_initializations\":0,\"cache_image_export_bytes\":0,\"native_cache_program_generations\":0,\"cache_initialization_host_seconds\":0"
          << ",\"asset_load_host_seconds\":" << asset_load_seconds << ",\"native_dataset_gold_export_host_seconds\":" << gold_export_seconds
          << ",\"native_dataset_gold_export_rows\":" << gold_export_rows
          << ",\"initialization_host_seconds\":" << p.initial_seconds << ",\"input_hash_host_seconds\":" << p.input_hash_seconds
          << ",\"input_hash_calls\":" << p.input_hash_calls << ",\"software_fill_provider_calls\":" << p.software_fill_calls
          << ",\"program_generation_host_seconds\":" << p.generation_seconds << ",\"program_generations\":" << p.generations
          << ",\"assertion_only_program_generation_host_seconds\":" << p.assertion_generation_seconds
          << ",\"assertion_only_program_generations\":" << p.assertion_generations
          << ",\"assertion_only_input_hash_host_seconds\":" << p.assertion_input_hash_seconds
          << ",\"assertion_only_input_hash_calls\":" << p.assertion_input_hash_calls
          << ",\"dataset_provider_host_seconds\":" << item_seconds << ",\"dataset_requests\":" << item_requests
          << ",\"assertion_only_dataset_host_seconds\":" << assertion_item_seconds << ",\"assertion_only_dataset_requests\":" << assertion_item_requests
          << ",\"assertion_only_hash_host_seconds\":" << p.assertion_seconds
          << ",\"provider_device_cycles\":null,\"provider_internal_physical_traffic_bytes\":null}\n";
        out.close(); require(bool(out), "statistics write");
    }
};
inline Dataset& dataset() { static Dataset value; return value; }
} // namespace prepared_lifecycle_native
