#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "ppu_recomp.h"
#include "ps3emu/guest_call.h"
#include "../vendor/ps3recomp/libs/system/cellSaveData.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" void ppu_hle_init(void);
extern "C" void ps3_hle_call(uint32_t, ppu_context*);
static unsigned fixed_count = 0, stat_count = 0, file_count = 0, phase = 0;
static bool loading = false, userdata_ok = true, contents_ok = true;
static uint32_t free_kb[2]{}, new_data[2]{};
static constexpr uint8_t payload[] = {0, 1, 2, 0x7f, 0x80, 0xfe, 0xff};

static void callback(uint32_t opd, uint64_t cb, uint64_t get, uint64_t set,
                     uint64_t, uint64_t, uint64_t, uint64_t, uint64_t) {
    const uint32_t expected = opd == 0x15000 ? 0xabcdef10 : opd == 0x15010 ? 0xabcdef11 : 0xabcdef12;
    userdata_ok &= vm_read32(cb + 16) == expected;
    vm_write32(cb + 16, expected + 1);
    vm_write32(cb, 0);
    if (opd == 0x15000) {
        ++fixed_count;
        vm_write32(set, 0x11000);
    } else if (opd == 0x15010) {
        const unsigned index = loading ? 1 : 0;
        ++stat_count; free_kb[index] = vm_read32(get); new_data[index] = vm_read32(get + 4);
        contents_ok &= vm_read32(get + 1624) == 35 && vm_read32(get + 1620) == (loading ? 36 : 0);
        if (!loading) vm_write32(set, 0x11200);
        else contents_ok &= std::strcmp((char*)vm_base + get + 64, "Authored save fixture") == 0 &&
                            vm_read32(get + 1628) == 1;
    } else if (opd == 0x15020) {
        ++file_count;
        if (phase++) {
            userdata_ok &= vm_read32(cb + 16) == 0xabcdef13;
            contents_ok &= vm_read32(get) == sizeof(payload);
            vm_write32(cb, 1);
            return;
        }
        vm_write32(cb + 16, 0xabcdef12); // Keep userdata stable across file operations.
        vm_write32(set, loading ? 0 : 1);
        vm_write32(set + 8, 1);
        vm_write32(set + 28, 0x11040);
        vm_write32(set + 36, sizeof(payload));
        vm_write32(set + 40, sizeof(payload));
        vm_write32(set + 44, 0x12000);
    } else contents_ok = false;
}

extern "C" int fifa_test_savedata_list_auto(const char* volume) {
    vm_base = (uint8_t*)std::calloc(1, 0x50000);
    if (!vm_base) return 3;
    ppu_hle_init();
    g_ps3_guest_caller = callback;
    if (cellSaveData_set_scratch_region(0x20000, 0x20000)) return 4;
    std::strcpy((char*)vm_base + 0x11000, "AUTHORED_SAVE");
    std::strcpy((char*)vm_base + 0x11040, "DATA.BIN");
    std::strcpy((char*)vm_base + 0x11080, "AUTHORED");
    std::strcpy((char*)vm_base + 0x11200, "Authored save fixture");
    std::memcpy(vm_base + 0x12000, payload, sizeof(payload));
    vm_write32(0x10008, 0x11080); // SetList.dirNamePrefix
    vm_write32(0x10100, 4); vm_write32(0x10104, 4);
    ppu_context ctx{}; ctx.gpr[1] = 0x4e000;
    ULARGE_INTEGER before{}, after{};
    GetDiskFreeSpaceExA(volume, &before, nullptr, nullptr);
    auto call = [&](uint32_t nid) {
        ctx.gpr[3] = 0; ctx.gpr[4] = 1; ctx.gpr[5] = 0x10000; ctx.gpr[6] = 0x10100;
        ctx.gpr[7] = 0x15000; ctx.gpr[8] = 0x15010; ctx.gpr[9] = 0x15020;
        ctx.gpr[10] = 0xffffffff;
        vm_write64(ctx.gpr[1] + 112, 0xabcdef10);
        ps3_hle_call(nid, &ctx);
        return (uint32_t)ctx.gpr[3];
    };
    const uint32_t saved = call(0x4dd03a4e);
    loading = true; phase = 0;
    std::memset(vm_base + 0x12000, 0, sizeof(payload));
    const uint32_t loaded = saved ? saved : call(0x21425307);
    GetDiskFreeSpaceExA(volume, &after, nullptr, nullptr);
    contents_ok &= std::memcmp(vm_base + 0x12000, payload, sizeof(payload)) == 0;
    std::printf("{\"save\":%u,\"load\":%u,\"fixed\":%u,\"stat\":%u,\"file\":%u,"
        "\"userdata\":%s,\"contents\":%s,\"free_kb\":[%u,%u],\"new\":[%u,%u],\"before\":%llu,\"after\":%llu}\n",
        saved, loaded, fixed_count, stat_count, file_count, userdata_ok ? "true" : "false",
        contents_ok ? "true" : "false", free_kb[0], free_kb[1], new_data[0], new_data[1],
        (unsigned long long)before.QuadPart, (unsigned long long)after.QuadPart);
    return 0;
}
