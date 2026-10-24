#define PPU_NO_INLINE_LOADS
#include "ppu_recomp.h"
#include <cstdio>
#include <cstdlib>

static uint8_t guest[0x20000];
extern "C" {
uint8_t* vm_base = guest;
int vm_inline_ok = 1;
uint32_t ppu_vm_size = sizeof guest;
uint32_t ppu_hle_inject_base = 0xF0000000;
uint32_t vm_read32(uint64_t address) {
    if (address + 4 > sizeof guest) std::exit(86);
    uint32_t result = 0;
    for (unsigned i = 0; i < 4; ++i) result = (result << 8) | guest[address + i];
    return result;
}
uint64_t vm_read64(uint64_t address) { return (uint64_t(vm_read32(address)) << 32) | vm_read32(address + 4); }
void vm_write64(uint64_t address, uint64_t value) {
    if (address + 8 > sizeof guest) std::exit(86);
    for (unsigned i = 0; i < 8; ++i) guest[address + i] = (uint8_t)(value >> (56 - 8 * i));
}
PPU_THREAD_LOCAL void (*g_trampoline_fn)(void*) = nullptr;
void ps3_indirect_call(ppu_context*) { std::exit(88); }
void fifa_boot_missing(const char*, uint64_t, ppu_context*) { std::exit(89); }
}

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    FILE* input = std::fopen(argv[1], "rb");
    if (!input) return 3;
    size_t bytes = std::fread(guest, 1, sizeof guest, input);
    std::fclose(input);
    if (bytes < 0x18004) return 4;
    const uint64_t values[] = {0, 1, 2, 3, 255, 0xFFFFFFFFu};
    const int64_t expected[] = {7, -9, 123, 99, 99, 99};
    for (unsigned i = 0; i < 6; ++i) {
        ppu_context ctx{};
        ctx.gpr[1] = 0x1F000; ctx.gpr[2] = 0x18000;
        ctx.gpr[3] = values[i]; ctx.gpr[31] = 0xDEADBEEF;
        function_table[0].func(&ctx);
        if ((int64_t)ctx.gpr[3] != expected[i] || ctx.gpr[1] != 0x1F000 || ctx.gpr[31] != 0xDEADBEEF)
            return 10 + i;
    }
    std::puts("6 native switch cases passed; stack and r31 preserved");
    return 0;
}
