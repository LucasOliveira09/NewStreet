#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "ppu_recomp.h"
#include "../vendor/ps3recomp/libs/input/cellPad.h"
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <cstring>

extern "C" void ps3_hle_register_ctx(uint32_t, const char*, void (*)(ppu_context*));

// Do not touch lazy/unmapped guest pages while diagnosing input. This observer
// only reads the current thread's already constructed device and bitset.
static bool readable(uint32_t address, size_t bytes) {
    if (!vm_base || address < 0x10000 || uint64_t(address) + bytes > 0x100000000ULL) return false;
    auto* cursor = vm_base + address;
    auto* end = cursor + bytes;
    while (cursor < end) {
        MEMORY_BASIC_INFORMATION page{};
        if (!VirtualQuery(cursor, &page, sizeof page) || page.State != MEM_COMMIT ||
            (page.Protect & (PAGE_NOACCESS | PAGE_GUARD))) return false;
        auto* next = static_cast<uint8_t*>(page.BaseAddress) + page.RegionSize;
        if (next <= cursor) return false;
        cursor = next;
    }
    return true;
}

static void observe(ppu_context* ctx) {
    // Reviewed original caller 0x1434e6c asks GetInfo2 for manager+0x5c.
    // At this point the PREVIOUS update has finished, before new pad data.
    if (ctx->lr != 0x1434eb0 || ctx->gpr[3] > 0xffffffffULL || ctx->gpr[3] < 0x1005c) return;
    const uint32_t manager = (uint32_t)ctx->gpr[3] - 0x5c;
    if (!readable(manager, 0x5c)) return;
    const uint32_t device = vm_read32(manager + 0x20); // port zero
    if (!readable(device, 0x2c)) return;
    const uint32_t status = vm_read32(device + 8);
    const uint32_t digital_count = vm_read32(device + 0x14);
    const uint32_t bits_ea = vm_read32(device + 0x20);
    const unsigned bit_bytes = digital_count > 8 ? 2 : 1;
    const bool valid_bits = digital_count >= 4 && readable(bits_ea, bit_bytes);
    const unsigned bits = valid_bits ? (vm_read8(bits_ea) |
        (bit_bytes == 2 ? vm_read8(bits_ea + 1) << 8 : 0)) : 0;
    const uint32_t pressure_count = vm_read32(device + 0x18);
    const uint32_t pressure_ea = vm_read32(device + 0x24);
    // The constructed device has four digital controls and twelve pressure
    // controls. Original handler reads button[14] at stack+0x90 for Cross,
    // writes control 14, and the setter subtracts four (pressure index 10).
    const bool valid_cross = digital_count == 4 && pressure_count >= 11 && readable(pressure_ea, 11);
    const unsigned cross = valid_cross ? vm_read8(pressure_ea + 10) : 0;
    const uint32_t packet = vm_read32(manager + 0x58);
    struct State { uint32_t device, status, count, ea, bits, packet, valid, pressure_ea, cross, valid_cross; };
    State current{device, status, digital_count, bits_ea, bits, packet, valid_bits, pressure_ea, cross, valid_cross};
    static thread_local State previous{};
    static thread_local bool seen = false;
    if (seen && !std::memcmp(&current, &previous, sizeof current)) return;
    previous = current; seen = true;
    static std::atomic_uint count{0};
    const unsigned sequence = count.fetch_add(1, std::memory_order_relaxed);
    if (sequence >= 64) return;
    std::fprintf(stderr, "[fifa-input] {\"sequence\":%u,\"phase\":\"before_input_update\","
        "\"thread\":%llu,\"manager\":%u,\"device\":%u,\"status\":%u,\"digital_count\":%u,"
        "\"bits_ea\":%u,\"bits_readable\":%s,\"digital_bits\":%u,\"last_packet\":%u,"
        "\"pressure_ea\":%u,\"cross_readable\":%s,\"cross_pressure\":%u}\n",
        sequence, (unsigned long long)ctx->thread_id, manager, device, status, digital_count,
        bits_ea, valid_bits ? "true" : "false", bits, packet,
        pressure_ea, valid_cross ? "true" : "false", cross);
    std::fflush(stderr);
}

static void get_info(ppu_context* ctx) {
    observe(ctx);
    ctx->gpr[3] = (uint32_t)cellPadGetInfo2((CellPadInfo2*)(uintptr_t)(uint32_t)ctx->gpr[3]);
}

extern "C" void fifa_install_input_observer(void) {
    if (std::getenv("FIFA_INPUT_TRACE"))
        ps3_hle_register_ctx(0xa703a51d, "cellPadGetInfo2", get_info);
}
