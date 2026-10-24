#include "ppu_recomp.h"
#include "ps3emu/nid.h"
#include <cstdio>
#include <cstdlib>
#include <initializer_list>

extern "C" void ppu_hle_init(void);
extern "C" void ps3_hle_call(uint32_t, ppu_context*);

static uint32_t call(const char* name, std::initializer_list<uint64_t> args) {
    ppu_context ctx{};
    ctx.gpr[1] = 0x2f000;
    unsigned reg = 3;
    for (auto arg : args) ctx.gpr[reg++] = arg;
    ps3_hle_call(ps3_compute_nid(name), &ctx);
    return (uint32_t)ctx.gpr[3];
}

extern "C" int fifa_test_offline_netctl(void) {
    vm_base = (uint8_t*)std::calloc(1, 0x30000);
    if (!vm_base) return 3;
    ppu_hle_init();
    vm_write32(0x10000, 0xa5a5a5a5);
    uint32_t before = call("cellNetCtlGetState", {0x10000});
    bool untouched_before = vm_read32(0x10000) == 0xa5a5a5a5;
    if (call("cellNetCtlInit", {})) return 4;
    uint32_t duplicate = call("cellNetCtlInit", {});
    uint32_t invalid = call("cellNetCtlGetState", {0});
    uint32_t result = call("cellNetCtlGetState", {0x10000});
    uint32_t state = vm_read32(0x10000);
    call("cellNetCtlTerm", {});
    vm_write32(0x10000, 0xa5a5a5a5);
    uint32_t after = call("cellNetCtlGetState", {0x10000});
    bool untouched_after = vm_read32(0x10000) == 0xa5a5a5a5;
    std::printf("{\"before\":%u,\"duplicate\":%u,\"invalid\":%u,\"result\":%u,\"state\":%u,\"after\":%u,\"untouched\":%s}\n",
        before, duplicate, invalid, result, state, after,
        untouched_before && untouched_after ? "true" : "false");
    return 0;
}
