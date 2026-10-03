# Edge AI Predictive Maintenance Engine

A developer-oriented demonstration of a C++17 firmware inference loop built for
an ARM Cortex-M3 QEMU machine, with a Python model-training pipeline and a
Streamlit telemetry dashboard. The end-to-end run is intentionally simulated
for convenient development and review; it does not connect to physical sensors
or control real equipment.

## What is included

- CMake host and ARM cross-compilation targets, a Clang ARM toolchain, and a
  single-stage Docker development image containing the compiler and QEMU.
- A fixed-capacity C++ ring buffer, RMS/peak-to-peak/kurtosis feature
  extraction, and TensorFlow Lite Micro inference using a static tensor arena.
- A Python pipeline that prepares FD001 training data, trains a small
  autoencoder, converts it to INT8 TFLite, and exports the model and calibrated
  thresholds to `firmware/include/ml/model_data.h`.
- A Streamlit dashboard and a UART text-line parser for the simulator's status
  output.

The simulated firmware cycles through ten hard-coded rows representing five
FD001 sensor channels. It does not ingest the dataset at runtime. UART telemetry
is newline-delimited human-readable text; this repository does not implement a
binary frame format, checksum, or `0xDEADBEEF` synchronization marker.

## Requirements

- Git (including submodule support)
- Python 3.10+ and `pip`
- CMake 3.15+ and a C++17 compiler for host tests
- Docker with the Compose plugin for the ARM/QEMU demo
- Windows PowerShell for the provided `scripts/run_qemu.ps1` helper

The repository includes `dashboard/requirements.txt` for dashboard packages;
there is no root `requirements.txt`. Install the ML pipeline's additional
packages separately.

## Setup and run

Clone with the TensorFlow Lite Micro submodule:

```bash
git clone --recursive <repository-url>
cd Edge-AI-Predictive-Maintenance-Engine
```

If the repository is already cloned:

```bash
git submodule update --init --recursive
```

Create an environment and install dependencies:

```bash
python -m venv .venv
# Activate .venv using the command for your shell.
python -m pip install -r dashboard/requirements.txt
python -m pip install tensorflow scipy scikit-learn
```

Download the NASA C-MAPSS FD001 archive and extract **`train_FD001.txt`** into
`ml_pipeline/data/`. The preparation script uses that file only; the
`test_FD001.txt` and `RUL_FD001.txt` files are not currently consumed.

```bash
python ml_pipeline/prepare_data.py
python ml_pipeline/train.py
```

Training splits by engine unit, fits normalization on healthy training units,
calibrates warning/critical thresholds on separate healthy units, and prints
false-positive and anomaly-recall rates for held-out units. These are
experimental dataset results, not evidence of operational performance.
Training writes `ml_pipeline/model.tflite` and updates
`firmware/include/ml/model_data.h`.

### Host build and tests

```bash
cmake -B build/host -S .
cmake --build build/host
ctest --test-dir build/host --output-on-failure
python -m unittest discover -s tests/python -v
```

The C++ tests cover DSP features and ring-buffer behavior. Python tests cover
INT8 conversion (when TensorFlow dependencies are installed), UART parsing, and
dashboard telemetry handling. GoogleTest is fetched by CMake, so host
configuration needs network access if it is not already cached.

### ARM/QEMU demo

Build the cross-compiled firmware in Docker:

```powershell
docker compose build
docker compose run --rm dev-environment cmake -S . -B build/clang-cmake -DCMAKE_TOOLCHAIN_FILE=cmake/clang-arm-none-eabi.cmake
docker compose run --rm dev-environment cmake --build build/clang-cmake --parallel 4
```

On Windows with Docker Desktop, launch the dashboard after building:

```powershell
python -m streamlit run dashboard/app.py
```

The dashboard attempts to start the QEMU simulator through Docker and connect
to its UART socket. Alternatively, use `scripts/run_qemu.ps1` to start QEMU and
run `python dashboard/uart_bridge.py socket://127.0.0.1:5555` in a second
terminal to print parsed UART events.

## Scope and limitations

- QEMU supplies a convenient simulated target; the firmware input is a
  repeating in-memory sample window rather than live or streamed sensor data.
- The model is trained on C-MAPSS FD001 training trajectories. The pipeline
  does not evaluate the official FD001 test set or its RUL targets.
- The held-out evaluation is a basic anomaly-detection check with healthy
  calibration thresholds. It is not a comprehensive model benchmark.
- CI currently provides limited host/format checks. It does not establish
  successful ARM builds, dashboard behavior, model quality, or hardware
  validation; the formatting workflow is non-blocking.

## Dataset citation

This project uses the C-MAPSS Flight Data Set from NASA's Prognostics Center of
Excellence. See the included `ml_pipeline/readme.txt` and the associated
publication: A. Saxena, K. Goebel, D. Simon, and N. Eklund, “Damage Propagation
Modeling for Aircraft Engine Run-to-Failure Simulation,” PHM 2008.

This independent educational project is not endorsed by or affiliated with
NASA.
