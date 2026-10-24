#include "ppu_recomp.h"
#include "ps3emu/guest_call.h"

extern "C" uint64_t ppu_guest_call(uint32_t, uint64_t, uint64_t, uint64_t, uint64_t,
                                   uint64_t, uint64_t, uint64_t, uint64_t);

static void call_guest(uint32_t opd, uint64_t a0, uint64_t a1, uint64_t a2, uint64_t a3,
                       uint64_t a4, uint64_t a5, uint64_t a6, uint64_t a7) {
    ppu_guest_call(opd, a0, a1, a2, a3, a4, a5, a6, a7);
}

extern "C" void fifa_install_guest_callbacks(void) {
    g_ps3_guest_caller = call_guest;
}
