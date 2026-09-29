# Detailed Build Guide

This guide covers the full setup and build flow for the Machine-Learning project, including dependency setup, model generation, host builds, ARM cross-compilation, and test execution.

---

## 1. System Requirements

Before beginning, make sure the host machine has:

- Git 2.25+
- CMake 3.15+
- A C++17 compiler
  - Linux: `gcc` / `g++`
  - macOS: Xcode Command Line Tools
  - Windows: MSYS2 MinGW-w64 or Visual Studio 2019+
- Python 3.9+
- `pip`
- Network access for fetching external dependencies and GoogleTest on first configuration
- ARM toolchain for cross-builds:
  - `arm-none-eabi-gcc`
  - `arm-none-eabi-g++`
  - `objcopy`
  - `objdump`
  - `size`

---

## 2. Clone the Repository

Use a recursive clone so submodules are fetched automatically:

```bash
git clone --recursive <repository-url>
cd Machine-Learning
```

If the repository was cloned without submodules:

```bash
git submodule update --init --recursive
```

---

## 3. Prepare TensorFlow Lite Micro Dependencies

The firmware relies on TensorFlow Lite Micro components and supporting headers from third-party libraries. These must be populated before building.

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

Install the packages required for training and export:

```bash
pip install tensorflow numpy scikit-learn
```

Then run the ML pipeline:

```bash
python ml_pipeline/train.py
```

This step creates the model artifact and updates the generated C++ header used by the firmware, including `firmware/include/model_data.h`.

---

## 5. Host Build: Native Unit Tests

Use a separate build directory for host builds to avoid mixing artifacts.

```bash
cmake -B build/host -S .
cmake --build build/host
ctest --test-dir build/host --output-on-failure
```

This workflow builds the host library and the GoogleTest-based unit tests.

---

## 6. ARM Build: Cross-Compilation

To build the bare-metal target, configure CMake with the ARM toolchain file:

```bash
cmake -B build/arm -S . -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake
cmake --build build/arm
```

After the build completes, `arm-none-eabi-size` prints the final memory footprint for the firmware image.

---

## 7. Running the Tests

From the host build directory:

```bash
cd build/host
ctest --output-on-failure
```

This validates DSP features, ring-buffer behavior, and host-side inference logic.

---

## 8. Build Notes and Constraints

### Host-only unit tests

GoogleTest executables are disabled when `CMAKE_CROSSCOMPILING` is active. Bare-metal builds generally cannot run host test binaries.

### Missing source files

CMake requires every file included in `add_library()` or `add_executable()` to exist before configuration succeeds.

### Compiler safety check

The ARM toolchain file sets `CMAKE_TRY_COMPILE_TARGET_TYPE` to `STATIC_LIBRARY` so CMake can validate the compiler without needing a full bare-metal link step.

---

## 9. Customizing the Build Setup

### Change CPU and hardware flags

File: `cmake/arm-none-eabi.cmake`

```cmake
set(ARM_FLAGS "-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard")
```

### Add new C++ sources

File: `firmware/CMakeLists.txt`

```cmake
add_library(firmware_core STATIC
    src/core/ring_buffer.cpp
    src/core/dsp_features.cpp
    src/core/new_module.cpp
)
```

### Add a new unit test

File: `tests/CMakeLists.txt`

```cmake
add_executable(unit_tests
    unit/test_ring_buffer.cpp
    unit/test_new_module.cpp
)
```

### Pin the GoogleTest version

```cmake
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.15.0
)
```

---

## 10. Common Troubleshooting

### Missing TensorFlow Lite headers

Verify that the TensorFlow Lite Micro source and third-party headers are present and that your include paths are configured correctly.

### Build fails during CMake configure

Check for missing source files and confirm the repository was cloned with submodules initialized.

### ARM build fails

Check the toolchain installation and confirm the ARM binaries are on `PATH`.

---

## 11. Summary

To build this project successfully:

1. Clone the repo recursively.
2. Populate TensorFlow Lite Micro dependencies.
3. Install Python packages.
4. Run the ML pipeline to generate model data.
5. Build the host target and run tests.
6. Build the ARM target using the cross-toolchain.

This is the full developer workflow for building and validating the project end-to-end.
