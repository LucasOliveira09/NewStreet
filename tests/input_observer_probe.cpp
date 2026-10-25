#include "ppu_recomp.h"
#include "../vendor/ps3recomp/libs/input/cellPad.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" void ppu_hle_init(void);
extern "C" void ps3_hle_call(uint32_t, ppu_context*);
extern "C" void fifa_install_input_observer(void);

extern "C" int fifa_test_input_observer(void) {
    vm_base = (uint8_t*)std::calloc(1, 0x30000);
    if (!vm_base || cellPadInit(1)) return 3;
    ppu_hle_init();
    fifa_install_input_observer();
    vm_write32(0x10020, 0x11000);
    vm_write32(0x11008, 1);
    vm_write32(0x11014, 4);
    vm_write32(0x11018, 12);
    vm_write32(0x11020, 0x12000);
    vm_write32(0x11024, 0x13000);
    vm_write32(0x10058, 0x00080000);
    vm_write8(0x12000, 8);
    uint8_t before[0x5c]; std::memcpy(before, vm_base + 0x10000, sizeof before);
    uint8_t device_before[0x2c]; std::memcpy(device_before, vm_base + 0x11000, sizeof device_before);
    for (unsigned pass = 0; pass < 7; ++pass) {
        ppu_context ctx{};
        for (unsigned reg = 0; reg < 32; ++reg) ctx.gpr[reg] = 0xa5000000 + reg;
        ctx.gpr[1] = 0x2f000; ctx.gpr[3] = 0x1005c;
        ctx.lr = pass == 6 ? 0x1234 : 0x1434eb0;
        if (pass == 2) { vm_write8(0x12000, 0); vm_write32(0x10058, 0); }
        if (pass == 3) { vm_write8(0x1300a, 255); vm_write32(0x10058, 0x40); }
        if (pass == 4) { vm_write8(0x1300a, 0); vm_write32(0x10058, 0); }
        if (pass == 5) vm_write32(0x10020, 0xffffffff); // Never dereference an invalid observed device.
        if (pass == 6) { vm_write32(0x10020, 0x11000); vm_write8(0x12000, 8); }
        ps3_hle_call(0xa703a51d, &ctx);
        if (ctx.gpr[3] || ctx.gpr[1] != 0x2f000 || vm_read32(0x1005c) != 1) return 4;
        for (unsigned reg = 4; reg < 32; ++reg)
            if (ctx.gpr[reg] != 0xa5000000 + reg) return 5;
        if (vm_read8(0x12000) != (pass < 2 || pass == 6 ? 8 : 0)) return 6;
        if (vm_read8(0x1300a) != (pass == 3 ? 255 : 0) ||
            std::memcmp(device_before, vm_base + 0x11000, sizeof device_before)) return 6;
        // Only the genuine API output (manager+0x5c) and normal ABI TOC slot
        // may change; the observed manager/device/bitset remain untouched.
        if (pass < 2 && std::memcmp(before, vm_base + 0x10000, sizeof before)) return 7;
    }
    cellPadEnd();
    std::puts("{\"api_result\":true,\"registers\":true,\"observed_memory\":true}");
    return 0;
}
