#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include "ppu_recomp.h"

extern "C" void ppu_report_guest_lrs(void);
extern "C" void fifa_dump_guest_ranges(void);
extern "C" const char* g_hle_inflight[];
extern "C" ppu_context* volatile g_ppu_main_ctx;

static DWORD WINAPI report_activity(void* delay) {
    Sleep((DWORD)(uintptr_t)delay);
    std::fprintf(stderr, "[fifa-watchdog] pid=%lu guest thread activity (best effort)\n", GetCurrentProcessId());
    if (const ppu_context* main = g_ppu_main_ctx) {
        std::fprintf(stderr, "[fifa-watchdog] main_thread=%llu lr=0x%08X ctr=0x%08X sp=0x%08X r3=0x%08X r4=0x%08X\n",
            (unsigned long long)main->thread_id, (uint32_t)main->lr, (uint32_t)main->ctr,
            (uint32_t)main->gpr[1], (uint32_t)main->gpr[3], (uint32_t)main->gpr[4]);
    }
    for (unsigned tid = 0; tid < 64; ++tid) {
        const char* name = g_hle_inflight[tid];
        if (name) std::fprintf(stderr, "[fifa-watchdog] guest_thread=%u in_hle=%s\n", tid, name);
    }
    ppu_report_guest_lrs();
    fifa_dump_guest_ranges();
    std::fflush(stderr);
    return 0;
}

extern "C" void fifa_start_hang_diagnostics(uint32_t entry) {
    // Only the main FIFAZF process, not the parent EBOOT waiting on its child.
    const char* value = std::getenv("FIFA_WATCHDOG_AFTER_MS");
    if (!value || entry != 0x2143230) return; // ELF entry OPD, not its code address.
    char* end = nullptr;
    unsigned long delay = std::strtoul(value, &end, 10);
    if (*end || delay < 100 || delay > 300000) return;
    HANDLE thread = CreateThread(nullptr, 0, report_activity, (void*)(uintptr_t)delay, 0, nullptr);
    if (thread) CloseHandle(thread);
    else std::fprintf(stderr, "[fifa-watchdog] diagnostic thread creation failed: %lu\n", GetLastError());
}
