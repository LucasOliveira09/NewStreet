#include "spu_workload.h"
#include <atomic>
#include <cstdio>
#include <cstdlib>

// Observe the first actual entry of each statically registered program/base.
// No guest register, memory, PC, completion flag or dispatch state is changed.
extern "C" void fifa_trace_spu_entry(spu_context* ctx, unsigned slot,
                                     const char* name, unsigned source, unsigned base) {
    static const bool enabled = std::getenv("FIFA_SPU_ENTRY_TRACE") != nullptr;
    static std::atomic_flag seen[128]{};
    if (!enabled || slot >= 128 || seen[slot].test_and_set(std::memory_order_relaxed)) return;
    std::fprintf(stderr, "[fifa-spu-entry] {\"name\":\"%s\",\"source_ea\":%u,\"ls_base\":%u,\"thread\":%u,\"pc\":%u}\n",
        name, source, base, ctx->spu_id, ctx->pc);
}
