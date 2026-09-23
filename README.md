# Edge AI Predictive Maintenance Engine
Note on Project Architecture & Tooling:
To ensure this project is 100% reproducible and isolated, the entire build ecosystem (CMake toolchains, cross-compilers, QEMU ARM simulation, and multi-stage Docker containers) is pre-configured for one-command execution.
  
  ​The administrative build infrastructure and containerization are provided purely for reviewer/user convenience. The core technical focus of this repository is the low-level bare-metal C++17 firmware, zero-allocation DSP algorithms, and embedded TFLM runtime execution.
An end-to-end bare-metal C++ edge inference engine running in a QEMU-simulated ARM Cortex-M architecture with real-time Python telemetry analytics.

## System Architecture
- **Firmware:** C++17, Bare-Metal ARM Cortex-M (QEMU)
- **ML Inference:** TensorFlow Lite for Microcontrollers (TFLM)
- **Data & Dashboard:** Python, Streamlit, Polars/Pandas
