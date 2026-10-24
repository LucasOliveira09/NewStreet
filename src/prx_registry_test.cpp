#include "ppu_recomp.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" uint32_t fifa_register_library(uint32_t, ppu_context*);
extern "C" uint32_t fifa_find_export(const char*, uint32_t, int);
extern "C" int fifa_call_export(const char*, uint32_t, ppu_context*);
extern "C" void ppu_register_function(uint32_t, void (*)(ppu_context*));

static void export_function(ppu_context* ctx) {
    // Observe the resolved OPD's TOC and the caller's original argument state.
    ctx->gpr[3] += ctx->gpr[2] == 0x6789 ? 10 : 1000;
}

extern "C" int fifa_test_prx_registry(void) {
    vm_base = (uint8_t*)std::calloc(1, 0x20000);
    if (!vm_base) return 3;
    uint32_t entry = 0x10000;
    vm_write8(entry, 28); vm_write16(entry + 4, 1);
    vm_write16(entry + 6, 1); vm_write16(entry + 8, 1);
    vm_write32(entry + 16, 0x11000); std::strcpy((char*)vm_base + 0x11000, "test_library");
    vm_write32(entry + 20, 0x11100); vm_write32(entry + 24, 0x11200);
    vm_write32(0x11100, 0x12345678); vm_write32(0x11104, 0x12345678);
    vm_write32(0x11200, 0x12000); vm_write32(0x11204, 0x15000);
    vm_write32(0x12000, 0x123400); vm_write32(0x12004, 0x6789);
    ppu_register_function(0x123400, export_function);
    ppu_context ctx{}; ctx.gpr[2] = 0xABCDE; ctx.gpr[3] = 32;
    uint32_t registered = fifa_register_library(entry, &ctx);
    fifa_call_export("test_library", 0x12345678, &ctx);
    vm_write8(entry, 4);
    uint32_t invalid = fifa_register_library(entry, &ctx);
    std::printf("{\"register_result\":%u,\"function\":%u,\"variable\":%u,\"other_library\":%u,"
                "\"call_result\":%llu,\"restored_toc\":%llu,\"bad_header_result\":%u,\"after_bad_header\":%u}\n",
        registered, fifa_find_export("test_library", 0x12345678, 0),
        fifa_find_export("test_library", 0x12345678, 1), fifa_find_export("other", 0x12345678, 0),
        (unsigned long long)ctx.gpr[3], (unsigned long long)ctx.gpr[2], invalid,
        fifa_find_export("test_library", 0x12345678, 0));
    return 0;
}
