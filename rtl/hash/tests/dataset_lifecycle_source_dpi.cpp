// SPDX-License-Identifier: BSD-3-Clause
// Same prepared cache/assertion boundary as the new VPI adapter.
#include "dataset_lifecycle_native.hpp"
#define lifecycle_native prepared_lifecycle_native
#define rx_provider_stats retained_rx_provider_stats
#include "lifecycle_source_dpi.cpp"
#undef rx_provider_stats
#undef lifecycle_native
extern "C" void rx_dataset_assertion(const svBitVecVal* address,svBitVecVal* result) {
    checked([&] {uint64_t value;std::memcpy(&value,address,8);alignas(64) uint8_t line[64];
        prepared_lifecycle_native::dataset().read_assertion(value,line);std::memcpy(result,line,64);});
}
extern "C" void rx_provider_stats(const char* filename) {
    checked([&] {prepared_lifecycle_native::ProviderCounters p;
        p.initial_seconds=initial_seconds;p.input_hash_seconds=input_hash_seconds;p.generation_seconds=generation_seconds;
        p.assertion_seconds=assertion_seconds;p.assertion_generation_seconds=assertion_generation_seconds;p.assertion_input_hash_seconds=assertion_input_hash_seconds;
        p.generations=generations;p.input_hash_calls=input_hash_calls;p.software_fill_calls=software_fill_calls;
        p.assertion_generations=assertion_generations;p.assertion_input_hash_calls=assertion_input_hash_calls;
        prepared_lifecycle_native::dataset().statistics(filename,p,"simulation-provider");});
}
