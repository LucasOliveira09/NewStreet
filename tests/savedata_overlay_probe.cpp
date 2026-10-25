#include "ppu_recomp.h"
#include <cstdio>
#include <cstdlib>

extern "C" void ppu_hle_init(void);
extern "C" void ppu_sysprx_register(void);
extern "C" void ps3_hle_call(uint32_t, ppu_context*);
extern "C" int ps3recomp_savedata_overlay_enabled(void);

extern "C" int fifa_test_savedata_overlay(void) {
    vm_base = (uint8_t*)std::calloc(1, 0x20000);
    if (!vm_base) return 3;
    ppu_hle_init();
    ppu_sysprx_register();
    if (ps3recomp_savedata_overlay_enabled()) return 5;
    ppu_context ctx{};
    ctx.gpr[1] = 0x1f000;
    const uint64_t values[] = {1, 0, 0xffffffffu, 2, 0x100000000ull,
                               0x100000001ull, 0xffffffffffffffffull};
    for (uint64_t value : values) {
        ctx.gpr[3] = value;
        ctx.gpr[4] = 0x123456789abcdef0ull;
        ps3_hle_call(0xe7fa820b, &ctx);
        if (ctx.gpr[3] != value || ctx.gpr[4] != 0x123456789abcdef0ull) return 4;
        if (ps3recomp_savedata_overlay_enabled() != ((uint32_t)value != 0)) return 6;
    }
    std::puts("{\"void_abi\":true,\"preference_cases\":7,\"default_disabled\":true}");
    return 0;
}
