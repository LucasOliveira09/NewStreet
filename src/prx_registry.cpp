// Export ABI: RPCS3 aa9ebd2f PPUModule.cpp::ppu_prx_module_info and
// lv2/sys_prx.cpp::_sys_prx_register_library. This owns real export state;
// loading/relocating an additional PRX remains a separate operation.
#include "ppu_recomp.h"
#include "ps3emu/error_codes.h"
#include "json_output.h"
#include <map>
#include <mutex>

extern "C" void ps3_hle_register_ctx(uint32_t, const char*, void (*)(ppu_context*));
extern "C" void ps3_indirect_call_to(ppu_context*, uint32_t);

struct Library {
    std::map<uint32_t, uint32_t> functions, variables;
};
static std::map<std::string, Library> libraries;
static std::mutex registry_mutex;

static bool valid_range(uint32_t address, uint64_t size) {
    return address >= 0x10000 && uint64_t(address) + size <= 0x100000000ULL;
}

extern "C" uint32_t fifa_register_library(uint32_t address, ppu_context* ctx) {
    if (!valid_range(address, 28)) return CELL_EFAULT;
    uint8_t size = vm_read8(address);
    if (size && size < 28) return CELL_EINVAL;
    uint16_t attributes = vm_read16(address + 4);
    if (!(attributes & 1)) return CELL_OK; // Non-library entries have no linkage.
    uint16_t functions = vm_read16(address + 6), variables = vm_read16(address + 8);
    if (vm_read16(address + 10)) fifa_boot_missing("prx-tls-exports", address, ctx);
    uint32_t name_address = vm_read32(address + 16);
    uint32_t nids = vm_read32(address + 20), exports = vm_read32(address + 24);
    uint64_t table_size = uint64_t(functions + variables) * 4;
    if (functions > 4096 || variables > 4096) return CELL_EINVAL;
    if (!valid_range(nids, table_size) || !valid_range(exports, table_size)) return CELL_EFAULT;
    std::string name;
    for (unsigned i = 0; i < 256; ++i) {
        if (!valid_range(name_address, i + 1)) return CELL_EFAULT;
        char c = (char)vm_read8(name_address + i);
        if (!c) break;
        name += c;
    }
    if (name.empty() || name.size() == 256) return CELL_EINVAL;
    Library pending;
    for (uint32_t i = 0; i < uint32_t(functions + variables); ++i) {
        uint32_t nid = vm_read32(nids + i * 4), target = vm_read32(exports + i * 4);
        if (!valid_range(target, i < functions ? 8 : 1)) return CELL_EFAULT;
        if (i < functions) {
            uint32_t code = vm_read32(target);
            if ((code & 3) || !valid_range(code, 4)) return CELL_EINVAL;
        }
        auto& table = i < functions ? pending.functions : pending.variables;
        if (!table.emplace(nid, target).second) return CELL_EINVAL;
    }
    {
        std::lock_guard lock(registry_mutex);
        // Like the reference library lock, an already registered name keeps
        // its existing exports. Invalid replacement metadata never modifies it.
        libraries.emplace(name, std::move(pending));
    }
    std::fprintf(stderr, "[fifa-prx] {\"name\":"); fifa_json_string(stderr, name);
    std::fprintf(stderr, ",\"functions\":%u,\"variables\":%u}\n", functions, variables);
    return CELL_OK;
}

extern "C" uint32_t fifa_find_export(const char* library, uint32_t nid, int variable) {
    std::lock_guard lock(registry_mutex);
    auto module = libraries.find(library);
    if (module == libraries.end()) return 0;
    const auto& table = variable ? module->second.variables : module->second.functions;
    auto entry = table.find(nid);
    return entry == table.end() ? 0 : entry->second;
}

extern "C" int fifa_call_export(const char* library, uint32_t nid, ppu_context* ctx) {
    uint32_t opd = fifa_find_export(library, nid, 0);
    if (!opd) return 0;
    uint64_t saved_toc = ctx->gpr[2];
    ctx->gpr[2] = vm_read32(opd + 4);
    ps3_indirect_call_to(ctx, vm_read32(opd));
    ctx->gpr[2] = saved_toc;
    return 1;
}

static void register_library_hle(ppu_context* ctx) {
    ctx->gpr[3] = (uint64_t)(int64_t)(int32_t)fifa_register_library((uint32_t)ctx->gpr[3], ctx);
}

extern "C" void fifa_register_prx_handlers(void) {
    ps3_hle_register_ctx(0x42B23552u, "sys_prx_register_library", register_library_hle);
}
