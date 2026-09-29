# Build and Setup Guide

This guide explains how to set up the project, install required dependencies, run the ML training/export pipeline, build the C++ firmware for host and ARM targets, and execute the test suite.

---

## 1. System Requirements

Before building, make sure the following tools are available:

- Git (v2.25 or newer)
- CMake (v3.15 or newer)
- A C++17 compiler:
  - Linux: `gcc` / `g++`
  - macOS: Apple Clang / Xcode Command Line Tools
  - Windows: MSYS2 MinGW-w64 or Visual Studio 2019+
- Python 3.9+
- `pip`
- Optional for ARM builds: `arm-none-eabi-gcc` toolchain and related utilities (`objcopy`, `objdump`, `size`)
- Network access for first-time dependency fetches, including GoogleTest and external third-party headers

---

## 2. Clone the Repository

Because this project includes TensorFlow Lite Micro submodules and third-party dependencies, clone the repository recursively.

### Option A: Recursive clone (recommended)

```bash
git clone --recursive <repository-url>
cd Machine-Learning
```

### Option B: If already cloned without `--recursive`

```bash
git submodule update --init --recursive
```

---

## 3. Prepare TensorFlow Lite Micro Dependencies

The project uses TensorFlow Lite Micro plus third-party support libraries. These dependencies must be available under `firmware/lib/tflite-micro/third_party`.

### Linux / macOS

```bash
cd firmware/lib/tflite-micro

mkdir -p third_party/flatbuffers/include third_party/gemmlowp third_party/ruy

git clone --depth 1 https://github.com/google/flatbuffers.git third_party/flatbuffers_repo
cp -r third_party/flatbuffers_repo/include/flatbuffers third_party/flatbuffers/include/

git clone --depth 1 https://github.com/google/gemmlowp.git third_party/gemmlowp_repo
cp -r third_party/gemmlowp_repo/fixedpoint third_party/gemmlowp/
cp -r third_party/gemmlowp_repo/internal third_party/gemmlowp/

rm -rf third_party/flatbuffers_repo third_party/gemmlowp_repo

cd ../../..
```

### Windows (PowerShell)

```powershell
cd firmware/lib/tflite-micro

New-Item -ItemType Directory -Force -Path "third_party/flatbuffers/include", "third_party/gemmlowp", "third_party/ruy"

git clone --depth 1 https://github.com/google/flatbuffers.git third_party/flatbuffers_repo
Copy-Item -Recurse -Force "third_party/flatbuffers_repo/include/flatbuffers" "third_party/flatbuffers/include/"

git clone --depth 1 https://github.com/google/gemmlowp.git third_party/gemmlowp_repo
Copy-Item -Recurse -Force "third_party/gemmlowp_repo/fixedpoint" "third_party/gemmlowp/"
Copy-Item -Recurse -Force "third_party/gemmlowp_repo/internal" "third_party/gemmlowp/"

Remove-Item -Recurse -Force "third_party/flatbuffers_repo", "third_party/gemmlowp_repo"

cd ../../..
```

---

## 4. Install Python Dependencies

Install the required Python packages for training and model export:

```bash
pip install tensorflow numpy scikit-learn
```

Then run the ML pipeline:

```bash
python ml_pipeline/train.py
```

This generates the model artifact and updates `firmware/include/model_data.h` with the embedded model data.

---

## 5. Build the Project with CMake

The project supports two build workflows:

- Host build for native unit tests
- ARM cross-build for bare-metal firmware

Use separate build directories for each workflow.

### 5.1 Host Build (Native Unit Tests)

Configure the host build:

```bash
cmake -B build/host -S .
```

Build the targets:

```bash
cmake --build build/host
```

Run the tests:

```bash
ctest --test-dir build/host --output-on-failure
```

This workflow compiles the core library and the GoogleTest-based unit test target.

### 5.2 ARM Cross-Compilation

Configure the ARM build using the toolchain file:

```bash
cmake -B build/arm -S . -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake
```

Build the bare-metal firmware:

```bash
cmake --build build/arm
```

After the build finishes, `arm-none-eabi-size` prints the resulting SRAM/Flash memory usage.

---

## 6. Run Unit Tests

To validate DSP feature extraction, ring buffer behavior, and host-side inference logic:

```bash
cd build/host
ctest --output-on-failure
```

---

## 7. CMake Build Notes and Constraints

### Host-only unit tests

GoogleTest targets are disabled during ARM cross-compilation when `CMAKE_CROSSCOMPILING` is enabled. Bare-metal targets generally cannot run host-based unit tests.

### Missing source files

CMake requires every file listed in `add_library()` or `add_executable()` to exist on disk before configuration succeeds.

### Compiler-check safety

The ARM toolchain file sets `CMAKE_TRY_COMPILE_TARGET_TYPE` to `STATIC_LIBRARY` to avoid failures during the initial compiler check when bare-metal memory constraints are not available in the host environment.

---

## 8. Customizing the CMake Setup

### Change hardware / CPU flags

File: `cmake/arm-none-eabi.cmake`

Update `ARM_FLAGS` for the target CPU and ABI:

```cmake
set(ARM_FLAGS "-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard")
```

### Add new C++ source files

File: `firmware/CMakeLists.txt`

Append the implementation paths to the `add_library(firmware_core STATIC ...)` block:

```cmake
add_library(firmware_core STATIC
    src/core/ring_buffer.cpp
    src/core/dsp_features.cpp
    src/core/new_module.cpp
)
```

### Add a new unit test suite

File: `tests/CMakeLists.txt`

Add the new test file to the `add_executable(unit_tests ...)` command:

```cmake
add_executable(unit_tests
    unit/test_ring_buffer.cpp
    unit/test_new_module.cpp
)
```

### Pin or update GoogleTest version

File: `tests/CMakeLists.txt`

Modify the `FetchContent_Declare` entry:

```cmake
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.15.0
)
```

---

## 9. Summary

To build and validate the project successfully:

1. Clone the repo recursively.
2. Populate the TensorFlow Lite Micro third-party dependencies.
3. Install Python dependencies.
4. Run the ML pipeline to generate the embedded model data.
5. Configure and build the host or ARM target with CMake.
6. Run CTest for verification.

This workflow keeps host development, ARM firmware compilation, and ML model generation separate while maintaining a consistent build flow.
