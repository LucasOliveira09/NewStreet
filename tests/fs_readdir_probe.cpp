#include "ppu_recomp.h"
#include "ps3emu/nid.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <initializer_list>

extern "C" void ppu_hle_init(void);
extern "C" void ppu_fs_register(void);
extern "C" void ps3_hle_call(uint32_t, ppu_context*);
extern "C" uint32_t ppu_vm_size;

static uint32_t call(const char* name, std::initializer_list<uint64_t> args) {
    ppu_context ctx{};
    ctx.gpr[1] = 0x2f000;
    unsigned reg = 3;
    for (auto value : args) ctx.gpr[reg++] = value;
    ps3_hle_call(ps3_compute_nid(name), &ctx);
    return (uint32_t)ctx.gpr[3];
}
static uint64_t be(uint32_t address, unsigned bytes) {
    uint64_t result = 0;
    for (unsigned i = 0; i < bytes; ++i) result = result * 256 + vm_base[address + i];
    return result;
}

extern "C" int fifa_test_fs_readdir(const char* path) {
    vm_base = (uint8_t*)std::calloc(1, 0x30000);
    if (!vm_base) return 3;
    ppu_vm_size = 0x30000;
    ppu_hle_init();
    ppu_fs_register();
    std::strcpy((char*)vm_base + 0x10000, path);
    if (call("cellFsOpendir", {0x10000, 0x11000})) return 4;
    uint32_t fd = (uint32_t)be(0x11000, 4), count = 0;
    unsigned char previous[258]{};
    bool eof = false;
    for (; count < 16; ++count) {
        std::memset(vm_base + 0x12000, 0xa5, 258);
        std::memset(vm_base + 0x13000, 0xff, 8);
        if (call("cellFsReaddir", {fd, 0x12000, 0x13000})) return 5;
        uint64_t bytes = be(0x13000, 8);
        if (!bytes) { eof = true; break; }
        if (bytes != 258 || (vm_base[0x12000] != 1 && vm_base[0x12000] != 2)) return 6;
        if (vm_base[0x12001] != std::strlen((char*)vm_base + 0x12002)) return 7;
        std::memcpy(previous, vm_base + 0x12000, sizeof previous);
    }
    if (!eof || count < 2) return 8;
    bool hdd1 = !std::strncmp(path, "/dev_hdd1/", 10);
    if (!hdd1) std::memset(previous, 0, 3);
    bool first = !std::memcmp(previous, vm_base + 0x12000, sizeof previous);
    std::memset(vm_base + 0x12000, 0xcc, 258);
    if (call("cellFsReaddir", {fd, 0x12000, 0x13000})) return 9;
    bool repeated = !std::memcmp(previous, vm_base + 0x12000, sizeof previous) && !be(0x13000, 8);
    if (call("cellFsClosedir", {fd})) return 10;
    std::printf("{\"entries\":%u,\"eof_bytes\":0,\"first_eof\":%s,\"repeated_eof\":%s}\n",
        count, first ? "true" : "false", repeated ? "true" : "false");
    return 0;
}
