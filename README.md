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

This repository was engineered following a Systems Architect & AI Execution Engine workflow. To ensure complete transparency regarding open-source contribution integrity, code auditing, and AI usage, the breakdown of system development is detailed below:

### 1. Architectural Ownership & Strategic Engineering (Human Lead: ~60% Mental Labor)

All high-level engineering decisions, target platform constraints, and system integration contracts were designed, directed, and verified by the developer:

- **System Boundaries & Constraints:** Defined bare-metal C++17 execution rules, zero dynamic memory allocation (`malloc`/`new`) bounds, static Tensor Arena memory budgeting, and ARM Cortex-M target profiling via QEMU simulation.
- **Protocol & Interface Design:** Authored the binary serialization contract—including memory-aligned (`#pragma pack(1)`) 29-byte telemetry structs, additive checksum safety checks, and header frame alignment (`0xDEADBEEF`) for serial transport over virtual UART.
- **Machine Learning & DSP Strategy:** Selected the time-domain feature set (RMS, Peak-to-Peak, Kurtosis), defined the INT8 Autoencoder anomaly threshold boundaries (0.045 Warning / 0.090 Critical), and established the dual-mode user experience strategy for non-technical operators vs. diagnostic engineers.
- **Build System & Toolchain Triage:** Managed multi-target CMake dependency graphs, Docker compilation environments, cross-compilation toolchain flags (`arm-none-eabi-gcc`), and GitHub Actions CI regression pipelines.

### 2. Automated Code Generation & Boilerplate Execution (AI Assistance: ~85% Grunt Work)

Generative AI tools (including GitHub Copilot and LLM assistants) were leveraged as high-speed execution engines to accelerate repetitive syntax generation under strict human oversight:

- **Boilerplate & Syntax Generation:** Synthesized repetitive C++ class templates, CMake target setups, Python `pyserial`/`struct.unpack` parsing loops, and initial Streamlit UI layout scaffolding.
- **Terminal & Container Orchestration:** Assisted in generating terminal commands, PowerShell Docker build pipelines, and QEMU virtual serial port initialization flags.
- **Documentation & Formatting:** Generated initial Markdown document structures, inline comments, and technical summaries based on developer specifications.
- **Verification Statement:** AI tools were utilized strictly for syntax acceleration and mechanical code generation. All embedded C++ algorithms, binary protocol contracts, ML quantization flows, and build configurations were audited, debugged, tested, and validated by the primary author.
