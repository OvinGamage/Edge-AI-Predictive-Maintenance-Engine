# Edge AI Predictive Maintenance Engine

An end-to-end bare-metal C++ edge inference engine running on a QEMU-simulated ARM Cortex-M architecture, with real-time Python telemetry analytics.

## Project Architecture and Tooling

The project is designed to be reproducible and isolated. The complete build ecosystem is pre-configured, including:

- CMake toolchains
- Cross-compilers
- QEMU ARM simulation
- Multi-stage Docker containers

The build infrastructure and containerization are provided for reviewer and user convenience. The core technical focus of this repository is the low-level bare-metal C++17 firmware and its edge machine learning pipeline.

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

This repository was developed using a systems-architect-led workflow with AI assistance used primarily for implementation acceleration and boilerplate generation. The underlying architecture, constraints, and validation strategy were defined and reviewed by the project author.

### Architectural Ownership and Strategic Engineering

The developer was responsible for the core engineering direction, including:

- defining bare-metal C++17 execution constraints;
- establishing zero-dynamic-allocation boundaries (`malloc`/`new`);
- sizing static Tensor Arena memory budgets;
- validating ARM Cortex-M behavior through QEMU simulation;
- designing the binary serialization contract, including memory-aligned telemetry structs, additive checksum checks, and frame synchronization using `0xDEADBEEF`;
- selecting the DSP feature set and anomaly threshold strategy;
- managing the build, cross-compilation, Docker, and CI integration.

### Automated Code Generation and Boilerplate Support

Generative AI tools, including GitHub Copilot and other LLM-based assistants, were used to accelerate repetitive implementation tasks under human oversight. Typical assisted tasks included:

- repetitive C++ class and template scaffolding;
- CMake target setup and build-file boilerplate;
- Python parsing and telemetry-processing loops;
- initial Streamlit UI layout and documentation drafting;
- shell, Docker, and QEMU command generation for local development workflows.

### Verification and Accountability

AI assistance was limited to syntax acceleration, scaffolding, and mechanical drafting. All critical algorithms, binary protocol definitions, ML quantization flows, configuration changes, and build settings were reviewed, tested, and validated by the project author prior to inclusion.
