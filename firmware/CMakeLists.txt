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

if(CMAKE_CROSSCOMPILING)
    set(TFLM_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/lib/tflite-micro")
    set(TFLM_FLATBUFFERS_INCLUDE_DIR "/opt/flatbuffers-25.9.23/include")

    file(GLOB TFLM_CORE_SOURCES CONFIGURE_DEPENDS
        "${TFLM_ROOT}/tensorflow/lite/micro/*.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/arena_allocator/*.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/c/*.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/memory_planner/*.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/tflite_bridge/*.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/kernels/kernel_util.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/kernels/tflite_kernel_util.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/kernels/micro_tensor_utils.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/kernels/internal/*.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/kernels/internal/reference/*.cc"
    )
    file(GLOB_RECURSE TFLITE_CORE_SOURCES CONFIGURE_DEPENDS
        "${TFLM_ROOT}/tensorflow/*.cc"
        "${TFLM_ROOT}/tensorflow/*.c"
    )
    list(FILTER TFLITE_CORE_SOURCES EXCLUDE REGEX "/tensorflow/lite/(experimental|micro)/")
    list(FILTER TFLITE_CORE_SOURCES EXCLUDE REGEX "(_test|_benchmark)\\.(cc|c)$")
    list(FILTER TFLITE_CORE_SOURCES EXCLUDE REGEX "/array\\.cc$")
    list(APPEND TFLM_CORE_SOURCES ${TFLITE_CORE_SOURCES})
    set(TFLM_KERNEL_SOURCES
        "${TFLM_ROOT}/tensorflow/lite/micro/kernels/activations.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/kernels/activations_common.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/kernels/dequantize.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/kernels/dequantize_common.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/kernels/fully_connected.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/kernels/fully_connected_common.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/kernels/quantize.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/kernels/quantize_common.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/kernels/reshape.cc"
        "${TFLM_ROOT}/tensorflow/lite/micro/kernels/reshape_common.cc"
    )
    list(APPEND TFLM_CORE_SOURCES ${TFLM_KERNEL_SOURCES})
    list(FILTER TFLM_CORE_SOURCES EXCLUDE REGEX "(_test|_benchmark)\\.cc$")
    list(FILTER TFLM_CORE_SOURCES EXCLUDE REGEX "/array\\.cc$")

    add_library(tflm_microlite STATIC ${TFLM_CORE_SOURCES})
    target_include_directories(tflm_microlite PUBLIC
        ${TFLM_ROOT}
        ${TFLM_FLATBUFFERS_INCLUDE_DIR}
        ${TFLM_ROOT}/third_party/gemmlowp
        /opt/ruy
    )
    target_compile_definitions(tflm_microlite PRIVATE
        TF_LITE_STATIC_MEMORY
        TF_LITE_USE_CTIME
    )
    target_compile_options(tflm_microlite PRIVATE
        -fno-rtti
        -fno-exceptions
        -fno-threadsafe-statics
        -ffunction-sections
        -fdata-sections
    )
    target_link_libraries(firmware_core PUBLIC tflm_microlite)
else()
    set(TFLM_FLATBUFFERS_INCLUDE_DIR
        "${CMAKE_CURRENT_SOURCE_DIR}/lib/tflite-micro/third_party/flatbuffers/include"
        CACHE PATH "FlatBuffers headers compatible with the TFLite Micro schema"
    )
endif()

# Expose header include paths to firmware_core and dependent targets
# Expose include directory paths to firmware_core and dependent targets
target_include_directories(firmware_core
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
        ${CMAKE_CURRENT_SOURCE_DIR}/lib/tflite-micro
        ${TFLM_FLATBUFFERS_INCLUDE_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}/lib/tflite-micro/third_party/gemmlowp
      
)

# ------------------------------------------------------------------------------
# 2. Executable Firmware Binary Target (firmware_app)
# ------------------------------------------------------------------------------
add_executable(firmware_app
    src/startup.S
    src/main.cpp
)

target_link_libraries(firmware_app
    PRIVATE
        firmware_core
)

if(CMAKE_CROSSCOMPILING)
    set_target_properties(firmware_app PROPERTIES SUFFIX ".elf")
    target_link_options(firmware_app PRIVATE
        "-T${CMAKE_CURRENT_SOURCE_DIR}/linker/mps2_an385.ld"
    )
    target_link_libraries(firmware_app PRIVATE stdc++ supc++ c m nosys gcc)
endif()

# ------------------------------------------------------------------------------
# 3. Post-Build Memory Print for Bare-Metal ARM Target
# ------------------------------------------------------------------------------
if(CMAKE_CROSSCOMPILING AND CMAKE_SIZE)
    add_custom_command(TARGET firmware_app POST_BUILD
        COMMAND ${CMAKE_SIZE} $<TARGET_FILE:firmware_app>
        COMMENT "Printing bare-metal executable RAM/Flash memory footprint:"
    )
endif()
