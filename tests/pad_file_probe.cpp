#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "ppu_recomp.h"
#include "../vendor/ps3recomp/libs/input/cellPad.h"
#include <cstdio>
#include <cstdlib>

extern "C" int fifa_test_pad_file(const char* path) {
    vm_base = (uint8_t*)std::calloc(1, 0x20000);
    if (!vm_base || cellPadInit(1)) return 3;
    auto* data = (CellPadData*)(uintptr_t)0x10000;
    if (std::getenv("PAD_ALWAYS_CHANGE")) {
        FILE* file = std::fopen(path, "wb");
        if (!file) return 5;
        std::fputs("0x0008 1", file); std::fclose(file);
        if (cellPadGetData(0, data) || !vm_read32(0x10000) ||
            !(vm_read16(0x10004 + CELL_PAD_BTN_OFFSET_DIGITAL1 * 2) & 8)) return 8;
        if (cellPadGetData(0, data) || !vm_read32(0x10000) ||
            (vm_read16(0x10004 + CELL_PAD_BTN_OFFSET_DIGITAL1 * 2) & 8)) return 9;
        cellPadEnd();
        std::puts("{\"press_released\":true}");
        return 0;
    }
    for (unsigned attempt = 0; attempt < 20; ++attempt) {
        // Consume a fresh host report, then queue a one-report Start press.
        Sleep(8);
        if (cellPadGetData(0, data)) return 4;
        FILE* file = std::fopen(path, "wb");
        if (!file) return 5;
        std::fputs("0x0008 1", file);
        std::fclose(file);
        if (cellPadGetData(0, data)) return 4;
        if (vm_read32(0x10000)) continue; // Host tick advanced: try an empty read.
        Sleep(8);
        if (cellPadGetData(0, data)) return 4;
        const bool delivered = vm_read32(0x10000) &&
            (vm_read16(0x10004 + CELL_PAD_BTN_OFFSET_DIGITAL1 * 2) & 8);
        cellPadEnd();
        if (!delivered) {
            std::fprintf(stderr, "Start consumed by an empty read before a fresh report\n");
            return 6;
        }
        std::puts("{\"held_through_empty_read\":true}");
        return 0;
    }
    std::fprintf(stderr, "Could not observe an empty pad read\n");
    return 7;
}
