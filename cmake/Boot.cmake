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
set(SPU_PIC_FIXTURE_DIR "${CMAKE_SOURCE_DIR}/private/generated/spu_pic_fixture")
execute_process(COMMAND "${Python3_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tools/build_spu_pic_fixture.py"
    COMMAND_ERROR_IS_FATAL ANY)
set(HLE_TABLE "${CMAKE_CURRENT_BINARY_DIR}/ppu_hle_nids.cpp")
execute_process(COMMAND "${Python3_EXECUTABLE}" "${PS3_SDK}/tools/gen_hle_nids.py" --all --out "${HLE_TABLE}"
    COMMAND_ERROR_IS_FATAL ANY)
add_executable(fifa_boot src/boot_main.cpp src/boot_diagnostics.cpp src/process_spawn.cpp ${BOOT_GENERATED} "${HLE_TABLE}"
    src/native_process.cpp src/guest_arguments.cpp src/crash_diagnostics.cpp
    src/prx_registry.cpp src/prx_registry_test.cpp
    src/guest_callbacks.cpp tests/callback_probe.cpp
    src/graphics.cpp
    src/spu_policy.cpp
    src/spu_diagnostics.cpp
    src/spu_job_observer.cpp
    src/spu_entry_observer.cpp
    src/filesystem_mounts.cpp
    src/guest_memory_diagnostics.cpp
    src/offline_np.cpp
    src/hang_diagnostics.cpp
    src/input_observer.cpp
    tests/input_observer_probe.cpp
    tests/offline_np_probe.cpp
    tests/offline_netctl_probe.cpp
    tests/savedata_overlay_probe.cpp
    tests/pad_file_probe.cpp
    tests/fifa_input_bitset_probe.cpp
    tests/fifa_input_sampler_probe.cpp
    tests/fs_mount_probe.cpp
    tests/fs_readdir_probe.cpp
    tests/rsx_fifo_probe.cpp
    tests/spu_group_probe.cpp
    tests/spu_overlay_probe.cpp
    tests/spu_job_observer_probe.cpp
    tests/spu_pic_lowering_probe.cpp
    "${SPU_PIC_FIXTURE_DIR}/main/spu_recomp.c"
    "${SPU_PIC_FIXTURE_DIR}/other/spu_recomp.c"
    "${PS3_SDK}/runtime/ppu/ppu_loader.cpp" "${PS3_SDK}/runtime/ppu/ppu_hle.cpp"
    "${PS3_SDK}/runtime/ppu/ppu_fs.cpp" "${PS3_SDK}/runtime/ppu/ppu_sysprx.cpp")

option(FIFA_BUILD_SPU "Link the generated native SPU programs" OFF)
set_source_files_properties("${SPU_PIC_FIXTURE_DIR}/main/spu_recomp.c"
    "${SPU_PIC_FIXTURE_DIR}/other/spu_recomp.c" PROPERTIES
    COMPILE_DEFINITIONS SPU_USE_DISPATCH_MT COMPILE_OPTIONS "/O2;/w")
set_source_files_properties(tests/spu_pic_lowering_probe.cpp PROPERTIES
    INCLUDE_DIRECTORIES "${SPU_PIC_FIXTURE_DIR}")
if(FIFA_BUILD_SPU)
    set(FIFA_SPU_DIR "${CMAKE_SOURCE_DIR}/private/generated/spu")
    if(NOT EXISTS "${FIFA_SPU_DIR}/sources.cmake")
        message(FATAL_ERROR "Run tools/build.ps1 -Target Spu before enabling native SPU programs")
    endif()
    include("${FIFA_SPU_DIR}/sources.cmake")
    set(FIFA_OVERLAY_DIR "${CMAKE_SOURCE_DIR}/private/generated/spu_overlays")
    if(NOT EXISTS "${FIFA_OVERLAY_DIR}/sources.cmake")
        message(FATAL_ERROR "Generate raw SPU overlays with tools/build.ps1 -Target Spu")
    endif()
    include("${FIFA_OVERLAY_DIR}/sources.cmake")
    target_sources(fifa_boot PRIVATE ${SPU_GENERATED_SOURCES} ${FIFA_SPU_OVERLAY_SOURCES})
    set_source_files_properties(${SPU_GENERATED_SOURCES} ${FIFA_SPU_OVERLAY_SOURCES} PROPERTIES
        COMPILE_DEFINITIONS SPU_USE_DISPATCH_MT COMPILE_OPTIONS "/O2;/w")
    # Scope this define to its consumer; changing it must not rebuild the
    # hundreds of unrelated generated PPU translation units.
    set_source_files_properties(src/spu_policy.cpp PROPERTIES COMPILE_DEFINITIONS FIFA_HAS_SPU)
endif()
target_include_directories(fifa_boot PRIVATE "${BOOT_RECOMP_DIR}" "${PS3_SDK}/include"
    "${PS3_SDK}/runtime/ppu" "${PS3_SDK}/runtime/spu" "${PS3_SDK}/runtime/memory"
    "${PS3_SDK}/runtime/syscalls" "${PS3_SDK}/runtime/platform" "${PS3_SDK}/libs/video")
target_compile_definitions(fifa_boot PRIVATE FIFA_STRICT_BOOT _CRT_SECURE_NO_WARNINGS)
target_compile_options(fifa_boot PRIVATE /clang:-fwrapv /clang:-fno-strict-aliasing /clang:-ffp-contract=off /bigobj)
target_link_libraries(fifa_boot PRIVATE ps3recomp_runtime dbghelp user32 gdi32 winmm)
target_link_options(fifa_boot PRIVATE /STACK:8388608 /DEBUG)
