# Quick Start Build Guide

This is the shortest path to getting the project built and running locally.

## 1. Requirements

Install:

- Git
- CMake 3.15+
- C++17 compiler
- Python 3.9+
- `pip`
- Optional for ARM builds: `arm-none-eabi-gcc`, `objcopy`, `objdump`, and `size`

## 2. Clone the repository

```bash
git clone --recursive <repository-url>
cd Machine-Learning
```

If you already cloned without `--recursive`:

```bash
git submodule update --init --recursive
```

## 3. Prepare TensorFlow Lite Micro dependencies

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

## 4. Install Python dependencies and train the model

```bash
pip install tensorflow numpy scikit-learn
python ml_pipeline/train.py
```

This generates the model artifact and updates `firmware/include/model_data.h`.

## 5. Build host tests

```bash
cmake -B build/host -S .
cmake --build build/host
ctest --test-dir build/host --output-on-failure
```

## 6. Build ARM firmware

```bash
cmake -B build/arm -S . -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake
cmake --build build/arm
```

## 7. Troubleshooting

- If you see missing TensorFlow Lite headers, ensure the TensorFlow Lite Micro source and third-party dependencies are present.
- If CMake fails during configuration, verify all source files listed in `add_library()` or `add_executable()` exist.
- If the ARM build fails, confirm the `arm-none-eabi-*` tools are installed and in `$PATH`.

For the full step-by-step developer version, see `DETAILED_BUILD_GUIDE.md`.
