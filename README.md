# Edge AI Predictive Maintenance Engine

An end-to-end bare-metal C++ edge inference engine running on a QEMU-simulated ARM Cortex-M architecture, with real-time Python telemetry analytics.

## Project Architecture and Tooling

The project is designed to be reproducible and isolated. The complete build ecosystem is pre-configured, including:

- CMake toolchains
- Cross-compilers
- QEMU ARM simulation
- Multi-stage Docker containers

The build infrastructure and containerization are provided for reviewer and user convenience. The core technical focus of this repository is the low-level bare-metal C++17 firmware and its edge machine-learning inference workflow.

## System Architecture

| Component | Technology |
| --- | --- |
| Firmware | C++17, bare-metal ARM Cortex-M, QEMU |
| ML inference | TensorFlow Lite for Microcontrollers (TFLM) |
| Data and dashboard | Python, Streamlit, Polars/Pandas |

## Dataset Setup

This project uses the NASA C-MAPSS (Commercial Modular Aero-Propulsion System Simulation) Flight Data Set, specifically the FD001 subset. Because of repository size constraints, the raw data files are not tracked in Git.

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
- **Citation:** Saxena, A., Goebel, K., Simon, D., & Eklund, N. (2008). “Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation.” In *Proceedings of the 1st International Conference on Prognostics and Health Management*.
- **License/access:** Public domain / Open NASA Data (U.S. Government work)

> **Disclaimer:** This repository is an independent open-source software project created solely for educational and portfolio demonstration purposes. It is not officially endorsed by, affiliated with, or sponsored by NASA or any other organization referenced in this README.
