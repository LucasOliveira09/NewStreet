#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "ppu_recomp.h"
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <string>
#include <vector>

static std::wstring disc_root;
extern "C" void fifa_set_disc_root(const char* path) { disc_root = std::filesystem::path(path).wstring(); }

// Microsoft C argv quoting rules: parsing-c-command-line-arguments on learn.microsoft.com.
static std::wstring quote(const std::wstring& input) {
    std::wstring result = L"\"";
    size_t slashes = 0;
    for (wchar_t c : input) {
        if (c == L'\\') { ++slashes; continue; }
        result.append(slashes * (c == L'"' ? 2 : 1), L'\\');
        slashes = 0;
        if (c == L'"') result += L'\\';
        result += c;
    }
    result.append(slashes * 2, L'\\');
    return result + L'"';
}

static std::wstring environment(const wchar_t* name) {
    DWORD length = GetEnvironmentVariableW(name, nullptr, 0);
    if (!length) return {};
    std::wstring value(length, L'\0');
    GetEnvironmentVariableW(name, value.data(), length);
    value.resize(length - 1);
    return value;
}

extern "C" void fifa_launch_native_child(const char* path, const std::vector<std::string>& arguments,
                                        const std::vector<std::string>& envp, ppu_context* ctx) {
    std::wstring executable = environment(L"FIFA_NEXT_EXE"), elf = environment(L"FIFA_NEXT_ELF");
    if (executable.empty() || elf.empty()) return; // Explicit capture-only diagnostic mode.
    if (_stricmp(path, "/dev_bdvd/PS3_GAME/USRDIR/fifazf.self") || !envp.empty() || ctx->gpr[7])
        fifa_boot_missing("spawn-transport", ctx->gpr[3], ctx);
    if (!std::filesystem::is_regular_file(executable) || !std::filesystem::is_regular_file(elf))
        fifa_boot_missing("spawn-native-image", 0, ctx);
    std::wstring command = quote(executable) + L" " + quote(elf) + L" " + quote(disc_root)
                         + L" --boot-path " + quote(std::filesystem::path(path).wstring());
    for (const auto& argument : arguments)
        command += L" --guest-arg " + quote(std::filesystem::path(argument).wstring());
    // Child handoffs need their own explicit mapping; do not recursively reuse this one.
    SetEnvironmentVariableW(L"FIFA_NEXT_EXE", nullptr);
    SetEnvironmentVariableW(L"FIFA_NEXT_ELF", nullptr);
    STARTUPINFOW startup{}; startup.cb = sizeof startup;
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    startup.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    startup.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    PROCESS_INFORMATION child{};
    // CreateProcessW receives an explicit executable and a mutable command line.
    if (!CreateProcessW(executable.c_str(), command.data(), nullptr, nullptr, TRUE,
                        CREATE_NO_WINDOW, nullptr, nullptr, &startup, &child))
        fifa_boot_missing("spawn-createprocess", GetLastError(), ctx);
    CloseHandle(child.hThread);
    std::fprintf(stderr, "[fifa-native-child] pid=%lu\n", (unsigned long)child.dwProcessId);
    WaitForSingleObject(child.hProcess, INFINITE);
    DWORD result = 1; GetExitCodeProcess(child.hProcess, &result);
    CloseHandle(child.hProcess);
    std::fflush(nullptr);
    ExitProcess(result);
}
