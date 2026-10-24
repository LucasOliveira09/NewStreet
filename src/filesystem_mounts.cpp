#include <cstdlib>

extern "C" void cellfs_add_path_mapping(const char*, const char*);

// Context-based Open/Write and generic HLE Rename must refer to the same
// files. Match ppu_fs/sys_fs device roots, including their writable overrides.
extern "C" void fifa_configure_filesystem_mounts(const char* disc_root) {
    cellfs_add_path_mapping("/dev_bdvd/", disc_root);
    cellfs_add_path_mapping("/app_home/", disc_root);
    const char* hdd0 = std::getenv("PS3_HDD0_ROOT");
    const char* hdd1 = std::getenv("PS3_HDD1_ROOT");
    cellfs_add_path_mapping("/dev_hdd0/", hdd0 && *hdd0 ? hdd0 : disc_root);
    cellfs_add_path_mapping("/dev_hdd1/", hdd1 && *hdd1 ? hdd1 : disc_root);
}
