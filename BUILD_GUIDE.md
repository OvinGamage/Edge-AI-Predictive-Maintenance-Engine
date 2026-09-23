# Dual-Target Build System & CMake Operational Guide

This document details the system requirements, build workflows, technical constraints, and configuration tweaks for the C++17 CMake dual-target build infrastructure.

---

## 1. System Requirements & Dependencies

To configure and execute builds across both target platforms, the environment must satisfy the following dependencies:

* **Build Tools:** CMake (v3.15 or newer) and Ninja or GNU Make.
* **Host Toolchain:** Native C++17 compiler (`g++` or `clang++`).
* **Cross-Compiler Toolchain:** `arm-none-eabi-gcc` toolchain (including `gcc`, `g++`, `objcopy`, `objdump`, and `size`) available in system `$PATH`.
* **Network Access:** Required on first host configuration to allow CMake’s `FetchContent` to download GoogleTest v1.14.0.

---

## 2. Operating Instructions

The build system supports two isolated compilation workflows. Always use separate build directories (e.g., `build/host` vs. `build/arm`) to avoid compiler cache pollution.

### A. Host Native Build (Unit Testing & Host Verification)
Generates native x86_64 host binaries, compiles the core library, fetches GoogleTest, and registers CTest test cases.

##bash
B. ARM Target Cross-Compilation (Bare-Metal Binary)
Invokes cmake/arm-none-eabi.cmake to switch the toolchain to arm-none-eabi-gcc for target ARM hardware. Automatically disables host GoogleTest execution.
## 1. Configure the host build
cmake -B build/host -S .

##2. Compile host targets (firmware_core & unit_tests)
cmake --build build/host

# 3. Execute unit tests via CTest
ctest --test-dir build/host --output-on-failure
B. ARM Target Cross-Compilation (Bare-Metal Binary)
Invokes cmake/arm-none-eabi.cmake to switch the toolchain to arm-none-eabi-gcc for target ARM hardware. Automatically disables host GoogleTest execution.
Bash
# 1. Configure the ARM target build
cmake -B build/arm -S . -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake

# 2. Compile bare-metal executable (firmware_app)
cmake --build build/arm
Upon build completion, arm-none-eabi-size automatically prints the final Flash/RAM memory footprint in the terminal.

3. Key Limitations & Design Constraints
Host-Only Unit Tests: GoogleTest targets (unit_tests) are disabled during ARM cross-compilation (if(CMAKE_CROSSCOMPILING) is active) because bare-metal environments lack standard OS threading and file I/O primitives.

Missing Source Files: CMake requires source files listed in add_library() or add_executable() to exist on disk during the configuration step. If files are missing, configuration will fail.

Compiler Test Safety: The toolchain file forces CMAKE_TRY_COMPILE_TARGET_TYPE to STATIC_LIBRARY. This prevents CMake's initial compiler check from failing due to missing bare-metal RAM/Flash linker maps.

4. How to Tweak & Customize the CMake Scripts
Changing Hardware/CPU Target Flags
If porting to a different ARM Cortex-M core (e.g., Cortex-M4 with Floating Point Unit):

File: cmake/arm-none-eabi.cmake

Modification: Update ARM_FLAGS:

CMake
# Example: Updating to Cortex-M4 with Hard FP support
set(ARM_FLAGS "-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard")
Adding New C++ Source Files
When adding new implementation files or modules to your application:

File: firmware/CMakeLists.txt

Modification: Append relative path strings to add_library(firmware_core STATIC ...):

CMake
add_library(firmware_core STATIC
    src/core/ring_buffer.cpp
    src/core/dsp_features.cpp
    src/core/new_module.cpp  # <--- Add new source files here
)
Adding New Unit Test Suites
When creating a new GoogleTest file:

File: tests/CMakeLists.txt

Modification: Add the test file to add_executable(unit_tests ...):

CMake
add_executable(unit_tests
    unit/test_ring_buffer.cpp
    unit/test_new_module.cpp # <--- Add test suites here
)
Adjusting GoogleTest Version
To update or freeze the version of GoogleTest downloaded:

File: tests/CMakeLists.txt

Modification: Change GIT_TAG inside FetchContent_Declare:

CMake
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG        v1.15.0  # <--- Modify target release tag or commit hash
