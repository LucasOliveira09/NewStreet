#include "spu_workload.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

extern "C" void fifa_install_spu_policy(void);
extern "C" void spu_indirect_branch(spu_context*);
extern "C" int spu_run_with_halt(void (*)(spu_context*), spu_context*);
extern "C" void spu_begin_image(int);
extern "C" void spu_register_function(uint32_t, void (*)(spu_context*));
using native_spu_fn = void (*)(spu_context*);
extern "C" native_spu_fn spu_lifted_lookup(const spu_context*, uint32_t);
static bool returned_to_caller;
static void fixture_return(spu_context*) { returned_to_caller = true; }

// Execute the original table constructor and BC encoders on authored LS pixels.
// This test-only entry neither queues jobs nor replaces the game's main entry.
extern "C" int fifa_test_spu_dxt(const char* image, const char* input, const char* output,
                                 const char* width_text, const char* height_text, const char* format) {
    unsigned width = (unsigned)std::atoi(width_text), height = (unsigned)std::atoi(height_text);
    bool bc3 = !std::strcmp(format, "3");
    if ((!bc3 && std::strcmp(format, "1")) || width < 4 || width > 64 ||
        height < 4 || height > 64 || (width | height) & 3) return 3;
    const unsigned source_pitch = width * 4 + 16;
    const unsigned row_bytes = width / 4 * (bc3 ? 16 : 8);
    const unsigned output_pitch = row_bytes + 16;
    const unsigned output_bytes = output_pitch * (height / 4);
    static spu_context context;
    spu_context_init(&context, 79);
    context.image_id = 0x23f1371d;
    FILE* file = std::fopen(image, "rb");
    if (!file) return 3;
    bool valid = std::fread(context.ls + 0x80, 1, 0x2250, file) == 0x2250 && std::fgetc(file) == EOF;
    std::fclose(file);
    if (!valid) return 3;
    fifa_install_spu_policy();
    if (!spu_lifted_lookup(&context, 0x3e0)) return 77;
    spu_begin_image(context.image_id);
    spu_register_function(0x3d000, fixture_return);
    spu_begin_image(0);
    context.gpr[0]._u32[0] = 0x3d000;
    context.gpr[1]._u32[0] = 0x3f000;
    context.status = SPU_STATUS_RUNNING;
    context.pc = 0x3e0;
    if (spu_run_with_halt(spu_indirect_branch, &context) || !returned_to_caller) return 5;
    file = std::fopen(input, "rb");
    if (!file) return 3;
    std::vector<uint8_t> source(source_pitch * height);
    valid = std::fread(source.data(), 1, source.size(), file) == source.size() && std::fgetc(file) == EOF;
    std::fclose(file);
    if (!valid) return 3;
    std::memcpy(context.ls + 0x8000, source.data(), source.size());
    std::memset(context.ls + 0x1ff00, 0xa5, 0x3000);
    returned_to_caller = false;
    context.gpr[0]._u32[0] = 0x3d000;
    context.gpr[1]._u32[0] = 0x3f000;
    context.gpr[3]._u32[0] = 0x20000;
    context.gpr[4]._u32[0] = 0x8000;
    context.gpr[5]._u32[0] = source_pitch;
    context.gpr[6]._u32[0] = output_pitch;
    context.gpr[7]._u32[0] = width;
    context.gpr[8]._u32[0] = height;
    context.pc = bc3 ? 0xa80 : 0x3f0;
    if (spu_run_with_halt(spu_indirect_branch, &context) || !returned_to_caller) return 5;
    if (context.gpr[3]._u32[0] != output_bytes ||
        std::memcmp(context.ls + 0x8000, source.data(), source.size())) return 6;
    for (unsigned i = 0x1ff00; i < 0x20000; ++i) if (context.ls[i] != 0xa5) return 6;
    for (unsigned i = 0x20000 + output_bytes; i < 0x22f00; ++i) if (context.ls[i] != 0xa5) return 6;
    for (unsigned y = 0; y < height / 4; ++y)
        for (unsigned x = row_bytes; x < output_pitch; ++x)
            if (context.ls[0x20000 + y * output_pitch + x] != 0xa5) return 6;
    file = std::fopen(output, "wb");
    if (!file) return 3;
    valid = std::fwrite(context.ls + 0x20000, 1, output_bytes, file) == output_bytes;
    valid = std::fclose(file) == 0 && valid;
    if (!valid) return 3;
    std::puts("{\"source_preserved\":true,\"output_guards\":true,\"row_padding\":true}");
    return 0;
}
