#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "ppu_recomp.h"
#include "../vendor/ps3recomp/libs/input/cellPad.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" int fifa_test_pad_modes(void) {
    vm_base = (uint8_t*)std::calloc(1, 0x20000);
    if (!vm_base || cellPadInit(1)) return 3;
    auto* data = (CellPadData*)(uintptr_t)0x10000;
    // RPCS3 aa9ebd2f cellPad.h / pad_get_data: valid lengths and mode nibbles.
    const unsigned settings[] = {0, 2, 4, 6};
    const unsigned lengths[] = {8, 20, 24, 24};
    const unsigned modes[] = {0x74, 0x7a, 0x7c, 0x7c};
    for (unsigned mode = 0; mode < 4; ++mode) {
        if (cellPadSetPortSetting(0, settings[mode])) return 4;
        std::memset(vm_base + 0x10004, 0xa5, sizeof(CellPadData) - 4);
        bool fresh = false;
        for (unsigned poll = 0; poll < 50; ++poll) {
            Sleep(2);
            if (cellPadGetData(0, data)) return 4;
            if (vm_read32(0x10000)) { fresh = true; break; }
        }
        if (!fresh || vm_read32(0x10000) != lengths[mode] || vm_read16(0x10006) != modes[mode]) {
            std::fprintf(stderr, "Pad mode %u: len=%u header=%X, expected len=%u header=%X\n",
                settings[mode], vm_read32(0x10000), vm_read16(0x10006), lengths[mode], modes[mode]);
            return 11;
        }
        if (!(settings[mode] & 2)) {
            for (unsigned word = 8; word < 20; ++word)
                if (vm_read16(0x10004 + word * 2)) return 12;
        }
        const unsigned written_words = lengths[mode] < 20 ? 20 : lengths[mode];
        for (unsigned byte = 4 + written_words * 2; byte < sizeof(CellPadData); ++byte) {
            if (vm_base[0x10000 + byte] != 0xa5) {
                std::fprintf(stderr, "Pad mode %u overwrote untouched payload at +%u\n", settings[mode], byte);
                return 13;
            }
        }
    }
    cellPadEnd();
    std::puts("{\"modes\":4,\"lengths\":true,\"headers\":true,\"untouched_tail\":true}");
    return 0;
}

extern "C" int fifa_test_pad_empty_payload(void) {
    vm_base = (uint8_t*)std::calloc(1, 0x20000);
    if (!vm_base || cellPadInit(1)) return 3;
    auto* data = (CellPadData*)(uintptr_t)0x10000;
    if (cellPadGetData(0, data)) return 4;
    for (unsigned attempt = 0; attempt < 20; ++attempt) {
        std::memset(vm_base + 0x10004, 0xa5, sizeof(CellPadData) - 4);
        if (cellPadGetData(0, data)) return 4;
        if (vm_read32(0x10000)) continue;
        for (unsigned offset = 4; offset < sizeof(CellPadData); ++offset)
            if (vm_base[0x10000 + offset] != 0xa5) {
                std::fprintf(stderr, "Empty report overwrote button payload at +%u\n", offset);
                return 10;
            }
        cellPadEnd();
        std::puts("{\"empty_payload_preserved\":true}");
        return 0;
    }
    return 7;
}

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
        Sleep(20);
        if (cellPadGetData(0, data)) return 4;
        FILE* file = std::fopen(path, "wb");
        if (!file) return 5;
        std::fputs("0x0008 1", file);
        std::fclose(file);
        if (cellPadGetData(0, data)) return 4;
        if (vm_read32(0x10000)) continue; // Host tick advanced: try an empty read.
        // GetTickCount64 can advance in coarse Windows timer ticks. Wait for
        // an actual report, rather than assuming an 8 ms sleep produced one.
        bool delivered = false;
        for (unsigned poll = 0; poll < 50; ++poll) {
            Sleep(2);
            if (cellPadGetData(0, data)) return 4;
            if (!vm_read32(0x10000)) continue;
            delivered = (vm_read16(0x10004 + CELL_PAD_BTN_OFFSET_DIGITAL1 * 2) & 8) != 0;
            break;
        }
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
