# Ubuntu 24.04 packages: gcc-14-riscv64-linux-gnu, g++-14-riscv64-linux-gnu.
# GCC 14 is needed even for scalar execution: pinned upstream also compiles
# RVV/Zvkned translation units with per-source flags.
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR riscv64)
set(CMAKE_C_COMPILER riscv64-linux-gnu-gcc-14)
set(CMAKE_CXX_COMPILER riscv64-linux-gnu-g++-14)
set(CMAKE_C_FLAGS_INIT "-march=rv64gc -mabi=lp64d")
set(CMAKE_CXX_FLAGS_INIT "-march=rv64gc -mabi=lp64d")
# Keep configure-time probes compile-only. Never discover the host ISA in a
# cross build; ARCH=default below avoids upstream native try_run probes.
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
set(ARCH default CACHE STRING "Pinned baseline ISA, no native feature discovery")
