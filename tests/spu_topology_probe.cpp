#include "spu_workload.h"
#include <cstdio>
#include <cstring>
#include <vector>
#include <cstdlib>

extern "C" void fifa_install_spu_policy(void);
extern "C" void spu_indirect_branch(spu_context*);
extern "C" int spu_run_with_halt(void (*)(spu_context*), spu_context*);
extern "C" void spu_begin_image(int);
extern "C" void spu_register_function(uint32_t, void (*)(spu_context*));
using native_spu_fn = void (*)(spu_context*);
extern "C" native_spu_fn spu_lifted_lookup(const spu_context*, uint32_t);
static bool returned_to_caller;
static void fixture_return(spu_context*) { returned_to_caller = true; }

// This fixture exercises ONLY the original static constructors, in CRT order.
// It does not replace the module's main body or claim to validate AI algorithms.
static int run_original_constructors(const char* image, size_t image_bytes, int image_id,
                                     uint32_t code_end, const uint32_t* entries, size_t entry_count) {
    std::vector<uint8_t> blob(image_bytes);
    FILE* file = std::fopen(image, "rb");
    if (!file) return 3;
    bool valid = std::fread(blob.data(), 1, blob.size(), file) == blob.size() && std::fgetc(file) == EOF;
    std::fclose(file);
    if (!valid) return 3;
    fifa_install_spu_policy();
    static spu_context context;
    spu_context_init(&context, 81);
    context.image_id = image_id;
    for (size_t i = 0; i < entry_count; ++i) if (!spu_lifted_lookup(&context, entries[i])) return 77;
    spu_begin_image(context.image_id);
    spu_register_function(0x3d000, fixture_return);
    spu_begin_image(0);
    // SPU context initialization zeros LS, as required for the module's BSS.
    std::memcpy(context.ls + 0x80, blob.data(), blob.size());
    unsigned count = 0;
    for (size_t i = 0; i < entry_count; ++i) {
        returned_to_caller = false;
        context.gpr[0]._u32[0] = 0x3d000;
        context.gpr[1]._u32[0] = 0x3f000;
        context.pc = entries[i];
        context.status = SPU_STATUS_RUNNING;
        if (spu_run_with_halt(spu_indirect_branch, &context) || !returned_to_caller) return 5;
        if (std::memcmp(context.ls + 0x80, blob.data(), code_end - 0x80)) return 6;
        ++count;
    }
    std::printf("{\"original_constructors\":%u,\"code_preserved\":true,\"ai_algorithm_validated\":false}\n", count);
    return 0;
}

extern "C" int fifa_test_spu_topology_constructors(const char* image) {
    const uint32_t entries[] = {0xd090,0xcfd0,0xa128,0x7db8,0x7a50,0x68b8,0xdc8};
    return run_original_constructors(image, 0xdb40, 0x206cb06e, 0xd360, entries, 7);
}

extern "C" int fifa_test_spu_railtracks_constructors(const char* image) {
    const uint32_t entries[] = {0x26868,0x24a38,0x1edb0,0x1d390};
    return run_original_constructors(image, 0x2a6a0, 0x2f0d60bc, 0x29080, entries, 4);
}

extern "C" int fifa_test_spu_ant_secondary_constructors(const char* image) {
    const uint32_t entries[] = {0x40b8,0x1de8};
    return run_original_constructors(image, 0x45c0, 0x218664f8, 0x4130, entries, 2);
}

extern "C" uint8_t* vm_base;
extern "C" void spu_overlay_note_get(spu_context*, uint32_t, const uint8_t*, uint32_t);

// The original PIC constructors run through checked source ownership, including
// both observed LS placements. This fixture never calls a replacement main.
static int run_pic_constructors(const char* image, uint32_t source, size_t bytes,
                                uint32_t code_end, const uint32_t* entries) {
    std::vector<uint8_t> blob(bytes);
    FILE* file = std::fopen(image, "rb");
    if (!file) return 3;
    bool valid = std::fread(blob.data(), 1, bytes, file) == bytes && std::fgetc(file) == EOF;
    std::fclose(file);
    if (!valid) return 3;
    vm_base = (uint8_t*)std::calloc(1, source + bytes);
    if (!vm_base) return 3;
    std::memcpy(vm_base + source, blob.data(), bytes);
    fifa_install_spu_policy();
    spu_begin_image(81);
    spu_register_function(0x3d000, fixture_return);
    spu_begin_image(0);
    const uint32_t bases[] = {0, 0x48f0, 0x4910, 0x10000};
    std::vector<uint8_t> reference;
    unsigned count = 0;
    for (uint32_t base : bases) {
        static spu_context ctx;
        spu_context_init(&ctx, 81);
        ctx.image_id = 81;
        std::memset(ctx.ls, 0xa5, SPU_LS_SIZE);
        std::memcpy(ctx.ls + base, blob.data(), bytes);
        std::memset(ctx.ls + base + bytes, 0, 0x50); // Original PIC BSS extent.
        spu_overlay_note_get(&ctx, source, ctx.ls + base, (uint32_t)bytes);
        for (unsigned i = 0; i < 3; ++i) { // Table is traversed forwards by this CRT.
            returned_to_caller = false;
            ctx.gpr[0]._u32[0] = 0x3d000;
            ctx.gpr[1]._u32[0] = 0x3f000;
            ctx.gpr[126]._u32[0] = base;
            ctx.pc = base + entries[i];
            ctx.status = SPU_STATUS_RUNNING;
            if (spu_run_with_halt(spu_indirect_branch, &ctx) || !returned_to_caller) return 5;
            if (std::memcmp(ctx.ls + base, blob.data(), code_end)) return 6;
            ++count;
        }
        for (unsigned i = 0; i < 16; ++i)
            if ((base && ctx.ls[base - 16 + i] != 0xa5) ||
                ctx.ls[base + bytes + 0x50 + i] != 0xa5) return 7;
        if (!base) reference.assign(ctx.ls, ctx.ls + bytes + 0x50);
        else {
            unsigned relocated = 0;
            for (uint32_t offset = code_end; offset < bytes + 0x50; offset += 4) {
                const uint8_t* p = reference.data() + offset;
                const uint32_t expected = (uint32_t(p[0]) << 24) | (uint32_t(p[1]) << 16) |
                    (uint32_t(p[2]) << 8) | p[3];
                const uint32_t actual = spu_ls_read32(&ctx, base + offset);
                if (actual == expected) continue;
                if (expected >= bytes + 0x50 || actual != expected + base) return 8;
                ++relocated;
            }
            if (!relocated) return 9;
        }
    }
    std::free(vm_base);
    vm_base = nullptr;
    std::printf("{\"original_constructors\":%u,\"positions\":4,\"code_preserved\":true,\"relocated_data_consistent\":true,\"ai_algorithm_validated\":false}\n", count);
    return 0;
}

extern "C" int fifa_test_spu_ant_vbr_constructors(const char* image) {
    const uint32_t entries[] = {0x4a00,0x5418,0x6290};
    return run_pic_constructors(image, 0x2100a00, 0x71e0, 0x62a0, entries);
}

extern "C" int fifa_test_spu_ant_pose_constructors(const char* image) {
    const uint32_t entries[] = {0xcd8,0xe20,0x10e8};
    return run_pic_constructors(image, 0x210b300, 0x1610, 0x10f8, entries);
}
