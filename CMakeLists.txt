# 1. Enforce minimum CMake version and compatibility range
cmake_minimum_required(VERSION 3.15...3.28)

# 2. Declare top-level project name and languages used
project(EdgePredictiveMaintenance LANGUAGES CXX C)

# 3. Enforce global C++ standard across all targets
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 4. Include custom CMake toolchain scripts folder
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

# 5. Enable testing capabilities globally for GoogleTest
enable_testing()

# 6. Add modular subdirectories (these will hold target-specific CMakeLists.txt)
add_subdirectory(firmware)
add_subdirectory(tests)
