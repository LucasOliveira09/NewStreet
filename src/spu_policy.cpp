#include "ppu_recomp.h"
#include "spu_workload.h"

extern "C" PPU_THREAD_LOCAL ppu_context* g_active_ctx;
#ifdef FIFA_HAS_SPU
extern "C" void fifa_spu_register_all(void);
#endif
static void missing_spu(const char* kind, uint64_t value, void* context) {
    fifa_boot_missing(kind, value, context ? (ppu_context*)context : g_active_ctx);
}

extern "C" void fifa_install_spu_policy(void) {
    spu_missing_execution_hook = missing_spu;
#ifdef FIFA_HAS_SPU
    fifa_spu_register_all();
#endif
}

extern "C" void fifa_test_missing_spu(ppu_context* ctx) {
    uint8_t image[64]{}; // Unregistered synthetic image: dispatch must halt.
    g_active_ctx = ctx;
    fifa_install_spu_policy();
    spu_workload_dispatch(image, sizeof image, 0);
}

extern "C" void spu_indirect_branch(spu_context*);
extern "C" void fifa_test_missing_spu_indirect(ppu_context* ctx) {
    static spu_context spu{};
    spu.image_id = 987654321;
    spu.pc = 0x3ff00; // Unregistered high LS; must not become interpreted stop.
    spu.gpr[0]._u32[0] = 0x1234;
    g_active_ctx = ctx;
    fifa_install_spu_policy();
    spu_indirect_branch(&spu);
}
