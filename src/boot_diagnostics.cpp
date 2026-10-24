#include "ppu_recomp.h"
#include <cstdio>
#include <cstdlib>

// Unsupported paths terminate before guest code can consume fabricated state.
extern "C" __declspec(noreturn)
void fifa_boot_missing(const char* kind, uint64_t value, ppu_context* ctx) {
    std::fprintf(stderr,
        "[fifa-block] {\"kind\":\"%s\",\"value\":%llu,\"guest_lr\":%llu,"
        "\"guest_pc\":%llu,\"thread_id\":%llu,\"guest_toc\":%llu,"
        "\"arguments\":[%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu]}\n",
        kind, (unsigned long long)value, (unsigned long long)(ctx ? ctx->lr : 0),
        (unsigned long long)(ctx ? ctx->cia : 0),
        (unsigned long long)(ctx ? ctx->thread_id : 0),
        (unsigned long long)(ctx ? ctx->gpr[2] : 0),
        (unsigned long long)(ctx ? ctx->gpr[3] : 0),
        (unsigned long long)(ctx ? ctx->gpr[4] : 0),
        (unsigned long long)(ctx ? ctx->gpr[5] : 0),
        (unsigned long long)(ctx ? ctx->gpr[6] : 0),
        (unsigned long long)(ctx ? ctx->gpr[7] : 0),
        (unsigned long long)(ctx ? ctx->gpr[8] : 0),
        (unsigned long long)(ctx ? ctx->gpr[9] : 0),
        (unsigned long long)(ctx ? ctx->gpr[10] : 0));
    std::fflush(stderr);
    std::_Exit(90);
}
