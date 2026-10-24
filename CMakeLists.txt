cmake_minimum_required(VERSION 3.20)
project(fifa_street_native_bootstrap LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT WIN32 OR NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
    message(FATAL_ERROR "This bootstrap is verified with clang-cl on Windows x64.")
endif()

if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/private/generated/probe/ppu_recomp.c")
    message(FATAL_ERROR "Run tools/lift_probe.py with your local decrypted ELF first.")
endif()

# Source-derived functions stay in ignored private/. This is a test executable.
add_executable(fifa_function_probe
    tests/probe_runner.c
    private/generated/probe/ppu_recomp.c
)
# The upstream emitter uses C++ linkage declarations inside its .c output.
set_source_files_properties(tests/probe_runner.c private/generated/probe/ppu_recomp.c
    PROPERTIES LANGUAGE CXX)
target_include_directories(fifa_function_probe PRIVATE
    private/generated/probe
    vendor/ps3recomp/runtime/ppu
    vendor/ps3recomp/include
)
target_compile_definitions(fifa_function_probe PRIVATE _CRT_SECURE_NO_WARNINGS)

option(FIFA_BUILD_BOOT "Build the real-game native startup diagnostic" OFF)
if(FIFA_BUILD_BOOT)
    include(cmake/Boot.cmake)
endif()
