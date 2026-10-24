#include "spu_workload.h"
#include "lv2_syscall_table.h"
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <initializer_list>

extern "C" void lv2_init_syscalls(void);
extern "C" void spu_begin_image(int);
extern "C" void spu_register_function(uint32_t, void (*)(spu_context*));
extern "C" void spu_stop(spu_context*);
extern "C" uint8_t* vm_base;
extern "C" uint32_t ppu_vm_size;

namespace {
constexpr uint32_t entry = 0x300;
void vm_write32(uint32_t address, uint32_t value) {
    for (unsigned i = 0; i < 4; ++i) vm_base[address + i] = (uint8_t)(value >> (24 - i * 8));
}
void vm_write64(uint32_t address, uint64_t value) {
    vm_write32(address, (uint32_t)(value >> 32)); vm_write32(address + 4, (uint32_t)value);
}
uint32_t vm_read32(uint32_t address) {
    uint32_t value = 0;
    for (unsigned i = 0; i < 4; ++i) value = (value << 8) | vm_base[address + i];
    return value;
}
struct Observation { uint32_t tid, group; uint8_t* ls; uint64_t argument; };
Observation observed[4]{};
std::atomic<unsigned> visits[4]{};

void worker(spu_context* ctx) {
    unsigned slot = ctx->gpr[3]._u32[1];
    if (slot < 4) {
        observed[slot] = {ctx->spu_id, ctx->spu_group_id, ctx->ls,
            ((uint64_t)ctx->gpr[3]._u32[0] << 32) | ctx->gpr[3]._u32[1]};
        visits[slot].fetch_add(1);
    }
    spu_channel_write(&ctx->ch_out_mbox, 11 + slot);
    ctx->stop_code = 0x102;
    ctx->status = SPU_STATUS_STOPPED_BY_STOP;
    spu_stop(ctx);
}

uint32_t call(uint32_t syscall, std::initializer_list<uint64_t> args) {
    ppu_context ctx{};
    unsigned i = 3;
    for (auto value : args) ctx.gpr[i++] = value;
    ctx.gpr[11] = syscall;
    lv2_syscall_dispatch(&g_lv2_syscalls, &ctx);
    return (uint32_t)ctx.gpr[3];
}
}

extern "C" int fifa_test_spu_groups(void) {
    vm_base = (uint8_t*)std::calloc(1, 0x100000);
    if (!vm_base) return 3;
    ppu_vm_size = 0x100000;
    lv2_init_syscalls();
    spu_begin_image(12345);
    spu_register_function(entry, worker);
    spu_begin_image(0);
    vm_write32(0x10004, entry); // Synthetic image, no data segments needed.
    const uint32_t numbers[] = {1, 255, 7, 2};
    uint32_t groups[3]{}, tids[4]{};
    for (unsigned group = 0; group < 3; ++group) {
        if (call(SYS_SPU_THREAD_GROUP_CREATE, {0x11000, group == 2 ? 2u : 1u, 100, 0})) return 4;
        groups[group] = vm_read32(0x11000);
        for (unsigned ordinal = 0; ordinal < (group == 2 ? 2u : 1u); ++ordinal) {
            unsigned slot = group + ordinal;
            vm_write64(0x12000, 0x1234567800000000ULL | slot);
            if (call(SYS_SPU_THREAD_INITIALIZE,
                {0x11004, groups[group], numbers[slot], 0x10000, 0, 0x12000})) return 5;
            tids[slot] = vm_read32(0x11004);
            // The caller's argument block can immediately be reused.
            vm_write64(0x12000, 0xdeadbeef);
        }
    }
    for (unsigned group = 0; group < 3; ++group) {
        if (call(SYS_SPU_THREAD_GROUP_START, {groups[group]})) return 6;
        if (call(SYS_SPU_THREAD_GROUP_JOIN, {groups[group], 0x11008, 0x1100c})) return 7;
        if (vm_read32(0x11008) != 2 || vm_read32(0x1100c) != 0) return 8;
    }
    for (unsigned slot = 0; slot < 4; ++slot) {
        auto& o = observed[slot];
        if (visits[slot] != 1 || o.tid != tids[slot] || o.group != groups[slot < 2 ? slot : 2] ||
            o.argument != (0x1234567800000000ULL | slot)) {
            std::fprintf(stderr, "SPU isolation failed at slot %u: visits=%u tid=%X expected=%X\n",
                slot, visits[slot].load(), o.tid, tids[slot]);
            return 9;
        }
        for (unsigned other = 0; other < slot; ++other)
            if (o.ls == observed[other].ls) return 10;
        if (call(SYS_SPU_THREAD_GET_EXIT_STATUS, {tids[slot], 0x11010}) ||
            vm_read32(0x11010) != 11 + slot) return 17;
    }
    // A sparse SPU number is valid; a duplicate or number >= 256 is not.
    if (call(SYS_SPU_THREAD_INITIALIZE, {0x11004, groups[2], 7, 0x10000, 0, 0x12000}) != CELL_EBUSY) return 11;
    if (call(SYS_SPU_THREAD_INITIALIZE, {0x11004, groups[2], 256, 0x10000, 0, 0x12000}) != CELL_EINVAL) return 12;
    if (call(SYS_SPU_THREAD_GROUP_CREATE, {0x11000, 1, 100, 0})) return 13;
    uint32_t empty = vm_read32(0x11000);
    if (call(SYS_SPU_THREAD_GROUP_START, {empty}) != CELL_ESTAT) return 14;
    for (auto group : groups) if (call(SYS_SPU_THREAD_GROUP_DESTROY, {group})) return 15;
    if (call(SYS_SPU_THREAD_GROUP_DESTROY, {empty})) return 16;
    std::puts("{\"groups\":3,\"threads\":4,\"isolated\":true,\"copied_arguments\":true,\"invalid_requests_rejected\":true}");
    return 0;
}
