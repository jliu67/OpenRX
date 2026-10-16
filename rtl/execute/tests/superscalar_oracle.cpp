// SPDX-License-Identifier: BSD-3-Clause
// Arithmetic gold is the unchanged pinned RandomX executeSuperscalar function.
#include <cstddef>
#include "superscalar.hpp"
#include "reciprocal.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <initializer_list>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using randomx::Instruction;
using randomx::SuperscalarInstructionType;
using randomx::SuperscalarProgram;
using Registers = std::array<uint64_t, 8>;
namespace fs = std::filesystem;

static constexpr unsigned TypeCount = 14;
static constexpr unsigned ProgramsPerSeed = 8;
static constexpr const char* Pin = "aaafe71322df6602c21a5c72937ac284724ae561";
static constexpr const char* Names[TypeCount] = {
    "ISUB_R", "IXOR_R", "IADD_RS", "IMUL_R", "IROR_C", "IADD_C7", "IXOR_C7",
    "IADD_C8", "IXOR_C8", "IADD_C9", "IXOR_C9", "IMULH_R", "ISMULH_R", "IMUL_RCP"
};

static void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

template<class Function>
static void write_file(const fs::path& path, Function write) {
    std::ofstream out(path);
    require(bool(out), "output open: " + path.string());
    write(out);
    out.close();
    require(bool(out), "output write: " + path.string());
}

