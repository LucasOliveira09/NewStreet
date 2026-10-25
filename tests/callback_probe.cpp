#include "ppu_recomp.h"
#include "ps3emu/guest_call.h"
#include <cstdio>
#include <cstdlib>

extern "C" void fifa_install_guest_callbacks(void);
extern "C" void ppu_register_function(uint32_t, void (*)(ppu_context*));
extern "C" PPU_THREAD_LOCAL ppu_context* g_active_ctx;
static uint64_t argument_sum = 0, identity = 0, toc = 0;
static void guest_function(ppu_context* ctx) {
    for (unsigned i = 3; i <= 10; ++i) argument_sum += ctx->gpr[i];
    identity = ctx->thread_id; toc = ctx->gpr[2];
    ctx->gpr[3] = argument_sum;
}

extern "C" int fifa_test_guest_callbacks(void) {
    vm_base = (uint8_t*)std::calloc(1, 0x20000);
    if (!vm_base) return 3;
    vm_write32(0x10000, 0x123400); vm_write32(0x10004, 0x6789);
    ppu_register_function(0x123400, guest_function);
    ppu_context caller{}; caller.thread_id = 77;
    g_active_ctx = &caller;
    fifa_install_guest_callbacks();
    ps3_invoke_guest(0x10000, 0x100000001ULL, 2, 3, 4, 5, 6, 7, 8);
    if (argument_sum != 0x100000024ULL || g_active_ctx != &caller) return 4;
    argument_sum = 0;
    const auto result = g_ps3_guest_caller_result(0x10000, 0x100000001ULL, 2, 3, 4, 5, 6, 7, 8);
    std::printf("{\"argument_sum\":%llu,\"identity\":%llu,\"toc\":%llu,\"callback_return\":%llu,\"caller_restored\":%s}\n",
        (unsigned long long)argument_sum, (unsigned long long)identity,
        (unsigned long long)toc, (unsigned long long)result, g_active_ctx == &caller ? "true" : "false");
    return 0;
}
