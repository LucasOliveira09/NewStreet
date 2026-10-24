#include "spu_workload.h"
#include <atomic>
#include <cstdio>
#include <cstdlib>

// Observe the first actual entry of each registered program at each physical base.
// No guest register, memory, PC, completion flag or dispatch state is changed.
extern "C" void fifa_trace_spu_entry(spu_context* ctx, unsigned slot,
                                     const char* name, unsigned source, unsigned base) {
    static const bool enabled = std::getenv("FIFA_SPU_ENTRY_TRACE") != nullptr;
    // All admitted raw-image bases are 16-byte aligned. A bounded bitmap also
    // covers relocatable images without allocation or a lock in guest execution.
    static std::atomic<uint64_t> seen[128][SPU_LS_SIZE / 16 / 64]{};
    if (!enabled || slot >= 128 || base >= SPU_LS_SIZE || (base & 15u)) return;
    const unsigned index = base / 16;
    const uint64_t mask = uint64_t{1} << (index % 64);
    if (seen[slot][index / 64].fetch_or(mask, std::memory_order_relaxed) & mask) return;
    std::fprintf(stderr, "[fifa-spu-entry] {\"name\":\"%s\",\"source_ea\":%u,\"ls_base\":%u,\"thread\":%u,\"pc\":%u}\n",
        name, source, base, ctx->spu_id, ctx->pc);
}

extern "C" int fifa_test_spu_entry_trace(void) {
    static spu_context ctx{};
    ctx.spu_id = 77;
    const unsigned bases[] = {0u, 0x7800u, 0x8480u, 0x7800u};
    for (unsigned base : bases) {
        ctx.pc = base + 0x30;
        fifa_trace_spu_entry(&ctx, 0, "fixture", 0x10000, base);
    }
    ctx.pc = 0x7830;
    fifa_trace_spu_entry(&ctx, 1, "other", 0x20000, 0x7800);
    return 0;
}
