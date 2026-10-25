#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "spu_workload.h"
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

extern "C" uint8_t* vm_base;
extern "C" void spu_indirect_branch(spu_context*);

static bool readable(uint32_t address, uint32_t bytes) {
    if (!vm_base || !bytes || bytes > 0x400000 || (uint64_t)address + bytes > 0x100000000ULL) return false;
    const uint8_t* cursor = vm_base + address;
    const uint8_t* end = cursor + bytes;
    while (cursor < end) {
        MEMORY_BASIC_INFORMATION info{};
        if (!VirtualQuery(cursor, &info, sizeof info) || info.State != MEM_COMMIT ||
            (info.Protect & (PAGE_NOACCESS | PAGE_GUARD))) return false;
        auto next = (uint8_t*)info.BaseAddress + info.RegionSize;
        if (next <= cursor) return false;
        cursor = next;
    }
    return true;
}

static bool save(const std::string& path, const void* data, size_t bytes) {
    FILE* file = std::fopen(path.c_str(), "wb");
    if (!file) return false;
    bool ok = std::fwrite(data, 1, bytes, file) == bytes;
    return std::fclose(file) == 0 && ok;
}

// Observe the original AssetStream ABI only: zlib(out, capacity, in, bytes),
// LZMA(out, capacity, in, bytes), RefPack(out, in, bytes).
// Reads are opt-in and never allocate guest pages.
// The nested drain follows translated tail transfers through the actual return.
extern "C" void fifa_observe_spu_job(spu_context* ctx, spu_lifted_entry_fn entry, int codec) {
    const char* folder = std::getenv("FIFA_SPU_JOB_TRACE_DIR");
    if (!folder || !*folder || codec < 0 || codec > 2) { entry(ctx); return; }
    static std::atomic<unsigned> counts[3]{};
    unsigned number = counts[codec].fetch_add(1);
    if (number >= 32) { entry(ctx); return; }
    uint32_t output = ctx->gpr[3]._u32[0];
    const bool refpack = codec == 1;
    const char* codec_name = codec == 0 ? "zlib" : (refpack ? "refpack" : "lzma");
    uint32_t input = ctx->gpr[refpack ? 4 : 5]._u32[0];
    uint32_t bytes = ctx->gpr[refpack ? 5 : 6]._u32[0];
    uint32_t capacity = refpack ? 0 : ctx->gpr[4]._u32[0];
    if (!readable(input, bytes)) { entry(ctx); return; }
    std::vector<uint8_t> compressed(vm_base + input, vm_base + input + bytes);
    // RefPack flags: bit 7 selects 32-bit sizes; bit 0 adds compressed size.
    // https://github.com/OpenSAGE/OpenSAGE/blob/master/src/OpenSage.FileFormats.RefPack/RefPackStream.cs
    if (refpack && bytes >= 5 && (compressed[0] & 0x3e) == 0x10 && compressed[1] == 0xfb) {
        size_t width = (compressed[0] & 0x80) ? 4 : 3;
        size_t header = 2 + ((compressed[0] & 1) ? width : 0);
        if (bytes >= header + width)
            for (size_t i = 0; i < width; ++i) capacity = (capacity << 8) | compressed[header + i];
    }
    std::string stem = std::string(codec_name) + "-" + std::to_string(number);
    std::string prefix = std::string(folder) + "/" + stem;
    if (!save(prefix + ".input", compressed.data(), compressed.size())) { entry(ctx); return; }
    uint32_t return_pc = ctx->gpr[0]._u32[0];
    uint32_t depth = ctx->host_depth;
    uint32_t drain_return = ctx->drain_ret_pc;
    ctx->host_depth++;
    entry(ctx);
    spu_drain_call(ctx, return_pc);
    ctx->host_depth = depth;
    ctx->drain_ret_pc = drain_return;
    if (!depth) g_spu_trampoline_fn = spu_indirect_branch;
    bool captured = readable(output, capacity) && save(prefix + ".output", vm_base + output, capacity);
    if (FILE* file = std::fopen((prefix + ".json").c_str(), "wb")) {
        std::fprintf(file, "{\"codec\":\"%s\",\"thread\":%u,\"input_ea\":%u,\"input_bytes\":%u,"
            "\"output_ea\":%u,\"output_bytes\":%u,\"return_pc\":%u,\"guest_result\":%u,\"captured\":%s}\n",
            codec_name, ctx->spu_id, input, bytes, output, capacity,
            return_pc, ctx->gpr[3]._u32[0], captured ? "true" : "false");
        std::fclose(file);
    }
    std::fprintf(stderr, "[fifa-spu-job] %s input=%u output=%u captured=%d\n", stem.c_str(), bytes, capacity, captured);
}
