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

static int run_audio_context_init(const char* path, uint32_t source, uint32_t bytes,
                                  uint32_t bss_bytes, uint32_t callback,
                                  uint32_t alternate_base, const char* algorithm,
                                  bool copies_context = true, uint32_t entry = 0x30) {
    std::vector<uint8_t> blob(bytes);
    FILE* file = std::fopen(path, "rb");
    if (!file) return 3;
    bool valid = std::fread(blob.data(), 1, blob.size(), file) == blob.size() &&
                 std::fgetc(file) == EOF;
    std::fclose(file);
    if (!valid) return 3;
    vm_base = static_cast<uint8_t*>(std::calloc(1, source + blob.size()));
    if (!vm_base) return 3;
    std::memcpy(vm_base + source, blob.data(), blob.size());
    fifa_install_spu_policy();
    spu_begin_image(81);
    spu_register_function(getter_pc, fixture_get_buffer);
    spu_register_function(return_pc, fixture_return);
    spu_begin_image(0);
    const uint32_t context_words[] = {0x10203040, 0x50607080, 0x90a0b0c0, 0xd0e0f000};
    const uint32_t bases[] = {0, alternate_base, 0x4910, 0x10000};
    getter_calls = 0;
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
        for (unsigned i = 0; i < 4; ++i)
            spu_ls_write32(&ctx, parameters + 0x110 + 4 * i, context_words[i]);
        ctx.gpr[3] = spu_splat_u32(parameters);
        if (!invoke(ctx, base + entry)) return 4;
        const uint32_t state = base + bytes;
        const uint32_t descriptor = state + (copies_context ? 0x20 : 0x10);
        if (spu_ls_read32(&ctx, state) != getter_pc ||
            spu_ls_read32(&ctx, descriptor) != 0 ||
            spu_ls_read32(&ctx, descriptor + 4) != 0 ||
            spu_ls_read32(&ctx, descriptor + 8) != base + callback ||
            spu_ls_read32(&ctx, descriptor + 12) != 0xa5a5a5a5) return 5;
        if (copies_context)
            for (unsigned i = 0; i < 4; ++i)
                if (spu_ls_read32(&ctx, state + 0x10 + 4 * i) != context_words[i]) return 6;
        for (uint32_t offset = copies_context ? 0x30 : 0x20; offset < bss_bytes; ++offset)
            if (ctx.ls[state + offset] != 0xa5) return 10;
        if (std::memcmp(ctx.ls + base, blob.data(), blob.size())) return 7;
        for (unsigned i = 0; i < 16; ++i)
            if ((base && ctx.ls[base - 16 + i] != 0xa5) ||
                ctx.ls[state + bss_bytes + i] != 0xa5) return 8;
    }
    if (getter_calls) return 9; // Initialization copies the callback; it must not call it.
    std::free(vm_base);
    vm_base = nullptr;
    std::printf("{\"positions\":4,\"initialization_validated\":true,\"callbacks_relocated\":true,"
                "\"external_pointer_preserved\":true,%s"
                "\"code_preserved\":true,\"guards_preserved\":true,"
                "\"untouched_state_bytes\":%u,\"%s_algorithm_validated\":false}\n",
                copies_context ? "\"context_vector_preserved\":true," : "",
                bss_bytes - (copies_context ? 0x30 : 0x20), algorithm);
    return 0;
}

extern "C" int fifa_test_spu_compressor_init(const char* path) {
    return run_audio_context_init(path, 0x1fcf280, 0x3930, 0x30, 0x420, 0x24500, "compressor");
}

extern "C" int fifa_test_spu_reverb_init(const char* path) {
    return run_audio_context_init(path, 0x1ff6580, 0x50c0, 0x50, 0xc48, 0x27f00, "reverb");
}

extern "C" int fifa_test_spu_matrixpanner_init(const char* path) {
    return run_audio_context_init(path, 0x1feaa80, 0x770, 0x20, 0xb8, 0x3780, "matrix", false);
}

extern "C" int fifa_test_spu_delay_init(const char* path) {
    return run_audio_context_init(path, 0x1fd2c00, 0x1d70, 0x30, 0x2f8, 0x8300, "delay");
}

extern "C" int fifa_test_spu_audio_effect_init(const char* name, const char* path) {
    struct Effect {
        const char* name;
        uint32_t source, bytes, bss, callback, alternate_base;
        bool context;
        uint32_t entry = 0x30;
    };
    // Each case was reviewed independently against its locked source bytes.
    const Effect effects[] = {
        {"bandpass_fir64", 0x1fcca80, 0x1a60, 0x20, 0xb8, 0x8000, false},
        {"bandpass_iir2", 0x1fce580, 0xcc0, 0x20, 0xb8, 0x8000, false},
        {"distortion_clip", 0x1fd4a00, 0x400, 0x20, 0xb8, 0x8000, false},
        {"spureverbir1", 0x1fb6d00, 0x7f00, 0x100, 0xc8, 0xa100, true},
        {"spuroute", 0x1ffb680, 0x1120, 0x30, 0x170, 0x12f00, true, 0xd8}
    };
    for (const auto& effect : effects)
        if (!std::strcmp(name, effect.name))
            return run_audio_context_init(path, effect.source, effect.bytes, effect.bss,
                                          effect.callback, effect.alternate_base,
                                          effect.name, effect.context, effect.entry);
    return 2;
}
