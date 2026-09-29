# Edge AI Predictive Maintenance Engine
Note on Project Architecture & Tooling:
To ensure this project is 100% reproducible and isolated, the entire build ecosystem (CMake toolchains, cross-compilers, QEMU ARM simulation, and multi-stage Docker containers) is pre-configured for one-command execution.
  
  ​The administrative build infrastructure and containerization are provided purely for reviewer/user convenience. The core technical focus of this repository is the low-level bare-metal C++17 firmware, zero-allocation DSP algorithms, and embedded TFLM runtime execution.
An end-to-end bare-metal C++ edge inference engine running in a QEMU-simulated ARM Cortex-M architecture with real-time Python telemetry analytics.
##📊 Dataset Setup & Quick Start
1. Acquiring the Dataset
This project uses the NASA C-MAPSS (Commercial Modular Aero-Propulsion System Simulation) Flight Data Set (FD001). Due to repository size constraints, raw data files are not tracked by Git.

Download the dataset archive from the NASA Data Portal.

Extract the archive contents into the local ml_pipeline/data/ directory:

Plaintext
ml_pipeline/data/
├── train_FD001.txt
├── test_FD001.txt
└── RUL_FD001.txt
2. How to Run the Pipeline locally
After cloning the repository, execute the automated data preparation and feature extraction scripts:

Bash
## 1. Install required Python dependencies
pip install -r requirements.txt

## 2. Extract DSP rolling-window features (RMS, Peak-to-Peak, Kurtosis)
python ml_pipeline/prepare_data.py

## 3. Train the model and export the INT8 quantized TFLite engine
python ml_pipeline/train.py
# Dataset Attribution & Acknowledgements
This project utilizes the C-MAPSS Flight Data Set, provided by the NASA Prognostics Center of Excellence (PCoE).

Source: NASA Ames Research Center / NASA PCoE Data Set Repository

Citation: Saxena, A., Goebel, K., Simon, D., & Eklund, N. (2008). "Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation." In Proceedings of the 1st International Conference on Prognostics and Health Management (PHM08), Denver, CO.

License/Access: Public domain / Open NASA Data (US Government Work).

Disclaimer: This repository is an independent open-source software project created solely for educational and portfolio demonstration purposes. It is not officially endorsed by, affiliated with, or supported by NASA.

## System Architecture
- **Firmware:** C++17, Bare-Metal ARM Cortex-M (QEMU)
- **ML Inference:** TensorFlow Lite for Microcontrollers (TFLM)
- **Data & Dashboard:** Python, Streamlit, Polars/Pandas
