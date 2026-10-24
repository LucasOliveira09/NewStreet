// ABI reference: RPCS3 aa9ebd2f Modules/sys_game_.cpp and Memory/vm_ptr.h.
// Capturing a request is an explicit handoff boundary, not a successful spawn.
#include "ppu_recomp.h"
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>
#include "json_output.h"

extern "C" void ps3_hle_register_ctx(uint32_t, const char*, void (*)(ppu_context*));
extern "C" uint64_t ppu_guest_call(uint32_t, uint64_t, uint64_t, uint64_t, uint64_t,
                                  uint64_t, uint64_t, uint64_t, uint64_t);
extern "C" void fifa_launch_native_child(const char*, const std::vector<std::string>&,
                                        const std::vector<std::string>&, ppu_context*);
static uint32_t exit_callback = 0, alternate_exit_callback = 0;
static void register_exit(ppu_context* ctx) {
    if (!exit_callback) exit_callback = (uint32_t)ctx->gpr[3];
}
static void register_alternate_exit(ppu_context* ctx) {
    if (!alternate_exit_callback) alternate_exit_callback = (uint32_t)ctx->gpr[3];
}

static std::string guest_string(uint32_t address, ppu_context* ctx) {
    if (address < 0x10000u) fifa_boot_missing("spawn-string", address, ctx);
    std::string result;
    for (uint32_t i = 0; i < 4096 && uint64_t(address) + i < 0x100000000ULL; ++i) {
        char character = (char)vm_read8(address + i);
        if (!character) return result;
        result.push_back(character);
    }
    fifa_boot_missing("spawn-string", address, ctx);
    std::abort();
}

static std::vector<std::string> guest_array(uint32_t address, ppu_context* ctx) {
    std::vector<std::string> result;
    if (!address) return result;
    for (unsigned i = 0; i < 32 && uint64_t(address) + i * 4 + 4 <= 0x100000000ULL; ++i) {
        // cpptr<char> stores big-endian u32 pointers, unlike LV2 entry argv slots.
        uint32_t pointer = vm_read32(address + i * 4);
        if (!pointer) return result;
        result.push_back(guest_string(pointer, ctx));
    }
    fifa_boot_missing("spawn-array", address, ctx);
    std::abort();
}

extern "C" void fifa_capture_spawn(ppu_context* ctx) {
    auto path = guest_string((uint32_t)ctx->gpr[3], ctx);
    auto arguments = guest_array((uint32_t)ctx->gpr[4], ctx);
    auto environment = guest_array((uint32_t)ctx->gpr[5], ctx);
    std::fprintf(stderr, "[fifa-spawn] {\"path\":"); fifa_json_string(stderr, path);
    std::fprintf(stderr, ",\"argv\":"); fifa_json_array(stderr, arguments);
    std::fprintf(stderr, ",\"envp\":"); fifa_json_array(stderr, environment);
    std::fprintf(stderr, ",\"data_address\":%u,\"data_size\":%u,\"priority\":%d,\"flags\":%llu}\n",
        (uint32_t)ctx->gpr[6], (uint32_t)ctx->gpr[7], (int32_t)ctx->gpr[8],
        (unsigned long long)ctx->gpr[9]);
    std::fflush(stderr);
    // sys_game_.cpp selects the registered callback using the top flag bits.
    uint64_t flags = ctx->gpr[9];
    uint32_t callback = flags >> 62 == 0 ? exit_callback : flags >> 62 == 1 ? alternate_exit_callback : 0;
    if (callback) ppu_guest_call(callback, 0, 0, 0, 0, 0, 0, 0, 0);
    fifa_launch_native_child(path.c_str(), arguments, environment, ctx);
    std::_Exit(92);
}

extern "C" void fifa_register_process_spawn(void) {
    ps3_hle_register_ctx(0x67F9FEDBu, "sys_game_process_exitspawn2", fifa_capture_spawn);
    ps3_hle_register_ctx(0x2C847572u, "_sys_process_atexitspawn", register_exit);
    ps3_hle_register_ctx(0x96328741u, "_sys_process_at_Exitspawn", register_alternate_exit);
}
