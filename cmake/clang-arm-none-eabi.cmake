set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

set(CMAKE_C_COMPILER clang CACHE STRING "Clang C compiler")
set(CMAKE_CXX_COMPILER clang++ CACHE STRING "Clang C++ compiler")
set(CMAKE_ASM_COMPILER clang CACHE STRING "Clang assembler driver")

set(CMAKE_C_COMPILER_TARGET arm-none-eabi)
set(CMAKE_CXX_COMPILER_TARGET arm-none-eabi)
set(CMAKE_ASM_COMPILER_TARGET arm-none-eabi)
set(CMAKE_SYSROOT /usr/lib/arm-none-eabi/newlib)

set(ARM_RUNTIME_INCLUDE_FLAGS
    "-isystem /usr/include/newlib -isystem /usr/include/newlib/c++/10.3.1 -isystem /usr/include/newlib/c++/10.3.1/arm-none-eabi -isystem /usr/include/newlib/c++/10.3.1/backward"
)
set(ARM_RUNTIME_LIBRARY_FLAGS
    "-L/usr/lib/arm-none-eabi/newlib/thumb/v7-m/nofp -L/usr/lib/gcc/arm-none-eabi/10.3.1/thumb/v7-m/nofp -rtlib=libgcc"
)

set(ARM_CLANG_FLAGS
    "-mcpu=cortex-m3 -mthumb -mfloat-abi=soft -fno-unwind-tables -fno-asynchronous-unwind-tables ${ARM_RUNTIME_INCLUDE_FLAGS}"
)
set(CMAKE_C_FLAGS_INIT "${ARM_CLANG_FLAGS}")
set(CMAKE_CXX_FLAGS_INIT "${ARM_CLANG_FLAGS} -stdlib=libstdc++ -fno-exceptions -fno-rtti")
set(CMAKE_ASM_FLAGS_INIT "${ARM_CLANG_FLAGS}")
set(CMAKE_EXE_LINKER_FLAGS_INIT
    "-fuse-ld=lld -nostartfiles -nostdlib++ -Wl,--gc-sections ${ARM_RUNTIME_LIBRARY_FLAGS}"
)

find_program(CMAKE_AR llvm-ar REQUIRED)
find_program(CMAKE_RANLIB llvm-ranlib REQUIRED)
find_program(CMAKE_LINKER ld.lld REQUIRED)
