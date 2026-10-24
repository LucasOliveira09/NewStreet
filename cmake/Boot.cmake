# Integrates the upstream PPU scaffold against this title's generated header.
# Reference: ps3recomp/templates/project/CMakeLists.txt at toolchain.lock.json.
set(BOOT_RECOMP_DIR "${CMAKE_SOURCE_DIR}/private/generated/eboot" CACHE PATH "PPU lift for native boot")
set(PS3_SDK "${CMAKE_SOURCE_DIR}/vendor/ps3recomp")
if(NOT EXISTS "${BOOT_RECOMP_DIR}/ppu_recomp.h")
    message(FATAL_ERROR "Generate the boot lift before configuring FIFA_BUILD_BOOT")
endif()
set(PS3RECOMP_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(FIFA_RUNTIME_ARCHIVE "" CACHE FILEPATH "Reuse the runtime archive built by the EBOOT target")
if(FIFA_RUNTIME_ARCHIVE)
    if(NOT EXISTS "${FIFA_RUNTIME_ARCHIVE}")
        message(FATAL_ERROR "Build the EBOOT runtime before reusing its archive")
    endif()
    add_library(ps3recomp_runtime STATIC IMPORTED)
    set_target_properties(ps3recomp_runtime PROPERTIES IMPORTED_LOCATION "${FIFA_RUNTIME_ARCHIVE}"
        INTERFACE_LINK_LIBRARIES "ws2_32;xinput;ole32;bcrypt")
else()
    add_subdirectory("${PS3_SDK}" "${CMAKE_BINARY_DIR}/sdk" EXCLUDE_FROM_ALL)
endif()
file(GLOB BOOT_GENERATED CONFIGURE_DEPENDS "${BOOT_RECOMP_DIR}/ppu_recomp*.c" "${BOOT_RECOMP_DIR}/ppu_recomp*.cpp")
set(FIFA_LIFT_OPTIMIZATION "/O1" CACHE STRING "Compiler mode for translated game code: /O1 or /Od")
set_property(CACHE FIFA_LIFT_OPTIMIZATION PROPERTY STRINGS "/O1" "/Od")
if(NOT FIFA_LIFT_OPTIMIZATION MATCHES "^/O(1|d)$")
    message(FATAL_ERROR "Unsupported FIFA_LIFT_OPTIMIZATION")
endif()
set_source_files_properties(${BOOT_GENERATED} PROPERTIES LANGUAGE CXX COMPILE_OPTIONS "/w;/bigobj;${FIFA_LIFT_OPTIMIZATION}")
find_package(Python3 COMPONENTS Interpreter REQUIRED)
set(HLE_TABLE "${CMAKE_CURRENT_BINARY_DIR}/ppu_hle_nids.cpp")
execute_process(COMMAND "${Python3_EXECUTABLE}" "${PS3_SDK}/tools/gen_hle_nids.py" --all --out "${HLE_TABLE}"
    COMMAND_ERROR_IS_FATAL ANY)
add_executable(fifa_boot src/boot_main.cpp src/boot_diagnostics.cpp src/process_spawn.cpp ${BOOT_GENERATED} "${HLE_TABLE}"
    src/native_process.cpp src/guest_arguments.cpp src/crash_diagnostics.cpp
    src/prx_registry.cpp src/prx_registry_test.cpp
    src/guest_callbacks.cpp tests/callback_probe.cpp
    "${PS3_SDK}/runtime/ppu/ppu_loader.cpp" "${PS3_SDK}/runtime/ppu/ppu_hle.cpp"
    "${PS3_SDK}/runtime/ppu/ppu_fs.cpp" "${PS3_SDK}/runtime/ppu/ppu_sysprx.cpp")
target_include_directories(fifa_boot PRIVATE "${BOOT_RECOMP_DIR}" "${PS3_SDK}/include"
    "${PS3_SDK}/runtime/ppu" "${PS3_SDK}/runtime/spu" "${PS3_SDK}/runtime/memory"
    "${PS3_SDK}/runtime/syscalls" "${PS3_SDK}/runtime/platform" "${PS3_SDK}/libs/video")
target_compile_definitions(fifa_boot PRIVATE FIFA_STRICT_BOOT _CRT_SECURE_NO_WARNINGS)
target_compile_options(fifa_boot PRIVATE /clang:-fwrapv /clang:-fno-strict-aliasing /clang:-ffp-contract=off /bigobj)
target_link_libraries(fifa_boot PRIVATE ps3recomp_runtime dbghelp user32 gdi32 winmm)
target_link_options(fifa_boot PRIVATE /STACK:8388608 /DEBUG)
