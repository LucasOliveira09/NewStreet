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

// Test-only entry: run the ORIGINAL DMA copy routine against authored bytes.
// No metadata provider, callback or game boot path is replaced by this fixture.
extern "C" int fifa_test_spu_memcpy(const char* image) {
    uint8_t blob[0x980];
    FILE* file = std::fopen(image, "rb");
    if (!file) return 3;
    const bool valid_size = std::fread(blob, 1, sizeof blob, file) == sizeof blob && std::fgetc(file) == EOF;
    std::fclose(file);
    if (!valid_size) return 3;
    vm_base = (uint8_t*)std::calloc(1, 0x40000);
    if (!vm_base) return 3;
    fifa_install_spu_policy();
    static spu_context context;
    spu_context_init(&context, 77);
    context.image_id = 0x2da7145f; // Manifest identity derived from original SHA256.
    if (!spu_lifted_lookup(&context, 0x1d0)) return 77; // FullGame with SPU is required.
    spu_begin_image(context.image_id);
    spu_register_function(0x3d000, fixture_return); // Authored caller, outside the original module.
    spu_begin_image(0);
    const unsigned lengths[] = {0,1,2,3,15,16,17,31,32,33,127,128,255,256,2047,2048,2049,4097};
    const unsigned offsets[] = {0,1,7,15};
    const unsigned entries[] = {0x1d0, 0xb0};
    unsigned cases = 0;
    unsigned bss_checks = 0;
    for (unsigned entry : entries) for (unsigned length : lengths)
    for (unsigned source_offset : offsets) for (unsigned dest_offset : offsets) {
        for (unsigned i = 0; i < 0x4000; ++i) vm_base[0x10000 + i] = (uint8_t)(i * 37 + length * 11);
        std::vector<uint8_t> source(vm_base + 0x10000, vm_base + 0x14000);
        std::memset(vm_base + 0x20000, 0xa5, 0x4000);
        std::vector<uint8_t> expected(0x4000, 0xa5);
        const uint32_t from = 0x10100 + source_offset, to = 0x20100 + dest_offset;
        std::memcpy(expected.data() + 0x100 + dest_offset, vm_base + from, length);
        std::memset(context.ls, 0, SPU_LS_SIZE);
        std::memcpy(context.ls + 0x80, blob, sizeof blob);
        // The CRT's computed branch enters its unrolled BSS clear at 0x134
        // for this image's 0x1080-byte BSS. Exercise the real entry as well.
        if (entry == 0xb0) std::memset(context.ls + 0xa00, 0xa5, 0x1080);
        std::memset(context.gpr, 0, sizeof context.gpr);
        returned_to_caller = false;
        context.gpr[0]._u32[0] = 0x3d000;
        context.gpr[1]._u32[0] = 0x3f000;
        context.gpr[3]._u32[0] = to;
        context.gpr[4]._u32[0] = from;
        context.gpr[5]._u32[0] = length;
        context.status = SPU_STATUS_RUNNING;
        context.pc = entry;
        // The original routine spans several AOT fragments. Use the real
        // driver to drain tail transfers, just as the game's SPU runner does.
        if (spu_run_with_halt(spu_indirect_branch, &context) || !returned_to_caller) return 5;
        if (entry == 0xb0 && length == 0) {
            for (unsigned i = 0xa00; i < 0x1a80; ++i) if (context.ls[i]) return 6;
            ++bss_checks;
        }
        if (std::memcmp(vm_base + 0x20000, expected.data(), expected.size()) ||
            std::memcmp(vm_base + 0x10000, source.data(), source.size())) {
            std::fprintf(stderr, "Original SPU copy mismatch: length=%u src_offset=%u dst_offset=%u\n",
                         length, source_offset, dest_offset);
            for (unsigned i = 0; i < expected.size(); ++i) if (vm_base[0x20000 + i] != expected[i]) {
                std::fprintf(stderr, "first difference EA=0x%X expected=%02X actual=%02X\n",
                             0x20000 + i, expected[i], vm_base[0x20000 + i]);
                break;
            }
            return 4;
        }
        ++cases;
    }
    std::printf("{\"original_entries\":[\"0x1d0\",\"0xb0\"],\"cases\":%u,\"bss_checks\":%u,\"bytes_match\":true,"
                "\"source_preserved\":true,\"destination_guards\":true}\n", cases, bss_checks);
    return 0;
}
