# Dual-Target Build System & CMake Operational Guide

This guide documents system requirements, supported build workflows, constraints, and common configuration tweaks for the C++17 CMake dual-target build infrastructure (host + ARM bare-metal).

---

## 1. System Requirements & Dependencies

To configure and execute builds for both target platforms, ensure the environment meets these prerequisites:

- **Build tools**
  - CMake v3.15 or newer
  - Ninja or GNU Make
- **Host toolchain**
  - Native C++17 compiler (`g++` or `clang++`)
- **Cross-compiler toolchain**
  - `arm-none-eabi-gcc` toolchain, including `gcc`, `g++`, `objcopy`, `objdump`, and `size`, available in the system `$PATH`
- **Network access**
  - Required during the first host configuration so CMake's `FetchContent` can download GoogleTest v1.14.0.

---

## 2. Operating Instructions

The build system supports two isolated compilation workflows. Always use separate build directories, such as `build/host` and `build/arm`, to avoid compiler-cache and artifact pollution.

### A. Host Native Build: Unit Testing and Host Verification

This workflow generates native x86_64 host binaries, compiles the core library, fetches GoogleTest, and registers CTest test cases.

1. Configure the host build:

   ```bash
   cmake -B build/host -S .
   ```

2. Compile the host targets (`firmware_core` and `unit_tests`):

   ```bash
   cmake --build build/host
   ```

3. Run the unit tests with CTest:

   ```bash
   ctest --test-dir build/host --output-on-failure
   ```

### B. ARM Target Cross-Compilation: Bare-Metal Binary

This workflow uses `cmake/arm-none-eabi.cmake` to select the `arm-none-eabi-gcc` toolchain for ARM hardware. Host GoogleTest execution is automatically disabled during cross-compilation.

1. Configure the ARM build:

   ```bash
   cmake -B build/arm -S . -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake
   ```

2. Compile the bare-metal executable (`firmware_app`):

   ```bash
   cmake --build build/arm
   ```

After the build completes, `arm-none-eabi-size` automatically prints the final Flash/RAM memory footprint in the terminal.

---

## 3. Key Limitations and Design Constraints

### Host-Only Unit Tests

GoogleTest targets such as `unit_tests` are disabled during ARM cross-compilation when `CMAKE_CROSSCOMPILING` is active. Bare-metal environments generally lack the standard OS threading, filesystem, and process support required by GoogleTest.

### Missing Source Files

CMake requires all source files listed in `add_library()` or `add_executable()` to exist on disk during configuration. If a source file is missing, configuration fails.

### Compiler-Test Safety

The toolchain file sets `CMAKE_TRY_COMPILE_TARGET_TYPE` to `STATIC_LIBRARY`. This prevents CMake's initial compiler check from failing when bare-metal RAM/Flash linker support is unavailable during the test link step.

---

## 4. How to Tweak and Customize the CMake Scripts

### Changing Hardware/CPU Target Flags

**File:** `cmake/arm-none-eabi.cmake`

When porting to a different ARM Cortex-M core, update `ARM_FLAGS` to match the target CPU and ABI. For example, the following flags target a Cortex-M4 with hard floating-point support:

```cmake
set(ARM_FLAGS "-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard")
```

### Adding New C++ Source Files

**File:** `firmware/CMakeLists.txt`

When adding implementation files or modules, append their relative paths to `add_library(firmware_core STATIC ...)`:

```cmake
add_library(firmware_core STATIC
    src/core/ring_buffer.cpp
    src/core/dsp_features.cpp
    src/core/new_module.cpp  # Add new source files here
)
```

Make sure the new files exist on disk before running CMake configuration.

### Adding New Unit Test Suites

**File:** `tests/CMakeLists.txt`

When creating a new GoogleTest file, add it to `add_executable(unit_tests ...)`:

```cmake
add_executable(unit_tests
    unit/test_ring_buffer.cpp
    unit/test_new_module.cpp  # Add new test suites here
)
```

The test target is configured only for host builds when GoogleTest is provided through `FetchContent`.

### Adjusting the GoogleTest Version

**File:** `tests/CMakeLists.txt`

To update or pin the GoogleTest version, change `GIT_TAG` inside `FetchContent_Declare`:

