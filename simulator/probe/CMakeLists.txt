cmake_minimum_required(VERSION 3.16)
project(openrx_riscv_probe LANGUAGES C CXX)

# A functional executable, not an architectural timing or power model.
get_filename_component(OPENRX_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
set(ARCH "default" CACHE STRING "RandomX baseline build; cross builds must use default")
if(CMAKE_CROSSCOMPILING AND NOT ARCH STREQUAL "default")
  message(FATAL_ERROR "Cross probes require -DARCH=default; native ISA discovery runs target code")
endif()
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build configuration" FORCE)
endif()

# Verify vendor/randomx.sha256.json with scripts/verify_vendor.py before configuring.
# The pinned source stays unmodified. Its own CMake selects the ISA-specific JIT.
add_subdirectory("${OPENRX_ROOT}/vendor/randomx" "${CMAKE_CURRENT_BINARY_DIR}/randomx")
add_executable(openrx-riscv-probe main.cpp)
target_compile_features(openrx-riscv-probe PRIVATE cxx_std_17)
target_compile_options(openrx-riscv-probe PRIVATE
  -Wall -Wextra -Werror -frounding-math -fno-fast-math -ffp-contract=off)
target_include_directories(openrx-riscv-probe SYSTEM PRIVATE "${OPENRX_ROOT}/vendor/randomx/src")
target_link_libraries(openrx-riscv-probe PRIVATE randomx)

string(TOUPPER "${CMAKE_BUILD_TYPE}" OPENRX_BUILD_TYPE_UPPER)
set(OPENRX_PROBE_COMPILER_FLAGS "${CMAKE_CXX_FLAGS} ${CMAKE_CXX_FLAGS_${OPENRX_BUILD_TYPE_UPPER}} -Wall -Wextra -Werror -frounding-math -fno-fast-math -ffp-contract=off")
target_compile_definitions(openrx-riscv-probe PRIVATE
  OPENRX_BUILD_COMPILER="${CMAKE_CXX_COMPILER}"
  OPENRX_BUILD_COMPILER_ID="${CMAKE_CXX_COMPILER_ID}"
  OPENRX_BUILD_COMPILER_FLAGS="${OPENRX_PROBE_COMPILER_FLAGS}"
  OPENRX_BUILD_SYSTEM_PROCESSOR="${CMAKE_SYSTEM_PROCESSOR}"
  OPENRX_BUILD_TYPE="${CMAKE_BUILD_TYPE}"
  OPENRX_BUILD_ARCH_SETTING="${ARCH}"
  OPENRX_BUILD_SOURCE_ROOT="${OPENRX_ROOT}"
  OPENRX_BUILD_LIBRARY_PATH="$<TARGET_FILE:randomx>")
