// OpenRX M3 functional gate. No throughput, power, or core timing is measured.
// Known hashes are the pinned upstream tests.cpp "Hash test 1a/1b" vectors.
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>

#include "randomx.h"
#include "intrin_portable.h"

// Manual compiler builds must supply metadata rather than fabricate CMake data.
#ifndef OPENRX_BUILD_COMPILER
#define OPENRX_BUILD_COMPILER "unrecorded"
#endif
#ifndef OPENRX_BUILD_COMPILER_ID
#define OPENRX_BUILD_COMPILER_ID "unrecorded"
#endif
#ifndef OPENRX_BUILD_COMPILER_FLAGS
#define OPENRX_BUILD_COMPILER_FLAGS "unrecorded"
#endif
#ifndef OPENRX_BUILD_SYSTEM_PROCESSOR
#define OPENRX_BUILD_SYSTEM_PROCESSOR "unrecorded"
#endif
#ifndef OPENRX_BUILD_TYPE
#define OPENRX_BUILD_TYPE "unrecorded"
#endif
#ifndef OPENRX_BUILD_ARCH_SETTING
#define OPENRX_BUILD_ARCH_SETTING "unrecorded"
#endif
#ifndef OPENRX_BUILD_SOURCE_ROOT
#define OPENRX_BUILD_SOURCE_ROOT "unrecorded"
#endif
#ifndef OPENRX_BUILD_LIBRARY_PATH
#define OPENRX_BUILD_LIBRARY_PATH "unrecorded"
#endif

namespace {
constexpr const char* vendorRevision = "aaafe71322df6602c21a5c72937ac284724ae561";
constexpr const char* cacheKey = "test key 000";
constexpr unsigned requiredChecks = 39; // 7 integer, 24 FP, 8 software-AES hashes.

struct Vector {
    const char* id;
    const char* input;
    const char* v1;
    const char* v2;
};
constexpr std::array<Vector, 2> vectors{{
    {"a", "This is a test",
     "639183aae1bf4c9a35884cb46b09cad9175f04efd7684e7262a0ac1c2f0b4e3f",
     "22ec6b861b3eb23686b2efbad69513c967ecfce80983df66c9c5b4fbfb4cdb6f"},
    {"b", "Lorem ipsum dolor sit amet",
     "300a0adb47603dedb42228ccb2b211104f4da45af709cd7547cd049e9489c969",
     "9e2c772c12fd48f93c14c97fdc89d556264d9100597023f44d9163e279012ecf"}
}};

std::string quote(const std::string& value) {
    std::ostringstream out;
    out << '"';
    for (unsigned char c : value) {
        switch (c) {
            case '"': out << "\\\""; break;
            case '\\': out << "\\\\"; break;
            case '\n': out << "\\n"; break;
            case '\r': out << "\\r"; break;
            case '\t': out << "\\t"; break;
            default:
                if (c < 0x20) {
                    out << "\\u" << std::hex << std::setw(4) << std::setfill('0')
                        << static_cast<unsigned>(c) << std::dec;
                } else {
                    out << c;
                }
        }
    }
    out << '"';
    return out.str();
}

std::string hex64(uint64_t value) {
    std::ostringstream out;
    out << std::hex << std::setw(16) << std::setfill('0') << value;
    return out.str();
}

uint64_t bits(double value) {
    uint64_t result;
    static_assert(sizeof(result) == sizeof(value), "Probe requires binary64-sized double");
    std::memcpy(&result, &value, sizeof(result));
    return result;
}

std::string hashHex(const std::array<unsigned char, RANDOMX_HASH_SIZE>& hash) {
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (unsigned char value : hash) out << std::setw(2) << static_cast<unsigned>(value);
    return out.str();
}

const char* compiledArchitecture() {
#if defined(__riscv) && __riscv_xlen == 64
    return "riscv64";
#elif defined(__x86_64__)
    return "x86_64";
#elif defined(__aarch64__)
    return "aarch64";
#else
    return "other";
#endif
}

struct Results {
    unsigned checks = 0;
    unsigned requiredPassed = 0;
    unsigned failures = 0;
    unsigned skips = 0;

