#include "ppu_recomp.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" void ppu_recomp_register(void);
extern "C" void ps3_indirect_call_to(ppu_context*, uint32_t);

extern "C" int fifa_test_input_bitset(void) {
    ppu_recomp_register();
    vm_base = (uint8_t*)std::calloc(1, 0x30000);
    if (!vm_base) return 3;
    vm_write32(0x10014, 16); // digital controls
    vm_write32(0x10018, 32); // pressure/analog controls
    vm_write32(0x10020, 0x11000);
    vm_write32(0x10024, 0x12000);
    unsigned cases = 0;
    const uint64_t values[] = {0, 1, 127, 255, 0x100, 0xffffffffffffffffull};
    for (unsigned control = 0; control < 64; ++control) {
        for (uint64_t value : values) {
            std::memset(vm_base + 0x11000, 0xa5, 64);
            std::memset(vm_base + 0x12000, 0xa5, 64);
            uint8_t expected_bits[64], expected_pressure[64];
            std::memset(expected_bits, 0xa5, sizeof expected_bits);
            std::memset(expected_pressure, 0xa5, sizeof expected_pressure);
            if (control < 16) {
                unsigned mask = 1u << (control & 7);
                if ((uint8_t)value) expected_bits[control / 8] |= mask;
                else expected_bits[control / 8] &= ~mask;
            } else if (control < 48) expected_pressure[control - 16] = (uint8_t)value;
            ppu_context ctx{};
            ctx.gpr[1] = 0x2f000; ctx.gpr[3] = 0x10000;
            ctx.gpr[4] = control; ctx.gpr[5] = value;
            // Use the public dispatcher to execute the original translated code.
            ps3_indirect_call_to(&ctx, 0x1434db8);
            if (ctx.gpr[1] != 0x2f000 ||
                std::memcmp(expected_bits, vm_base + 0x11000, 64) ||
                std::memcmp(expected_pressure, vm_base + 0x12000, 64)) {
                std::fprintf(stderr, "Original input bitset mismatch control=%u value=0x%llX bits=%02X.%02X expected=%02X.%02X\n",
                    control, (unsigned long long)value, vm_base[0x11000], vm_base[0x11001], expected_bits[0], expected_bits[1]);
                return 4;
            }
            ++cases;
        }
    }
    std::printf("{\"original_function\":\"0x1434db8\",\"cases\":%u,\"digital_bits\":true,\"pressure\":true,\"bounds\":true}\n", cases);
    return 0;
}
