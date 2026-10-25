#include "spu_workload.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

extern "C" uint8_t* vm_base;
extern "C" void fifa_install_spu_policy(void);
extern "C" void spu_indirect_branch(spu_context*);
extern "C" int spu_run_with_halt(void (*)(spu_context*), spu_context*);
extern "C" void spu_begin_image(int);
extern "C" void spu_register_function(uint32_t, void (*)(spu_context*));
using native_spu_fn = void (*)(spu_context*);
extern "C" native_spu_fn spu_lifted_lookup(const spu_context*, uint32_t);
static bool returned_to_caller;
static void fixture_return(spu_context*) { returned_to_caller = true; }

// This CLI is a test-only original-code runner. The host codec supplies authored
// input and checks output; it never provides decompressed bytes to game boot.
extern "C" int fifa_test_spu_lzma(const char* image, const char* input,
                                  const char* output, const char* size_text) {
    char* end = nullptr;
    const unsigned long capacity = std::strtoul(size_text, &end, 10);
    if (!*size_text || *end || capacity > 0x20000) return 3;
    uint8_t blob[0x2000];
    FILE* file = std::fopen(image, "rb");
    if (!file) return 3;
    bool valid = std::fread(blob, 1, sizeof blob, file) == sizeof blob && std::fgetc(file) == EOF;
    std::fclose(file);
    if (!valid) return 3;
    file = std::fopen(input, "rb");
    if (!file) return 3;
    std::vector<uint8_t> compressed(0x18001);
    size_t bytes = std::fread(compressed.data(), 1, compressed.size(), file);
    valid = !std::ferror(file);
    std::fclose(file);
    if (!valid || !bytes || bytes > 0x18000 ||
        ((bytes + 15) & ~size_t(15)) + capacity > 0x2b800) return 3;
    compressed.resize(bytes);
    vm_base = (uint8_t*)std::calloc(1, 0x100000);
    if (!vm_base) return 3;
    std::memcpy(vm_base + 0x10000, compressed.data(), bytes);
    std::memset(vm_base + 0x3ff00, 0xa5, 0x20300);
    fifa_install_spu_policy();
    static spu_context context;
    spu_context_init(&context, 78);
    context.image_id = 0x26d5c19b;
    if (!spu_lifted_lookup(&context, 0x100)) return 77;
    spu_begin_image(context.image_id);
    spu_register_function(0x3d000, fixture_return);
    spu_begin_image(0);
    std::memcpy(context.ls + 0x80, blob, sizeof blob);
    context.gpr[0]._u32[0] = 0x3d000;
    context.gpr[1]._u32[0] = 0x3f000;
    context.gpr[3]._u32[0] = 0x40000;
    context.gpr[4]._u32[0] = (uint32_t)capacity;
    context.gpr[5]._u32[0] = 0x10000;
    context.gpr[6]._u32[0] = (uint32_t)bytes;
    context.pc = 0x100;
    context.status = SPU_STATUS_RUNNING;
    if (spu_run_with_halt(spu_indirect_branch, &context) || !returned_to_caller) return 5;
    if (std::memcmp(vm_base + 0x10000, compressed.data(), bytes)) return 6;
    // The original job writes whole 16-byte DMA quanta, including tail padding.
    // Guards are outside that physical output span, not inside its padding.
    const unsigned padded = ((unsigned)capacity + 15) & ~15u;
    for (unsigned i = 0x3ff00; i < 0x40000; ++i) if (vm_base[i] != 0xa5) return 6;
    for (unsigned i = 0x40000 + padded; i < 0x60200; ++i) if (vm_base[i] != 0xa5) return 6;
    file = std::fopen(output, "wb");
    if (!file) return 3;
    valid = std::fwrite(vm_base + 0x40000, 1, capacity, file) == capacity;
    valid = std::fclose(file) == 0 && valid;
    if (!valid) return 3;
    std::printf("{\"original_entry\":\"0x100\",\"source_preserved\":true,\"dma_guards\":true}\n");
    return 0;
}
