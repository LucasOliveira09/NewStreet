#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "ppu_recomp.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" void ppu_hle_init(void);
extern "C" void ppu_fs_register(void);
extern "C" void ps3_hle_call(uint32_t, ppu_context*);

extern "C" int fifa_test_fs_free_space(const char* root) {
    vm_base = (uint8_t*)std::calloc(1, 0x20000);
    if (!vm_base) return 3;
    ppu_hle_init(); ppu_fs_register();
    std::strcpy((char*)vm_base + 0x10000, "/dev_hdd0");
    ULARGE_INTEGER before{}, after{};
    const bool before_ok = GetDiskFreeSpaceExA(root, &before, nullptr, nullptr) != 0;
    ppu_context ctx{}; ctx.gpr[1] = 0x1f000;
    ctx.gpr[3] = 0x10000; ctx.gpr[4] = 0x11000; ctx.gpr[5] = 0x11008;
    ps3_hle_call(0xaa3b4bcd, &ctx);
    const bool after_ok = GetDiskFreeSpaceExA(root, &after, nullptr, nullptr) != 0;
    const uint32_t result = (uint32_t)ctx.gpr[3];
    const uint32_t block = vm_read32(0x11000);
    const uint64_t count = vm_read64(0x11008);
    for (unsigned argument = 3; argument <= 5; ++argument) {
        vm_write32(0x11000, 0xa5a5a5a5); vm_write64(0x11008, 0xa5a5a5a5a5a5a5a5ULL);
        ctx.gpr[3] = 0x10000; ctx.gpr[4] = 0x11000; ctx.gpr[5] = 0x11008;
        ctx.gpr[argument] = 0;
        ps3_hle_call(0xaa3b4bcd, &ctx);
        if ((uint32_t)ctx.gpr[3] != 0x8001000d || vm_read32(0x11000) != 0xa5a5a5a5 ||
            vm_read64(0x11008) != 0xa5a5a5a5a5a5a5a5ULL) return 5;
    }
    std::printf("{\"result\":%u,\"block\":%u,\"count\":%llu,\"before\":%llu,\"after\":%llu,"
        "\"host_queries\":%s,\"null_arguments_preserved\":true}\n", result, block, (unsigned long long)count,
        (unsigned long long)before.QuadPart, (unsigned long long)after.QuadPart,
        before_ok && after_ok ? "true" : "false");
    return 0;
}
