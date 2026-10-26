#include "spu_workload.h"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

extern "C" void fifa_install_spu_policy(void);
extern "C" void spu_indirect_branch(spu_context*);
extern "C" int spu_run_with_halt(void (*)(spu_context*), spu_context*);
extern "C" void spu_halt(spu_context*);
extern "C" void spu_begin_image(int);
extern "C" void spu_register_function(uint32_t, void (*)(spu_context*));
using native_fn = void (*)(spu_context*);
extern "C" native_fn spu_lifted_lookup(const spu_context*, uint32_t);

#ifdef FIFA_HAS_SPU
#define ORIGINAL_CTOR(address) extern "C" void fifa_job_raw_1ee9580_spu_func_##address(spu_context*)
ORIGINAL_CTOR(00004A30); ORIGINAL_CTOR(000047E8); ORIGINAL_CTOR(00004728);
ORIGINAL_CTOR(00004580); ORIGINAL_CTOR(000044C0); ORIGINAL_CTOR(00004480);
ORIGINAL_CTOR(00004328); ORIGINAL_CTOR(000042E8); ORIGINAL_CTOR(00003EE0);
ORIGINAL_CTOR(00000738);
#undef ORIGINAL_CTOR
extern "C" void fifa_replay_matrixload_spu_func_00003978(spu_context*);
extern "C" void fifa_fifarna_batchplayer_pass0_spu_func_00015830(spu_context*);
extern "C" void fifa_fifarna_batchplayer_pass0_spu_func_00001758(spu_context*);
extern "C" void fifa_railtracks_pathestimates_spu_func_0002A2B8(spu_context*);
extern "C" void fifa_railtracks_pathestimates_spu_func_00028488(spu_context*);
extern "C" void fifa_railtracks_pathestimates_spu_func_00022800(spu_context*);
extern "C" void fifa_railtracks_pathestimates_spu_func_00020E38(spu_context*);
namespace {
constexpr int image_id = 0x256ac370;
constexpr uint32_t constructors[] = {
    0x4a30, 0x47e8, 0x4728, 0x4580, 0x44c0,
    0x4480, 0x4328, 0x42e8, 0x3ee0, 0x738
};
const native_fn originals[] = {
    fifa_job_raw_1ee9580_spu_func_00004A30, fifa_job_raw_1ee9580_spu_func_000047E8,
    fifa_job_raw_1ee9580_spu_func_00004728, fifa_job_raw_1ee9580_spu_func_00004580,
    fifa_job_raw_1ee9580_spu_func_000044C0, fifa_job_raw_1ee9580_spu_func_00004480,
    fifa_job_raw_1ee9580_spu_func_00004328, fifa_job_raw_1ee9580_spu_func_000042E8,
    fifa_job_raw_1ee9580_spu_func_00003EE0, fifa_job_raw_1ee9580_spu_func_00000738
};
unsigned calls;
bool ordered, zeroed, stopped;
uint32_t expected_stop_code, expected_pc_start, expected_pc_end;
spu_context* active;
decltype(spu_missing_execution_hook) strict_missing;
constexpr uint32_t path_constructors[] = {0x2a2b8, 0x28488, 0x22800, 0x20e38};
const native_fn path_originals[] = {
    fifa_railtracks_pathestimates_spu_func_0002A2B8,
    fifa_railtracks_pathestimates_spu_func_00028488,
    fifa_railtracks_pathestimates_spu_func_00022800,
    fifa_railtracks_pathestimates_spu_func_00020E38
};

void observe_path_constructor(spu_context* ctx) {
    for (unsigned i = 0; i < 4; ++i) {
        if (ctx->pc != path_constructors[i]) continue;
        if (!calls)
            zeroed = std::all_of(ctx->ls + 0x2e180, ctx->ls + 0x34370,
                                 [](uint8_t value) { return value == 0; });
        ordered = ordered && calls == i;
        ++calls;
        path_originals[i](ctx);
        return;
    }
    std::abort();
}

void observe_constructor(spu_context* ctx) {
    for (unsigned i = 0; i < 10; ++i) {
        if (ctx->pc != constructors[i]) continue;
        if (!calls)
            zeroed = std::all_of(ctx->ls + 0x5000, ctx->ls + 0x25a60,
                                 [](uint8_t value) { return value == 0; });
        ordered = ordered && calls == i;
        ++calls;
        originals[i](ctx); // Execute the original constructor, never a replacement result.
        return;
    }
    std::abort();
}

void observe_matrixload_constructor(spu_context* ctx) {
    zeroed = std::all_of(ctx->ls + 0x3c60, ctx->ls + 0x3c90,
                         [](uint8_t value) { return value == 0; });
    ++calls;
    fifa_replay_matrixload_spu_func_00003978(ctx);
}

void observe_batchplayer_constructor(spu_context* ctx) {
    if (ctx->pc == 0x15830) {
        ordered = ordered && calls == 0;
        zeroed = std::all_of(ctx->ls + 0x16370, ctx->ls + 0x16530,
                             [](uint8_t value) { return value == 0; });
        ++calls;
        fifa_fifarna_batchplayer_pass0_spu_func_00015830(ctx);
    } else if (ctx->pc == 0x1758) {
        ordered = ordered && calls == 1;
        ++calls;
        fifa_fifarna_batchplayer_pass0_spu_func_00001758(ctx);
    } else std::abort();
}

void observe_original_stop(const char* kind, uint64_t value, void* ppu) {
    // Capture only the exact original stop selected by this test-only caller.
    // Image, PC range and stop code must match; every other fault stays strict.
    if (!std::strcmp(kind, "spu-stop") &&
        value == ((uint64_t(active->image_id) << 32) | expected_stop_code) &&
        active->pc >= expected_pc_start && active->pc < expected_pc_end &&
        active->stop_code == expected_stop_code && active->status == SPU_STATUS_STOPPED_BY_STOP) {
        stopped = true;
        spu_halt(active);
        return;
    }
    strict_missing(kind, value, ppu);
}

int run_to_fixture_stop(spu_context& ctx, uint32_t entry, uint32_t stop_code,
                        uint32_t pc_start, uint32_t pc_end) {
    active = &ctx;
    stopped = false;
    expected_stop_code = stop_code;
    expected_pc_start = pc_start;
    expected_pc_end = pc_end;
    ctx.pc = entry;
    ctx.status = SPU_STATUS_RUNNING;
    strict_missing = spu_missing_execution_hook;
    spu_missing_execution_hook = observe_original_stop;
    int halted = spu_run_with_halt(spu_indirect_branch, &ctx);
    spu_missing_execution_hook = strict_missing;
    return halted;
}

int run_to_original_crt_stop(spu_context& ctx) {
    ctx.gpr[1]._u32[0] = 0x3f000;
    ctx.gpr[125]._u32[0] = 1; // Authored harness input; never used in game execution.
    return run_to_fixture_stop(ctx, 0xb0, 0x3fff, 0x184, 0x1a8);
}
}

