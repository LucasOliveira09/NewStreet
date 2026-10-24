#include "spu_workload.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" uint8_t* vm_base;
extern "C" void fifa_install_spu_policy(void);
extern "C" void spu_begin_image(int);
extern "C" void spu_register_function(uint32_t, void (*)(spu_context*));
extern "C" void spu_overlay_register_region_checked(uint32_t, uint32_t, uint32_t, uint32_t, uint32_t, int, uint64_t);
extern "C" void spu_overlay_note_get(spu_context*, uint32_t, const uint8_t*, uint32_t);

static void base_entry(spu_context* ctx) { ctx->gpr[3]._u32[0] = 1; }
static void overlay_entry(spu_context* ctx) { ctx->gpr[3]._u32[0] = 7; }

extern "C" int fifa_test_spu_overlay(const char* mode) {
    vm_base = (uint8_t*)std::calloc(1, 0x30000);
    if (!vm_base) return 3;
    fifa_install_spu_policy();
    spu_begin_image(111);
    spu_register_function(0x100, base_entry);
    spu_register_function(0x104, base_entry);
    spu_begin_image(222);
    spu_register_function(0x100, overlay_entry);
    spu_begin_image(0);
    if (!std::strcmp(mode, "many")) {
        // Audio modules coexist in different LS spans. Loading a fifth module
        // must not silently lose its identity or discard an earlier module.
        static spu_context many;
        spu_context_init(&many, 77);
        many.image_id = 111;
        for (unsigned i = 0; i < 7; ++i) {
            uint32_t source = 0x10000 + i * 0x400, base = 0x80 + i * 0x400;
            for (unsigned j = 0; j < 256; ++j) vm_base[source + j] = (uint8_t)(j * 37 + i);
            uint64_t fp = spu_workload_fingerprint(vm_base + source, 256);
            spu_begin_image(300 + i);
            spu_register_function(base + 0x80, overlay_entry);
            spu_overlay_register_region_checked(source, 256, base, 0x80, 0x20, 300 + i, fp);
            std::memcpy(many.ls + base, vm_base + source, 256);
            spu_overlay_note_get(&many, source, many.ls + base, 256);
        }
        for (unsigned i = 0; i < 7; ++i) {
            many.gpr[3]._u32[0] = 0;
            many.pc = 0x100 + i * 0x400;
            spu_indirect_branch(&many);
            if (many.gpr[3]._u32[0] != 7) return 23;
        }
        std::printf("{\"modules\":7,\"dispatched\":7}\n");
        return 0;
    }
    for (unsigned i = 0; i < 256; ++i) vm_base[0x10000 + i] = (uint8_t)(i * 37 + 3);
    uint64_t fp = spu_workload_fingerprint(vm_base + 0x10000, 256);
    spu_overlay_register_region_checked(0x10000, 256, 0x80, 0x80, 0x20, 222, fp);
    static spu_context ctx;
    spu_context_init(&ctx, 77);
    ctx.image_id = 111;
    if (!std::strcmp(mode, "base")) {
        std::memcpy(ctx.ls + 0x100, vm_base + 0x10000, 128);
        spu_overlay_note_get(&ctx, 0x10000, ctx.ls + 0x100, 128);
        return 17;
    }
    if (!std::strcmp(mode, "tamper")) vm_base[0x10003] ^= 1;
    std::memcpy(ctx.ls + 0x80, vm_base + 0x10000, 128);
    spu_overlay_note_get(&ctx, 0x10000, ctx.ls + 0x80, 128);
    std::memcpy(ctx.ls + 0x100, vm_base + 0x10080, 128);
    spu_overlay_note_get(&ctx, 0x10080, ctx.ls + 0x100, 128);
    if (!std::strcmp(mode, "overwrite")) {
        std::memcpy(ctx.ls + 0x100, vm_base + 0x20000, 128);
        spu_overlay_note_get(&ctx, 0x20000, ctx.ls + 0x100, 128);
    }
    if (!std::strcmp(mode, "data")) {
        std::memcpy(ctx.ls + 0x140, vm_base + 0x20000, 16);
        spu_overlay_note_get(&ctx, 0x20000, ctx.ls + 0x140, 16);
    }
    ctx.pc = !std::strcmp(mode, "missing") ? 0x104 : 0x100;
    spu_indirect_branch(&ctx);
    std::printf("{\"value\":%u,\"owner\":%d}\n", ctx.gpr[3]._u32[0], ctx.resident_code[0].image_id);
    return 0;
}
