#include "spu_workload.h"
#include <cstdio>
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
