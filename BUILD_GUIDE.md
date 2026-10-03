# Quick Start Build Guide

This guide builds and runs the project's simulated ARM/QEMU demo. It does not
set up physical sensor hardware.

## Requirements

- Git with submodule support
- Python 3.9+ and `pip`
- CMake 3.15+ and a C++17 compiler for host tests
- Docker with Compose for ARM cross-compilation and QEMU
- Windows PowerShell for `scripts/run_qemu.ps1`

## Clone and initialize dependencies

```bash
git clone --recursive <repository-url>
cd Edge-AI-Predictive-Maintenance-Engine
```

For an existing clone:

```bash
git submodule update --init --recursive
```

The TensorFlow Lite Micro source is provided as a Git submodule.
`Dockerfile` installs the additional FlatBuffers and Ruy revisions needed for
the ARM build; do not manually copy dependencies into the submodule.

## Install Python packages and prepare the model

There is no root `requirements.txt`. Install the dashboard dependencies and
the additional model-training packages:

```bash
python -m venv .venv
# Activate .venv using the command for your shell.
python -m pip install -r dashboard/requirements.txt
python -m pip install tensorflow scipy scikit-learn
```

Download the NASA C-MAPSS FD001 archive and extract `train_FD001.txt` into
`ml_pipeline/data/`. The current preparation script uses this training file
only; it does not read `test_FD001.txt` or `RUL_FD001.txt`.

```bash
python ml_pipeline/prepare_data.py
python ml_pipeline/train.py
```

The training script splits by engine unit, calibrates on healthy units, and
prints held-out healthy false-positive rates and anomaly recall. These metrics
are a basic experiment, not an operational guarantee. The pipeline writes
`ml_pipeline/model.tflite` and `firmware/include/ml/model_data.h`.

## Build and run host tests

```bash
cmake -B build/host -S .
cmake --build build/host
ctest --test-dir build/host --output-on-failure
python -m unittest discover -s tests/python -v
```

The Python INT8 conversion test requires TensorFlow and skips when the ML
dependencies are unavailable. CMake fetches GoogleTest for the native C++ test
target.

## Build ARM firmware

Run from a PowerShell terminal at the repository root:

```powershell
docker compose build
docker compose run --rm dev-environment cmake -S . -B build/clang-cmake -DCMAKE_TOOLCHAIN_FILE=cmake/clang-arm-none-eabi.cmake
docker compose run --rm dev-environment cmake --build build/clang-cmake --parallel 4
```

The output is `build/clang-cmake/firmware/firmware_app.elf`.

## Run the simulated demo

The Streamlit dashboard attempts to start Docker Desktop/QEMU and connect to
the UART socket:

```powershell
python -m streamlit run dashboard/app.py
```

For a manual simulator/bridge run, start the firmware with the included QEMU
script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_qemu.ps1
```

Then, in another terminal, connect the command-line UART bridge:

```powershell
python dashboard/uart_bridge.py socket://127.0.0.1:5555
```

Firmware telemetry is newline-delimited text. The demo repeatedly processes
hard-coded FD001-like sample values; it does not ingest live sensor data.

## CI and validation scope

Local tests cover DSP, ring-buffer, conversion, UART parsing, and dashboard
telemetry helpers. Current CI does not validate ML metrics, dashboard
rendering, ARM/QEMU execution, or physical hardware. The formatting workflow
does not fail the job when formatting differs.

For more detail, see `DETAILED_BUILD_GUIDE.md`.
