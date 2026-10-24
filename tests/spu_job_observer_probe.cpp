#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "spu_workload.h"
#include <cstdio>
#include <cstring>
#include <cstdlib>

extern "C" uint8_t* vm_base;
extern "C" void fifa_observe_spu_job(spu_context*, spu_lifted_entry_fn, int);

static void tail(spu_context* ctx) {
    std::memcpy(vm_base + 0x10000, "OUT!", 5);
    ctx->gpr[3]._u32[0] = 7;
    SPU_RET(ctx);
}
static void entry(spu_context* ctx) {
    ctx->pc = 0x104;
    g_spu_trampoline_fn = tail;
}

extern "C" int fifa_test_spu_observer(const char* argument) {
    vm_base = (uint8_t*)VirtualAlloc(nullptr, 0x30000, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    if (!vm_base) return 3;
    std::memcpy(vm_base + 0x20000, "IN!!", 4);
    static spu_context ctx;
    spu_context_init(&ctx, 77);
    ctx.host_depth = (uint32_t)std::atoi(argument);
    ctx.gpr[0]._u32[0] = 0x300;
    ctx.gpr[3]._u32[0] = 0x10000;
    ctx.gpr[4]._u32[0] = 5;
    ctx.gpr[5]._u32[0] = 0x20000;
    ctx.gpr[6]._u32[0] = 4;
    ctx.drain_ret_pc = 0x300;
    fifa_observe_spu_job(&ctx, entry, 0);
    spu_drain_call(&ctx, 0x300);
    std::printf("{\"pc\":%u,\"depth\":%u,\"result\":%u,\"pending\":%s,\"output\":\"%s\"}\n",
        ctx.pc, ctx.host_depth, ctx.gpr[3]._u32[0], g_spu_trampoline_fn ? "true" : "false", vm_base + 0x10000);
    return 0;
}
