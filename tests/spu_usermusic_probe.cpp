#include "spu_workload.h"
#include "spu_helpers.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

extern "C" uint8_t* vm_base;
extern "C" void fifa_install_spu_policy(void);
extern "C" void spu_indirect_branch(spu_context*);
extern "C" int spu_run_with_halt(void (*)(spu_context*), spu_context*);
extern "C" void spu_begin_image(int);
extern "C" void spu_register_function(uint32_t, void (*)(spu_context*));
extern "C" void spu_overlay_note_get(spu_context*, uint32_t, const uint8_t*, uint32_t);

namespace {
bool returned, getter_arguments_valid;
unsigned getter_calls;
constexpr uint32_t parameters = 0x38000, audio = 0x20000, header = 0x30000;
constexpr uint32_t samples = 0x32000, getter_pc = 0x3d000, return_pc = 0x3d100;

void fixture_return(spu_context*) { returned = true; }

void fixture_get_buffer(spu_context* ctx) {
    // Authored service input: return this channel's real LS sample buffer.
    // All gain calculations and writes are performed by the original plugin.
    uint32_t channel = ctx->gpr[4]._u32[0];
    getter_arguments_valid = getter_arguments_valid && ctx->gpr[3]._u32[0] == header && channel < 2;
    ++getter_calls;
    ctx->gpr[3] = spu_splat_u32(samples + 0x400 * channel);
    ctx->pc = ctx->gpr[0]._u32[0];
    g_spu_trampoline_fn = spu_indirect_branch;
}

bool invoke(spu_context& ctx, uint32_t entry) {
    returned = false;
    ctx.gpr[0]._u32[0] = return_pc;
    ctx.gpr[1]._u32[0] = 0x3f000;
    ctx.pc = entry;
    ctx.status = SPU_STATUS_RUNNING;
    return !spu_run_with_halt(spu_indirect_branch, &ctx) && returned;
}

uint32_t float_bits(float value) {
    uint32_t bits;
    std::memcpy(&bits, &value, sizeof(bits));
    return bits;
}
}

extern "C" int fifa_test_spu_usermusic(const char* path) {
    std::vector<uint8_t> blob(0x4c0);
    FILE* file = std::fopen(path, "rb");
    if (!file) return 3;
    bool valid = std::fread(blob.data(), 1, blob.size(), file) == blob.size() &&
                 std::fgetc(file) == EOF;
    std::fclose(file);
    if (!valid) return 3;
    constexpr uint32_t source = 0x2004900;
    vm_base = static_cast<uint8_t*>(std::calloc(1, source + blob.size()));
    if (!vm_base) return 3;
    std::memcpy(vm_base + source, blob.data(), blob.size());
    fifa_install_spu_policy();
    spu_begin_image(81);
    spu_register_function(getter_pc, fixture_get_buffer);
    spu_register_function(return_pc, fixture_return);
    spu_begin_image(0);
    const uint32_t bases[] = {0, 0x1b780, 0x4910, 0x10000};
    for (auto base : bases) {
        static spu_context ctx;
        spu_context_init(&ctx, 81);
        ctx.image_id = 81;
        std::memset(ctx.ls, 0xa5, SPU_LS_SIZE);
        std::memcpy(ctx.ls + base, blob.data(), blob.size());
        spu_overlay_note_get(&ctx, source, ctx.ls + base, static_cast<uint32_t>(blob.size()));
        std::memset(ctx.ls + parameters, 0, 0x300);
        spu_ls_write32(&ctx, parameters + 20, parameters + 0x100);
        spu_ls_write32(&ctx, parameters + 0x104, parameters + 0x200);
        spu_ls_write32(&ctx, parameters + 0x200, getter_pc);
        ctx.gpr[3] = spu_splat_u32(parameters);
        if (!invoke(ctx, base + 0x30)) return 4;
        if (spu_ls_read32(&ctx, base + 0x4c0) != getter_pc ||
            spu_ls_read32(&ctx, base + 0x4d0) != 0 ||
            spu_ls_read32(&ctx, base + 0x4d4) != 0 ||
            spu_ls_read32(&ctx, base + 0x4d8) != base + 0x238 ||
            spu_ls_read32(&ctx, base + 0x4dc) != 0xa5a5a5a5) return 5;
        spu_ls_write32(&ctx, audio + 0x8128, header);
        spu_ls_write32(&ctx, header + 16, 0x40);
        spu_ls_write32(&ctx, header + 0x40, 0x100);
        spu_ls_write32(&ctx, header + 0x44, 0x200);
        ctx.ls[parameters + 58] = 2;
        getter_calls = 0;
        getter_arguments_valid = true;
        for (unsigned fade = 0; fade < 2; ++fade) {
            ctx.ls[parameters + 89] = fade ? 0 : 1;
            ctx.ls[parameters + 90] = fade ? 1 : 0;
            for (unsigned channel = 0; channel < 2; ++channel) {
                ctx.ls[header + 0x100 * (channel + 1) + 21] = 0x7f;
                for (unsigned sample = 0; sample < 256; ++sample)
                    spu_ls_write32(&ctx, samples + channel * 0x400 + 4 * sample,
                                   float_bits(static_cast<float>(channel + 1)));
            }
            ctx.gpr[3] = spu_splat_u32(parameters);
            ctx.gpr[4] = spu_splat_u32(audio);
            if (!invoke(ctx, base + 0x238) || ctx.gpr[3]._u32[0] != 1) return 6;
            if (ctx.ls[parameters + 90] != ctx.ls[parameters + 89]) return 7;
            for (unsigned channel = 0; channel < 2; ++channel) {
                if (ctx.ls[header + 0x100 * (channel + 1) + 21] != 0) return 8;
                for (unsigned sample = 0; sample < 256; ++sample) {
                    float gain = static_cast<float>(sample + 1) / 256.0f;
                    if (fade) gain = 1.0f - gain;
                    uint32_t expected = float_bits(static_cast<float>(channel + 1) * gain);
                    if (spu_ls_read32(&ctx, samples + channel * 0x400 + 4 * sample) != expected) return 9;
                }
            }
        }
        if (!getter_arguments_valid || getter_calls != 4) return 10;
        if (std::memcmp(ctx.ls + base, blob.data(), blob.size())) return 11;
        for (unsigned i = 0; i < 16; ++i)
            if ((base && ctx.ls[base - 16 + i] != 0xa5) ||
                ctx.ls[base + 0x4e0 + i] != 0xa5 ||
                ctx.ls[samples - 16 + i] != 0xa5 || ctx.ls[samples + 0x800 + i] != 0xa5) return 12;
    }
    std::free(vm_base);
    vm_base = nullptr;
    std::printf("{\"positions\":4,\"fade_cases\":8,\"channels\":2,\"compared_samples\":4096,"
                "\"initialization_validated\":true,\"relocation_validated\":true,"
                "\"code_preserved\":true,\"guards_preserved\":true}\n");
    return 0;
}
