# Detailed Build Guide

This guide covers the full setup and build flow for the Machine-Learning project, including dependency setup, model generation, host builds, ARM cross-compilation, and test execution.

---

## 1. System Requirements

Before beginning, make sure the host machine has:
- Git 2.25+
- CMake 3.15+
- Docker Desktop with the Linux engine enabled
- Python 3.9+ and `pip`
- Network access to fetch the Docker image and Python dependencies


## 2. Clone the Repository

Use a recursive clone so the TensorFlow Lite Micro submodule is fetched automatically:

```bash
git clone --recursive <repository-url>
cd Machine-Learning
```

If the repository was cloned without submodules:

```bash
git submodule update --init --recursive
```

---

## 3. TensorFlow Lite Micro Dependencies

The ARM Docker image fetches the FlatBuffers and Ruy revisions required by the
checked-out TensorFlow Lite Micro source. Do not manually copy dependencies into
`firmware/lib/tflite-micro`; keep that submodule unchanged.

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

## 6. ARM Build: Clang Cross-Compilation

Build the Docker image, then configure and build the bare-metal target through CMake:

```powershell
docker compose build
docker compose run --rm dev-environment cmake -S . -B build/clang-cmake -DCMAKE_TOOLCHAIN_FILE=cmake/clang-arm-none-eabi.cmake
docker compose run --rm dev-environment cmake --build build/clang-cmake --parallel 4
```

The generated firmware ELF is `build/clang-cmake/firmware/firmware_app.elf`.

---

## 7. Run in QEMU

In one PowerShell terminal, launch the containerized MPS2-AN385 emulator:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_qemu.ps1
```

In another terminal, connect the telemetry bridge:

```powershell
python dashboard/uart_bridge.py socket://127.0.0.1:5555
```

## 8. Running the Tests

From the host build directory:

```bash
cd build/host
ctest --output-on-failure
```
This validates DSP features, ring-buffer behavior, and host-side inference logic.

---

## 9. Build Notes and Constraints

### Host-only unit tests

GoogleTest executables are disabled when `CMAKE_CROSSCOMPILING` is active. Bare-metal builds generally cannot run host test binaries.

### Missing source files

CMake requires every file included in `add_library()` or `add_executable()` to exist before configuration succeeds.

### Compiler safety check

The ARM toolchain file sets `CMAKE_TRY_COMPILE_TARGET_TYPE` to `STATIC_LIBRARY` so CMake can validate the compiler without needing a full bare-metal link step.

---

## 10. Customizing the Build Setup

### Change CPU and hardware flags

File: `cmake/clang-arm-none-eabi.cmake`

```cmake
set(ARM_CLANG_FLAGS "-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard")
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

## 11. Common Troubleshooting

### Missing TensorFlow Lite headers

Verify that the TensorFlow Lite Micro source and third-party headers are present and that your include paths are configured correctly.

### Build fails during CMake configure

Check for missing source files and confirm the repository was cloned with submodules initialized.

### ARM build fails

Check that Docker Desktop is running and the image contains Clang/LLD.

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
