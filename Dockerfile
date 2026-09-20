# Base environment for compiling ARM C++ and running QEMU + Python
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install base toolchains
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gcc-arm-none-eabi \
    g++-arm-none-eabi \
    qemu-system-arm \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
CMD ["/bin/bash"]
