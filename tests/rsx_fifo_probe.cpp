#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "ppu_recomp.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" uint32_t ppu_vm_size;
extern "C" uint32_t ppu_hle_inject_base;
extern "C" uint32_t cellGcmSetupContext(uint32_t, uint32_t, uint32_t, uint32_t,
    uint32_t (*)(uint32_t, uint32_t), void (*)(uint32_t, uint32_t));
extern "C" void cellGcm_rsx_process_fifo(void);
extern "C" void fifa_install_fifo_policy(void);
extern "C" int cellGcm_take_flip_pending(void);
extern "C" int cellGcmSetDisplayBuffer(uint32_t, uint32_t, uint32_t, uint32_t, uint32_t);
extern "C" int cellGcmSetFlipCommand(uint32_t);

static uint32_t allocate(uint32_t size, uint32_t alignment) {
    static uint32_t next = 0x10000;
    next = (next + alignment - 1) & ~(alignment - 1);
    auto result = next; next += size; return result;
}
static void write(uint32_t a, uint32_t v) { vm_write32(a, v); }

extern "C" int fifa_test_rsx_fifo(const char* mode) {
    vm_base = (uint8_t*)std::calloc(1, 0x400000);
    if (!vm_base) return 3;
    ppu_vm_size = 0x400000;
    ppu_hle_inject_base = 0x300000;
    fifa_install_fifo_policy();
    const uint32_t context = cellGcmSetupContext(0x11000, 0x10000, 0x100000,
                                                0x100000, allocate, write);
    constexpr uint32_t io = 0x100000, control = 0x302000, label = 0x300400;
    if (!std::strcmp(mode, "frame-markers") || !std::strcmp(mode, "direct-frame")) {
        if (cellGcmSetDisplayBuffer(0, 0x200000, 512, 128, 128)) return 20;
        write(io, 0x00040064); write(io + 4, 0x400);
        write(io + 8, 0x0004006c); write(io + 12, 7);
        if (!std::strcmp(mode, "direct-frame")) {
            write(context + 8, io + 16); write(control, 16);
            if (cellGcmSetFlipCommand(0)) return 21;
            const int before = cellGcm_take_flip_pending();
            cellGcm_rsx_process_fifo();
            const int after = cellGcm_take_flip_pending();
            std::printf("{\"before_drain\":%d,\"after_drain\":%d,\"final_get\":%u,\"label\":%u}\n",
                        before, after, vm_read32(control + 4), vm_read32(label));
            return 0;
        }
        write(io + 16, 0xfead0000); // Genuine FIFO flip after the first completed frame.
        write(io + 20, 0x00040064); write(io + 24, 0x410);
        write(io + 28, 0x0004006c); write(io + 32, 9);
        write(io + 36, 0xfead0000);
        // More than the recovery backlog threshold remains after either marker.
        write(context + 8, io + 0x20000); write(control, 0x20000);
        cellGcm_rsx_process_fifo();
        const uint32_t first_get = vm_read32(control + 4);
        const bool second_untouched = vm_read32(label + 16) == 0;
        cellGcm_rsx_process_fifo(); // Must not mix the next frame before the host presents.
        const bool held = vm_read32(control + 4) == first_get;
        const int first_ready = cellGcm_take_flip_pending();
        cellGcm_rsx_process_fifo();
        const uint32_t second_get = vm_read32(control + 4);
        const int second_ready = cellGcm_take_flip_pending();
        std::printf("{\"first_get\":%u,\"second_untouched\":%s,\"held\":%s,"
                    "\"first_ready\":%d,\"second_get\":%u,\"second_ready\":%d,\"label\":%u}\n",
                    first_get, second_untouched ? "true" : "false", held ? "true" : "false",
                    first_ready, second_get, second_ready, vm_read32(label + 16));
        return 0;
    }
    if (!std::strcmp(mode, "invalid-jump") || !std::strcmp(mode, "unknown-word")) {
        write(io, !std::strcmp(mode, "invalid-jump") ? 0x20f00000 : 0x60000000);
        write(context + 8, io + 4); write(control, 4);
        cellGcm_rsx_process_fifo();
        return 19; // The strict host must stop before changing GET.
    }
    const bool park = !std::strcmp(mode, "park");
    uint32_t end = park ? 0x50 : 0x20;
    if (park) {
        write(io, 0x20000000); // Wait here until the producer links its work.
        write(io + 0x40, 0x00041d6c); write(io + 0x44, 0x400);
        write(io + 0x48, 0x00041d74); write(io + 0x4c, 7);
    } else {
        write(io, 0x00040064); write(io + 4, 0x400);
        write(io + 8, 0x00040068); write(io + 12, 7);
        write(io + 16, 0x00040064); write(io + 20, 0x410);
        write(io + 24, 0x0004006c); write(io + 28, 9);
    }
    write(context + 8, io + end);
    write(control, end);
    cellGcm_rsx_process_fifo();
    Sleep(80); // Longer than the old 50 ms recovery heuristic.
    for (unsigned n = 0; n < 10; ++n) cellGcm_rsx_process_fifo();
    const uint32_t waiting_get = vm_read32(control + 4);
    const bool untouched = vm_read32(park ? label : label + 16) == 0;
    if (park) write(io, 0x20000040); // Genuine producer update, no host bypass.
    else write(label, 7);
    cellGcm_rsx_process_fifo();
    std::printf("{\"waiting_get\":%u,\"untouched\":%s,\"final_get\":%u,\"label\":%u}\n",
        waiting_get, untouched ? "true" : "false", vm_read32(control + 4),
        vm_read32(park ? label : label + 16));
    return 0;
}
