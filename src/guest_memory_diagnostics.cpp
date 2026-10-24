#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "ppu_recomp.h"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <string>

// Opt-in failure snapshots. Skip uncommitted/unreadable pages rather than
// triggering lazy guest allocation and inventing bytes for missing memory.
extern "C" void fifa_dump_guest_ranges(void) {
    const char* directory = std::getenv("FIFA_PPU_DUMP_DIR");
    const char* cursor = std::getenv("FIFA_PPU_DUMP_RANGES");
    if (!directory || !cursor || !vm_base) return;
    for (unsigned count = 0; *cursor && count < 16; ++count) {
        char* next = nullptr;
        uint64_t address = std::strtoull(cursor, &next, 0);
        if (next == cursor || *next != ':') break;
        cursor = next + 1;
        uint64_t bytes = std::strtoull(cursor, &next, 0);
        if (next == cursor || (*next && *next != ',')) break;
        cursor = *next ? next + 1 : next;
        if (!bytes || bytes > 0x400000 || address > 0x100000000ULL - bytes) continue;
        uint64_t end = address + bytes;
        while (address < end) {
            MEMORY_BASIC_INFORMATION info{};
            if (!VirtualQuery(vm_base + address, &info, sizeof info)) break;
            uintptr_t region_end = (uintptr_t)info.BaseAddress + info.RegionSize;
            if (region_end <= (uintptr_t)(vm_base + address)) break;
            uint64_t finish = (std::min)(end, (uint64_t)(region_end - (uintptr_t)vm_base));
            if (info.State == MEM_COMMIT && !(info.Protect & (PAGE_NOACCESS | PAGE_GUARD))) {
                std::string name = "guest-" + std::to_string(address) + "-" + std::to_string(finish - address) + ".bin";
                std::string path = std::string(directory) + "/" + name;
                size_t written = 0;
                if (FILE* file = std::fopen(path.c_str(), "wb")) {
                    written = std::fwrite(vm_base + address, 1, (size_t)(finish - address), file);
                    std::fclose(file);
                }
                std::fprintf(stderr, "[fifa-memory] {\"address\":%llu,\"bytes\":%zu,\"file\":\"%s\"}\n",
                    (unsigned long long)address, written, name.c_str());
            }
            address = finish;
        }
    }
    std::fflush(stderr);
}
