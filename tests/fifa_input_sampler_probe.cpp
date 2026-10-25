#include "ppu_recomp.h"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" void ppu_recomp_register(void);
extern "C" void ppu_register_function(uint32_t, void (*)(ppu_context*));
extern "C" void ps3_indirect_call_to(ppu_context*, uint32_t);

// Authored metadata providers isolate the ORIGINAL sampler's byte-to-float
// conversion and two authored logical bindings; this does not test UI events.
static void metadata_interface(ppu_context* ctx) { ctx->gpr[3] = 0x17000; }
static void bindings(ppu_context* ctx) {
    vm_write32(ctx->gpr[4], 0x17700); vm_write32(ctx->gpr[5], 2);
}

extern "C" int fifa_test_input_sampler(void) {
    ppu_recomp_register();
    vm_base = (uint8_t*)std::calloc(1, 0x1200000);
    if (!vm_base) return 3;
    // Device layout observed in the game: four digital, twelve pressure.
    vm_write32(0x10014, 4); vm_write32(0x10018, 12);
    vm_write32(0x10020, 0x11000); vm_write32(0x10024, 0x12000);
    vm_write32(0x10028, 0x12500); // neutral axes
    vm_write32(0x13004, 0); vm_write32(0x13008, 16); vm_write32(0x1300c, 8);
    vm_write32(0x14000, 0x15000); vm_write32(0x15024, 0x16000);
    vm_write32(0x16000, 0x08000000);
    vm_write32(0x17000, 0x17500); vm_write32(0x1750c, 0x17600);
    vm_write32(0x17600, 0x08000010);
    ppu_register_function(0x08000000, metadata_interface);
    ppu_register_function(0x08000010, bindings);
    // Pair source/destination nodes in the metadata interface's binding list.
    // The original dispatcher selects type 0 and clamps each sum to [0,1].
    vm_write32(0x17700, 0x17800); vm_write32(0x17704, 0x17900);
    vm_write32(0x17708, 0x17810); vm_write32(0x1770c, 0x17910);
    vm_write32(0x17800, 19); vm_write32(0x17810, 30); // Start/Cross sampler float indices
    vm_write32(0x17900, 0); vm_write32(0x17910, 1);   // authored logical destinations
    vm_write32(0x21f1c0, 0x3f800000); vm_write32(0x21f1c4, 0); // original clamp constants
    // Exact constant words reviewed in FIFAZF ELF at 0x11aa164..0x11aa174.
    const uint32_t constants[] = {0x80000000, 0x477fff00, 0x3a83126f, 0x3f800000, 0x3b808081};
    for (unsigned i = 0; i < 5; ++i) vm_write32(0x11aa164 + i * 4, constants[i]);
    const unsigned pressures[] = {0, 1, 64, 127, 128, 254, 255};
    unsigned cases = 0;
    for (unsigned digital = 0; digital < 16; ++digital) {
        for (unsigned pressure : pressures) {
            vm_write8(0x11000, (uint8_t)digital);
            for (unsigned i = 0; i < 12; ++i) vm_write8(0x12000 + i, (uint8_t)pressure);
            std::memset(vm_base + 0x18000, 0xa5, 0x210);
            ppu_context ctx{}; ctx.gpr[1] = 0x2f000;
            ctx.gpr[3] = 0x18000; ctx.gpr[4] = 0x14000;
            ctx.gpr[5] = 0x10000; ctx.gpr[6] = 0x13000;
            ps3_indirect_call_to(&ctx, 0x11aa178);
            if (ctx.gpr[1] != 0x2f000) return 4;
            for (unsigned control = 0; control < 16; ++control) {
                const float expected = control < 4 ? float((digital >> control) & 1) : float(pressure) / 255.0f;
                uint32_t raw = vm_read32(0x18040 + control * 4);
                float actual; std::memcpy(&actual, &raw, 4);
                if (!std::isfinite(actual) || std::fabs(actual - expected) > 0.000001f) {
                    std::fprintf(stderr, "Original sampler mismatch digital=%u pressure=%u control=%u actual=%g expected=%g raw=%08X\n",
                        digital, pressure, control, actual, expected, raw);
                    return 5;
                }
            }
            for (unsigned action = 0; action < 2; ++action) {
                const float expected = action ? float(pressure) / 255.0f : float((digital >> 3) & 1);
                uint32_t raw = vm_read32(0x18100 + action * 4);
                float actual; std::memcpy(&actual, &raw, 4);
                if (!std::isfinite(actual) || std::fabs(actual - expected) > 0.000001f) {
                    std::fprintf(stderr, "Original logical binding mismatch digital=%u pressure=%u action=%u actual=%g expected=%g\n",
                        digital, pressure, action, actual, expected);
                    return 6;
                }
            }
            ++cases;
        }
    }
    std::printf("{\"original_function\":\"0x11aa178\",\"cases\":%u,\"controls_per_case\":16,\"normalized\":true,\"logical_actions\":2}\n", cases);
    return 0;
}
