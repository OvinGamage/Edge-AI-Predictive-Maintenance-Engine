# Edge AI Predictive Maintenance Engine

A prototype repository containing a bare-metal C++17 firmware target, Python scripts for preparing C-MAPSS features and exporting a model, and a Streamlit UART viewer. The firmware demo repeatedly processes a fixed set of ten sensor rows; it does not read live sensors or simulate a degradation trajectory. The repository is an educational proof of concept, not a demonstrated end-to-end predictive-maintenance product or a production-ready system.

## Project Architecture and Tooling

The repository contains configuration and scripts for an intended demo environment, including:

- CMake cross-compilation toolchain files
- A Dockerfile that declares Linux ARM cross-compilation and QEMU tools
- A PowerShell QEMU launch script and Python UART bridge

These files do not by themselves establish that the full QEMU and model-export workflow works on every host. Native host tests cover only selected C++ components; the ARM build requires the TensorFlow Lite Micro submodule and its dependencies.

## System Architecture

| Component | Technology |
| --- | --- |
| Firmware | C++17, bare-metal ARM Cortex-M, QEMU |
| ML inference | TensorFlow Lite for Microcontrollers (TFLM) |
| Data and dashboard | Python, Streamlit, Polars/Pandas |

## Dataset Setup

This project uses the NASA C-MAPSS (Commercial Modular Aero-Propulsion System Simulation) Flight Data Set, specifically the FD001 subset. Because of repository size constraints, the raw data files are not included in the repository.

### 1. Download the dataset

Download the dataset archive from the NASA Data Portal.

### 2. Extract the data

Extract the following files into `ml_pipeline/data/`:

```text
ml_pipeline/data/
├── train_FD001.txt
├── test_FD001.txt
└── RUL_FD001.txt
```

## Quick Start

The Python scripts require the NASA FD001 training file described above. There is no repository-level `requirements.txt`; install the dependencies used by the scripts, then run:

```bash
# Install Python dependencies
python -m pip install numpy pandas scipy tensorflow scikit-learn

# Extract DSP rolling-window features
# (RMS, peak-to-peak, and kurtosis)
python ml_pipeline/prepare_data.py

# Train the model and export an INT8 TFLite model and C++ header
python ml_pipeline/train.py
```

The preparation script derives RMS, peak-to-peak, and kurtosis features from five sensor channels over ten-cycle windows. The training script fits a small autoencoder to samples labeled healthy, converts it to INT8 TFLite, calculates warning and critical thresholds from healthy calibration reconstruction errors, and writes those values into a generated C++ header. Thresholds are fixed in the firmware image; they are not updated or learned at runtime. This workflow does not establish model accuracy or suitability for real equipment.

The firmware itself uses a compiled table containing the first ten FD001 rows for channels s_2, s_3, s_4, s_11, and s_12, then repeats those rows. This is deterministic test input, not live acquisition, a realistic engine simulation, or evidence of predictive performance.

## Telemetry Dashboard

The `dashboard/` directory contains a Streamlit application and UART bridge for viewing received firmware messages over serial or a TCP socket. This is a local development visualization tool, not a hardened or continuously monitored telemetry service. It has no application-level buffering, retry, or backpressure handling.

## Testing

The host-side GoogleTest suite covers ring-buffer behavior and DSP feature extraction. It does not test model inference, UART hardware access, the Python pipeline, firmware startup, or QEMU integration. A native build deliberately omits the bare-metal executable and TFLite Micro model runner so tests can run without an ARM toolchain or initialized submodule. Cross-compiling disables the host tests.

Run the same native configure, build, and test sequence used by CI from the repository root:

```bash
cmake -B build/host -S . -DCMAKE_BUILD_TYPE=Debug
cmake --build build/host --parallel 4
ctest --test-dir build/host --output-on-failure
```

GoogleTest is fetched by CMake on the first configure, so network access may be needed. The CI workflow runs these host tests; it does not validate the ARM firmware, generated model, dashboard, or QEMU runtime.

## Dataset Attribution and Acknowledgements

This project uses the C-MAPSS Flight Data Set, provided by the NASA Prognostics Center of Excellence (PCoE).

- **Source:** NASA Ames Research Center / NASA PCoE Data Set Repository
- **Citation:** Saxena, A., Goebel, K., Simon, D., & Eklund, N. (2008). “Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation.” In *Proceedings of the 1st International Conference on Prognostics and Health Management (PHM 2008)*.
- **License/access:** Public domain / Open NASA Data (U.S. Government work)

> **Disclaimer:** This repository is an independent open-source software project created solely for educational and portfolio demonstration purposes. It is not officially endorsed by, affiliated with, or maintained by NASA or any other organization referenced in the dataset materials.

## About This Project

This repository was built independently by a self-taught developer as a demonstration of applied skills across embedded systems, machine learning deployment, and software tooling. The author has no formal degree in the field; background includes self-study and Coursera certificate coursework. The project is scoped as a proof of concept, and no claim is made that it reflects production-hardened engineering practice — reaching that bar would require a real production environment, real operating constraints, and real-world validation that a solo, self-directed project cannot fully replicate.

## AI Transparency & Architectural Ownership Disclaimer

This repository was developed with limited AI assistance for implementation acceleration and drafting support. The overall architecture, embedded-system constraints, model strategy, and validation approach were defined and reviewed by the project author.

### Human-Led Engineering Decisions

The project author was responsible for the core technical direction, including:

- defining the bare-metal C++17 execution model;
- establishing the no-dynamic-allocation constraint (`malloc`/`new`);
- sizing the static Tensor Arena memory budget;
- documenting an intended Cortex-M/QEMU development workflow;
- choosing line-oriented UART messages (the current messages do not include checksum framing);
- selecting the DSP feature set and the reconstruction-error threshold percentiles;
- managing the build, cross-compilation, Docker, and CI setup.

### AI-Assisted Implementation Support

AI coding tools were used primarily to speed up repetitive and mechanical tasks under human supervision. Examples of supported work include:

- C++ class and template scaffolding;
- CMake target and build-file boilerplate;
- Python data-processing and telemetry-parsing loops;
- Streamlit UI scaffolding and documentation drafting;
- shell, Docker, and QEMU command generation for local development workflows.

### Review and Accountability

All substantive algorithms, protocol definitions, model quantization steps, and build configuration changes were reviewed and approved by the project author before inclusion. AI assistance was used as a productivity aid, not as an autonomous decision-maker for the project's technical direction.