```cmake
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG        v1.15.0  # Set the desired release tag or commit hash
)
```
# Firmware & ML Development Setup Guide

This guide details the prerequisites and step-by-step commands required to set up the environment, run the ML training pipeline, compile the C++ firmware, and execute unit tests.

---

## 1. System Prerequisites

Ensure the following tools are installed on your host system:

* **Git** (v2.25 or higher)
* **CMake** (v3.14 or higher)
* **C++ Compiler** with standard `C++17` support:
  * **Linux:** `gcc` / `g++` (v9+)
  * **Windows:** MSYS2 MinGW-w64 (`g++`) or MSVC (Visual Studio 2019+)
  * **macOS:** Apple Clang / Xcode Command Line Tools
* **Python 3.9+** (with `pip`)

---

## 2. Cloning the Repository

Because this project utilizes TensorFlow Lite Micro as a Git submodule, you must clone the repository recursively to fetch all dependencies.

### Option A: Recursive Clone (Recommended)
```bash
git clone --recursive <repository-url>
cd Machine-Learning
Option B: If Cloned Without --recursive
If you already ran a standard git clone, initialize and update the submodules manually:

Bash
git submodule update --init --recursive
3. Populating Third-Party Dependencies
TensorFlow Lite Micro requires third-party C++ headers (FlatBuffers and gemmlowp). If these are not present inside firmware/lib/tflite-micro/third_party, populate them using the script below.

Windows (PowerShell)
PowerShell
cd firmware/lib/tflite-micro

# Create third-party target directories
New-Item -ItemType Directory -Force -Path "third_party/flatbuffers/include", "third_party/gemmlowp", "third_party/ruy"

# Fetch FlatBuffers headers
git clone --depth 1 [https://github.com/google/flatbuffers.git](https://github.com/google/flatbuffers.git) third_party/flatbuffers_repo
Copy-Item -Recurse -Force "third_party/flatbuffers_repo/include/flatbuffers" "third_party/flatbuffers/include/"

# Fetch Gemmlowp headers
git clone --depth 1 [https://github.com/google/gemmlowp.git](https://github.com/google/gemmlowp.git) third_party/gemmlowp_repo
Copy-Item -Recurse -Force "third_party/gemmlowp_repo/fixedpoint" "third_party/gemmlowp/"
Copy-Item -Recurse -Force "third_party/gemmlowp_repo/internal" "third_party/gemmlowp/"

# Clean up temporary clones
Remove-Item -Recurse -Force "third_party/flatbuffers_repo", "third_party/gemmlowp_repo"
cd ../../..
Linux / macOS (Bash)
Bash
cd firmware/lib/tflite-micro

# Create third-party target directories
mkdir -p third_party/flatbuffers/include third_party/gemmlowp third_party/ruy

# Fetch FlatBuffers headers
git clone --depth 1 [https://github.com/google/flatbuffers.git](https://github.com/google/flatbuffers.git) third_party/flatbuffers_repo
cp -r third_party/flatbuffers_repo/include/flatbuffers third_party/flatbuffers/include/

# Fetch Gemmlowp headers
git clone --depth 1 [https://github.com/google/gemmlowp.git](https://github.com/google/gemmlowp.git) third_party/gemmlowp_repo
cp -r third_party/gemmlowp_repo/fixedpoint third_party/gemmlowp/
cp -r third_party/gemmlowp_repo/internal third_party/gemmlowp/

# Clean up temporary clones
rm -rf third_party/flatbuffers_repo third_party/gemmlowp_repo
cd ../../..
4. Machine Learning Pipeline (Python)
The ML pipeline handles model training, INT8 post-training quantization, threshold extraction, and C++ header generation (model_data.h).

Install Python dependencies:

Bash
pip install tensorflow numpy scikit-learn
Run the consolidated training and export pipeline:

Bash
python ml_pipeline/train.py
This outputs model.tflite and automatically updates firmware/include/model_data.h.

5. Building the Firmware (CMake)
Create and enter the build directory:

Bash
mkdir -p build && cd build
Generate build files with CMake:

Bash
cmake ..
Compile the binary targets:

Bash
cmake --build .
6. Running Unit Tests
To verify DSP feature extraction, ring buffer handling, and TFLm model inference on host hardware:

Bash
# Execute unit tests from inside the build directory
ctest --output-on-failure




