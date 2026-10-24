#include "ppu_recomp.h"
#include <cstdint>
#include <cstdio>
#include <atomic>

extern "C" int np_is_initialized(void);
extern "C" int np_psnr_enabled(void);
extern "C" void ps3_hle_register_ctx(uint32_t, const char*, void (*)(ppu_context*));

// RPCS3 aa9ebd2f, sceNp.cpp: initialization and null-argument checks precede
// the offline error; country/language are not written on any of these errors.
// https://github.com/RPCS3/rpcs3/blob/aa9ebd2f/rpcs3/Emu/Cell/Modules/sceNp.cpp#L3836
static void account_region(ppu_context* ctx) {
    uint32_t result;
    if (!np_is_initialized()) result = 0x8002aa01; // SCE_NP_ERROR_NOT_INITIALIZED
    else if (!(uint32_t)ctx->gpr[3] || !(uint32_t)ctx->gpr[4]) result = 0x8002aa03;
    else if (np_psnr_enabled()) {
        // The port has no authenticated account-region provider. Keep this
        // unsupported online path explicit instead of inventing a country.
        fifa_boot_missing("np-account-region-online", 0xb1e0718b, ctx);
        return;
    }
    else {
        result = 0x8002aa0c; // SCE_NP_ERROR_OFFLINE
        static std::atomic_flag logged = ATOMIC_FLAG_INIT;
        if (!logged.test_and_set()) {
            std::fprintf(stderr, "[fifa-np] account region unavailable: manager offline\n");
        }
    }
    ctx->gpr[3] = (uint64_t)(int64_t)(int32_t)result;
}

extern "C" void fifa_register_offline_np(void) {
    ps3_hle_register_ctx(0xb1e0718b, "sceNpManagerGetAccountRegion", account_region);
}
