#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <dbghelp.h>
#include "ppu_recomp.h"
#include "json_output.h"
#include <cstdio>

extern "C" PPU_THREAD_LOCAL ppu_context* g_active_ctx;

static LONG WINAPI native_crash(EXCEPTION_POINTERS* exception) {
    static volatile LONG reporting = 0;
    if (InterlockedExchange(&reporting, 1)) return EXCEPTION_EXECUTE_HANDLER;
    auto* context = g_active_ctx;
    alignas(SYMBOL_INFO) char symbol_storage[sizeof(SYMBOL_INFO) + MAX_SYM_NAME]{};
    auto* symbol = reinterpret_cast<SYMBOL_INFO*>(symbol_storage);
    symbol->SizeOfStruct = sizeof(SYMBOL_INFO);
    symbol->MaxNameLen = MAX_SYM_NAME;
    DWORD64 displacement = 0;
    bool symbols = SymInitialize(GetCurrentProcess(), nullptr, TRUE) != FALSE;
    bool resolved = symbols && SymFromAddr(GetCurrentProcess(), exception->ContextRecord->Rip,
                                           &displacement, symbol);
    std::fprintf(stderr, "[fifa-crash] {\"exception\":%lu,\"host_rip\":%llu,\"symbol\":",
        (unsigned long)exception->ExceptionRecord->ExceptionCode,
        (unsigned long long)exception->ContextRecord->Rip);
    fifa_json_string(stderr, resolved ? symbol->Name : "");
    std::fprintf(stderr, ",\"symbol_offset\":%llu,\"guest_lr\":%llu,\"guest_ctr\":%llu,\"guest_pc\":%llu,\"guest_sp\":%llu}\n",
        (unsigned long long)displacement,
        (unsigned long long)(context ? context->lr : 0),
        (unsigned long long)(context ? context->ctr : 0),
        (unsigned long long)(context ? context->cia : 0),
        (unsigned long long)(context ? context->gpr[1] : 0));
    std::fflush(stderr);
    if (symbols) SymCleanup(GetCurrentProcess());
    return EXCEPTION_EXECUTE_HANDLER;
}

extern "C" void fifa_install_crash_diagnostics(void) {
    SetUnhandledExceptionFilter(native_crash);
}
