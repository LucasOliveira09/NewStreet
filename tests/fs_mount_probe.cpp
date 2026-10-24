#include "ppu_recomp.h"
#include "ps3emu/nid.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <initializer_list>

extern "C" const char* ppu_vfs_root;
extern "C" uint32_t ppu_vm_size;
extern "C" void fifa_configure_filesystem_mounts(const char*);
extern "C" void ppu_hle_init(void);
extern "C" void ppu_fs_register(void);
extern "C" void ps3_hle_call(uint32_t, ppu_context*);

static uint32_t call(const char* name, std::initializer_list<uint64_t> args) {
    ppu_context ctx{};
    unsigned r = 3;
    for (auto argument : args) ctx.gpr[r++] = argument;
    ps3_hle_call(ps3_compute_nid(name), &ctx);
    return (uint32_t)ctx.gpr[3];
}

extern "C" int fifa_test_filesystem_mounts(const char* root) {
    vm_base = (uint8_t*)std::calloc(1, 0x20000);
    if (!vm_base) return 3;
    ppu_vm_size = 0x20000;
    ppu_vfs_root = root;
    fifa_configure_filesystem_mounts(root);
    ppu_hle_init();
    ppu_fs_register();
    std::strcpy((char*)vm_base + 0x10000, "/dev_hdd1/cache/test/data.tmp");
    std::strcpy((char*)vm_base + 0x10100, "/dev_hdd1/cache/test/data.big");
    const unsigned char payload[] = {0x46,0x49,0x46,0x41,0,0xff,1,2,3,4,5};
    std::memcpy(vm_base + 0x13000, payload, sizeof payload);
    if (call("cellFsOpen", {0x10000, 0x242, 0x12000, 0600, 0, 0})) return 4;
    uint32_t fd = vm_read32(0x12000);
    if (call("cellFsWrite", {fd, 0x13000, sizeof payload, 0x12010}) ||
        vm_read64(0x12010) != sizeof payload) return 5;
    if (call("cellFsClose", {fd})) return 6;
    uint32_t renamed = call("cellFsRename", {0x10000, 0x10100});
    if (renamed) { std::fprintf(stderr, "Rename returned 0x%08X\n", renamed); return 7; }
    if (call("cellFsOpen", {0x10100, 0, 0x12000, 0, 0, 0})) return 8;
    fd = vm_read32(0x12000);
    if (call("cellFsRead", {fd, 0x13100, sizeof payload, 0x12010}) ||
        vm_read64(0x12010) != sizeof payload ||
        std::memcmp(vm_base + 0x13100, payload, sizeof payload)) return 9;
    if (call("cellFsClose", {fd})) return 10;
    uint32_t missing = call("cellFsRename", {0x10000, 0x10100});
    std::printf("{\"renamed\":%u,\"bytes\":%zu,\"missing_source\":%u}\n", renamed, sizeof payload, missing);
    return 0;
}
