// SPDX-License-Identifier: BSD-3-Clause
// Reuse all accepted native callbacks with a separately loaded prepared context.
// Only the statistics/registration wrapper and assertion-only dataset task are new.
#include "dataset_lifecycle_native.hpp"
#define lifecycle_native prepared_lifecycle_native
#define statistics retained_provider_statistics
#define register_tasks retained_register_tasks
#define vlog_startup_routines retained_vlog_startup_routines
#include "lifecycle_source_vpi.cpp"
#undef vlog_startup_routines
#undef register_tasks
#undef statistics
#undef lifecycle_native
static prepared_lifecycle_native::ProviderCounters counters() {
    prepared_lifecycle_native::ProviderCounters p;
    p.initial_seconds=initial_seconds;p.input_hash_seconds=input_hash_seconds;p.generation_seconds=generation_seconds;
    p.assertion_seconds=assertion_seconds;p.assertion_generation_seconds=assertion_generation_seconds;p.assertion_input_hash_seconds=assertion_input_hash_seconds;
    p.generations=generations;p.input_hash_calls=input_hash_calls;p.software_fill_calls=software_fill_calls;
    p.assertion_generations=assertion_generations;p.assertion_input_hash_calls=assertion_input_hash_calls;return p;
}
static PLI_INT32 dataset_assertion(PLI_BYTE8*) { try {
    auto a=arguments();if(a.size()!=2)throw std::runtime_error("rx_dataset_assertion arguments");
    uint64_t address;read_bytes(a[0],&address,8);alignas(64) uint8_t line[64];
    prepared_lifecycle_native::dataset().read_assertion(address,line);write_bytes(a[1],line,64);
} catch(const std::exception& e) {vpi_printf("FAIL native dataset assertion: %s\n",e.what());vpi_control(vpiFinish,1);}return 0; }
static PLI_INT32 prepared_statistics(PLI_BYTE8*) { try {
    auto a=arguments();if(a.size()!=1)throw std::runtime_error("rx_provider_stats arguments");
    prepared_lifecycle_native::dataset().statistics(string_value(a[0]),counters(),"simulation-provider");
} catch(const std::exception& e) {vpi_printf("FAIL prepared provider statistics: %s\n",e.what());vpi_control(vpiFinish,1);}return 0; }
static void prepared_register_tasks() {
    for(auto pair:std::vector<std::pair<const char*,PLI_INT32(*)(PLI_BYTE8*)>>{
        {"$rx_life_initial",initial},{"$rx_life_input_hash",input_hash},{"$rx_life_input_hash_assertion",input_hash_assertion},
        {"$rx_generate",generate},{"$rx_generate_assertion",generate_assertion},{"$rx_next_seed",next_seed},
        {"$rx_dataset",dataset_read},{"$rx_dataset_assertion",dataset_assertion},{"$rx_provider_stats",prepared_statistics}}) {
        s_vpi_systf_data d{};d.type=vpiSysTask;d.tfname=(PLI_BYTE8*)pair.first;d.calltf=pair.second;vpi_register_systf(&d);
    }
}
extern "C" {void (*vlog_startup_routines[])()={prepared_register_tasks,nullptr};}
