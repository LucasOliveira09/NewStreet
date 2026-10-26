#include "ppu_recomp.h"
#include "ps3emu/nid.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <initializer_list>

extern "C" void ppu_hle_init(void);
extern "C" void ps3_hle_call(uint32_t, ppu_context*);
extern "C" void fifa_register_offline_np(void);

static uint64_t call(const char* name, std::initializer_list<uint64_t> args) {
    ppu_context ctx{};
    ctx.gpr[1] = 0x2f000;
    unsigned reg = 3;
    for (auto value : args) ctx.gpr[reg++] = value;
    ps3_hle_call(ps3_compute_nid(name), &ctx);
    return ctx.gpr[3];
}

extern "C" int fifa_test_offline_np(void) {
    vm_base = (uint8_t*)std::calloc(1, 0x30000);
    if (!vm_base) return 3;
    std::memset(vm_base + 0x10000, 0xa5, 16);
    ppu_hle_init();
    fifa_register_offline_np();
    if (ps3_compute_nid("sceNpManagerGetAccountRegion") != 0xb1e0718b) return 4;
    uint32_t before = call("sceNpManagerGetAccountRegion", {0x10000, 0x10008});
    if (call("sceNpInit", {0x10000, 0x20000})) return 5;
    uint32_t invalid_country = call("sceNpManagerGetAccountRegion", {0, 0x10008});
    uint32_t invalid_language = call("sceNpManagerGetAccountRegion", {0x10000, 0});
    uint32_t offline = call("sceNpManagerGetAccountRegion", {0x10000, 0x10008});
    if (call("sceNpTerm", {})) return 6;
    uint32_t after = call("sceNpManagerGetAccountRegion", {0x10000, 0x10008});
    bool untouched = true;
    for (unsigned i = 0; i < 16; ++i) untouched &= vm_base[0x10000 + i] == 0xa5;
    std::printf("{\"before\":%u,\"invalid_country\":%u,\"invalid_language\":%u,\"offline\":%u,\"after\":%u,\"untouched\":%s}\n",
        before, invalid_country, invalid_language, offline, after, untouched ? "true" : "false");
    return 0;
}

extern "C" int fifa_test_np_message_count(void) {
    vm_base = (uint8_t*)std::calloc(1, 0x30000);
    if (!vm_base) return 3;
    std::memset(vm_base + 0x10000, 0xa5, 16);
    ppu_hle_init();
    fifa_register_offline_np();
    if (ps3_compute_nid("sceNpBasicGetMessageEntryCount") != 0xecd503de) return 4;
    bool sign_extended = true;
    auto query = [&](uint32_t type, uint32_t count) {
        uint64_t result = call("sceNpBasicGetMessageEntryCount", {type, count});
        sign_extended &= result == (uint64_t)(int64_t)(int32_t)result;
        return (uint32_t)result;
    };
    uint32_t before = query(6, 0x10004);
    uint32_t before_invalid_type = query(8, 0x10004);
    uint32_t before_null = query(6, 0);
    if (call("sceNpInit", {0x10000, 0x20000})) return 5;
    uint32_t invalid_type = query(8, 0x10004);
    uint32_t invalid_unsigned_type = query(0xffffffff, 0x10004);
    uint32_t null_count = query(6, 0);
    uint32_t offline[8];
    for (unsigned i = 0; i < 8; ++i) offline[i] = query(i, 0x10004);
    uint32_t unmapped_count = query(6, 0xdeadbeef);
    if (call("sceNpTerm", {})) return 6;
    uint32_t after = query(6, 0x10004);
    uint32_t after_invalid_type = query(8, 0x10004);
    bool untouched = true;
    for (unsigned i = 0; i < 16; ++i) untouched &= vm_base[0x10000 + i] == 0xa5;
    std::printf("{\"before\":%u,\"before_invalid_type\":%u,\"before_null\":%u,"
                "\"invalid_type\":%u,\"invalid_unsigned_type\":%u,\"null_count\":%u,\"offline_types\":[",
                before, before_invalid_type, before_null, invalid_type, invalid_unsigned_type, null_count);
    for (unsigned i = 0; i < 8; ++i) std::printf("%s%u", i ? "," : "", offline[i]);
    std::printf("],\"unmapped_count\":%u,\"after\":%u,\"after_invalid_type\":%u,"
                "\"untouched\":%s,\"sign_extended\":%s}\n", unmapped_count, after, after_invalid_type,
                untouched ? "true" : "false", sign_extended ? "true" : "false");
    return 0;
}
