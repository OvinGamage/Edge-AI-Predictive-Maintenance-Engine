# ------------------------------------------------------------------------------
# 1. Core Static Library Target (firmware_core)
# ------------------------------------------------------------------------------
add_library(firmware_core STATIC
    src/core/ring_buffer.cpp
    src/core/dsp_features.cpp
    src/ml/model_runner.cpp
    src/drivers/uart.cpp
)

# Enforce strict C++17 standard rules on the library target
set_target_properties(firmware_core PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

# Expose header include paths to firmware_core and dependent targets
# Expose include directory paths to firmware_core and dependent targets
target_include_directories(firmware_core
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
        ${CMAKE_CURRENT_SOURCE_DIR}/lib/tflite-micro
        ${CMAKE_CURRENT_SOURCE_DIR}/lib/tflite-micro/third_party/flatbuffers/include
        ${CMAKE_CURRENT_SOURCE_DIR}/lib/tflite-micro/third_party/gemmlowp
      
)

# ------------------------------------------------------------------------------
# 2. Executable Firmware Binary Target (firmware_app)
# ------------------------------------------------------------------------------
add_executable(firmware_app
    src/main.cpp
)

target_link_libraries(firmware_app
    PRIVATE
        firmware_core
)

# ------------------------------------------------------------------------------
# 3. Post-Build Memory Print for Bare-Metal ARM Target
# ------------------------------------------------------------------------------
if(CMAKE_CROSSCOMPILING AND CMAKE_SIZE)
    add_custom_command(TARGET firmware_app POST_BUILD
        COMMAND ${CMAKE_SIZE} $<TARGET_FILE:firmware_app>
        COMMENT "Printing bare-metal executable RAM/Flash memory footprint:"
    )
endif()
