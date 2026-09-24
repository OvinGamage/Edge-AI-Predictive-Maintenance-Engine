# ------------------------------------------------------------------------------
# Host-Only Unit Tests (GoogleTest Integration)
# ------------------------------------------------------------------------------
# Skip test generation when cross-compiling for bare-metal ARM targets
if(CMAKE_CROSSCOMPILING)
    message(STATUS "Cross-compiling for ARM target: host unit tests disabled.")
    return()
endif()

message(STATUS "Native host build detected: enabling unit test targets.")

# Enable CTest framework execution BEFORE fetching test dependencies
enable_testing()

# Include FetchContent module to download/manage GoogleTest
include(FetchContent)

# Set configuration options BEFORE declaring content
set(INSTALL_GTEST OFF CACHE BOOL "Disable installation of GoogleTest" FORCE)

FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG        v1.14.0
)

FetchContent_MakeAvailable(googletest)

# ------------------------------------------------------------------------------
# Define Test Executable Target (unit_tests)
# ------------------------------------------------------------------------------
add_executable(unit_tests
    tests/test_ring_buffer.cpp
    tests/test_dsp_features.cpp
)

# Enforce strict C++17 on unit test runner
set_target_properties(unit_tests PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

# Expose local test includes directory
target_include_directories(unit_tests
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link unit tests to firmware_core static library and GoogleTest library
target_link_libraries(unit_tests
    PRIVATE
        firmware_core
        gtest_main
)

# Register target with CTest execution engine
include(GoogleTest)
gtest_discover_tests(unit_tests)
