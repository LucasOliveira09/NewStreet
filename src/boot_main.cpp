// Initial headless native boot: no renderer or fake success paths.
// Runtime interface: vendor/ps3recomp/runtime/ppu/tests/boot_main.cpp.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "ppu_recomp.h"
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <filesystem>
#include <string>

extern "C" {
uint8_t* vm_base = nullptr;
extern uint32_t ppu_vm_size;
extern const char* ppu_vfs_root;
uint32_t ppu_load_elf(const char*);
void ppu_recomp_register(void);
void ppu_hle_init(void);
void ppu_sysprx_register(void);
void ppu_fs_register(void);
void lv2_init_syscalls(void);
void ps3_hle_call(uint32_t, ppu_context*);
void ps3_indirect_call(ppu_context*);
void ppu_unlifted_stub(uint64_t, ppu_context*);
int ppu_run(uint32_t, uint32_t);
void cellGame_init_from_paramsfo(const char*);
void fifa_register_process_spawn(void);
void fifa_capture_spawn(ppu_context*);
int fifa_configure_guest_arguments(int, char**);
void fifa_dump_guest_arguments(void);
void fifa_set_disc_root(const char*);
void fifa_install_crash_diagnostics(void);
void fifa_register_prx_handlers(void);
int fifa_test_prx_registry(void);
void fifa_install_guest_callbacks(void);
int fifa_test_guest_callbacks(void);
void fifa_install_spu_policy(void);
void fifa_test_missing_spu(ppu_context*);
void fifa_test_missing_spu_indirect(ppu_context*);
int fifa_test_spu_groups(void);
int fifa_test_spu_image_mismatch(void);
int fifa_test_spu_termination(const char*);
uint64_t ppu_guest_call(uint32_t, uint64_t, uint64_t, uint64_t, uint64_t, uint64_t, uint64_t, uint64_t, uint64_t);
uint64_t ppu_guest_call_ct(uint32_t, uint32_t, uint64_t, uint64_t, uint64_t, uint64_t, uint64_t, uint64_t, uint64_t, uint64_t);
extern PPU_THREAD_LOCAL ppu_context* g_active_ctx;
}

static LONG CALLBACK commit_guest_page(EXCEPTION_POINTERS* exception) {
    auto* record = exception->ExceptionRecord;
    if (record->ExceptionCode != EXCEPTION_ACCESS_VIOLATION || record->NumberParameters < 2)
        return EXCEPTION_CONTINUE_SEARCH;
    uintptr_t fault = record->ExceptionInformation[1], base = (uintptr_t)vm_base;
    if (!vm_base || fault < base || fault - base >= 0x100000000ULL)
        return EXCEPTION_CONTINUE_SEARCH;
    // Only back valid reserved guest pages. Never turn execute faults into data.
    if (record->ExceptionInformation[0] == 8) return EXCEPTION_CONTINUE_SEARCH;
    void* page = (void*)(fault & ~uintptr_t(0xFFFF));
    if (VirtualAlloc(page, 0x10000, MEM_COMMIT, PAGE_READWRITE))
        return EXCEPTION_CONTINUE_EXECUTION;
    return EXCEPTION_CONTINUE_SEARCH;
}

static int test_missing(const char* kind) {
    ppu_context context{};
    context.lr = 0x12345678;
    context.gpr[3] = 0x1122334455667788ULL;
    if (!std::strcmp(kind, "hle")) ps3_hle_call(0xDEADBEEFu, &context);
    else if (!std::strcmp(kind, "syscall")) { context.gpr[11] = 1023; lv2_syscall(&context); }
    else if (!std::strcmp(kind, "indirect")) { context.ctr = 0x123400; ps3_indirect_call(&context); }
    else if (!std::strcmp(kind, "unlifted")) ppu_unlifted_stub(0x123400, &context);
    else if (!std::strcmp(kind, "spu-workload")) fifa_test_missing_spu(&context);
    else if (!std::strcmp(kind, "spu-indirect")) fifa_test_missing_spu_indirect(&context);
    else if (!std::strcmp(kind, "callback") || !std::strcmp(kind, "callback-ct")) {
        vm_base = (uint8_t*)std::calloc(1, 0x20000);
        if (!vm_base) return 3;
        g_active_ctx = &context;
        vm_write32(0x10000, 0x123400); vm_write32(0x10004, 0x6789);
        if (!std::strcmp(kind, "callback")) ppu_guest_call(0x10000, 0, 0, 0, 0, 0, 0, 0, 0);
        else ppu_guest_call_ct(0x123400, 0x6789, 0, 0, 0, 0, 0, 0, 0, 0);
    }
    else return 2;
    return 1; // Unsupported boundaries must terminate, never return success.
}

