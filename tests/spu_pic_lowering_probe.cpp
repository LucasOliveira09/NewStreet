#include "spu_workload.h"
#include "images.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" uint8_t* vm_base;
extern "C" void fifa_install_spu_policy(void);
extern "C" void spu_begin_image(int);
extern "C" void fifa_pic_fixture_main_spu_recomp_register(void);
extern "C" void fifa_pic_fixture_other_spu_recomp_register(void);
extern "C" void spu_overlay_note_get(spu_context*, uint32_t, const uint8_t*, uint32_t);

extern "C" int fifa_test_spu_pic_lowering(void) {
    vm_base = (uint8_t*)std::calloc(1, 0x20000);
    if (!vm_base) return 3;
    fifa_install_spu_policy();
    std::memcpy(vm_base + 0x10000, fixture_main, sizeof fixture_main);
    std::memcpy(vm_base + 0x11000, fixture_other, sizeof fixture_other);
    spu_begin_image(444);
    fifa_pic_fixture_main_spu_recomp_register();
    spu_overlay_register_pic_region_checked(0x10000, sizeof fixture_main, 0x100,
        0x30, 0x78, 444, spu_workload_fingerprint(fixture_main, sizeof fixture_main));
    spu_begin_image(555);
    fifa_pic_fixture_other_spu_recomp_register();
    spu_overlay_register_pic_region_checked(0x11000, sizeof fixture_other, 0x600,
        0x30, 0x10, 555, spu_workload_fingerprint(fixture_other, sizeof fixture_other));
    spu_begin_image(0);
    const uint32_t bases[] = {0x100, 0, 0x900, 0x5000};
    unsigned runs = 0;
    for (unsigned case_id = 0; case_id < 8; ++case_id) {
        const uint32_t base = bases[case_id / 2];
        const bool event = (case_id & 1) != 0;
        static spu_context ctx;
        spu_context_init(&ctx, 77);
        ctx.image_id = 111;
        const uint32_t other = base == 0x100 ? 0x600 : 0x7000;
        std::memcpy(ctx.ls + base, fixture_main, sizeof fixture_main);
        std::memcpy(ctx.ls + other, fixture_other, sizeof fixture_other);
        spu_overlay_note_get(&ctx, 0x10000, ctx.ls + base, sizeof fixture_main);
        spu_overlay_note_get(&ctx, 0x11000, ctx.ls + other, sizeof fixture_other);
        const uint32_t relative = 0x12340000u + base;
        const uint32_t external = 0x56780000u + other;
        spu_ls_write32(&ctx, base + 0xd0, relative);
        spu_ls_write32(&ctx, other + 0xc0, external);
        spu_ls_write32(&ctx, 0x3000, 0xabcdef01);
        ctx.gpr[0]._u32[0] = 0x3e000;
        ctx.gpr[29]._u32[0] = base + 0x90;
        ctx.gpr[30]._u32[0] = base + 0xa0;
        ctx.gpr[31]._u32[0] = other + 0x30;
        ctx.host_depth = 1;
        ctx.event_mask = 1;
        ctx.event_status = event ? 1 : 0;
        ctx.pc = base + 0x30;
        spu_indirect_branch(&ctx);
        spu_drain_call(&ctx, 0x3e000);
        const bool valid = ctx.pc == 0x3e000 && !g_spu_trampoline_fn && ctx.host_depth == 1 &&
            ctx.gpr[3]._u32[0] == 42 && ctx.gpr[7]._u32[0] == 42 && ctx.gpr[8]._u32[0] == 43 &&
            ctx.gpr[9]._u32[0] == (event ? 99u : 0u) && ctx.gpr[72]._u32[0] == base + 0x74 &&
            ctx.gpr[10]._u32[0] == base + 0x34 && ctx.gpr[11]._u32[0] == base + 0x58 &&
            ctx.gpr[12]._u32[0] == base + 0x64 && ctx.gpr[13]._u32[0] == base + 0x6c &&
            ctx.gpr[14]._u32[0] == external && ctx.gpr[20]._u32[0] == other + 0x34 &&
            ctx.gpr[74]._u32[0] == base + 0x60 &&
            spu_ls_read32(&ctx, base + 0xe0) == relative && spu_ls_read32(&ctx, 0x3010) == 0xabcdef01;
        if (!valid) {
            std::fprintf(stderr, "PIC lowering failed case=%u base=0x%X pc=0x%X r3=%X r7=%X r8=%X r10=%X r11=%X r12=%X r13=%X r14=%X r20=%X rel=%X abs=%X\n",
                case_id, base, ctx.pc, ctx.gpr[3]._u32[0], ctx.gpr[7]._u32[0], ctx.gpr[8]._u32[0],
                ctx.gpr[10]._u32[0], ctx.gpr[11]._u32[0], ctx.gpr[12]._u32[0], ctx.gpr[13]._u32[0],
                ctx.gpr[14]._u32[0], ctx.gpr[20]._u32[0], spu_ls_read32(&ctx, base+0xe0), spu_ls_read32(&ctx, 0x3010));
            return 4;
        }
        ++runs;
    }
    std::printf("{\"positions\":4,\"event_paths\":2,\"runs\":%u,\"relative_memory\":true,\"absolute_memory\":true,\"physical_links\":true,\"cross_program_call\":true}\n", runs);
    return 0;
}
