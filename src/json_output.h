#pragma once
#include <cstdio>
#include <string>
#include <vector>

inline void fifa_json_string(FILE* stream, const std::string& value) {
    std::fputc('"', stream);
    for (unsigned char c : value) {
        if (c == '"' || c == '\\') std::fprintf(stream, "\\%c", c);
        else if (c < 32) std::fprintf(stream, "\\u%04x", c);
        else std::fputc(c, stream);
    }
    std::fputc('"', stream);
}

inline void fifa_json_array(FILE* stream, const std::vector<std::string>& values) {
    std::fputc('[', stream);
    for (size_t i = 0; i < values.size(); ++i) {
        if (i) std::fputc(',', stream);
        fifa_json_string(stream, values[i]);
    }
    std::fputc(']', stream);
}