extern "C" int fifa_test_spu_fixed_startup(const char* path) {
    std::vector<uint8_t> blob(0x4f30);
    FILE* file = std::fopen(path, "rb");
    if (!file) return 3;
    bool valid = std::fread(blob.data(), 1, blob.size(), file) == blob.size() &&
                 std::fgetc(file) == EOF;
    std::fclose(file);
    if (!valid) return 3;
    // Registry lookup uses the first registration. Install observers before the
    // normal image, retaining direct pointers to the original generated bodies.
    spu_begin_image(image_id);
    for (auto address : constructors) spu_register_function(address, observe_constructor);
    spu_begin_image(0);
    fifa_install_spu_policy();
    static spu_context ctx;
    spu_context_init(&ctx, 81);
    ctx.image_id = image_id;
    std::memset(ctx.ls, 0xa5, SPU_LS_SIZE);
    std::memcpy(ctx.ls + 0x80, blob.data(), blob.size());
    for (unsigned i = 0; i < 10; ++i) {
        if (spu_ls_read32(&ctx, 0x4fa4 - 4 * i) != constructors[i]) return 4;
        if (spu_lifted_lookup(&ctx, constructors[i]) != observe_constructor) return 77;
    }
    if (!spu_lifted_lookup(&ctx, 0xb0)) return 77;
    calls = 0;
    ordered = true;
    zeroed = stopped = false;
    int halted = run_to_original_crt_stop(ctx);
    if (!halted || !stopped || calls != 10 || !ordered || !zeroed) return 5;
    if (std::memcmp(ctx.ls + 0x80, blob.data(), 0x4a40 - 0x80)) return 6;
    for (uint32_t address = 0x4fb0; address < 0x5000; ++address)
        if (ctx.ls[address] != 0xa5) return 7;
    for (uint32_t address = 0x25a60; address < 0x25a70; ++address)
        if (ctx.ls[address] != 0xa5) return 7;
    std::printf("{\"original_constructors\":10,\"reverse_order\":true,"
                "\"bss_zero_before_constructors\":true,\"bss_guards_preserved\":true,"
                "\"code_preserved\":true,\"original_stop\":16383,"
                "\"main_executed\":false,\"algorithm_validated\":false}\n");
    return 0;
}

