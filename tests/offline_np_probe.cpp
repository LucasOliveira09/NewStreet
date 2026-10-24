#include "ppu_recomp.h"
#include "ps3emu/nid.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <initializer_list>

extern "C" void ppu_hle_init(void);
extern "C" void ps3_hle_call(uint32_t, ppu_context*);
extern "C" void fifa_register_offline_np(void);

static uint32_t call(const char* name, std::initializer_list<uint64_t> args) {
    ppu_context ctx{};
    ctx.gpr[1] = 0x2f000;
    unsigned reg = 3;
    for (auto value : args) ctx.gpr[reg++] = value;
    ps3_hle_call(ps3_compute_nid(name), &ctx);
    return (uint32_t)ctx.gpr[3];
}

extern "C" int fifa_test_offline_np(void) {
    vm_base = (uint8_t*)std::calloc(1, 0x30000);
    if (!vm_base) return 3;
    std::memset(vm_base + 0x10000, 0xa5, 16);
    ppu_hle_init();
    fifa_register_offline_np();
    if (ps3_compute_nid("sceNpManagerGetAccountRegion") != 0xb1e0718b) return 4;
    uint32_t before = call("sceNpManagerGetAccountRegion", {0x10000, 0x10008});
    if (call("sceNpInit", {0x10000, 0x20000})) return 5;
    uint32_t invalid_country = call("sceNpManagerGetAccountRegion", {0, 0x10008});
    uint32_t invalid_language = call("sceNpManagerGetAccountRegion", {0x10000, 0});
    uint32_t offline = call("sceNpManagerGetAccountRegion", {0x10000, 0x10008});
    if (call("sceNpTerm", {})) return 6;
    uint32_t after = call("sceNpManagerGetAccountRegion", {0x10000, 0x10008});
    bool untouched = true;
    for (unsigned i = 0; i < 16; ++i) untouched &= vm_base[0x10000 + i] == 0xa5;
    std::printf("{\"before\":%u,\"invalid_country\":%u,\"invalid_language\":%u,\"offline\":%u,\"after\":%u,\"untouched\":%s}\n",
        before, invalid_country, invalid_language, offline, after, untouched ? "true" : "false");
    return 0;
}
