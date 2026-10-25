#include "rsx_texture_fingerprint.h"
#include <cstdio>
#include <cstring>
#include <vector>

// Reproduce the old cache's blind spot without a D3D device or game bytes.
static uint32_t legacy_sparse(const std::vector<uint8_t>& data) {
    uint32_t hash = 2166136261u;
    size_t step = data.size() > 4096 ? data.size() / 1024 : 4;
    for (size_t i = 0; i + 3 < data.size(); i += step) {
        uint32_t word; std::memcpy(&word, data.data() + i, sizeof word);
        hash = (hash ^ word) * 16777619u;
    }
    return hash;
}

extern "C" int fifa_test_texture_fingerprint() {
    std::vector<uint8_t> atlas(512 * 256);
    const auto sparse_before = legacy_sparse(atlas);
    const auto before = rsx_texture_fingerprint(atlas.data(), atlas.size());
    for (unsigned y = 20; y < 40; ++y)
        std::memset(atlas.data() + y * 512 + 40, 0xff, 16);
    if (legacy_sparse(atlas) != sparse_before) return 3;
    if (rsx_texture_fingerprint(atlas.data(), atlas.size()) == before) return 4;
    const auto expected = atlas;
    const auto after = rsx_texture_fingerprint(atlas.data(), atlas.size());
    if (after != rsx_texture_fingerprint(atlas.data(), atlas.size()) || atlas != expected) return 5;
    unsigned changes = 0;
    const size_t sizes[] = {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,129,512,513,131075};
    for (size_t size : sizes) {
        std::vector<uint8_t> data(size + 17, 0xa5);
        std::memset(data.data() + 9, 0, size); // Deliberately unaligned.
        const auto baseline = rsx_texture_fingerprint(data.data() + 9, size);
        const size_t offsets[] = {0, size / 2, size - 1};
        for (size_t offset : offsets) {
            data[9 + offset] = 0x71;
            if (rsx_texture_fingerprint(data.data() + 9, size) == baseline) return 6;
            data[9 + offset] = 0;
            if (rsx_texture_fingerprint(data.data() + 9, size) != baseline) return 6;
            ++changes;
        }
        for (unsigned i = 0; i < 8; ++i)
            if (data[i] != 0xa5 || data[9 + size + i] != 0xa5) return 7;
        if (data[8] != 0xa5) return 7;
    }
    std::printf("{\"old_atlas_blindspot_reproduced\":true,\"glyph_change_detected\":true,"
                "\"byte_mutations\":%u,\"stable_and_readonly\":true}\n", changes);
    return 0;
}