extern "C" int fifa_test_spu_matrixsave_startup(const char* path) {
    std::vector<uint8_t> blob(0x1950);
    FILE* file = std::fopen(path, "rb");
    if (!file) return 3;
    bool valid = std::fread(blob.data(), 1, blob.size(), file) == blob.size() &&
                 std::fgetc(file) == EOF;
    std::fclose(file);
    if (!valid) return 3;
    fifa_install_spu_policy();
    static spu_context ctx;
    spu_context_init(&ctx, 81);
    ctx.image_id = 0x23c34933;
    std::memset(ctx.ls, 0xa5, SPU_LS_SIZE);
    std::memcpy(ctx.ls + 0x80, blob.data(), blob.size());
    if (!spu_lifted_lookup(&ctx, 0xb0)) return 77;
    if (!run_to_original_crt_stop(ctx) || !stopped) return 5;
    if (std::memcmp(ctx.ls + 0x80, blob.data(), blob.size())) return 6;
    for (unsigned i = 0; i < 16; ++i)
        if (ctx.ls[0x70 + i] != 0xa5 || ctx.ls[0x19d0 + i] != 0xa5) return 7;
    std::printf("{\"original_constructors\":0,\"bss_bytes\":0,\"image_preserved\":true,"
                "\"image_guards_preserved\":true,\"original_stop\":16383,"
                "\"main_executed\":false,\"algorithm_validated\":false}\n");
    return 0;
}