    void check(const std::string& name, const std::string& actual,
               const std::string& expected, const std::string& extra = "",
               bool required = true) {
        const bool ok = actual == expected;
        ++checks;
        if (!ok) ++failures;
        if (ok && required) ++requiredPassed;
        std::cout << "{\"type\":\"check\",\"name\":" << quote(name)
                  << ",\"status\":" << quote(ok ? "pass" : "fail")
                  << ",\"required\":" << (required ? "true" : "false")
                  << ",\"actual\":" << quote(actual)
                  << ",\"expected\":" << quote(expected) << extra << "}" << std::endl;
    }

    void skip(const std::string& name, const std::string& reason) {
        ++checks;
        ++skips;
        std::cout << "{\"type\":\"check\",\"name\":" << quote(name)
                  << ",\"status\":\"skip\",\"required\":false,\"reason\":"
                  << quote(reason) << "}" << std::endl;
    }

    void fatal(const std::string& reason) {
        ++failures;
        std::cout << "{\"type\":\"fatal\",\"status\":\"fail\",\"error\":"
                  << quote(reason) << "}" << std::endl;
    }

    int summary() const {
        const bool ok = failures == 0 && requiredPassed == requiredChecks;
        std::cout << "{\"type\":\"summary\",\"status\":" << quote(ok ? "pass" : "fail")
                  << ",\"checks\":" << checks << ",\"failures\":" << failures
                  << ",\"skips\":" << skips << ",\"required_checks\":" << requiredChecks
                  << ",\"required_passed\":" << requiredPassed
                  << ",\"functional_only\":true}" << std::endl;
        return ok ? 0 : 1;
    }
};

void integerChecks(Results& r) {
    // Volatile inputs prevent constant-folding away the target's instructions.
    volatile uint64_t max = std::numeric_limits<uint64_t>::max();
    volatile uint64_t zero = 0;
    volatile uint64_t one = 1;
    volatile uint64_t two = 2;
    volatile uint64_t high = UINT64_C(0x8000000000000000);
    volatile int64_t minimum = std::numeric_limits<int64_t>::min();
    volatile int64_t signedTwo = 2;
    r.check("integer/add-wrap", hex64(max + one), "0000000000000000");
    r.check("integer/sub-wrap", hex64(zero - one), "ffffffffffffffff");
    r.check("integer/mul-low-wrap", hex64(max * two), "fffffffffffffffe");
    r.check("integer/mul-unsigned-high-max", hex64(mulh(max, max)), "fffffffffffffffe");
    r.check("integer/mul-unsigned-high-carry", hex64(mulh(high, two)), "0000000000000001");
    r.check("integer/mul-signed-high-negative", hex64(static_cast<uint64_t>(smulh(minimum, signedTwo))), "ffffffffffffffff");
    r.check("integer/mul-signed-high-positive", hex64(static_cast<uint64_t>(smulh(minimum, minimum))), "4000000000000000");
}

struct RoundVector {
    unsigned mode;
    const char* name;
    uint64_t positiveAdd;
    uint64_t negativeSubtract;
    uint64_t multiply;
    uint64_t divide;
    uint64_t squareRoot;
};
// Exact binary64 oracles: +/-1 +/- 2^-53 are half-way cases; (1+2^-52)^2
// lies above 1+2^-51; 1/10 and sqrt(2) lie between the two listed neighbors.
constexpr std::array<RoundVector, 4> rounding{{
    {RoundToNearest, "nearest", UINT64_C(0x3ff0000000000000), UINT64_C(0xbff0000000000000),
     UINT64_C(0x3ff0000000000002), UINT64_C(0x3fb999999999999a), UINT64_C(0x3ff6a09e667f3bcd)},
    {RoundDown, "down", UINT64_C(0x3ff0000000000000), UINT64_C(0xbff0000000000001),
     UINT64_C(0x3ff0000000000002), UINT64_C(0x3fb9999999999999), UINT64_C(0x3ff6a09e667f3bcc)},
    {RoundUp, "up", UINT64_C(0x3ff0000000000001), UINT64_C(0xbff0000000000000),
     UINT64_C(0x3ff0000000000003), UINT64_C(0x3fb999999999999a), UINT64_C(0x3ff6a09e667f3bcd)},
    {RoundToZero, "zero", UINT64_C(0x3ff0000000000000), UINT64_C(0xbff0000000000000),
     UINT64_C(0x3ff0000000000002), UINT64_C(0x3fb9999999999999), UINT64_C(0x3ff6a09e667f3bcc)}
}};

void floatingPointChecks(Results& r) {
    static_assert(std::numeric_limits<double>::is_iec559 &&
                  std::numeric_limits<double>::digits == 53,
                  "RandomX probe requires IEEE-754 binary64");
    const auto previousMode = rx_get_rounding_mode();
    for (const auto& test : rounding) {
        rx_set_rounding_mode(test.mode);
        const std::string name = std::string("fp/") + test.name + "/";
        r.check(name + "mode", std::to_string(rx_get_rounding_mode()), std::to_string(test.mode));
        volatile double one = 1.0;
        volatile double negativeOne = -1.0;
        volatile double halfUlp = 0x1p-53;
        volatile double nextOne = 0x1.0000000000001p+0;
        volatile double ten = 10.0;
        volatile double two = 2.0;
        volatile double positiveAdd = one + halfUlp;
        volatile double negativeSubtract = negativeOne - halfUlp;
        volatile double multiply = nextOne * nextOne;
        volatile double divide = one / ten;
        volatile double squareRoot = std::sqrt(two);
        r.check(name + "add-positive", hex64(bits(positiveAdd)), hex64(test.positiveAdd));
        r.check(name + "subtract-negative", hex64(bits(negativeSubtract)), hex64(test.negativeSubtract));
        r.check(name + "multiply", hex64(bits(multiply)), hex64(test.multiply));
        r.check(name + "divide", hex64(bits(divide)), hex64(test.divide));
        r.check(name + "sqrt", hex64(bits(squareRoot)), hex64(test.squareRoot));
    }
    rx_set_rounding_mode(previousMode);
}

using Cache = std::unique_ptr<randomx_cache, decltype(&randomx_release_cache)>;
using Vm = std::unique_ptr<randomx_vm, decltype(&randomx_destroy_vm)>;

void hashChecks(Results& r, randomx_flags supported, bool hardwareRequested) {
    if (!(supported & RANDOMX_FLAG_JIT)) {
        throw std::runtime_error("Required pinned RandomX JIT is not supported by this build/platform");
    }
    // Only one 256-MiB light cache exists at a time, never a full dataset.
    // Reference Argon2 also avoids silently enabling host-specific ISA paths.
    for (const bool useJit : {false, true}) {
        const auto cacheFlags = useJit ? RANDOMX_FLAG_JIT : RANDOMX_FLAG_DEFAULT;
        std::cout << "{\"type\":\"stage\",\"name\":\"cache-init\",\"status\":\"begin\",\"engine\":"
                  << quote(useJit ? "jit" : "interpreter") << ",\"cache_flags\":"
                  << static_cast<unsigned>(cacheFlags) << "}" << std::endl;
        Cache cache(randomx_alloc_cache(cacheFlags), &randomx_release_cache);
        if (!cache) throw std::runtime_error("Could not allocate the required 256-MiB light cache");
        randomx_init_cache(cache.get(), cacheKey, std::strlen(cacheKey));
        std::cout << "{\"type\":\"stage\",\"name\":\"cache-init\",\"status\":\"pass\",\"engine\":"
                  << quote(useJit ? "jit" : "interpreter") << "}" << std::endl;
        for (const bool v2 : {true, false}) {
            auto run = [&](bool hardware) {
                auto flags = cacheFlags | (v2 ? RANDOMX_FLAG_V2 : RANDOMX_FLAG_DEFAULT);
                // Secure is required on builds that advertise W^X mode.
                if (useJit) flags |= supported & RANDOMX_FLAG_SECURE;
                if (hardware) flags |= RANDOMX_FLAG_HARD_AES;
                Vm vm(randomx_create_vm(flags, cache.get(), nullptr), &randomx_destroy_vm);
                if (!vm) throw std::runtime_error("Required RandomX VM allocation failed");
                for (const auto& vector : vectors) {
                    std::array<unsigned char, RANDOMX_HASH_SIZE> output{};
                    randomx_calculate_hash(vm.get(), vector.input, std::strlen(vector.input), output.data());
                    const auto name = std::string("hash/") + (v2 ? "v2/" : "v1/") +
                                      (useJit ? "jit/" : "interpreter/") +
                                      (hardware ? "hardware/" : "software/") + vector.id;
                    const auto extra = std::string(",\"algorithm\":") + quote(v2 ? "v2" : "v1") +
                        ",\"engine\":" + quote(useJit ? "jit" : "interpreter") +
                        ",\"aes\":" + quote(hardware ? "hardware" : "software") +
                        ",\"vector\":" + quote(vector.id) + ",\"vm_flags\":" +
                        std::to_string(static_cast<unsigned>(flags)) + ",\"input_bytes\":" +
                        std::to_string(std::strlen(vector.input));
                    r.check(name, hashHex(output), v2 ? vector.v2 : vector.v1, extra, !hardware);
                }
            };
            run(false);
            if (useJit && hardwareRequested && (supported & RANDOMX_FLAG_HARD_AES)) run(true);
        }
    }
    if (!hardwareRequested) r.skip("hardware-aes", "Not requested; required software-AES controls completed");
    else if (!(supported & RANDOMX_FLAG_HARD_AES)) r.skip("hardware-aes", "randomx_get_flags did not advertise hardware AES; no unsupported AES path was invoked");
}

void config(randomx_flags supported, bool hardwareRequested, const char* executable) {
    std::cout << "{\"type\":\"config\",\"schema_version\":1,\"functional_only\":true,\"compiled_architecture\":"
              << quote(compiledArchitecture()) << ",\"compiler_version\":" << quote(__VERSION__)
              << ",\"compiler\":" << quote(OPENRX_BUILD_COMPILER)
              << ",\"compiler_id\":" << quote(OPENRX_BUILD_COMPILER_ID)
              << ",\"compiler_flags\":" << quote(OPENRX_BUILD_COMPILER_FLAGS)
              << ",\"cmake_system_processor\":" << quote(OPENRX_BUILD_SYSTEM_PROCESSOR)
              << ",\"build_type\":" << quote(OPENRX_BUILD_TYPE)
              << ",\"arch_setting\":" << quote(OPENRX_BUILD_ARCH_SETTING)
              << ",\"source_root\":" << quote(OPENRX_BUILD_SOURCE_ROOT)
              << ",\"library_path\":" << quote(OPENRX_BUILD_LIBRARY_PATH)
              << ",\"argv0\":" << quote(executable) << ",\"vendor_revision\":" << quote(vendorRevision)
              << ",\"auto_flags\":" << static_cast<unsigned>(supported)
              << ",\"cache_size_bytes\":268435456,\"full_dataset\":false,\"key\":" << quote(cacheKey)
              << ",\"key_bytes\":" << std::strlen(cacheKey)
              << ",\"hardware_aes_requested\":" << (hardwareRequested ? "true" : "false")
              << ",\"reference_source\":\"vendor/randomx/src/tests/tests.cpp: Hash test 1a/1b\",\"vectors\":[";
    for (size_t i = 0; i < vectors.size(); ++i) {
        const auto& vector = vectors[i];
        std::cout << (i ? "," : "") << "{\"id\":" << quote(vector.id)
                  << ",\"input\":" << quote(vector.input) << ",\"input_bytes\":" << std::strlen(vector.input)
                  << ",\"v1\":" << quote(vector.v1) << ",\"v2\":" << quote(vector.v2) << "}";
    }
    std::cout << "]}" << std::endl;
}
} // namespace

int main(int argc, char** argv) {
    Results results;
    try {
        bool hardwareRequested = false;
        if (argc == 2 && std::string(argv[1]) == "--hardware-aes") hardwareRequested = true;
        else if (argc != 1) throw std::runtime_error("Usage: openrx-riscv-probe [--hardware-aes]");
        const auto supported = randomx_get_flags();
        config(supported, hardwareRequested, argv[0]);
        integerChecks(results);
        floatingPointChecks(results);
        hashChecks(results, supported, hardwareRequested);
    } catch (const std::exception& ex) {
        results.fatal(ex.what());
    } catch (...) {
        results.fatal("Unknown exception");
    }
    return results.summary();
}
