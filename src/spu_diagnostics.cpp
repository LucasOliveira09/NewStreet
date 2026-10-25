#include "spu_workload.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

// The runner provides an existing private directory. Preserve the original
// context at a failure boundary; never reinterpret or modify its instructions.
extern "C" void fifa_dump_spu_state(const char* kind, spu_context* ctx) {
    const char* directory = std::getenv("FIFA_SPU_DUMP_DIR");
    if (!directory || !*directory || !ctx || !ctx->ls) return;
    std::string stem = std::string(std::strcmp(kind, "spu-sample") ? "spu-" : "sample-spu-") + std::to_string(ctx->spu_id) + "-" +
        std::to_string(ctx->image_id) + "-" + std::to_string(ctx->pc);
    std::string prefix = std::string(directory) + "/" + stem;
    size_t written = 0;
    if (FILE* file = std::fopen((prefix + ".ls").c_str(), "wb")) {
        written = std::fwrite(ctx->ls, 1, SPU_LS_SIZE, file);
        std::fclose(file);
    }
    if (FILE* file = std::fopen((prefix + ".json").c_str(), "wb")) {
        std::fprintf(file, "{\"kind\":\"%s\",\"image\":%d,\"thread\":%u,\"group\":%u,"
            "\"pc\":%u,\"lr\":%u,\"steps\":%llu,\"status\":%u,\"stop_code\":%u,\"gpr\":[\n",
            kind, ctx->image_id, ctx->spu_id, ctx->spu_group_id, ctx->pc,
            ctx->gpr[0]._u32[0], (unsigned long long)ctx->steps, ctx->status, ctx->stop_code);
        for (unsigned r = 0; r < 128; ++r)
            std::fprintf(file, "%s[%u,%u,%u,%u]\n", r ? "," : "",
                ctx->gpr[r]._u32[0], ctx->gpr[r]._u32[1], ctx->gpr[r]._u32[2], ctx->gpr[r]._u32[3]);
        std::fputs("],\"resident_code\":[", file);
        unsigned count = 0;
        for (const auto& span : ctx->resident_code) {
            if (!span.image_id) continue;
            std::fprintf(file, "%s{\"lsa\":%u,\"size\":%u,\"source\":%u,\"image\":%d,\"bias\":%d}",
                count++ ? "," : "", span.lsa, span.size, span.source_ea, span.image_id, span.relocation_bias);
        }
        std::fputs("]}\n", file);
        std::fclose(file);
    }
    std::fprintf(stderr, "[fifa-spu-state] {\"kind\":\"%s\",\"image\":%d,\"thread\":%u,"
        "\"pc\":%u,\"lr\":%u,\"local_store_bytes\":%zu,\"stem\":\"%s\"}\n",
        kind, ctx->image_id, ctx->spu_id, ctx->pc, ctx->gpr[0]._u32[0], written, stem.c_str());
    std::fflush(stderr);
}
