#include "spu_workload.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <initializer_list>

extern "C" uint8_t* vm_base;
extern "C" void fifa_install_spu_policy(void);
extern "C" void spu_begin_image(int);
extern "C" void spu_register_function(uint32_t, void (*)(spu_context*));
extern "C" void spu_overlay_register_region_checked(uint32_t, uint32_t, uint32_t, uint32_t, uint32_t, int, uint64_t);
extern "C" void spu_overlay_note_get(spu_context*, uint32_t, const uint8_t*, uint32_t);

static void base_entry(spu_context* ctx) { ctx->gpr[3]._u32[0] = 1; }
static void overlay_entry(spu_context* ctx) { ctx->gpr[3]._u32[0] = 7; }
static void replacement_entry(spu_context* ctx) { ctx->gpr[3]._u32[0] = 9; }
static void pic_entry(spu_context* ctx) {
    const int32_t bias = spu_code_relocation_bias(ctx);
    ctx->gpr[3]._u32[0] = spu_ls_read32(ctx, 0x120u + (uint32_t)bias);
    ctx->gpr[4]._u32[0] = (uint32_t)bias;
}
using test_spu_fn = void (*)(spu_context*);
extern "C" test_spu_fn spu_lifted_lookup(const spu_context*, uint32_t);

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
    if (!std::strncmp(mode, "pic", 3)) {
        static spu_context pic;
        spu_context_init(&pic, 77);
        pic.image_id = 111;
        for (unsigned i = 0; i < 0x180; ++i) vm_base[0x10000 + i] = (uint8_t)(i * 19);
        std::memset(vm_base + 0x1001c, 0, 4);
        vm_base[0x1001c] = std::strcmp(mode, "pic-absolute-source") ? 0x80 : 0;
        spu_begin_image(444);
        spu_register_function(0x100, pic_entry);
        spu_register_function(0x110, pic_entry);
        spu_overlay_register_pic_region_checked(0x10000, 0x180, 0x80, 0x80, 0x20, 444,
            spu_workload_fingerprint(vm_base + 0x10000, 0x180));
        spu_begin_image(0);
        if (!std::strcmp(mode, "pic-source")) vm_base[0x10060] ^= 1;
        if (!std::strcmp(mode, "pic-boundary")) {
            std::memcpy(pic.ls + 0x3fff0, vm_base + 0x10000, 16);
            spu_overlay_note_get(&pic, 0x10000, pic.ls + 0x3fff0, 16);
            return 34;
        }
        const uint32_t bases[] = {!std::strcmp(mode, "pic-unaligned") ? 0x801u : 0x800u, 0x1800, 0};
        for (uint32_t base : bases) {
            std::memcpy(pic.ls + base, vm_base + 0x10000, 0x180);
            spu_overlay_note_get(&pic, 0x10000, pic.ls + base, 0x180);
            spu_ls_write32(&pic, base + 0xa0, 0x12340000u + base);
            spu_overlay_note_get(&pic, 0x20000, pic.ls + base + 0xa0, 4);
        }
        // An unknown middle instruction splits a PIC interval; both retained
        // sides keep the original displacement and independent data address.
        std::memcpy(pic.ls + 0x1888, vm_base + 0x20000, 4);
        spu_overlay_note_get(&pic, 0x20000, pic.ls + 0x1888, 4);
        for (uint32_t pc : {0x1880u, 0x1890u}) {
            pic.pc = pc;
            if (spu_lifted_lookup(&pic, pc) != pic_entry) return 35;
            spu_indirect_branch(&pic);
            if (pic.gpr[3]._u32[0] != 0x12341800 || pic.gpr[4]._u32[0] != 0x1780) return 36;
        }
        for (uint32_t base : bases) {
            pic.pc = base + 0x80;
            if (spu_lifted_lookup(&pic, pic.pc) != pic_entry) return 30;
            spu_indirect_branch(&pic);
            if (pic.gpr[3]._u32[0] != 0x12340000u + base ||
                pic.gpr[4]._u32[0] != base - 0x80u) return 31;
        }
        if (!std::strcmp(mode, "pic-overwrite")) {
            std::memcpy(pic.ls + 0x1880, vm_base + 0x20000, 4);
            spu_overlay_note_get(&pic, 0x20000, pic.ls + 0x1880, 4);
            if (spu_lifted_lookup(&pic, 0x1880)) return 32;
            pic.pc = 0x1880;
            spu_indirect_branch(&pic);
            return 33;
        }
        std::puts("{\"positions\":3,\"isolated\":true,\"negative_bias\":true,\"split_preserved\":true}");
        return 0;
    }
    if (!std::strcmp(mode, "overlap") || !std::strcmp(mode, "overlap-unknown")) {
        // A smaller plugin replaces the middle of an earlier plugin's code.
        // Header and body arrive separately; the valid outer code must survive.
        static spu_context nested;
        spu_context_init(&nested, 77);
        nested.image_id = 111;
        for (unsigned i = 0; i < 0x300; ++i) vm_base[0x10000 + i] = (uint8_t)(i * 19);
        for (unsigned i = 0; i < 0x100; ++i) vm_base[0x20000 + i] = (uint8_t)(i * 31 + 5);
        spu_begin_image(222);
        spu_register_function(0x180, overlay_entry);
        spu_register_function(0x2f0, overlay_entry);
        spu_overlay_register_region_checked(0x10000, 0x300, 0x80, 0x80, 0x200, 222,
            spu_workload_fingerprint(vm_base + 0x10000, 0x300));
        spu_begin_image(333);
        spu_register_function(0x180, replacement_entry);
        spu_register_function(0x1a0, replacement_entry);
        spu_overlay_register_region_checked(0x20000, 0x100, 0x140, 0x30, 0xb0, 333,
            spu_workload_fingerprint(vm_base + 0x20000, 0x100));
        std::memcpy(nested.ls + 0x80, vm_base + 0x10000, 0x300);
        spu_overlay_note_get(&nested, 0x10000, nested.ls + 0x80, 0x300);
        std::memcpy(nested.ls + 0x140, vm_base + 0x20000, 0x30);
        spu_overlay_note_get(&nested, 0x20000, nested.ls + 0x140, 0x30);
        std::memcpy(nested.ls + 0x170, vm_base + 0x20030, 0xd0);
        spu_overlay_note_get(&nested, 0x20030, nested.ls + 0x170, 0xd0);
        for (uint32_t pc : {0x100u, 0x180u, 0x2f0u}) {
            nested.pc = pc;
            spu_indirect_branch(&nested);
            if (nested.gpr[3]._u32[0] != (pc == 0x180 ? 9u : 7u)) return 24;
        }
        // Unknown code invalidates only the overwritten instructions.
        std::memcpy(nested.ls + 0x1a0, vm_base + 0x28000, 4);
        spu_overlay_note_get(&nested, 0x28000, nested.ls + 0x1a0, 4);
        nested.pc = !std::strcmp(mode, "overlap-unknown") ? 0x1a0 : 0x180;
        spu_indirect_branch(&nested);
        if (nested.gpr[3]._u32[0] != 9) return 25;
        // Reloading the larger original image must replace the smaller owner.
        std::memcpy(nested.ls + 0x80, vm_base + 0x10000, 0x300);
        spu_overlay_note_get(&nested, 0x10000, nested.ls + 0x80, 0x300);
        nested.pc = 0x180;
        spu_indirect_branch(&nested);
        if (nested.gpr[3]._u32[0] != 7) return 26;
        std::printf("{\"nested\":9,\"outer\":7,\"reloaded\":7}\n");
        return 0;
    }
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
    if (!std::strcmp(mode, "relocated")) {
        spu_begin_image(333);
        spu_register_function(0x500, replacement_entry);
        spu_overlay_register_region_checked(0x10000, 256, 0x480, 0x80, 0x20, 333, fp);
        static spu_context relocated;
        spu_context_init(&relocated, 77);
        relocated.image_id = 111;
        std::memcpy(relocated.ls + 0x480, vm_base + 0x10000, 256);
        spu_overlay_note_get(&relocated, 0x10000, relocated.ls + 0x480, 256);
        relocated.pc = 0x500;
        spu_indirect_branch(&relocated);
        std::printf("{\"value\":%u,\"owner\":%d}\n", relocated.gpr[3]._u32[0], relocated.resident_code[0].image_id);
        return 0;
    }
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
