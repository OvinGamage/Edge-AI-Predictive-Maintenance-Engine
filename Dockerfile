# Base environment for compiling ARM C++ and running QEMU + Python
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install base toolchains
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gcc-arm-none-eabi \
    libnewlib-arm-none-eabi \
    libstdc++-arm-none-eabi-newlib \
    qemu-system-arm \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    clang \
    lld \
    llvm \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch v25.9.23 \
    https://github.com/google/flatbuffers.git /opt/flatbuffers-25.9.23

RUN git init /opt/ruy \
    && git -C /opt/ruy fetch --depth=1 https://github.com/google/ruy.git 2264753777198e4393fb83c44c693462d57a2be1 \
    && git -C /opt/ruy checkout --detach FETCH_HEAD

WORKDIR /app
CMD ["/bin/bash"]
