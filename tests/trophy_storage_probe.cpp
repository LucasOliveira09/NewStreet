#include "ppu_recomp.h"
#include "ps3emu/guest_call.h"
#include "../vendor/ps3recomp/libs/network/sceNpTrophy.h"
#include "../vendor/ps3recomp/libs/system/cellSysutil.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>

extern "C" const char* ppu_vfs_root;
static unsigned statuses[8]{}, status_count = 0;
static void notification(uint32_t, uint64_t, uint64_t status, uint64_t, uint64_t,
                         uint64_t, uint64_t, uint64_t, uint64_t) {
    if (status_count < 8) statuses[status_count++] = (unsigned)status;
}
static uint64_t permission(uint32_t opd, uint64_t a0, uint64_t a1, uint64_t a2,
        uint64_t a3, uint64_t a4, uint64_t a5, uint64_t a6, uint64_t a7) {
    notification(opd, a0, a1, a2, a3, a4, a5, a6, a7);
    return std::getenv("FIFA_TEST_TROPHY_DENY") ? uint64_t(-1) : 0;
}

extern "C" int fifa_test_trophy_storage(const char* disc, const char* storage) {
    vm_base = (uint8_t*)std::calloc(1, 0x20000);
    if (!vm_base || std::strlen(storage) > 1023) return 3;
    ppu_vfs_root = disc;
    std::strcpy((char*)vm_base + 0x10000, storage);
    sceNpTrophySetStoragePath((const char*)0x10000);
    std::memcpy(vm_base + 0x11000, "NPWR00001", 9);
    g_ps3_guest_caller = notification;
    g_ps3_guest_caller_result = permission;
    sceNpTrophyInit(nullptr, 0, 0, 0);
    if (sceNpTrophyCreateContext((SceNpTrophyContext*)0x12000,
            (const SceNpCommunicationId*)0x11000, nullptr, 0)) return 4;
    sceNpTrophyCreateHandle((SceNpTrophyHandle*)0x12004);
    const auto context = vm_read32(0x12000), handle = vm_read32(0x12004);
    vm_write64(0x12100, 0xa5a5a5a5a5a5a5a5ULL);
    const uint32_t before_result = sceNpTrophyGetRequiredDiskSpace(context, handle, (u64*)0x12100, 0);
    const auto before = vm_read64(0x12100);
    const uint32_t registered = sceNpTrophyRegisterContext(context, handle, 0x13000, 0, 0);
    cellSysutilCheckCallback();
    const uint32_t after_result = sceNpTrophyGetRequiredDiskSpace(context, handle, (u64*)0x12100, 0);
    const auto after = vm_read64(0x12100);
    vm_write64(0x12100, 0xa5a5a5a5a5a5a5a5ULL);
    const uint32_t invalid_handle = sceNpTrophyGetRequiredDiskSpace(context, 0, (u64*)0x12100, 0);
    const bool error_preserved = vm_read64(0x12100) == 0xa5a5a5a5a5a5a5a5ULL;
    std::printf("{\"before_result\":%u,\"before\":%llu,\"registered\":%u,"
        "\"after_result\":%u,\"after\":%llu,\"invalid_handle\":%u,\"error_preserved\":%s,\"statuses\":[",
        before_result, (unsigned long long)before, registered, after_result,
        (unsigned long long)after, invalid_handle, error_preserved ? "true" : "false");
    for (unsigned i = 0; i < status_count; ++i) std::printf("%s%u", i ? "," : "", statuses[i]);
    std::puts("]}");
    return 0;
}
