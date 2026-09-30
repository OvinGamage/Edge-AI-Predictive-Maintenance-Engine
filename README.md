# Edge AI Predictive Maintenance Engine

A self-directed embedded AI proof-of-concept that combines a bare-metal C++17 firmware target, an offline Python data/ML pipeline, and a Streamlit telemetry dashboard. The project simulates a predictive-maintenance workflow on a QEMU-emulated ARM Cortex-M platform. It was built independently as a skills demonstration and is not intended to represent a production-ready system.

## Project Architecture and Tooling

The repository includes the build and runtime pieces needed to reproduce the demo environment, including:

- CMake toolchains
- Cross-compilers
- QEMU ARM simulation
- Multi-stage Docker containers

The core technical focus is the low-level bare-metal C++17 firmware and the edge ML pipeline that produces the model artifacts used by the firmware.

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

After cloning the repository, install the required dependencies and run the data preparation and training pipeline:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Extract DSP rolling-window features
# (RMS, peak-to-peak, and kurtosis)
python ml_pipeline/prepare_data.py

# Train the model and export the INT8-quantized TFLite engine
python ml_pipeline/train.py
```

The anomaly-detection thresholds used by the firmware (`THRESHOLD_WARN` / `THRESHOLD_CRIT`) are set manually based on the reconstruction-error distribution observed during training. They are not learned automatically and are not recalibrated at runtime.

## Telemetry Dashboard

The `dashboard/` directory contains a Streamlit application that connects to the firmware's UART output (directly over serial, or via a TCP socket when running in QEMU) and displays incoming inference events as they arrive. It is a visualization tool for locally observing firmware output during development, not a hardened or continuously monitored production telemetry service. There is no buffering, retry, or backpressure handling beyond what Streamlit and pyserial provide out of the box.

## Testing

The `tests/` directory contains a small set of host-side unit tests (GoogleTest) covering the ring buffer and DSP feature extraction logic in `firmware_core`. These tests run on the host machine and are skipped entirely when cross-compiling for the ARM target (see `tests/CMakeLists.txt`). They validate specific algorithmic building blocks, not full firmware behavior, end-to-end inference, or QEMU runtime integration. CI additionally runs a `clang-format` check against the firmware source.

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
- validating Cortex-M behavior under QEMU;
- designing the telemetry serialization format and checksum framing;
- selecting the DSP feature set and manually setting the anomaly-detection thresholds;
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
