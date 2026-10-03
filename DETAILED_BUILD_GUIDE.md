# Detailed Build Guide

This guide describes how to prepare the FD001-based model, run host tests, and
build/run the intentionally simulated ARM/QEMU demonstration. It does not
describe deployment to physical equipment.

## 1. Requirements

- Git with submodule support
- CMake 3.15+ and a C++17 compiler for native tests
- Python 3.10+ and `pip`
- Docker with the Compose plugin for ARM cross-compilation and QEMU
- Docker Desktop and Windows PowerShell for the provided QEMU script and
  dashboard-managed simulator startup
- Network access for the TFLite Micro submodule, Python packages, GoogleTest,
  and Docker image dependencies

## 2. Clone and initialize the submodule

```bash
git clone --recursive <repository-url>
cd Edge-AI-Predictive-Maintenance-Engine
```

If already cloned:

```bash
git submodule update --init --recursive
```

`firmware/lib/tflite-micro` is a Git submodule. The Docker image installs
additional FlatBuffers and Ruy source dependencies for the ARM build.

## 3. Python dependencies and data

The repository has no root `requirements.txt`. Create and activate a virtual
environment, then install dashboard packages and ML packages:

```bash
python -m venv .venv
# Activate .venv using the command for your shell.
python -m pip install -r dashboard/requirements.txt
python -m pip install tensorflow scipy scikit-learn
```

Download the NASA C-MAPSS archive for FD001 and extract `train_FD001.txt` to
`ml_pipeline/data/`. The current preparation step reads only that file. The
documented `test_FD001.txt` and `RUL_FD001.txt` files are not used by the
pipeline.

```bash
python ml_pipeline/prepare_data.py
python ml_pipeline/train.py
```

Preparation creates rolling windows independently per engine and extracts
RMS, peak-to-peak, and kurtosis features. Training splits complete engine
units into training, calibration, and holdout partitions; fits the scaler on
healthy training rows only; calibrates warning and critical thresholds using
healthy calibration rows; and prints healthy false-positive rates and anomaly
recall on held-out units. This is a basic anomaly-detection evaluation, not
RUL scoring or a comprehensive validation. The generated artifacts are
`ml_pipeline/model.tflite` and `firmware/include/ml/model_data.h`.

## 4. Native host build and tests

Build and run the existing C++ tests:

```bash
cmake -B build/host -S .
cmake --build build/host
ctest --test-dir build/host --output-on-failure
```

Run the Python tests:

```bash
python -m unittest discover -s tests/python -v
```

The C++ tests cover DSP feature extraction and ring-buffer behavior. Python
tests cover the TFLite INT8 conversion and evaluation helper, UART line
parsing, and dashboard telemetry conversion/retention/health selection. The
ML test module requires TensorFlow, NumPy, Pandas, and scikit-learn; it is
skipped if these imports are unavailable. Host CMake configuration fetches
GoogleTest through `FetchContent`.

## 5. ARM cross-compilation

Build from PowerShell at the repository root:

```powershell
docker compose build
docker compose run --rm dev-environment cmake -S . -B build/clang-cmake -DCMAKE_TOOLCHAIN_FILE=cmake/clang-arm-none-eabi.cmake
docker compose run --rm dev-environment cmake --build build/clang-cmake --parallel 4
```

The configured target is Cortex-M3 and the ELF is
`build/clang-cmake/firmware/firmware_app.elf`. The Dockerfile is a single-stage
Ubuntu-based development image; it installs Clang/LLD, the ARM runtime, and
QEMU.

## 6. Run the QEMU/UART demonstration

The sample firmware cycles over ten fixed rows for five FD001 sensor channels,
computes a 50-sample feature window, runs the embedded model, and writes
human-readable status lines to UART. It does not load dataset files or read
physical sensor peripherals.

Start the dashboard after building the ELF:

```powershell
python -m streamlit run dashboard/app.py
```

The dashboard tries to start Docker Desktop/QEMU and connect to
`socket://127.0.0.1:5555`. Alternatively, start QEMU manually:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_qemu.ps1
```

Then use the CLI bridge in a second terminal:

```powershell
python dashboard/uart_bridge.py socket://127.0.0.1:5555
```

The UART format is newline-delimited text. The bridge classifies the status
prefix and extracts an optional `MSE:` value; it is not a binary framed
protocol.

## 7. Validation limitations

- The pipeline does not use the official FD001 test trajectories or RUL labels.
- Held-out engine metrics characterize only this dataset split and training
  run; they do not establish real-world failure prediction performance.
- Python tests exercise conversion and dashboard telemetry helpers, not a
  complete Streamlit browser session or Docker/QEMU integration.
- CI does not currently run the Python tests or validate ARM/QEMU behavior.
- The formatting workflow uses `|| true`, so formatting differences do not
  fail CI.

## 8. Troubleshooting

- If CMake cannot find TFLite Micro headers, initialize the submodule.
- If host configuration cannot fetch GoogleTest, check network access or retry
  after connectivity is restored.
- If the ARM build cannot find FlatBuffers or Ruy, rebuild the Docker image.
- If the dashboard reports that the firmware ELF is missing, complete the ARM
  build first.
- If the UART bridge cannot connect, verify that QEMU is running and that both
  the simulator and bridge use port `5555`.

See `BUILD_GUIDE.md` for the shorter workflow.