extern "C" int fifa_test_spu_matrixload_startup(const char* path) {
    std::vector<uint8_t> blob(0x3be0);
    FILE* file = std::fopen(path, "rb");
    if (!file) return 3;
    bool valid = std::fread(blob.data(), 1, blob.size(), file) == blob.size() &&
                 std::fgetc(file) == EOF;
    std::fclose(file);
    if (!valid) return 3;
    spu_begin_image(0x200e35e0);
    spu_register_function(0x3978, observe_matrixload_constructor);
    spu_begin_image(0);
    fifa_install_spu_policy();
    static spu_context ctx;
    spu_context_init(&ctx, 81);
    ctx.image_id = 0x200e35e0;
    std::memset(ctx.ls, 0xa5, SPU_LS_SIZE);
    std::memcpy(ctx.ls + 0x80, blob.data(), blob.size());
    if (spu_ls_read32(&ctx, 0x3c50) != 0x3978 ||
        spu_lifted_lookup(&ctx, 0x3978) != observe_matrixload_constructor ||
        !spu_lifted_lookup(&ctx, 0xb0)) return 77;
    calls = 0;
    zeroed = false;
    if (!run_to_original_crt_stop(ctx) || !stopped || calls != 1 || !zeroed) return 5;
    if (std::memcmp(ctx.ls + 0x80, blob.data(), blob.size())) return 6;
    // The original packing helper at 0x38c8 assembles four authored constants
    // from scalar arguments; compare those words independently of the lift.
    const uint32_t expected[] = {
        0xffff8000, 0x00007c00, 0x7f800000, 0xffffff90,
        0x80000000, 0x7f800000, 0x00007c00, 0x00000070, 0, 0, 0, 0
    };
    for (unsigned i = 0; i < 12; ++i)
        if (spu_ls_read32(&ctx, 0x3c60 + 4 * i) != expected[i]) return 8;
    for (unsigned i = 0; i < 16; ++i)
        if (ctx.ls[0x70 + i] != 0xa5 || ctx.ls[0x3c90 + i] != 0xa5) return 7;
    std::printf("{\"original_constructors\":1,\"bss_bytes\":48,"
                "\"bss_zero_before_constructors\":true,\"constructor_constants_correct\":true,"
                "\"code_preserved\":true,\"bss_guards_preserved\":true,"
                "\"original_stop\":16383,\"main_executed\":false,\"algorithm_validated\":false}\n");
    return 0;
}
extern "C" int fifa_test_spu_batchplayer_startup(const char* path) {
    std::vector<uint8_t> blob(0x162f0);
    FILE* file = std::fopen(path, "rb");
    if (!file) return 3;
    bool valid = std::fread(blob.data(), 1, blob.size(), file) == blob.size() &&
                 std::fgetc(file) == EOF;
    std::fclose(file);
    if (!valid) return 3;
    spu_begin_image(0x2c7b9464);
    spu_register_function(0x15830, observe_batchplayer_constructor);
    spu_register_function(0x1758, observe_batchplayer_constructor);
    spu_begin_image(0);
    fifa_install_spu_policy();
    static spu_context ctx;
    spu_context_init(&ctx, 81);
    ctx.image_id = 0x2c7b9464;
    std::memset(ctx.ls, 0xa5, SPU_LS_SIZE);
    std::memcpy(ctx.ls + 0x80, blob.data(), blob.size());
    if (spu_ls_read32(&ctx, 0x16350) != 0x1758 ||
        spu_ls_read32(&ctx, 0x16354) != 0x15830 ||
        spu_lifted_lookup(&ctx, 0x15830) != observe_batchplayer_constructor ||
        spu_lifted_lookup(&ctx, 0x1758) != observe_batchplayer_constructor ||
        !spu_lifted_lookup(&ctx, 0xb0)) return 77;
    calls = 0;
    zeroed = false;
    ordered = true;
    if (!run_to_original_crt_stop(ctx) || !stopped || calls != 2 || !zeroed || !ordered) return 5;
    if (std::memcmp(ctx.ls + 0x80, blob.data(), blob.size())) return 6;
    for (unsigned i = 0; i < 4; ++i)
        if (spu_ls_read32(&ctx, 0x16370 + 4 * i) != 0x43c80000 ||
            spu_ls_read32(&ctx, 0x16380 + 4 * i) != 0x42652ee0 ||
            spu_ls_read32(&ctx, 0x16390 + 4 * i) != 0x3c8efa34) return 8;
    const uint32_t expected[] = {
        0xffff8000, 0x00007c00, 0x7f800000, 0xffffff90,
        0x80000000, 0x7f800000, 0x00007c00, 0x00000070, 0, 0, 0, 0
    };
    for (unsigned i = 0; i < 12; ++i)
        if (spu_ls_read32(&ctx, 0x163a0 + 4 * i) != expected[i]) return 8;
    if (!std::all_of(ctx.ls + 0x163d0, ctx.ls + 0x16530,
                     [](uint8_t value) { return value == 0; })) return 9;
    for (unsigned i = 0; i < 16; ++i)
        if (ctx.ls[0x70 + i] != 0xa5 || ctx.ls[0x16530 + i] != 0xa5) return 7;
    std::printf("{\"original_constructors\":2,\"reverse_order\":true,\"bss_bytes\":448,"
                "\"bss_zero_before_constructors\":true,\"constructor_constants_correct\":true,"
                "\"unused_bss_zero\":true,\"code_preserved\":true,\"bss_guards_preserved\":true,"
                "\"original_stop\":16383,\"main_executed\":false,\"algorithm_validated\":false}\n");
    return 0;
}
extern "C" int fifa_test_spu_pathestimates_startup(const char* path, bool exit_tail) {
    std::vector<uint8_t> blob(0x2e100);
    FILE* file = std::fopen(path, "rb");
    if (!file) return 3;
    bool valid = std::fread(blob.data(), 1, blob.size(), file) == blob.size() &&
                 std::fgetc(file) == EOF;
    std::fclose(file);
    if (!valid) return 3;
    spu_begin_image(0x2baccdc7);
    for (auto address : path_constructors) spu_register_function(address, observe_path_constructor);
    spu_begin_image(0);
    fifa_install_spu_policy();
    static spu_context ctx;
    spu_context_init(&ctx, 81);
    ctx.image_id = 0x2baccdc7;
    std::memset(ctx.ls, 0xa5, SPU_LS_SIZE);
    std::memcpy(ctx.ls + 0x80, blob.data(), blob.size());
    for (unsigned i = 0; i < 4; ++i)
        if (spu_ls_read32(&ctx, 0x2e10c - 4 * i) != path_constructors[i] ||
            spu_lifted_lookup(&ctx, path_constructors[i]) != observe_path_constructor) return 77;
    if (!spu_lifted_lookup(&ctx, 0xb0)) return 77;
    calls = 0;
    zeroed = false;
    ordered = true;
    if (!run_to_original_crt_stop(ctx) || !stopped || calls != 4 || !zeroed || !ordered) return 5;
    if (std::memcmp(ctx.ls + 0x80, blob.data(), 0x2cacc - 0x80)) return 6;
    for (unsigned i = 0; i < 16; ++i)
        if (ctx.ls[0x70 + i] != 0xa5 || ctx.ls[0x34370 + i] != 0xa5) return 7;
    if (exit_tail) {
        if (!run_to_fixture_stop(ctx, 0x2ca88, 0, 0x2ca88, 0x2cacc) || !stopped) return 10;
        if (std::memcmp(ctx.ls + 0x80, blob.data(), 0x2cacc - 0x80)) return 6;
        std::printf("{\"exit_tail_executed\":true,\"original_stop\":0,"
                    "\"main_executed\":false,\"code_preserved\":true}\n");
        return 0;
    }
    std::printf("{\"original_constructors\":4,\"reverse_order\":true,\"bss_bytes\":25072,"
                "\"bss_zero_before_constructors\":true,\"code_preserved\":true,"
                "\"bss_guards_preserved\":true,\"original_stop\":16383,"
                "\"main_executed\":false,\"algorithm_validated\":false}\n");
    return 0;
}
#else
extern "C" int fifa_test_spu_fixed_startup(const char*) { return 77; }
extern "C" int fifa_test_spu_matrixsave_startup(const char*) { return 77; }
extern "C" int fifa_test_spu_matrixload_startup(const char*) { return 77; }
extern "C" int fifa_test_spu_batchplayer_startup(const char*) { return 77; }
extern "C" int fifa_test_spu_pathestimates_startup(const char*, bool) { return 77; }
#endif
