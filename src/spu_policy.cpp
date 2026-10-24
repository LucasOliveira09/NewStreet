#include "ppu_recomp.h"
#include "spu_workload.h"
#include "spu_lifted_thread.h"
#include <cstdio>
#include <cstring>

extern "C" PPU_THREAD_LOCAL ppu_context* g_active_ctx;
extern "C" void fifa_dump_spu_state(const char*, spu_context*);
#ifdef FIFA_HAS_SPU
extern "C" void fifa_spu_register_all(void);
extern "C" void fifa_spu_register_overlays(void);
#endif
static void missing_spu(const char* kind, uint64_t value, void* context) {
    fifa_boot_missing(kind, value, context ? (ppu_context*)context : g_active_ctx);
}

extern "C" void fifa_install_spu_policy(void) {
    spu_missing_execution_hook = missing_spu;
    spu_execution_diagnostic_hook = fifa_dump_spu_state;
#ifdef FIFA_HAS_SPU
    fifa_spu_register_all();
    fifa_spu_register_overlays();
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
    spu_context_init(&spu, 0);
    spu.image_id = 987654321;
    spu.pc = 0x3ff00; // Unregistered high LS; must not become interpreted stop.
    spu.gpr[0]._u32[0] = 0x1234;
    spu.ls[0x300] = 0xa5;
    g_active_ctx = ctx;
    fifa_install_spu_policy();
    spu_indirect_branch(&spu);
}

extern "C" void spu_stop(spu_context*);
extern "C" int spu_run_with_halt(void (*)(spu_context*), spu_context*);
extern "C" void spu_begin_image(int);
extern "C" void spu_register_function(uint32_t, void (*)(spu_context*));
static bool continued_after_stop;
static void test_returning_entry(spu_context*) {}
static void test_zero_tail(spu_context* ctx) {
    ctx->pc = 0;
    g_spu_trampoline_fn = spu_indirect_branch;
}
static void test_zero_start(spu_context* ctx) {
    ctx->pc = 0x80;
    g_spu_trampoline_fn = test_zero_tail;
}
static void test_stopping_entry(spu_context* ctx) {
    ctx->status = SPU_STATUS_STOPPED_BY_STOP;
    spu_stop(ctx);
    continued_after_stop = true;
}
extern "C" int fifa_test_spu_termination(const char* mode) {
    static spu_context spu{};
    spu_context_init(&spu, 0);
    spu.image_id = 987654321;
    spu.spu_id = 77;
    fifa_install_spu_policy();
    if (!std::strcmp(mode, "fault")) {
        spu_begin_image(spu.image_id);
        spu_register_function(0x300, test_returning_entry);
        spu_begin_image(0);
        spu.pc = 0x300;
        spu_lifted_thread_result result{};
        spu_lifted_thread_run(&spu, &result);
        return 17;
    }
    if (!std::strcmp(mode, "zero")) {
        spu_run_with_halt(test_zero_start, &spu);
        return 17;
    }
    spu.stop_code = !std::strcmp(mode, "exit") ? 0x102 : 0x3fff;
    spu_channel_write(&spu.ch_out_mbox, 23);
    int halted = spu_run_with_halt(test_stopping_entry, &spu);
    std::printf("{\"halted\":%s,\"continued\":%s,\"stop_code\":%u,\"mailbox\":%u}\n",
        halted ? "true" : "false", continued_after_stop ? "true" : "false",
        spu.stop_code, spu.ch_out_mbox.value);
    return 0;
}
