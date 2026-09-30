# Edge AI Predictive Maintenance Engine

A reproducible embedded AI demo that combines a bare-metal C++17 firmware target, an offline Python data/ML pipeline, and a Streamlit telemetry dashboard. The project simulates a predictive-maintenance workflow on a QEMU-emulated ARM Cortex-M platform and is intended as a technical portfolio / proof-of-concept rather than a production deployment.

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

## Dataset Attribution and Acknowledgements

This project uses the C-MAPSS Flight Data Set, provided by the NASA Prognostics Center of Excellence (PCoE).

- **Source:** NASA Ames Research Center / NASA PCoE Data Set Repository
- **Citation:** Saxena, A., Goebel, K., Simon, D., & Eklund, N. (2008). “Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation.” In *Proceedings of the 1st International Conference on Prognostics and Health Management (PHM 2008)*.
- **License/access:** Public domain / Open NASA Data (U.S. Government work)

> **Disclaimer:** This repository is an independent open-source software project created solely for educational and portfolio demonstration purposes. It is not officially endorsed by, affiliated with, or maintained by NASA or any other organization referenced in the dataset materials.

## AI Transparency & Architectural Ownership Disclaimer

This repository was developed with limited AI assistance for implementation acceleration and drafting support. The overall architecture, embedded-system constraints, model strategy, and validation approach were defined and reviewed by the project author.

### Human-Led Engineering Decisions

The project author was responsible for the core technical direction, including:

- defining the bare-metal C++17 execution model;
- establishing the no-dynamic-allocation constraint (`malloc`/`new`);
- sizing the static Tensor Arena memory budget;
- validating Cortex-M behavior under QEMU;
- designing the telemetry serialization format and checksum framing;
- selecting the DSP feature set and anomaly-detection approach;
- managing the build, cross-compilation, Docker, and CI setup.

### AI-Assisted Implementation Support

AI coding tools were used primarily to speed up repetitive and mechanical tasks under human supervision. Examples of supported work include:

- C++ class and template scaffolding;
- CMake target and build-file boilerplate;
- Python data-processing and telemetry-parsing loops;
- Streamlit UI scaffolding and documentation drafting;
- shell, Docker, and QEMU command generation for local development workflows.

### Review and Accountability

All substantive algorithms, protocol definitions, model quantization steps, and build configuration changes were reviewed and approved by the project author before inclusion. AI assistance was used as a productivity aid, not as an autonomous decision-maker for the project’s technical direction.