int main(int argc, char** argv) {
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
    setvbuf(stdout, nullptr, _IONBF, 0);
    setvbuf(stderr, nullptr, _IONBF, 0);
    fifa_install_crash_diagnostics();
    if (argc == 2 && !std::strcmp(argv[1], "--test-prx")) return fifa_test_prx_registry();
    if (argc == 2 && !std::strcmp(argv[1], "--test-callback")) return fifa_test_guest_callbacks();
    if (argc == 2 && !std::strcmp(argv[1], "--test-spu-groups")) return fifa_test_spu_groups();
    if (argc == 2 && !std::strcmp(argv[1], "--test-spu-image-mismatch")) return fifa_test_spu_image_mismatch();
    if (argc == 2 && !std::strcmp(argv[1], "--test-native-crash")) {
        RaiseException(0xE0464946u, EXCEPTION_NONCONTINUABLE, 0, nullptr);
        return 1;
    }
    if (argc == 3 && !std::strcmp(argv[1], "--test-missing")) return test_missing(argv[2]);
    if (argc == 3 && !std::strcmp(argv[1], "--test-spu-termination")) return fifa_test_spu_termination(argv[2]);
    if (argc == 2 && (!std::strcmp(argv[1], "--test-spawn") || !std::strcmp(argv[1], "--test-spawn-child"))) {
        bool child = !std::strcmp(argv[1], "--test-spawn-child");
        vm_base = (uint8_t*)std::calloc(1, 0x20000);
        if (!vm_base) return 3;
        std::strcpy((char*)vm_base + 0x10000, "/dev_bdvd/PS3_GAME/USRDIR/fifazf.self");
        std::strcpy((char*)vm_base + 0x10100, "hello world");
        std::strcpy((char*)vm_base + 0x10200, "quote\"slash\\");
        std::strcpy((char*)vm_base + 0x10300, "TEST=1");
        std::strcpy((char*)vm_base + 0x10400, "a;b");
        vm_write32(0x11000, 0x10100); vm_write32(0x11004, 0x10200);
        vm_write32(0x11100, 0x10300);
        ppu_context ctx{}; ctx.gpr[3]=0x10000; ctx.gpr[4]=0x11000;
        ctx.gpr[5]=child ? 0 : 0x11100; ctx.gpr[8]=1001;
        if (child) {
            vm_write32(0x11008, 0x10400); vm_write32(0x1100c, 0x10500);
            fifa_set_disc_root("C:/disc with spaces/");
        }
        fifa_capture_spawn(&ctx);
        return 1;
    }
    if (argc >= 3 && !std::strcmp(argv[1], "--test-argv")) {
        if (fifa_configure_guest_arguments(argc, argv)) return 2;
        fifa_dump_guest_arguments(); return 0;
    }
    if (argc < 3 || fifa_configure_guest_arguments(argc, argv)) {
        std::fprintf(stderr, "Usage: fifa_boot.exe <decrypted-elf> <disc-root>\n");
        return 2;
    }
    std::filesystem::path elf = std::filesystem::absolute(argv[1]);
    std::filesystem::path disc = std::filesystem::absolute(argv[2]);
    if (!std::filesystem::is_regular_file(elf) || !std::filesystem::is_directory(disc)) return 2;
    // A 4 GB-aligned base is required by upstream host-to-guest pointer recovery.
    for (int attempt = 0; attempt < 8 && !vm_base; ++attempt) {
        void* reservation = VirtualAlloc(nullptr, 0x200000000ULL, MEM_RESERVE, PAGE_NOACCESS);
        if (!reservation) return 3;
        uintptr_t aligned = ((uintptr_t)reservation + 0xFFFFFFFFULL) & ~uintptr_t(0xFFFFFFFFULL);
        VirtualFree(reservation, 0, MEM_RELEASE);
        vm_base = (uint8_t*)VirtualAlloc((void*)aligned, 0x100000000ULL, MEM_RESERVE, PAGE_READWRITE);
    }
    if (!vm_base) return 3;
    ppu_vm_size = 0; // 0 denotes the full 4 GB guest address space in this SDK.
    AddVectoredExceptionHandler(1, commit_guest_page);
    std::string root = disc.generic_string();
    fifa_set_disc_root(root.c_str());
    ppu_vfs_root = root.c_str();
    uint32_t entry = ppu_load_elf(elf.string().c_str());
    if (!entry) return 4;
    auto sfo = disc / "PS3_GAME/PARAM.SFO";
    if (std::filesystem::exists(sfo)) cellGame_init_from_paramsfo(sfo.string().c_str());
    ppu_recomp_register();
    ppu_hle_init();
    fifa_register_process_spawn();
    fifa_register_prx_handlers();
    ppu_sysprx_register();
    ppu_fs_register();
    lv2_init_syscalls();
    fifa_install_guest_callbacks();
    fifa_install_spu_policy();
    std::fprintf(stderr, "[fifa-boot] entry=0x%08X functions=%llu root=%s\n", entry,
                 (unsigned long long)function_table_count, root.c_str());
    int result = ppu_run(entry, 0x0FF00000u);
    std::fprintf(stderr, "[fifa-boot] entry returned rc=%d; gameplay not established\n", result);
    return result ? result : 91;
}
