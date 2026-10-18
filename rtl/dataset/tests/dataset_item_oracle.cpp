// SPDX-License-Identifier: BSD-3-Clause
// Final gold is the unmodified pinned initDatasetItem; instruction gold is
// unmodified executeSuperscalar. Cache images are actual initCache inputs.
#include "randomx.h"
#include "dataset.hpp"
#include "superscalar.hpp"
#include "blake2_generator.hpp"
#include "reciprocal.h"
#include "blake2/endian.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
using Registers = std::array<uint64_t, 8>;
using Programs = randomx::SuperscalarProgramList;
using Clock = std::chrono::steady_clock;
static constexpr uint64_t Mul = UINT64_C(6364136223846793005);
static constexpr uint64_t Adds[7] = {UINT64_C(9298411001130361340), UINT64_C(12065312585734608966),
    UINT64_C(9306329213124626780), UINT64_C(5281919268842080866), UINT64_C(10536153434571861004),
    UINT64_C(3398623926847679864), UINT64_C(9549104520008361294)};
static constexpr uint64_t Mask = randomx::CacheSize / randomx::CacheLineSize - 1;
static void require(bool value, const std::string& message) { if (!value) throw std::runtime_error(message); }
static double seconds(Clock::time_point start) { return std::chrono::duration<double>(Clock::now() - start).count(); }
template<class Function> static void write_file(const fs::path& path, Function fn) {
    std::ofstream out(path, std::ios::binary); require(bool(out), "open " + path.string());
    fn(out); out.close(); require(bool(out), "write " + path.string());
}
static void hex(std::ostream& out, uint64_t value, unsigned width = 16) {
    out << std::hex << std::setfill('0') << std::setw(width) << value;
}
static void regs(std::ostream& out, const Registers& value) { for (unsigned i = 8; i; --i) hex(out, value[i - 1]); }
static uint64_t word(const randomx::Instruction& i) {
    return uint64_t(i.opcode) | uint64_t(i.dst) << 8 | uint64_t(i.src) << 16 |
        uint64_t(i.mod) << 24 | uint64_t(i.getImm32()) << 32;
}
static std::string case_name(unsigned id) { std::ostringstream out; out << "case-" << std::setw(3) << std::setfill('0') << id; return out.str(); }
static std::string key_hex(const std::vector<uint8_t>& key) { std::ostringstream out; for (auto b : key) hex(out, b, 2); return out.str(); }
static Registers seed(uint64_t item) {
    Registers r{}; r[0] = (item + uint64_t(1)) * Mul;
    for (unsigned q = 1; q < 8; ++q) r[q] = r[0] ^ Adds[q - 1];
    return r;
}
static void execute(Registers& r, randomx::SuperscalarProgram& p, std::vector<uint64_t>& table) {
    uint64_t native[8]; std::copy(r.begin(), r.end(), native);
    randomx::executeSuperscalar(native, p, &table);
    std::copy(native, native + 8, r.begin());
}
struct Stage {
    uint32_t index = 0;
    Registers line{}, before{}, after{}, mixed{};
    uint64_t selected = 0;
    std::vector<Registers> steps;
};
struct Case {
    unsigned id = 0, cache = 0;
    uint64_t item = 0;
    bool generated = true;
    std::string kind;
    Programs programs{};
    uint32_t rcp_count = 0;
    Registers initial{}, final{};
    std::array<Stage, 8> stages{};
    uint64_t retired = 0, muls = 0;
};
static void counts_hex(std::ostream& out, const Programs& programs) {
    std::array<uint8_t, 10> bytes{};
    for (unsigned i = 0; i < 8; ++i) for (unsigned bit = 0; bit < 10; ++bit)
        if ((programs[i].size >> bit) & 1) bytes[(10 * i + bit) / 8] |= uint8_t(1u << ((10 * i + bit) % 8));
    for (unsigned i = 10; i; --i) hex(out, bytes[i - 1], 2);
}
static uint64_t address_pack(const Programs& programs) {
    uint64_t out = 0;
    for (unsigned i = 0; i < 8; ++i) { require(programs[i].addrReg >= 0 && programs[i].addrReg < 8, "address register"); out |= uint64_t(programs[i].addrReg) << (8 * i); }
    return out;
}
static Programs tiny_programs(unsigned variant, bool empty) {
    Programs programs{};
    for (unsigned i = 0; i < 8; ++i) {
        auto& p = programs[i]; p.setSize(empty ? 0 : 3); p.setAddressRegister(empty ? int(i) : int(7 - i));
        if (empty) continue;
        p(0) = {}; p(0).opcode = 3; p(0).dst = uint8_t(i); p(0).src = uint8_t((i + 1) % 8);
        p(1) = {}; p(1).opcode = 5; p(1).dst = uint8_t((i + 2) % 8); p(1).src = 255;
        p(1).setImm32(UINT32_C(0x80000001) + variant * 123 + i);
        p(2) = {}; p(2).opcode = 1; p(2).dst = uint8_t((i + 3) % 8); p(2).src = uint8_t((i + 4 + variant) % 8);
    }
    return programs;
}
static Programs maximum_programs() {
    Programs programs{};
    for (unsigned i = 0; i < 8; ++i) {
        programs[i].setSize(512); programs[i].setAddressRegister(int(i));
        for (unsigned pc = 0; pc < 512; ++pc) {
            auto& instruction = programs[i](pc); instruction = {}; instruction.opcode = 3;
            instruction.dst = uint8_t(i); instruction.src = uint8_t((i + 1) % 8);
        }
    }
    return programs;
}
static void verify_preparation(randomx_cache* cache, const std::vector<uint8_t>& key, const fs::path& output, unsigned id) {
    randomx::Blake2Generator generator(key.data(), key.size());
    Programs original{}, prepared{};
    std::vector<uint64_t> reciprocals;
    std::vector<uint32_t> divisors;
    for (unsigned i = 0; i < 8; ++i) {
        randomx::generateSuperscalar(original[i], generator); prepared[i] = original[i];
        for (unsigned pc = 0; pc < prepared[i].size; ++pc) {
            auto& instruction = prepared[i](pc);
            if (instruction.opcode == 13) {
                uint32_t divisor = instruction.getImm32(); divisors.push_back(divisor);
                instruction.setImm32(uint32_t(reciprocals.size())); reciprocals.push_back(randomx_reciprocal(divisor));
            }
        }
        require(prepared[i].size == cache->programs[i].size && prepared[i].addrReg == cache->programs[i].addrReg, "native prepared descriptor identity");
        for (unsigned pc = 0; pc < prepared[i].size; ++pc)
            require(word(prepared[i](pc)) == word(cache->programs[i](pc)), "native prepared instruction identity");
    }
    require(reciprocals == cache->reciprocalCache, "native global reciprocal table identity");
    write_file(output / ("cache-" + std::to_string(id) + "-reciprocals.mem"), [&](std::ostream& out) {
        for (uint64_t r : cache->reciprocalCache) { hex(out, r); out << '\n'; }
    });
    write_file(output / ("cache-" + std::to_string(id) + "-reciprocal-metadata.json"), [&](std::ostream& out) {
        out << "{\"global_indices\":true,\"deduplicated\":false,\"entries\":[";
        for (size_t i = 0; i < reciprocals.size(); ++i) { if (i) out << ','; out << "{\"index\":" << std::dec << i << ",\"divisor\":" << divisors[i] << ",\"value_hex\":\""; hex(out, reciprocals[i]); out << "\"}"; }
        out << "]}\n";
    });
    for (bool raw : {false, true}) write_file(output / ("cache-" + std::to_string(id) + (raw ? "-original-programs.mem" : "-prepared-programs.mem")), [&](std::ostream& out) {
        const Programs& list = raw ? original : cache->programs;
        for (unsigned i = 0; i < 8; ++i) for (unsigned pc = 0; pc < 512; ++pc) { hex(out, pc < list[i].size ? word(list[i].programBuffer[pc]) : 0); out << '\n'; }
    });
}
static Case make_case(unsigned id, unsigned cache_id, uint64_t item, randomx_cache* actual, const Programs& programs, bool generated, const std::string& kind) {
    Case result; result.id = id; result.cache = cache_id; result.item = item; result.programs = programs;
    result.generated = generated; result.kind = kind; result.rcp_count = uint32_t(actual->reciprocalCache.size()); result.initial = seed(item);
    // This prepared context changes only explicitly synthetic program inputs;
    // its memory and complete reciprocal vector are actual native cache inputs.
    randomx_cache context{}; context.memory = actual->memory; context.programs = programs; context.reciprocalCache = actual->reciprocalCache;
    randomx::initDatasetItem(&context, reinterpret_cast<uint8_t*>(result.final.data()), item);
    Registers r = result.initial; uint64_t register_value = item;
    for (unsigned i = 0; i < 8; ++i) {
        Stage& stage = result.stages[i]; stage.before = r; stage.index = uint32_t(register_value & Mask);
        const uint8_t* block = context.memory + uint64_t(stage.index) * 64;
        for (unsigned q = 0; q < 8; ++q) stage.line[q] = load64_native(block + q * 8);
        Registers stepped = r;
        auto& program = context.programs[i];
        require(program.size <= 512 && program.addrReg >= 0 && program.addrReg < 8, "descriptor bounds");
        for (unsigned pc = 0; pc < program.size; ++pc) {
            randomx::SuperscalarProgram singleton{}; singleton.setSize(1); singleton(0) = program(pc);
            execute(stepped, singleton, context.reciprocalCache); stage.steps.push_back(stepped);
            ++result.retired; const unsigned op = program(pc).opcode; result.muls += op == 3 || op == 11 || op == 12 || op == 13;
        }
        execute(r, program, context.reciprocalCache); require(r == stepped, "native singleton/full stage disagreement"); stage.after = r;
        for (unsigned q = 0; q < 8; ++q) r[q] ^= stage.line[q];
        stage.mixed = r; stage.selected = register_value = r[program.addrReg];
    }
    require(r == result.final, "traced/full initDatasetItem disagreement");
    return result;
}
static void export_case(const fs::path& output, const Case& item, const std::vector<uint64_t>& table) {
    fs::path directory = output / case_name(item.id); require(fs::create_directory(directory), "fresh case directory");
    write_file(directory / "seed.hex", [&](std::ostream& out) { regs(out, item.initial); out << '\n'; });
    write_file(directory / "final.hex", [&](std::ostream& out) { regs(out, item.final); out << '\n'; });
    write_file(directory / "stages.mem", [&](std::ostream& out) {
        for (const Stage& stage : item.stages) { hex(out, stage.index, 6); out << ' '; regs(out, stage.line); out << ' '; regs(out, stage.before); out << ' '; regs(out, stage.after); out << ' '; regs(out, stage.mixed); out << ' '; hex(out, stage.selected); out << '\n'; }
    });
    for (unsigned i = 0; i < 8; ++i) for (unsigned field = 0; field < 5; ++field) {
        std::string name = field == 0 ? "program-" : field == 1 ? "steps-" : field == 2 ? "rcp-valid-" : field == 3 ? "rcp-index-" : "reciprocals-";
        write_file(directory / (name + std::to_string(i) + ".mem"), [&](std::ostream& out) {
            for (unsigned pc = 0; pc < 512; ++pc) {
                bool valid = pc < item.programs[i].size; const auto& instruction = item.programs[i].programBuffer[pc];
                bool reciprocal = valid && instruction.opcode == 13; uint32_t index = reciprocal ? instruction.getImm32() : 0;
                require(!reciprocal || index < table.size(), "reciprocal index");
                if (field == 0) hex(out, valid ? word(instruction) : 0);
                else if (field == 1) { if (valid) regs(out, item.stages[i].steps[pc]); else regs(out, Registers{}); }
                else if (field == 2) out << (reciprocal ? '1' : '0');
                else if (field == 3) hex(out, index, 8);
                else hex(out, reciprocal ? table[index] : 0);
                out << '\n';
            }
        });
    }
    write_file(directory / "metadata.json", [&](std::ostream& out) {
        out << "{\"case_id\":" << item.id << ",\"cache_id\":" << item.cache << ",\"item_hex\":\""; hex(out, item.item);
        out << "\",\"kind\":\"" << item.kind << "\",\"native_generated_programs\":" << (item.generated ? "true" : "false")
            << ",\"retired\":" << std::dec << item.retired << ",\"muls\":" << item.muls << ",\"full_native_final_agrees\":true,\"singleton_full_stage_agrees\":true}\n";
    });
}
int main(int argc, char** argv) {
    try {
        require(argc == 2 && fs::is_directory(argv[1]), "usage: dataset_item_oracle FRESH_EXISTING_OUTPUT_DIRECTORY"); const fs::path output(argv[1]);
        require(fs::is_empty(output), "fixture output must be empty");
        static_assert(RANDOMX_CACHE_ACCESSES == 8 && randomx::CacheSize == 268435456 && randomx::CacheLineSize == 64 && randomx::SuperscalarMaxSize == 512, "pinned configuration changed");
        uint64_t endian = 1; require(*reinterpret_cast<uint8_t*>(&endian) == 1, "native helper export requires little-endian host");
        std::array<std::vector<uint8_t>, 2> keys{}; std::string canonical = "test key 000"; keys[0].assign(canonical.begin(), canonical.end()); for (unsigned i = 0; i < 32; ++i) keys[1].push_back(uint8_t(i));
        const uint64_t items[2][8] = {{0, 10000000, 20000000, 30000000, UINT64_C(0x3fffff), UINT64_C(0x400000), UINT64_C(0x207fffe), UINT64_MAX},
            {0, 1, 2, UINT64_C(0x400001), UINT64_C(0xffffffff), UINT64_C(0x100000000), UINT64_MAX - 1, UINT64_C(0x8000000000000000)}};
        const uint64_t anchors[4] = {UINT64_C(0x680588a85ae222db), UINT64_C(0x7943a1f6186ffb72), UINT64_C(0x9035244d718095e1), UINT64_C(0x145a5091f7853099)};
        std::vector<Case> cases; std::array<double, 2> init_seconds{}, export_seconds{};
        uint64_t post_xor_address_differences = 0, total_steps = 0;
        for (unsigned id = 0; id < 2; ++id) {
            auto start = Clock::now(); std::unique_ptr<randomx_cache, decltype(&randomx_release_cache)> cache(randomx_alloc_cache(RANDOMX_FLAG_DEFAULT), randomx_release_cache);
            require(bool(cache), "native256MiB cache allocation failed"); randomx_init_cache(cache.get(), keys[id].data(), keys[id].size()); init_seconds[id] = seconds(start);
            start = Clock::now(); write_file(output / ("cache-" + std::to_string(id) + ".bin"), [&](std::ostream& out) { out.write(reinterpret_cast<char*>(cache->memory), randomx::CacheSize); }); export_seconds[id] = seconds(start);
            verify_preparation(cache.get(), keys[id], output, id);
            for (unsigned n = 0; n < 8; ++n) {
                auto item = make_case(id * 8 + n, id, items[id][n], cache.get(), cache->programs, true, "actual-initCache-generated-programs");
                if (id == 0 && n < 4) require(item.final[0] == anchors[n], "upstream canonical first-word anchor");
                export_case(output, item, cache->reciprocalCache); cases.push_back(std::move(item));
            }
            auto control = make_case(16 + id, id, id ? UINT64_MAX - 1 : 1, cache.get(), tiny_programs(id, false), false, "crafted-tiny-eight-program-context");
            export_case(output, control, cache->reciprocalCache); cases.push_back(std::move(control));
            if (id == 0) { auto empty = make_case(18, id, 0, cache.get(), tiny_programs(0, true), false, "crafted-empty-eight-program-context"); export_case(output, empty, cache->reciprocalCache); cases.push_back(std::move(empty)); }
            if (id == 1) { auto maximum = make_case(19, id, 2, cache.get(), maximum_programs(), false, "crafted-eight-by512-aggregate-width-context"); require(maximum.retired == 4096 && maximum.muls == 4096, "aggregate counter width fixture"); export_case(output, maximum, cache->reciprocalCache); cases.push_back(std::move(maximum)); }
            write_file(output / ("cache-" + std::to_string(id) + "-metadata.json"), [&](std::ostream& out) {
                out << "{\"cache_id\":" << id << ",\"key_hex\":\"" << key_hex(keys[id]) << "\",\"key_bytes\":" << keys[id].size() << ",\"cache_bytes\":268435456,\"cache_lines\":4194304,\"native_flags\":0,\"argon_initializations\":1,\"reciprocal_count\":" << cache->reciprocalCache.size() << ",\"prepared_programs\":8,\"prepared_replay_identity_checked\":true}\n";
            });
        }
        std::sort(cases.begin(), cases.end(), [](const Case& a, const Case& b) { return a.id < b.id; }); require(cases.size() == 20, "case inventory");
        for (const Case& item : cases) for (unsigned i = 0; i < 8; ++i) { total_steps += item.stages[i].steps.size(); post_xor_address_differences += (item.stages[i].after[item.programs[i].addrReg] & Mask) != (item.stages[i].selected & Mask); }
        require(post_xor_address_differences > 0, "post-XOR address difference coverage absent");
        for (std::string selection : {"cases.hex", "cases-real.hex", "cases-control.hex", "cases-empty.hex", "cases-mapped.hex"}) write_file(output / selection, [&](std::ostream& out) {
            for (const Case& item : cases) {
                bool chosen = selection == "cases.hex" || (selection == "cases-real.hex" && item.id < 16) || (selection == "cases-control.hex" && (item.id == 16 || item.id == 17)) || (selection == "cases-empty.hex" && item.id == 18) || (selection == "cases-mapped.hex" && (item.id == 0 || item.id == 8 || (item.id >= 16 && item.id <= 18)));
                if (!chosen) continue;
                out << std::dec << item.id << ' ' << item.cache << ' '; hex(out, item.item); out << ' '; hex(out, item.rcp_count, 8); out << ' '; counts_hex(out, item.programs); out << ' '; hex(out, address_pack(item.programs)); out << ' '; regs(out, item.final); out << '\n';
            }
        });
        write_file(output / "native-summary.json", [&](std::ostream& out) {
            out << "{\"status\":\"pass\",\"pin\":\"aaafe71322df6602c21a5c72937ac284724ae561\",\"tag\":\"v2.0.1\",\"oracle\":\"unchanged initDatasetItem final and executeSuperscalar instruction states\",\"item_bits\":64,\"native_generated_cases\":16,\"crafted_control_cases\":2,\"crafted_empty_cases\":1,\"crafted_maximum_cases\":1,\"cases\":20,\"mapped_cases\":5,\"cache_images\":2,\"cache_image_bytes\":268435456,\"argon_initializations\":2,\"dataset_allocation_bytes\":0,\"full_native_item_calls\":20,\"stages\":160,\"max_aggregate_retired\":4096,\"max_aggregate_muls\":4096,\"post_instruction_states\":" << total_steps << ",\"post_xor_address_differences\":" << post_xor_address_differences << ",\"upstream_first_word_anchors\":4,\"little_endian\":true,\"full_native_final_agrees\":true,\"singleton_full_stage_agrees\":true}\n";
        });
        const fs::path timing = output.parent_path() / "native-cache-host-timing.json";
        require(!fs::exists(timing), "fresh host timing artifact required");
        write_file(timing, [&](std::ostream& out) {
            out << "{\"scope\":\"Measured host cache preparation/export wall time; outside deterministic fixtures and hardware clock accounting\",\"cache_initialization_host_seconds\":[" << init_seconds[0] << ',' << init_seconds[1] << "],\"cache_export_host_seconds\":[" << export_seconds[0] << ',' << export_seconds[1] << "]}\n";
        });
        std::cout << "PASS native_dataset_item cases=20 real=16 crafted=4 stages=160 instruction_states=" << total_steps << " cache_images=2 argon_initializations=2 dataset_allocation=0\n";
        return 0;
    } catch (const std::exception& error) { std::cerr << "FAIL native_dataset_item: " << error.what() << '\n'; return 1; }
}
