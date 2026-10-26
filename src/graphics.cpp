// Frame-clock contract: pinned ps3recomp/templates/project/main.cpp.
// Start only after the title has created its real GCM context.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <timeapi.h>
#include "ppu_recomp.h"
#include <atomic>
#include <chrono>
#include <cstdio>
#include <string>

extern "C" {
int rsx_d3d12_backend_init(uint32_t, uint32_t, const char*);
void rsx_d3d12_backend_present(void);
void rsx_d3d12_backend_shutdown(void);
int rsx_d3d12_backend_pump_messages(void);
void cellGcmTickVBlank(void);
void cellGcmTickFlip(void);
int cellGcm_take_flip_pending(void);
void cellGcm_rsx_process_fifo(void);
void cellGcm_fifo_kick_wait(unsigned);
void ps3recomp_gcm_fifo_set_fault_handler(void (*)(const char*, uint32_t, uint32_t));
void ps3recomp_gcm_fifo_set_frame_boundaries(int);
}

static std::atomic<bool> started{false};
static void fifo_fault(const char* reason, uint32_t get, uint32_t put) {
    const std::string kind = std::string("rsx-fifo-") + reason;
    fifa_boot_missing(kind.c_str(), ((uint64_t)get << 32) | put, nullptr);
}
extern "C" void fifa_install_fifo_policy(void) {
    ps3recomp_gcm_fifo_set_fault_handler(fifo_fault);
    ps3recomp_gcm_fifo_set_frame_boundaries(1);
}
static HANDLE ready = nullptr;
static uint64_t guest_flips = 0; // Renderer-thread owned; no empty-window presents counted.

static void present_pending(void) {
    if (!cellGcm_take_flip_pending()) return;
    rsx_d3d12_backend_present();
    ++guest_flips;
    if (guest_flips <= 3 || guest_flips % 60 == 0)
        std::fprintf(stderr, "[fifa-present] {\"guest_flips\":%llu}\n", (unsigned long long)guest_flips);
}

static DWORD WINAPI frame_clock(void*) {
    int result = rsx_d3d12_backend_init(1280, 720, "FIFA Street");
    if (result) fifa_boot_missing("rsx-backend", (uint32_t)result, nullptr);
    std::fprintf(stderr, "[fifa-rsx] D3D12 initialized; no game frame established\n");
    timeBeginPeriod(1);
    SetEvent(ready);
    using clock = std::chrono::steady_clock;
    auto next_tick = clock::now();
    constexpr auto period = std::chrono::nanoseconds(16666667);
    for (;;) {
        cellGcm_fifo_kick_wait(4);
        auto now = clock::now();
        unsigned fired = 0;
        while (now >= next_tick && fired < 240) {
            cellGcmTickVBlank();
            cellGcmTickFlip();
            present_pending();
            cellGcm_rsx_process_fifo();
            next_tick += period;
            ++fired;
        }
        if (fired == 240) next_tick = now + period;
        present_pending();
        cellGcm_rsx_process_fifo();
        if (rsx_d3d12_backend_pump_messages()) {
            rsx_d3d12_backend_shutdown();
            timeEndPeriod(1);
            std::fprintf(stderr, "[fifa-window-closed] diagnostic session ended\n");
            ExitProcess(93);
        }
    }
}

extern "C" void fifa_start_graphics(ppu_context* ctx) {
    if (started.exchange(true)) return;
    fifa_install_fifo_policy();
    ready = CreateEventW(nullptr, TRUE, FALSE, nullptr);
    if (!ready) fifa_boot_missing("rsx-event", GetLastError(), ctx);
    HANDLE renderer = CreateThread(nullptr, 4u * 1024 * 1024, frame_clock, nullptr, 0, nullptr);
    if (!renderer) fifa_boot_missing("rsx-thread", GetLastError(), ctx);
    CloseHandle(renderer);
    if (WaitForSingleObject(ready, 30000) != WAIT_OBJECT_0)
        fifa_boot_missing("rsx-init-timeout", GetLastError(), ctx);
    CloseHandle(ready);
}
