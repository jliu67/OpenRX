// SPDX-License-Identifier: BSD-3-Clause
// Full default reference only: reuse the accepted cache0 loader and unchanged
// native reference algorithm. The older two-item reference role stays unchanged.
#include "dataset_capacity_native.hpp"
#include <cstdio>

namespace fullhash_native {
using prepared_lifecycle_native::Clock;
using prepared_lifecycle_native::seconds;
using prepared_lifecycle_native::initial;
using prepared_lifecycle_native::unhex;
using prepared_lifecycle_native::cache_key;
using prepared_lifecycle_native::require;
struct Dataset final : prepared_lifecycle_native::Dataset {
    Dataset() {
        // The inherited bounded reference role remains false. Only this adapter
        // exports a full sequence and owns the separate 16,384-demand guard.
        require(!prepared_lifecycle_native::reference_role, "full reference role isolation");
        const char* value = std::getenv("RX_PREPARED_REFERENCE_OUTPUT");
        require(value && *value, "full reference output is mandatory");
        reference_output = value;
        require(std::filesystem::is_directory(reference_output) &&
                !std::filesystem::is_symlink(reference_output), "fresh full reference directory");
        enable_gold_export(reference_output / "dataset-items.hex");
    }
    void read(uint64_t address, void* output) {
        require(item_requests < 16384, "full reference demand budget");
        prepared_lifecycle_native::Dataset::read(address, output);
    }
    ~Dataset() {
        // Only PROGRAMS=8, ITERATIONS=2048 can close this budget through the
        // unchanged reference main. A partial invocation must exit nonzero.
        if (item_requests != 16384 || gold_export_rows != 16384 || assertion_item_requests) {
            std::fputs("FAIL full reference exact demand/export closure\n", stderr);
            std::abort();
        }
        close_gold_export();
        statistics((reference_output / "dataset-native-host-time.json").string(),
                   {}, "native-reference");
    }
};
inline Dataset& dataset() { static Dataset value; return value; }
} // namespace fullhash_native

#define lifecycle_native fullhash_native
#include "../../hash/tests/lifecycle_reference.cpp"
#undef lifecycle_native