static std::string quoted(const std::string& value) {
    std::ostringstream out;
    out << '"';
    for (unsigned char c : value) {
        if (c == '"' || c == '\\') out << '\\' << char(c);
        else if (c < 32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << unsigned(c);
        else out << char(c);
    }
    out << '"';
    return out.str();
}

static void hex64(std::ostream& out, uint64_t value) {
    out << std::hex << std::setw(16) << std::setfill('0') << value;
}

static void hex32(std::ostream& out, uint32_t value) {
    out << std::hex << std::setw(8) << std::setfill('0') << value;
}

// readmemh words place r0 in bits 63:0 and r7 in bits 511:448.
static void registers_hex(std::ostream& out, const Registers& registers) {
    for (unsigned i = 8; i; --i) hex64(out, registers[i - 1]);
}

static std::string registers_string(const Registers& registers) {
    std::ostringstream out;
    registers_hex(out, registers);
    return out.str();
}

// Instruction byte order is opcode,dst,src,mod, followed by little-endian imm32.
static uint64_t instruction_word(const Instruction& instruction) {
    return uint64_t(instruction.opcode) | (uint64_t(instruction.dst) << 8)
        | (uint64_t(instruction.src) << 16) | (uint64_t(instruction.mod) << 24)
        | (uint64_t(instruction.getImm32()) << 32);
}

static bool source_used(unsigned opcode) {
    return opcode <= 3 || opcode == 11 || opcode == 12;
}

static bool reciprocal_op(const Instruction& instruction) {
    return instruction.opcode == unsigned(SuperscalarInstructionType::IMUL_RCP);
}

static bool valid_divisor(uint32_t value) {
    return value != 0 && (value & (value - 1)) != 0;
}

struct Table {
    unsigned id = 0;
    std::string seed;
    std::string kind = "exact-initCache-program-reciprocals";
    bool generated = true;
    std::array<SuperscalarProgram, ProgramsPerSeed> original{};
    std::array<SuperscalarProgram, ProgramsPerSeed> prepared{};
    std::array<size_t, ProgramsPerSeed> begins{}, ends{};
    std::vector<uint32_t> divisors;
    std::vector<uint64_t> reciprocals;
};

static void prepare_table(Table& table) {
    // This is the program/reciprocal part of initCache, with no cache or Argon.
    randomx::Blake2Generator generator(table.seed.data(), table.seed.size());
    for (unsigned program = 0; program < ProgramsPerSeed; ++program) {
        randomx::generateSuperscalar(table.original[program], generator);
        require(table.original[program].getSize() > 0
            && table.original[program].getSize() <= randomx::SuperscalarMaxSize, "generated program size");
        table.prepared[program] = table.original[program];
        table.begins[program] = table.reciprocals.size();
        for (unsigned pc = 0; pc < table.prepared[program].getSize(); ++pc) {
            Instruction& instruction = table.prepared[program](pc);
            if (reciprocal_op(instruction)) {
                const uint32_t divisor = instruction.getImm32();
                require(valid_divisor(divisor), "generated reciprocal divisor");
                require(table.reciprocals.size() <= UINT32_MAX, "reciprocal index width");
                const uint64_t reciprocal = randomx_reciprocal(divisor);
                instruction.setImm32(uint32_t(table.reciprocals.size()));
                table.divisors.push_back(divisor);
                table.reciprocals.push_back(reciprocal);
            }
        }
        table.ends[program] = table.reciprocals.size();
    }
    require(table.reciprocals.size() >= 5 && table.divisors.size() == table.reciprocals.size(),
        "generated reciprocal table coverage");
}

static void prepare_width_table(Table& table) {
    table.id = 2;
    table.generated = false;
    table.kind = "handbuilt-padded-native-reciprocal-index-width-context";
    // Distinct from initCache tables: every odd divisor 2*index+3 is valid.
    // In particular 512/513 do not alias 0/1, and 65537 does not alias 1.
    table.divisors.reserve(65538);
    table.reciprocals.reserve(65538);
    for (uint32_t index = 0; index < 65538; ++index) {
        const uint32_t divisor = index * 2 + 3;
        require(valid_divisor(divisor), "width-context reciprocal divisor");
        table.divisors.push_back(divisor);
        table.reciprocals.push_back(randomx_reciprocal(divisor));
    }
    require(table.reciprocals[512] != table.reciprocals[0]
        && table.reciprocals[513] != table.reciprocals[1]
        && table.reciprocals[65537] != table.reciprocals[1], "index truncation must be observable");
}

struct Case {
    unsigned id = 0, table = 0, address_register = 0;
    std::string label, kind;
    int generated_program = -1;
    bool mapped = false, control = false;
    SuperscalarProgram original{}, prepared{};
    Registers initial{}, final{};
    std::vector<Registers> steps;
    std::array<uint64_t, TypeCount> opcounts{};
};

static Registers initial_registers(unsigned id) {
    const uint64_t variation = UINT64_C(0x9e3779b97f4a7c15) * (uint64_t(id) + 1);
    return {{0, 1, UINT64_MAX, UINT64_C(0x8000000000000000), UINT64_C(0x7fffffffffffffff),
        UINT64_C(0xaaaaaaaaaaaaaaaa) ^ variation,
        UINT64_C(0x5555555555555555) + variation,
        variation ^ (variation >> 29) ^ UINT64_C(0x0123456789abcdef)}};
}

static uint32_t corner_immediate(unsigned variant) {
    static constexpr uint32_t values[8] = {
        0, 1, UINT32_C(0x7fffffff), UINT32_C(0x80000000), UINT32_MAX,
        UINT32_C(0xfffffff8), UINT32_C(0x12345678), UINT32_C(0x80000001)
    };
    return values[variant % 8];
}

static uint32_t reciprocal_index(const Table& table, unsigned variant) {
    if (table.id == 2) {
        static constexpr uint32_t indices[8] = {0, 1, 2, 4, 511, 512, 513, 65537};
        return indices[variant % 8];
    }
    const uint32_t last = uint32_t(table.reciprocals.size() - 1);
    const uint32_t indices[8] = {0, 1, 2, 4, last, 0, last / 2, 2};
    return indices[variant % 8];
}

static void append_instruction(Case& item, const Table& table, unsigned opcode,
    unsigned dst, unsigned src, unsigned mod, uint32_t immediate) {
    const unsigned pc = item.prepared.getSize();
    require(pc < unsigned(randomx::SuperscalarMaxSize) && opcode < TypeCount && dst < 8,
        "crafted instruction bounds");
    require(!source_used(opcode) || src < 8, "crafted source register");
    require(opcode != 4 || immediate <= 63, "rotate immediate range");
    Instruction instruction{};
    instruction.opcode = uint8_t(opcode);
    instruction.dst = uint8_t(dst);
    instruction.src = uint8_t(src);
    instruction.mod = uint8_t(mod);
    instruction.setImm32(immediate);
    item.prepared(pc) = instruction;
    if (opcode == 13) {
        require(immediate < table.reciprocals.size(), "crafted reciprocal index");
        instruction.setImm32(table.divisors[immediate]);
    }
    item.original(pc) = instruction;
    item.prepared.setSize(pc + 1);
    item.original.setSize(pc + 1);
}

static void append_corner(Case& item, const Table& table, unsigned opcode,
    unsigned variant, unsigned dst, unsigned src) {
    static constexpr uint32_t rotations[8] = {0, 63, 1, 32, 31, 2, 62, 7};
    uint32_t immediate = opcode == 4 ? rotations[variant % 8]
        : opcode == 13 ? reciprocal_index(table, variant) : corner_immediate(variant);
    const unsigned mod = ((variant % 4) << 2) | ((variant & 1) ? 0xf3 : 0);
    append_instruction(item, table, opcode, dst, source_used(opcode) ? src : 255, mod, immediate);
}

static void highmul_operands(Case& item, unsigned variant, unsigned dst, unsigned src) {
    static constexpr uint64_t lhs[8] = {0, UINT64_MAX, UINT64_C(0x8000000000000000),
        UINT64_C(0x7fffffffffffffff), UINT64_C(0x8000000000000000),
        UINT64_C(0x8000000000000000), 1, UINT64_C(0x7fffffffffffffff)};
    static constexpr uint64_t rhs[8] = {0, UINT64_MAX, UINT64_C(0x7fffffffffffffff),
        UINT64_C(0x8000000000000000), UINT64_MAX, UINT64_C(0x8000000000000000),
        UINT64_MAX, UINT64_C(0x7fffffffffffffff)};
    require(dst != src || lhs[variant] == rhs[variant], "high multiply alias fixture");
    item.initial[dst] = lhs[variant];
    item.initial[src] = rhs[variant];
}

// No instruction arithmetic is duplicated here: this only adapts the array type.
static void native_execute(Registers& registers, SuperscalarProgram& program,
    std::vector<uint64_t>* reciprocals) {
    uint64_t native[8];
    std::copy(registers.begin(), registers.end(), native);
    randomx::executeSuperscalar(native, program, reciprocals);
    std::copy(native, native + 8, registers.begin());
}

static void execute_case(Case& item, Table& table) {
    require(item.prepared.getSize() == item.original.getSize()
        && item.prepared.getSize() <= randomx::SuperscalarMaxSize, "case program size");
    Registers stepped = item.initial;
    for (unsigned pc = 0; pc < item.prepared.getSize(); ++pc) {
        const Instruction instruction = item.prepared(pc);
        require(instruction.opcode < TypeCount && instruction.dst < 8
            && (!source_used(instruction.opcode) || instruction.src < 8), "native instruction bounds");
        require(instruction.opcode != 4 || instruction.getImm32() <= 63, "native rotate bounds");
        if (reciprocal_op(instruction)) {
            require(instruction.getImm32() < table.reciprocals.size(), "native reciprocal bounds");
            require(item.original(pc).getImm32() == table.divisors[instruction.getImm32()],
                "original divisor/index identity");
        }
        SuperscalarProgram singleton{};
        singleton.setSize(1);
        singleton(0) = instruction;
        native_execute(stepped, singleton, &table.reciprocals);
        item.steps.push_back(stepped);
        ++item.opcounts[instruction.opcode];
    }
    Registers full = item.initial, raw = item.initial;
    native_execute(full, item.prepared, &table.reciprocals);
    native_execute(raw, item.original, nullptr);
    require(full == stepped, "singleton/full native disagreement: " + item.label);
    require(full == raw, "prepared/raw native disagreement: " + item.label);
    item.final = full;
}

static std::string case_name(unsigned id) {
    std::ostringstream name;
    name << "case-" << std::setw(3) << std::setfill('0') << id;
    return name.str();
}

static void counts_json(std::ostream& out, const std::array<uint64_t, TypeCount>& counts) {
    out << '{';
    for (unsigned op = 0; op < TypeCount; ++op) {
        if (op) out << ',';
        out << quoted(Names[op]) << ':' << std::dec << counts[op];
    }
    out << '}';
}

static void case_json(std::ostream& out, const Case& item, const Table& table) {
    out << "{\"case_id\":" << std::dec << item.id << ",\"label\":" << quoted(item.label)
        << ",\"kind\":" << quoted(item.kind) << ",\"directory\":" << quoted(case_name(item.id))
        << ",\"table_id\":" << item.table << ",\"reciprocal_table_count\":" << table.reciprocals.size()
        << ",\"instruction_count\":" << item.prepared.size
        << ",\"post_instruction_steps\":" << item.steps.size()
        << ",\"address_register\":" << item.address_register
        << ",\"generated_program\":" << item.generated_program
        << ",\"mapped\":" << (item.mapped ? "true" : "false")
        << ",\"control\":" << (item.control ? "true" : "false")
        << ",\"initial_registers_r7_to_r0\":" << quoted(registers_string(item.initial))
        << ",\"final_registers_r7_to_r0\":" << quoted(registers_string(item.final))
        << ",\"singleton_full_native_agree\":true,\"prepared_raw_native_agree\":true,\"opcounts\":";
    counts_json(out, item.opcounts);
    out << '}';
}

static void export_case(const fs::path& root, const Case& item, const Table& table) {
    const fs::path directory = root / case_name(item.id);
    require(fs::create_directory(directory), "fresh case directory required: " + directory.string());
    for (bool original : {false, true}) {
        write_file(directory / (original ? "original-programs.mem" : "programs.mem"), [&](std::ostream& out) {
            const SuperscalarProgram& program = original ? item.original : item.prepared;
            for (unsigned pc = 0; pc < item.prepared.size; ++pc) {
                hex64(out, instruction_word(program.programBuffer[pc]));
                out << '\n';
            }
        });
    }
    write_file(directory / "steps.mem", [&](std::ostream& out) {
        for (const auto& registers : item.steps) { registers_hex(out, registers); out << '\n'; }
    });
    for (unsigned field = 0; field < 3; ++field) {
        const char* filename = field == 0 ? "rcp-valid.mem" : field == 1 ? "rcp-index.mem" : "reciprocals.mem";
        write_file(directory / filename, [&](std::ostream& out) {
            for (unsigned pc = 0; pc < item.prepared.size; ++pc) {
                const Instruction& instruction = item.prepared.programBuffer[pc];
                const bool valid = reciprocal_op(instruction);
                if (field == 0) out << (valid ? '1' : '0');
                else if (field == 1) hex32(out, valid ? instruction.getImm32() : 0);
                else hex64(out, valid ? table.reciprocals.at(instruction.getImm32()) : 0);
                out << '\n';
            }
        });
    }
    write_file(directory / "initial.hex", [&](std::ostream& out) { registers_hex(out, item.initial); out << '\n'; });
    write_file(directory / "final.hex", [&](std::ostream& out) { registers_hex(out, item.final); out << '\n'; });
    write_file(directory / "metadata.json", [&](std::ostream& out) { case_json(out, item, table); out << '\n'; });
}

static void export_table(const fs::path& root, const Table& table) {
    write_file(root / ("table-" + std::to_string(table.id) + ".json"), [&](std::ostream& out) {
        out << "{\"table_id\":" << table.id << ",\"seed\":" << quoted(table.seed)
            << ",\"kind\":" << quoted(table.kind)
            << ",\"generated_initCache_context\":" << (table.generated ? "true" : "false")
            << ",\"divisor_rule\":" << quoted(table.generated ? "native generated instruction divisors in program/PC order" : "2*index+3")
            << ",\"nonce\":0,\"continuous_generator\":" << (table.generated ? "true" : "false")
            << ",\"global_indices\":true,\"deduplicated\":false,\"entry_count\":"
            << table.reciprocals.size() << ",\"programs\":[";
        for (unsigned i = 0; i < (table.generated ? ProgramsPerSeed : 0); ++i) {
            if (i) out << ',';
            out << "{\"program\":" << std::dec << i << ",\"case_id\":" << table.id * 8 + i
                << ",\"instruction_count\":" << table.prepared[i].size
                << ",\"address_register\":" << table.prepared[i].addrReg
                << ",\"reciprocal_begin\":" << table.begins[i] << ",\"reciprocal_end\":" << table.ends[i] << '}';
        }
        out << "],\"entries\":[";
        for (size_t i = 0; i < table.reciprocals.size(); ++i) {
            if (i) out << ',';
            out << "{\"index\":" << std::dec << i << ",\"original_divisor\":" << table.divisors[i]
                << ",\"reciprocal_hex\":\"";
            hex64(out, table.reciprocals[i]);
            out << "\"}";
        }
        out << "]}\n";
    });
}

int main(int argc, char** argv) {
    try {
        require(argc == 2, "usage: superscalar_oracle OUTPUT_DIRECTORY");
        const fs::path output = argv[1];
        require(fs::is_directory(output), "output directory must already exist");
        static_assert(randomx::SuperscalarMaxSize == 512, "pinned superscalar maximum changed");
        static_assert(RANDOMX_CACHE_ACCESSES == ProgramsPerSeed, "pinned cache program count changed");
        static_assert(unsigned(SuperscalarInstructionType::COUNT) == TypeCount, "pinned opcode count changed");
        std::array<Table, 3> tables{};
        tables[0].id = 0; tables[0].seed = "OpenRX superscalar fixed seed zero 20261016";
        tables[1].id = 1; tables[1].seed = "OpenRX superscalar fixed seed one 20261016";
        for (unsigned group = 0; group < 2; ++group) prepare_table(tables[group]);
        prepare_width_table(tables[2]);
        // Execution starts only after both complete eight-program groups exist.
        std::vector<Case> cases;
        cases.reserve(130);
        for (unsigned group = 0; group < 2; ++group) {
            const auto& table = tables[group];
            for (unsigned program = 0; program < ProgramsPerSeed; ++program) {
                Case item{};
                item.id = unsigned(cases.size()); item.table = table.id;
                item.kind = "native-generated-complete";
                item.label = "seed-" + std::to_string(table.id) + "-program-" + std::to_string(program);
                item.generated_program = int(program);
                item.original = table.original[program]; item.prepared = table.prepared[program];
                item.address_register = unsigned(table.prepared[program].addrReg);
                item.initial = initial_registers(item.id);
                item.mapped = item.control = program == 0;
                cases.push_back(item);
            }
        }
        for (unsigned opcode = 0; opcode < TypeCount; ++opcode) {
            for (unsigned variant = 0; variant < 8; ++variant) {
                Case item{};
                item.id = unsigned(cases.size()); item.kind = "one-op-corner"; item.mapped = true;
                item.table = opcode == 13 ? 2 : 0;
                item.address_register = variant;
                item.label = std::string(Names[opcode]) + "-corner-" + std::to_string(variant);
                item.initial = initial_registers(item.id);
                const unsigned dst = (variant * 3 + opcode) % 8;
                const unsigned offsets[8] = {0, 0, 1, 7, 3, 0, 2, 5};
                const unsigned src = (dst + offsets[variant]) % 8;
                append_corner(item, tables[item.table], opcode, variant, dst, src);
                if (opcode == 11 || opcode == 12) highmul_operands(item, variant, dst, src);
                if (opcode == 13) item.initial[dst] = variant & 1 ? 1 : UINT64_MAX;
                cases.push_back(item);
            }
        }
        Case maximum{};
        maximum.id = unsigned(cases.size()); maximum.kind = "crafted-maximum-all-register-pairs";
        maximum.label = "crafted-512-all-pairs-and-ignored-source";
        maximum.mapped = true; maximum.initial = initial_registers(maximum.id);
        for (unsigned opcode : {0U, 1U, 2U, 3U, 11U, 12U}) {
            for (unsigned pair = 0; pair < 64; ++pair)
                append_corner(maximum, tables[0], opcode, pair, pair / 8, pair % 8);
        }
        for (unsigned opcode : {4U, 5U, 6U, 7U, 8U, 9U, 10U, 13U}) {
            for (unsigned variant = 0; variant < 16; ++variant)
                append_corner(maximum, tables[0], opcode, variant, variant % 8, 255);
        }
        require(maximum.id == 128 && maximum.prepared.getSize() == 512, "maximum case identity/size");
        cases.push_back(maximum);
        Case empty{};
        empty.id = unsigned(cases.size()); empty.kind = "empty-program"; empty.label = "empty-0";
        empty.mapped = true; empty.initial = initial_registers(empty.id);
        cases.push_back(empty);
        require(cases.size() == 130 && empty.id == 129, "case inventory");

        std::array<uint64_t, TypeCount> opcounts{};
        uint64_t steps = 0;
        unsigned mapped_count = 0, control_count = 0;
        for (auto& item : cases) {
            execute_case(item, tables[item.table]);
            steps += item.steps.size();
            for (unsigned op = 0; op < TypeCount; ++op) opcounts[op] += item.opcounts[op];
            mapped_count += item.mapped; control_count += item.control;
        }
        require(mapped_count == 116 && control_count == 2, "mapped/control inventory");
        for (unsigned op = 0; op < TypeCount; ++op) require(opcounts[op] != 0, "opcode coverage");
        for (const auto& table : tables) export_table(output, table);
        write_file(output / "tables.hex", [&](std::ostream& out) {
            for (const auto& table : tables) for (size_t i = 0; i < table.reciprocals.size(); ++i) {
                out << std::dec << table.id << ' ' << i << ' ';
                hex32(out, table.divisors[i]); out << ' '; hex64(out, table.reciprocals[i]); out << '\n';
            }
        });
        for (const auto& item : cases) export_case(output, item, tables[item.table]);
        for (unsigned selection = 0; selection < 3; ++selection) {
            const char* name = selection == 0 ? "cases.hex" : selection == 1 ? "cases-mapped.hex" : "cases-control.hex";
            write_file(output / name, [&](std::ostream& out) {
                for (const auto& item : cases) {
                    if ((selection == 1 && !item.mapped) || (selection == 2 && !item.control)) continue;
                    out << std::dec << item.id << ' ' << item.prepared.size << ' ' << item.address_register
                        << ' ' << tables[item.table].reciprocals.size() << ' ';
                    registers_hex(out, item.initial); out << ' '; registers_hex(out, item.final); out << '\n';
                }
            });
        }
        write_file(output / "native-summary.json", [&](std::ostream& out) {
            out << "{\"status\":\"pass\",\"oracle\":\"unchanged pinned executeSuperscalar\",\"pin\":" << quoted(Pin)
                << ",\"randomx_tag\":\"v2.0.1\",\"cases\":" << std::dec << cases.size()
                << ",\"mapped_cases\":" << mapped_count << ",\"control_cases\":" << control_count
                << ",\"real_program_cases\":16,\"corner_cases\":112,\"crafted_maximum_case\":128,\"empty_case\":129"
                << ",\"seed_groups\":2,\"programs_per_seed\":8,\"native_types\":14,\"maximum_instructions\":512"
                << ",\"reciprocal_tables\":3,\"index_width_test_table\":2,\"index_width_test_entries\":65538"
                << ",\"singleton_steps\":" << steps << ",\"post_instruction_steps\":" << steps
                << ",\"full_program_checks\":" << cases.size() << ",\"raw_prepared_checks\":" << cases.size()
                << ",\"singleton_full_native_agree\":true,\"prepared_raw_native_agree\":true"
                << ",\"complete_real_programs\":true,\"cache_allocation\":false,\"argon_calls\":0,\"dataset_calls\":0"
                << ",\"reciprocal_indices_are_global_per_seed\":true,\"reciprocal_entries_are_not_deduplicated\":true"
                << ",\"instruction_word_format\":\"opcode|dst<<8|src<<16|mod<<24|imm32<<32\""
                << ",\"register_word_format\":\"512-bit hex r7 through r0; r0 in low64\""
                << ",\"tables_hex_format\":\"table_id_decimal index_decimal original_divisor_hex8 reciprocal_hex16\""
                << ",\"opcounts\":";
            counts_json(out, opcounts);
            out << ",\"full_real_program_sizes\":[";
            for (unsigned i = 0; i < 16; ++i) { if (i) out << ','; out << std::dec << cases[i].prepared.size; }
            out << "],\"tables\":[";
            for (unsigned i = 0; i < tables.size(); ++i) {
                if (i) out << ',';
                out << "{\"table_id\":" << std::dec << i << ",\"seed\":" << quoted(tables[i].seed)
                    << ",\"kind\":" << quoted(tables[i].kind)
                    << ",\"entries\":" << tables[i].reciprocals.size()
                    << ",\"identity_file\":" << quoted("table-" + std::to_string(i) + ".json") << '}';
            }
            out << "],\"case_metadata\":[";
            for (size_t i = 0; i < cases.size(); ++i) {
                if (i) out << ',';
                case_json(out, cases[i], tables[cases[i].table]);
            }
            out << "]}\n";
        });
        std::cout << "PASS native_superscalar cases=" << cases.size() << " mapped_cases=" << mapped_count
            << " control_cases=" << control_count << " types=14 steps=" << steps
            << " singleton_full_raw_agree=1 cache_allocation=0\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL native_superscalar: " << error.what() << '\n';
        return 1;
    }
}
