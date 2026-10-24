#include "json_output.h"
#include <cstdint>
#include <cstdlib>
#include <cstring>

static std::vector<std::string> arguments;
static std::vector<const char*> pointers;

extern "C" int fifa_configure_guest_arguments(int argc, char** argv) {
    arguments.clear(); pointers.clear();
    if (argc == 3) return 0; // Preserve upstream defaults when no explicit vector was supplied.
    const char* boot = std::getenv("PS3_BOOT_PATH");
    arguments.emplace_back(boot && *boot ? boot : "/dev_bdvd/PS3_GAME/USRDIR/EBOOT.BIN");
    for (int i = 3; i < argc; i += 2) {
        if (i + 1 == argc) return 2;
        if (!std::strcmp(argv[i], "--boot-path")) arguments[0] = argv[i + 1];
        else if (!std::strcmp(argv[i], "--guest-arg")) arguments.emplace_back(argv[i + 1]);
        else return 2;
    }
    if (arguments.size() > 31 || arguments[0].empty()) return 2;
    for (const auto& argument : arguments) pointers.push_back(argument.c_str());
    return 0;
}

extern "C" const char* const* fifa_boot_arguments(uint32_t* count) {
    *count = (uint32_t)pointers.size();
    return pointers.empty() ? nullptr : pointers.data();
}

extern "C" void fifa_dump_guest_arguments(void) {
    fifa_json_array(stdout, arguments);
    std::fputc('\n', stdout);
}
